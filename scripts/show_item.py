"""
show_item.py
Prints one item for hand-scoring: the prompt the model saw, the gold answer,
and the model's response.

Usage (from the project root):
    python scripts/show_item.py item_02
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/show_item.py item_02")
        return

    item_id = sys.argv[1]
    item = json.loads(
        (ROOT / "gold_set" / "items" / f"{item_id}.json").read_text(encoding="utf-8")
    )
    output = json.loads(
        (ROOT / "results" / "raw_outputs" / f"{item_id}.json").read_text(encoding="utf-8")
    )

    line = "=" * 72
    print(line)
    print(f"{item_id}  |  {item['difficulty']}  |  {item['title']}")
    print(line)
    print("\nWHAT THE MODEL SAW\n")
    print(output["prompt"])

    print("\n" + line)
    print("GOLD ANSWER")
    print(line)
    for figure in item["gold_answer"]["key_figures"]:
        print(f"  {figure['label']}: {figure['value']} {figure['unit']}")
    print(f"\nSummary: {item['gold_answer']['summary']}")
    print(f"\nMain driver: {item['gold_answer']['main_driver']}")

    print("\n" + line)
    print("MODEL RESPONSE")
    print(line)
    print(output["response"])
    print()


if __name__ == "__main__":
    main()