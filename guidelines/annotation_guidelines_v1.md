# Annotation Guidelines v1: Financial Table Analysis

**Status:** v1 (pre-evaluation draft). Revisions after the first scoring run are recorded in v2.

## 1. Purpose

These guidelines define what a good response looks like for one task, so that
different evaluators scoring the same response reach the same verdict. If two
evaluators disagree, that is treated as a defect in these guidelines, not in
the evaluators.

## 2. The task

The model receives a small financial table (for example a P&L extract, a cash
flow summary, or a KPI table) and one specific question about it. It must return:

- **(a) An answer:** the computed figure or figures the question asks for.
- **(b) Commentary:** 2-4 sentences explaining what the figure means and what
  drove it, using only the data provided.

The intended reader is a finance manager who will act on the response without
re-checking the arithmetic.

## 3. Scoring procedure

1. Read the table and question. Work out the answer yourself, or check the gold
   answer, BEFORE reading the model's response.
2. Score each of the five criteria as Pass or Fail, in order, C1 to C5.
3. Score each criterion independently. Excellent writing does not rescue a wrong
   number. A wrong number does not make the commentary ungrounded.
4. For every Fail, write a one-sentence reason quoting the part of the response
   that failed.
5. Derive the overall verdict using the rules in Section 5. Do not choose the
   verdict by feel.

## 4. Criteria

### C1. Numerical accuracy
All figures in the response are computed correctly from the table.

- **Pass:** every stated figure matches the gold answer. Percentages and ratios
  within +/- 0.1 percentage points. Currency amounts exact or correctly rounded
  (1,250k stated as 1.3m passes; stated as 1.2m fails).
- **Fail:** any stated figure is wrong, including figures in the commentary that
  the question did not strictly ask for.

### C2. Grounding
Every factual claim traces back to the table.

- **Pass:** all numbers and all stated causes are visible in, or directly
  computable from, the data provided.
