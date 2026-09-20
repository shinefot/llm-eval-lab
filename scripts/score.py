"""
score.py
Scores each saved model response against a chosen version of the annotation
guidelines using two independent LLM judges. Each judge returns Pass/Fail per
criterion with a reason; the overall verdict is derived in code.

Usage (from the project root):
    python scripts/score.py v2            -> both judges, every item, guidelines v2
    python scripts/score.py v2 item_01    -> one item only, with reasons shown
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

# ---------- Settings ----------
JUDGES = {
    "judge_a": "claude-sonnet-5",
    "judge_b": "claude-opus-5",
}
MAX_TOKENS = 4000

# Each guidelines version has its own file, criteria list and Fail rule.
VERSIONS = {
    "v1": {
        "file": "annotation_guidelines_v1.md",
        "criteria": ["C1", "C2", "C3", "C4", "C5"],
        "fail_on": ["C1", "C3"],
    },
    "v2": {
        "file": "annotation_guidelines_v2.md",
        "criteria": ["C1a", "C1b", "C2", "C3", "C4", "C5"],
        "fail_on": ["C1a", "C3"],
    },
}

ROOT = Path(__file__).resolve().parent.parent
ITEMS_DIR = ROOT / "gold_set" / "items"
OUTPUTS_DIR = ROOT / "results" / "raw_outputs"
SCORES_DIR = ROOT / "results" / "scores"
GUIDELINES_DIR = ROOT / "guidelines"


def build_instructions(criteria):
    format_lines = "\n".join(f"{c} || reason || P" for c in criteria)
    return (
        "You are an evaluator scoring a model's response to a financial analysis "
        "task. Follow the annotation guidelines below exactly, including the "
        "scoring procedure and the rulings in the worked examples.\n\n"
        "Recompute every figure stated in the response from the table yourself, "
        "including figures that appear only in the commentary, before scoring "
        "the numerical criteria.\n\n"
        f"Reply with exactly {len(criteria)} lines and nothing else, one per "
        "criterion, in this format:\n"
        f"{format_lines}\n\n"
        "The last field must be P or F. Each reason is one or two sentences on a "
        "single line; for an F, quote the part of the response that failed. Do "
        "not give an overall verdict.\n\n"
        "=== ANNOTATION GUIDELINES ===\n"
    )


def build_judge_prompt(item, output):
    """The judge sees: the task as the model saw it, the gold answer, and the
    response. It does NOT see the title, trap type or design note."""
    gold = item["gold_answer"]
    figures = "\n".join(
        f"- {f['label']}: {f['value']} {f['unit']}" for f in gold["key_figures"]
    )
    return (
        "=== TASK GIVEN TO THE MODEL ===\n"
        f"{output['prompt']}\n\n"
        "=== GOLD ANSWER ===\n"
        f"Key figures:\n{figures}\n\n"
        f"Summary: {gold['summary']}\n\n"
        f"Main driver: {gold['main_driver']}\n\n"
        "=== MODEL RESPONSE TO SCORE ===\n"
        f"{output['response']}"
    )


def parse_judge_reply(text, criteria):
    """Reads the 'C1a || reason || P' lines and checks all criteria are present."""
    lookup = {c.upper(): c for c in criteria}
    scores = {}
    for line in text.splitlines():
        parts = [p.strip() for p in line.split("||")]
        if len(parts) < 3:
            continue
        criterion = lookup.get(parts[0].strip("*# ").upper())
        score = parts[-1].strip("*. ").upper()
        if criterion and score in ("P", "F"):
            scores[criterion] = {"reason": " || ".join(parts[1:-1]), "score": score}
    missing = [c for c in criteria if c not in scores]
    if missing:
        raise ValueError(f"could not read a valid score for {', '.join(missing)}")
    return scores


def derive_verdict(scores, config):
    """Section 5 of the guidelines, applied mechanically."""
    if any(scores[c]["score"] == "F" for c in config["fail_on"]):
        return "Fail"
    if any(scores[c]["score"] == "F" for c in config["criteria"]):
        return "Send back"
    return "Pass"


def main():
    args = sys.argv[1:]
    if not args or args[0] not in VERSIONS:
        print("Usage: python scripts/score.py v2   (or v1), optionally followed by an item id")
        return
    version = args[0]
    only_item = args[1] if len(args) > 1 else None
    config = VERSIONS[version]
    criteria = config["criteria"]

    load_dotenv(ROOT / ".env")
    client = Anthropic()
    guidelines_text = (GUIDELINES_DIR / config["file"]).read_text(encoding="utf-8")
    system_prompt = build_instructions(criteria) + guidelines_text

    for judge_label, judge_model in JUDGES.items():
        judge_dir = SCORES_DIR / version / judge_label
        judge_dir.mkdir(parents=True, exist_ok=True)

        for item_file in sorted(ITEMS_DIR.glob("item_*.json")):
            item = json.loads(item_file.read_text(encoding="utf-8"))
            item_id = item["id"]
            if only_item and item_id != only_item:
                continue

            score_file = judge_dir / f"{item_id}.json"
            if score_file.exists():
                print(f"SKIP  {version} {judge_label}  {item_id}  (already scored)")
                continue

            output_file = OUTPUTS_DIR / f"{item_id}.json"
            if not output_file.exists():
                print(f"MISS  {version} {judge_label}  {item_id}  (no raw output)")
                continue
            output = json.loads(output_file.read_text(encoding="utf-8"))

            reply_text = ""
            try:
                reply = client.messages.create(
                    model=judge_model,
                    max_tokens=MAX_TOKENS,
                    system=system_prompt,
                    messages=[{"role": "user", "content": build_judge_prompt(item, output)}],
                )
                reply_text = "".join(
                    block.text for block in reply.content if block.type == "text"
                )
                scores = parse_judge_reply(reply_text, criteria)
            except Exception as error:
                print(f"ERROR {version} {judge_label}  {item_id}  {error}")
                if reply_text:
                    print(f"      Judge replied: {reply_text[:400]}")
                continue

            verdict = derive_verdict(scores, config)
            record = {
                "id": item_id,
                "judge": judge_label,
                "judge_model": judge_model,
                "guidelines_version": version,
                "guidelines_file": config["file"],
                "scored_at": datetime.now(timezone.utc).isoformat(),
                "scores": scores,
                "verdict": verdict,
            }
            score_file.write_text(
                json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            summary = " ".join(f"{c}={scores[c]['score']}" for c in criteria)
            print(f"DONE  {version} {judge_label}  {item_id}  {summary}  ->  {verdict}")

            if only_item:
                for c in criteria:
                    print(f"      {c} {scores[c]['score']}: {scores[c]['reason']}")


if __name__ == "__main__":
    main()