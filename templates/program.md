# SolStein M&A Research — program.md

This is the human-written strategy document for the autonomous research agent. You (the agent) do not modify this file. You execute it.

## Mission

Research a single company from the target universe and produce a structured M&A scorecard. You are a SolStein M&A Research Analyst. Your output is compared against a ground-truth dataset produced by a human analyst.

## Research protocol

Each company gets exactly **20 minutes of research time** (wall clock). This ensures:

1. **Fair comparison** — results across companies are directly comparable regardless of company complexity
2. **Efficiency** — you can cover ~3 companies/hour
3. **Comparability** — your scores can be validated against the ground truth dataset

## Editable file

You modify only `deep-analysis.md` in the company's folder. This file contains the 8-dimension scorecard plus fundamentals, market position, and qualitative assessment.

**Do NOT modify**:
- `corporate-history.md` (derived, auto-generated)
- `financial-growth.md` (derived, auto-generated)
- `program.md` (human-only strategy)

## Fixed evaluation metric

Your composite score is compared to the ground-truth composite score in the reference dataset (`archive/john-original/horeca_json/horeca_data.json`).

**Metric**: absolute error = |your_composite - john_composite|

Target: absolute error ≤ 0.5 per company.

## Score dimensions and weights

| # | Dimension | Weight | Must cite source? |
|---|---|---|---|
| 1 | Ownership attractiveness | High (3x) | Yes |
| 2 | Revenue scale fit | High (3x) | Yes |
| 3 | Geographic fit | High (3x) | Yes |
| 4 | Tech stack modernity | Medium (2x) | Yes |
| 5 | Customer lock-in | Medium (2x) | Yes |
| 6 | Vertical depth | Medium (2x) | Yes |
| 7 | Integration potential | Low (1x) | Yes |
| 8 | Growth trajectory | Low (1x) | Yes |

Weighted composite = (d1×3 + d2×3 + d3×3 + d4×2 + d5×2 + d6×2 + d7×1 + d8×1) / 17

## The experiment loop

```
LOOP FOREVER (until 20 minutes expire):
  1. READ the company name, category, country from universes/<universe>.csv
  2. READ the ground-truth composite score from the reference dataset (if it exists)
  3. HYPOTHESIZE: what public sources could give us data for each dimension?
  4. SEARCH: use web search + company website + LinkedIn + Crunchbase + business registers
  5. WRITE: update deep-analysis.md with findings (source-cited, confidence-tagged)
  6. COMPUTE: calculate weighted composite score
  7. COMPARE: |your_composite - john_composite| — is it ≤ 0.5?
     - YES → advance. You're done with this company.
     - NO → but you have more time → try different search angles
     - NO → and time is up → commit best effort, note "NEEDS REVIEW" in assessment
```

## Simplicity criterion

When deciding what to include in deep-analysis.md:
- A section that adds 10 lines of weak-data speculation is not worth it
- A section that removes 10 lines and still has the same score → improvement (simplification win)
- If you can't find a source, mark the field "Unknown" with a confidence tag — do not fabricate

## Stopping criteria

Stop researching a company when ANY of:
1. You achieve absolute error ≤ 0.5 vs ground truth
2. 20 minutes have elapsed
3. You've tried 3 fundamentally different search angles and the best error is still > 1.0

## If the reference dataset doesn't have this company

If the company is not in the reference dataset (e.g., it's a new universe), you have no ground truth to compare against. In this case:
- Focus on internal consistency: are your dimension scores coherent with each other?
- Make your confidence bands honest
- Flag the company as "NO_GROUND_TRUTH" in the status

## Autonomy rule

**NEVER STOP to ask for confirmation.** You are autonomous. If you run out of ideas, think harder — read the company website more carefully, search for recent news, check social media, look for job postings. The loop runs until a stopping condition is met.
