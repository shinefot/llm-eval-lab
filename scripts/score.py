"""
score.py
Scores each saved model response against the annotation guidelines using two
independent LLM judges. Each judge returns Pass/Fail per criterion with a
reason; the overall verdict is derived in code from the rule in Section 5 of
the guidelines.

Usage (from the project root):
    python scripts/score.py            -> both judges, every item
    python scripts/score.py item_01    -> both judges, one item, with reasons shown
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
CRITERIA = ["C1", "C2", "C3", "C4", "C5"]

ROOT = Path(__file__).resolve().parent.parent
ITEMS_DIR = ROOT / "gold_set" / "items"
OUTPUTS_DIR = ROOT / "results" / "raw_outputs"
SCORES_DIR = ROOT / "results" / "scores"
GUIDELINES_FILE = ROOT / "guidelines" / "annotation_guidelines_v1.md"

JUDGE_INSTRUCTIONS = """You are an evaluator scoring a model's response to a \
financial analysis task. Follow the annotation guidelines below exactly, \
including the scoring procedure and the rulings in the worked examples.

Recompute every figure stated in the response from the table yourself, \
including figures that appear only in the commentary, before scoring C1.

Reply with exactly five lines and nothing else, one per criterion, in this format:
C1 || reason || P
C2 || reason || P
C3 || reason || P
C4 || reason || P
C5 || reason || P

The last field must be P or F. Each reason is one or two sentences on a single \
line; for an F, quote the part of the response that failed. Do not give an \
overall verdict.

=== ANNOTATION GUIDELINES ===
"""


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


def parse_judge_reply(text):
    """Reads the five 'C1 || reason || P' lines and checks all are present."""
    scores = {}
    for line in text.splitlines():
        parts = [p.strip() for p in line.split("||")]
        if len(parts) < 3:
            continue
        criterion = parts[0].strip("*# ").upper()
        score = parts[-1].strip("*. ").upper()
        if criterion in CRITERIA and score in ("P", "F"):
            scores[criterion] = {
                "reason": " || ".join(parts[1:-1]),
                "score": score,
            }
    missing = [c for c in CRITERIA if c not in scores]
    if missing:
        raise ValueError(f"could not read a valid score for {', '.join(missing)}")
    return scores


def derive_verdict(scores):
    """Section 5 of the guidelines, applied mechanically."""
    if scores["C1"]["score"] == "F" or scores["C3"]["score"] == "F":
        return "Fail"
    if any(scores[c]["score"] == "F" for c in CRITERIA):
        return "Send back"
    return "Pass"


def main():
    load_dotenv(ROOT / ".env")
    client = Anthropic()
    system_prompt = JUDGE_INSTRUCTIONS + GUIDELINES_FILE.read_text(encoding="utf-8")
    only_item = sys.argv[1] if len(sys.argv) > 1 else None

    for judge_label, judge_model in JUDGES.items():
        judge_dir = SCORES_DIR / judge_label
        judge_dir.mkdir(parents=True, exist_ok=True)

        for item_file in sorted(ITEMS_DIR.glob("item_*.json")):
            item = json.loads(item_file.read_text(encoding="utf-8"))
            item_id = item["id"]
            if only_item and item_id != only_item:
                continue

            score_file = judge_dir / f"{item_id}.json"
            if score_file.exists():
                print(f"SKIP  {judge_label}  {item_id}  (already scored)")
                continue

            output_file = OUTPUTS_DIR / f"{item_id}.json"
            if not output_file.exists():
                print(f"MISS  {judge_label}  {item_id}  (no raw output; run run_eval.py first)")
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
                scores = parse_judge_reply(reply_text)
            except Exception as error:
                print(f"ERROR {judge_label}  {item_id}  {error}")
                if reply_text:
                    print(f"      Judge replied: {reply_text[:400]}")
                continue

            verdict = derive_verdict(scores)
            record = {
                "id": item_id,
                "judge": judge_label,
                "judge_model": judge_model,
                "guidelines_file": GUIDELINES_FILE.name,
                "scored_at": datetime.now(timezone.utc).isoformat(),
                "scores": scores,
                "verdict": verdict,
            }
            score_file.write_text(
                json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            summary = " ".join(f"{c}={scores[c]['score']}" for c in CRITERIA)
            print(f"DONE  {judge_label}  {item_id}  {summary}  ->  {verdict}")

            if only_item:
                for c in CRITERIA:
                    print(f"      {c} {scores[c]['score']}: {scores[c]['reason']}")


if __name__ == "__main__":
    main()