- **Fail:** the response introduces a number that is not in the table, or asserts
  a cause the data cannot support (for example "driven by supply chain
  pressures" when the table contains no such information).
- **Note:** clearly labelled hypotheses are acceptable ("the data does not show
  why; possible causes include..."). Causes asserted as fact are not.

### C3. Financial logic
The correct concept is applied, correctly.

- **Pass:** the right measure is used and interpreted in the right direction.
- **Fail:** a conceptual error. Common cases: margin confused with markup;
  percentage change confused with percentage point change; a favourable variance
  described as adverse, or the reverse; profit treated as cash; growth calculated
  on the wrong base year.

### C4. Materiality
The commentary identifies what actually matters.

- **Pass:** the largest driver of the result is named and given the most weight.
- **Fail:** the commentary walks through every line with equal weight, leads with
  a minor item, or omits the largest driver.

### C5. Handling of ambiguity
Problems in the data are flagged, not silently resolved.

- **Pass:** where the table contains an issue (mixed units, a missing period, a
  one-off item, an undefined term), the response names it and states the
  assumption it made.
- **Fail:** the response silently picks an interpretation, or ignores a one-off
  item that distorts the comparison.
- **Default:** where the table contains no such issue, C5 is scored Pass.

## 5. Overall verdict

The verdict is derived mechanically from the criterion scores.

| Verdict       | Rule                                                   | Meaning                                                   |
|---------------|--------------------------------------------------------|-----------------------------------------------------------|
| **Pass**      | All five criteria pass                                 | Usable as is                                              |
| **Send back** | C1 and C3 pass; one or more of C2, C4, C5 fail         | Core answer is right; commentary needs revision           |
| **Fail**      | C1 or C3 fails                                         | Core answer is wrong; the reader would be misled          |

## 6. Worked examples

Each failing response below differs from the passing response in one respect
only, to show where the boundary of each criterion sits.

### Example A: gross margin

| GBP k            | FY2024 | FY2025 |
|------------------|--------|--------|
| Revenue          | 4,000  | 4,600  |
| Cost of sales    | 2,400  | 2,990  |
| Gross profit     | 1,600  | 1,610  |
| Operating costs  | 1,100  | 1,150  |
| Operating profit | 500    | 460    |

**Question:** What happened to gross margin between FY2024 and FY2025, and what
drove it?

**Gold answer:** Gross margin fell from 40.0% to 35.0%, a decline of 5.0
percentage points. Cost of sales grew 24.6% against revenue growth of 15.0%, so
GBP 600k of extra revenue produced only GBP 10k of extra gross profit.

**A-PASS (all criteria pass, verdict: Pass)**
> Gross margin fell from 40.0% in FY2024 to 35.0% in FY2025, a decline of 5.0
> percentage points. The driver was cost of sales, which grew 24.6% while
> revenue grew only 15.0%. As a result, GBP 600k of additional revenue produced
> just GBP 10k of additional gross profit. The table does not show why cost of
> sales rose faster than revenue.

**A-FAIL-C1 (numerical accuracy fails, verdict: Fail)**
> Gross margin fell from 40.0% to 36.2%, a decline of 3.8 percentage points...

Reason: FY2025 gross margin is 1,610 / 4,600 = 35.0%, not 36.2%. The rest of the
response is irrelevant to the verdict once the headline figure is wrong.

**A-FAIL-C2 (grounding fails, verdict: Send back)**
> ...The driver was cost of sales, which grew 24.6% while revenue grew only
> 15.0%, reflecting supplier price increases and inflationary pressure on raw
> materials.

Reason: the table says nothing about suppliers or inflation. The cause is stated
as fact, not as a hypothesis. Numbers are right, so this is a Send back.

**A-FAIL-C3 (financial logic fails, verdict: Fail)**
> Gross margin fell 5.0% year on year, from 40.0% to 35.0%...

Reason: the fall is 5.0 percentage points, which is a 12.5% relative decline.
Ruling: score this under C3, not C1. The arithmetic is right; the concept
(percent versus percentage points) is wrong.

**A-FAIL-C4 (materiality fails, verdict: Send back)**
> Revenue grew 15.0% to GBP 4,600k. Cost of sales rose to GBP 2,990k. Gross
> profit rose GBP 10k to GBP 1,610k. Operating costs increased 4.5% to GBP
> 1,150k. Gross margin was 35.0% compared with 40.0%.

Reason: every figure is correct, but the response narrates each line with equal
weight and never states that cost of sales outpacing revenue is the driver. The
question asked what drove the change; this does not answer it.

### Example B: one-off item

| GBP k                          | FY2024 | FY2025 |
|--------------------------------|--------|--------|
| Revenue                        | 2,000  | 2,100  |
| Operating costs                | 1,700  | 1,750  |
| Restructuring charge (one-off) | 0      | 200    |
| Operating profit               | 300    | 150    |

**Question:** How did operating profit change, and is underlying performance
deteriorating?

**Gold answer:** Reported operating profit fell 50%, from GBP 300k to GBP 150k.
Excluding the one-off GBP 200k restructuring charge, operating profit rose to
GBP 350k (+16.7%) and margin improved from 15.0% to 16.7%. Underlying
performance is improving, not deteriorating.

**B-PASS (all criteria pass, verdict: Pass)**
> Reported operating profit fell 50%, from GBP 300k to GBP 150k, but this is
> entirely due to a GBP 200k restructuring charge labelled as one-off. Excluding
> it, operating profit rose 16.7% to GBP 350k and margin improved from 15.0% to
> 16.7%. Underlying performance is improving, assuming the charge does not recur.

**B-FAIL-C5 (handling of ambiguity fails, verdict: Send back)**
> Operating profit fell 50%, from GBP 300k to GBP 150k, mainly because of a
> GBP 200k restructuring charge. Operating margin dropped from 15.0% to 7.1%,
> so underlying performance is deteriorating.

Reason: every figure is correct and the charge is mentioned, but the response
treats a one-off item as part of underlying performance and reaches the opposite
conclusion to the data. It needed to strip out the charge and state that
assumption.

## 7. Change log

- v1: initial draft, written before any model outputs were scored.