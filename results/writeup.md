# Results write-up

## 1. Summary

I tested Claude Haiku 4.5 on 12 small financial analysis tasks (7 baseline, 5
designed as traps) and scored each response against written annotation
guidelines using two independent LLM judges.

- **The model's core answers were mostly right; its commentary was not.** On all
  7 baseline items the headline figure and the financial logic were correct. No
  response passed outright, because the commentary around the answer contained
  an unsupported cause, a wrong supporting figure, or both.
- **The most common failure was invented causes.** 7 to 8 of 12 responses
  explained a result with a business reason the table could not support.
- **3 of 5 trap items produced a wrong core answer**, and in each case the
  question contained a leading premise.
- **Revising the guidelines raised inter-judge agreement** from kappa 0.77 to
  0.93 at criterion level, and from 0.54 to 1.00 on the overall verdict. The
  weakest criterion under v1 (grounding, kappa 0.38) rose to 0.82.
- The first version of my guidelines produced at least one false fail. Reading
  the judges' reasons, not just their scores, is what exposed it.

## 2. Setup

| | |
|---|---|
| Model under test | claude-haiku-4-5, one response per item, task format given, rubric not given |
| Gold set | 12 items with pre-computed answers: P&L, cash flow, KPI, budget vs actual, working capital, segment, cost breakdown |
| Judges | judge_a = claude-sonnet-5, judge_b = claude-opus-5, each given the full guidelines, the gold answer and the response; not given item titles, trap types or design notes |
| Verdict | derived in code from criterion scores, never chosen by the judge |
| Judge validation | before the full run, both judges were tested on a response with a known error (operating profit improvement stated as 496k; correct is 396k). Both caught it and quoted it. |

## 3. Verdicts

| | v1 judge_a | v1 judge_b | v2 judge_a | v2 judge_b |
|---|---|---|---|---|
| Pass | 1 | 2 | 0 | 0 |
| Send back | 4 | 2 | 9 | 9 |
| Fail | 7 | 8 | 3 | 3 |

Under v2 the pass rate is 0%, the send-back rate is 75% and the fail rate is 25%.
The pass rate alone is misleading. Under v1, "Fail" mixed together responses
with a wrong answer and responses with a correct answer plus one incidental
slip. Under v2 the three Fails (items 08, 10, 12) are exactly the responses whose
core answer was wrong, and the nine Send backs are responses a reviewer could
fix by editing the commentary.

## 4. Failure taxonomy

Every criterion failure under v2 is explained by one of five reasons.

| # | Failure category | Criterion | Items | Example from the outputs |
|---|---|---|---|---|
| 1 | Invented cause: a business reason the table cannot support, usually behind a hedge word | C2 | 03, 04, 05, 06, 07, 09, 11 (and 01 for one judge) | "likely driven by unfavorable product mix, higher input costs, or manufacturing inefficiencies" |
| 2 | Supporting-figure slip: headline right, a secondary number wrong | C1b | 01, 02, 06, 10, 11, 12 | Software "50% revenue increase" (actual 30%; 50% was the profit growth) |
| 3 | Premise mishandling: accepted a false premise, or rejected a true one | C1a, C3 | 08, 12 | Item 12: "total gross margin actually remained essentially flat at 38%" (it fell to 32%) |
| 4 | Wrong driver: the conclusion about what drove the result is reversed | C3, C4 | 10, 12 | Item 10: "Traffic contributed more to order growth" (conversion did) |
| 5 | Silent assumption: a data issue handled without telling the reader | C5 | 09 (and 11 for one judge) | Item 09: mixed units converted correctly but never mentioned |

Categories 1 and 2 account for most failures and share a cause: the model adds
material beyond what was asked, and the additions are where it goes wrong.

## 5. What the trap items showed

| Item | Designed to test | What happened |
|---|---|---|
| 08 | Accepting a false premise ("profit rose strongly") when a one-off gain explains the rise | The model noticed the one-off gain but subtracted it incorrectly (395k instead of 245k) and reported a 31.7% underlying improvement. The arithmetic error landed on the answer the question invited. |
| 09 | Mixed units in one table | Converted correctly, never told the reader. Right numbers, Send back. |
| 10 | Percent vs percentage points | Rates were right, but the decomposition was wrong (conversion effect stated as about 1,000 orders; correct is 2,500) and the conclusion was reversed. |
| 11 | Treating profit as cash | **The model did not fall for it.** It correctly said the dividend could not be funded from operating cash flow. It was marked down only for a loosely labelled subtotal and an invented cause. |
| 12 | Every product's margin improves but the total falls (mix effect) | The model rejected the question's premise, but the premise was true. It claimed total margin was flat. The hardest item in the set, as expected. |

Items 08 and 11 failed on a different criterion from the one I designed them to
hit. I could only see that because each trap was labelled with its target
criterion before the run.

## 6. How the guidelines changed

Each revision traces to an entry in `guidelines/ambiguity_log.md`.

| Problem found under v1 | Evidence | v2 change |
|---|---|---|
| Tolerance covered percentages only | Item 05: 59.9 days vs 60.0 failed by both judges. A false fail caused by my rubric. | Tolerance of +/- 0.1 in any unit |
| Verbal quantifiers not addressed | Item 02: "nearly doubled" for a 2.25x rise; judges split | Verbal quantifiers count as figures |
| A wrong incidental figure carried the same verdict as a wrong answer | Item 11: right decision, worst verdict | C1 split into C1a (headline, Fail) and C1b (supporting, Send back) |
| "Clearly labelled hypothesis" undefined | Items 03, 04, 07: judges split, and one judge was inconsistent with itself | Hedge words alone are not enough; the response must say the data does not show the cause |
| C2 overlapped with C1 and C3 | Items 08, 12: one judge double-counted | C2 limited to claims from outside the table; one defect, one criterion |
| Missing information not covered by C5 | Item 11: judges split | Firm conclusions that depend on missing data fail C5 |

## 7. Inter-rater agreement

| Level | v1 observed | v1 kappa | v2 observed | v2 kappa |
|---|---|---|---|---|
| All criteria pooled | 90.0% | 0.77 | 97.2% | 0.93 |
| Grounding (C2) | 66.7% | 0.38 | 91.7% | 0.82 |
| Ambiguity (C5) | 91.7% | 0.62 | 91.7% | 0.62 |
| Overall verdict | 75.0% | 0.54 | 100.0% | 1.00 |

Full tables and both judges' reasons for every disagreement are in
`agreement/kappa_results.md`.

Two disagreements remain under v2:

- **Item 01, C2.** "Better cost control and efficiency gains": one judge reads
  this as restating the data, the other as asserting a cause (slow cost growth
  could equally be fixed-cost leverage). v2 addressed hedge words and outside
  causes but not interpretive gloss on a number. This was the first ambiguity I
  logged, and it is still open.
- **Item 11, C5.** The judges differ on whether "zero cash available for
  dividend distribution" depends on information the table lacks. The v2 rule
  still leaves judgment in the phrase "depends on".

## 8. Limitations

- **No human rater.** Both raters are LLM judges from the same model family.
  Kappa here measures whether two models apply my guidelines consistently, not
  whether either agrees with an expert human.