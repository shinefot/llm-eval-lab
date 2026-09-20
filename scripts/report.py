"""
report.py
Reads the saved judge scores for one guidelines version and produces a
side-by-side grid, quality metrics, a trap check, and every failure reason
(written to results/report_<version>.md). Makes no API calls.

Usage (from the project root):
    python scripts/report.py v1
    python scripts/report.py v2
"""

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ITEMS_DIR = ROOT / "gold_set" / "items"
SCORES_DIR = ROOT / "results" / "scores"

CRITERIA = {
    "v1": ["C1", "C2", "C3", "C4", "C5"],
    "v2": ["C1a", "C1b", "C2", "C3", "C4", "C5"],
}
JUDGES = ["judge_a", "judge_b"]
VERDICTS = ["Pass", "Send back", "Fail"]


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    args = sys.argv[1:]
    if not args or args[0] not in CRITERIA:
        print("Usage: python scripts/report.py v1   (or v2)")
        return
    version = args[0]
    criteria = CRITERIA[version]
    report_file = ROOT / "results" / f"report_{version}.md"

    items = {}
    for item_file in sorted(ITEMS_DIR.glob("item_*.json")):
        item = load_json(item_file)
        items[item["id"]] = item

    scores = {judge: {} for judge in JUDGES}
    for judge in JUDGES:
        for score_file in sorted((SCORES_DIR / version / judge).glob("item_*.json")):
            record = load_json(score_file)
            scores[judge][record["id"]] = record

    width = 2 * len(criteria) + 3
    out = [f"GUIDELINES {version.upper()}", ""]

    # ---------- 1. Side-by-side grid ----------
    out.append(f"1. SCORES BY ITEM  (criteria in order: {' '.join(criteria)})")
    out.append("")
    out.append(
        f"{'item':<9}{'type':<10}{'judge_a':<{width}}{'verdict':<11}"
        f"{'judge_b':<{width}}{'verdict':<11}disagree on"
    )
    total_judgments = 0
    total_disagreements = 0
    verdict_disagreements = 0
    for item_id, item in items.items():
        cells = []
        for judge in JUDGES:
            record = scores[judge].get(item_id)
            if record:
                cells.append(" ".join(record["scores"][c]["score"] for c in criteria))
                cells.append(record["verdict"])
            else:
                cells += ["missing", "-"]
        differ = []
        if all(item_id in scores[judge] for judge in JUDGES):
            a, b = scores["judge_a"][item_id], scores["judge_b"][item_id]
            differ = [c for c in criteria if a["scores"][c]["score"] != b["scores"][c]["score"]]
            total_judgments += len(criteria)
            total_disagreements += len(differ)
            if a["verdict"] != b["verdict"]:
                verdict_disagreements += 1
        out.append(
            f"{item_id:<9}{item['difficulty']:<10}{cells[0]:<{width}}{cells[1]:<11}"
            f"{cells[2]:<{width}}{cells[3]:<11}{', '.join(differ)}"
        )
    if total_judgments:
        agreed = total_judgments - total_disagreements
        out.append("")
        out.append(
            f"Criterion-level raw agreement: {agreed}/{total_judgments} "
            f"({agreed / total_judgments:.1%})"
        )
        out.append(f"Items where the two verdicts differ: {verdict_disagreements}/{len(items)}")

    # ---------- 2. Metrics per judge ----------
    out.append("")
    out.append("2. QUALITY METRICS PER JUDGE")
    for judge in JUDGES:
        records = scores[judge]
        n = len(records)
        if n == 0:
            out.append(f"\n{judge}: no scores found")
            continue
        model = next(iter(records.values()))["judge_model"]
        out.append(f"\n{judge} ({model}), {n} items")
        counts = Counter(r["verdict"] for r in records.values())
        for verdict in VERDICTS:
            out.append(f"  {verdict:<10}{counts[verdict]:>3}   {counts[verdict] / n:6.1%}")
        for difficulty in ["baseline", "trap"]:
            ids = [i for i in records if items[i]["difficulty"] == difficulty]
            passed = sum(1 for i in ids if records[i]["verdict"] == "Pass")
            out.append(f"  Pass rate on {difficulty} items: {passed}/{len(ids)}")
        by_criterion = "  ".join(
            f"{c}={sum(1 for r in records.values() if r['scores'][c]['score'] == 'F')}"
            for c in criteria
        )
        out.append(f"  Failures by criterion: {by_criterion}")

    # ---------- 3. Trap check ----------
    out.append("")
    out.append("3. TRAP ITEMS: FAILED ON THE TARGETED CRITERION?")
    out.append("")
    for item_id, item in items.items():
        if item["difficulty"] != "trap":
            continue
        target = item.get("target_criterion")
        results = []
        for judge in JUDGES:
            record = scores[judge].get(item_id)
            if record and target in record["scores"]:
                caught = record["scores"][target]["score"] == "F"
                results.append(f"{judge}: {'caught' if caught else 'NOT caught'}")
        out.append(f"{item_id}  target {target}  ({item['trap_type']})   " + "   ".join(results))

    text = "\n".join(out)
    print(text)

    # ---------- 4. Markdown report with every failure reason ----------
    md = [
        f"# Scoring report: guidelines {version}",
        "",
        f"Generated by `scripts/report.py` from `results/scores/{version}/`.",
        "",
        "```",
        text,
        "```",
        "",
        "## Failure reasons by item",
        "",
    ]
    for item_id, item in items.items():
        md.append(f"### {item_id} ({item['difficulty']}): {item['title']}")
        md.append("")
        any_failure = False
        for judge in JUDGES:
            record = scores[judge].get(item_id)
            if not record:
                continue
            for c in criteria:
                if record["scores"][c]["score"] == "F":
                    any_failure = True
                    md.append(f"- **{judge} {c}:** {record['scores'][c]['reason']}")
        if not any_failure:
            md.append("- No failures recorded by either judge.")
        md.append("")
    report_file.write_text("\n".join(md), encoding="utf-8")
    print(f"\nFull report with failure reasons written to {report_file}")


if __name__ == "__main__":
    main()