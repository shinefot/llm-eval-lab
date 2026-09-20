"""
run_eval.py
Sends each gold-set item to the model under test and saves the raw response.
No scoring happens here: outputs are saved untouched so they can be scored,
re-scored, and audited later without calling the API again.

Usage (from the project root):
    python scripts\run_eval.py            -> runs every item
    python scripts\run_eval.py item_01    -> runs one item only
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

# ---------- Settings ----------
MODEL_UNDER_TEST = "claude-haiku-4-5-20251001"
MAX_TOKENS = 600

ROOT = Path(__file__).resolve().parent.parent      # the llm-eval-lab folder
ITEMS_DIR = ROOT / "gold_set" / "items"
OUTPUT_DIR = ROOT / "results" / "raw_outputs"

# The model is told the task format, but NOT the scoring rubric.
SYSTEM_PROMPT = (
    "You are a financial analyst. You will be given a small financial table "
    "and one question about it. Respond with:\n"
    "Answer: the computed figure or figures the question asks for.\n"
    "Commentary: 2-4 sentences explaining what the figures mean and what "
    "drove the result.\n"
    "Use only the data provided in the table."
)


def format_number(value):
    """Whole numbers get thousands separators (8,000); decimals stay as typed (12.0)."""
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def table_to_markdown(table):
    """Turns the table stored in the item file into a text table the model can read."""
    lines = [f"Units: {table['unit']}", ""]
    lines.append("| " + " | ".join(table["columns"]) + " |")
    lines.append("|" + "---|" * len(table["columns"]))
    for row in table["rows"]:
        cells = [row[0]] + [format_number(v) for v in row[1:]]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_prompt(item):
    """Only the table and the question go to the model.
    Title, trap type, design note and gold answer are never sent (no leakage)."""
    return f"{table_to_markdown(item['table'])}\n\nQuestion: {item['question']}"


def main():
    load_dotenv(ROOT / ".env")          # reads ANTHROPIC_API_KEY from the .env file
    client = Anthropic()                # picks the key up automatically
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    only_item = sys.argv[1] if len(sys.argv) > 1 else None
    item_files = sorted(ITEMS_DIR.glob("item_*.json"))
    print(f"Found {len(item_files)} items in {ITEMS_DIR}")

    for item_file in item_files:
        item = json.loads(item_file.read_text(encoding="utf-8"))
        if only_item and item["id"] != only_item:
            continue

        output_file = OUTPUT_DIR / f"{item['id']}.json"
        if output_file.exists():
            print(f"SKIP  {item['id']}  (output already exists; delete it to re-run)")
            continue

        prompt = build_prompt(item)
        try:
            response = client.messages.create(
                model=MODEL_UNDER_TEST,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as error:
            print(f"ERROR {item['id']}  {error}")
            continue

        response_text = "".join(
            block.text for block in response.content if block.type == "text"
        )

        record = {
            "id": item["id"],
            "model": MODEL_UNDER_TEST,
            "run_at": datetime.now(timezone.utc).isoformat(),
            "system_prompt": SYSTEM_PROMPT,
            "prompt": prompt,
            "response": response_text,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
        output_file.write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"DONE  {item['id']}  ({response.usage.output_tokens} output tokens)")

        if only_item:
            print("\n--- Prompt sent ---\n" + prompt)
            print("\n--- Response ---\n" + response_text)


if __name__ == "__main__":
    main()