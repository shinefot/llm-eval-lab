# llm-eval-lab

A small, end-to-end LLM evaluation project in the finance domain. It mirrors the
work of an annotation and evaluation team: write the guidelines, build a gold
set, score model outputs, analyse the failures, revise the guidelines, and
measure whether two raters agree.

## What I found

I tested Claude Haiku 4.5 on 12 financial analysis tasks (P&L, cash flow, KPI
and variance tables), 5 of them designed as traps.

- **The model's answers were mostly right; its explanations were not.** On all 7
  baseline items the headline figure and the financial logic were correct. No
  response passed outright, because the commentary added an unsupported cause, a
  wrong supporting figure, or both.
- **The most common failure was an invented cause**: a plausible business reason
  ("likely driven by higher input costs") that the table could not support.
- **Leading questions were the most dangerous input.** 3 of 5 trap items
  produced a wrong core answer, and each contained a premise in the question. In
  one case the model accepted a false premise; in another it rejected a true one.
- **Revising the guidelines raised agreement between two independent judges**
  from kappa 0.77 to 0.93 (criterion level) and from 0.54 to 1.00 (overall
  verdict). The weakest criterion, grounding, went from 0.38 to 0.82.
- **My first rubric caused a false fail** (59.9 days marked wrong against 60.0).
  I found it by reading the judges' reasons, not their scores.

Full analysis: [results/writeup.md](results/writeup.md)

## How it works

```
guidelines  ->  gold set  ->  run_eval.py  ->  score.py  ->  report.py  ->  kappa.py
(the rubric)    (12 items     (model answers,  (two LLM      (metrics and   (inter-rater
                with known     saved raw)       judges score   failure        agreement)
                answers)                        each answer)   reasons)
```

1. **Guidelines** define the task, the scoring criteria with pass/fail worked
   examples, and a mechanical rule that turns criterion scores into a verdict:
   Pass, Send back, or Fail.
2. **Gold set**: 12 items, each with a table, a question, a pre-computed answer
   and a design note. Trap items are labelled with the criterion they target.
3. **run_eval.py** sends only the table and question to the model (never the
   title, trap type or gold answer) and saves the raw response.
4. **score.py** gives two judges (Claude Sonnet 5 and Claude Opus 5) the same
   guidelines a human annotator would read, plus the gold answer. Judges score
   each criterion with a reason; the verdict is computed in code.
5. **report.py** produces pass, send-back and fail rates, failures by criterion,
   a trap check, and every failure reason.
6. **kappa.py** computes Cohen's kappa between the judges, pooled, per criterion
   and on the verdict, and lists every disagreement with both reasons.

## The revision loop

The part of this project I would point to first is the change from guidelines
v1 to v2. Scoring under v1 surfaced eight ambiguities, each recorded in
[guidelines/ambiguity_log.md](guidelines/ambiguity_log.md) with the item that
exposed it. Every change in v2 cites its log entry. I then re-scored all 12
responses under v2 to measure whether the revisions worked.

| | v1 | v2 |
|---|---|---|
| Criterion-level agreement (kappa) | 0.77 | 0.93 |
| Verdict agreement (kappa) | 0.54 | 1.00 |
| Items where the judges' verdicts differed | 3 of 12 | 0 of 12 |

Two disagreements remain under v2. Both are documented in the write-up as open
questions for a v3.

## Repo map

| Path | What it is |
|---|---|
| `guidelines/annotation_guidelines_v1.md` | First rubric, written before any outputs were scored |
| `guidelines/annotation_guidelines_v2.md` | Revised rubric, with change log |
| `guidelines/ambiguity_log.md` | Every case where v1 did not give a clear answer |
| `gold_set/items/` | 12 test items with gold answers and design notes |
| `scripts/` | `run_eval.py`, `score.py`, `report.py`, `kappa.py`, `show_item.py` |
|