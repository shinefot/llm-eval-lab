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

(To be added in the next commit.)

## 7. Change log

- v1: initial draft, written before any model outputs were scored.