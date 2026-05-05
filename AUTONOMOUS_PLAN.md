# Autonomous Plan: SolStein HORECA Research Pipeline

## Goal

Run the Karpathy-style autoresearch loop on all 73 HORECA companies. For each company, research using public sources, produce an 8-dimension scorecard, compare against John's ground-truth scores, and keep only if error ≤ 0.5.

## Acceptance Criteria

1. All 73 HORECA companies have a `deep-analysis.md` with scorecard
2. Each company's composite score is within 0.5 of John's ground truth
3. Results logged to `results.tsv` with all 8 dimension scores + error
4. `horeca_data.json` updated with all scorecards
5. Final report produced

## Stop Conditions

- All 73 companies processed → stop
- Same company fails 3 times in a row → skip, note in results, continue
- Resource exhaustion → stop, report progress

## Strategy

### Batch size
I'll process companies in batches of variable size. For each company:
1. Read John's ground-truth scores from `archive/john-original/horeca_json/horeca_data.json`
2. Research using web search (5-10 minutes of source gathering)
3. Score all 8 dimensions
4. Compute weighted composite
5. Compare against John's composite
6. If error ≤ 0.5 → write deep-analysis.md, log to results.tsv
7. If error > 0.5 → identify largest dimension gaps, research more, retry (max 3 attempts)
8. If still failing after 3 attempts → log with "FAIL" status, skip

### Priority order
Process companies in order of John's score (highest first) — the highest-value targets first.

### Pipeline structure:
- Company folders: `output/HORECA/<company-name>/`
- Deep analysis: `output/HORECA/<company-name>/deep-analysis.md`
- Results log: `output/HORECA/results.tsv`  
- Aggregated JSON: `output/HORECA/Data/horeca_data.json`

## Checkpoint cadence

Log progress after every 5 companies. Self-critique every 30 min.
