# Autonomous Plan V2 — Pipeline Upgrades

## Goal
Implement the top 5 high-priority upgrades from the GitHub research survey. Build them, test them against the existing HORECA dataset, and document results.

## Priority-ordered work items

### P0 — Critical (implement now)
1. **Veto/auto-pass conditions** — hard-code rules that force dimension scores: PE-owned → Ownership=1, US HQ → Geographic≤2, bootstrapped 15+ yrs → Revenue≥3
2. **Dimension-level validation** — the keep/discard loop must check individual dimension errors, not just composite
3. **Quick-scan pre-pass** — automated company website crawl data extraction before deep-analysis
4. **12-source data layer** — structured data fetching from free public sources

### P1 — Important
5. **SQLite tracking** — replace flat TSV with queryable database
6. **Deal-breaker detection** — auto-flag companies that should be skipped
7. **Similarity search** — KNN to find comparable companies

## Acceptance Criteria
- Veto conditions produce correct scores for known cases (Zenchef=PE→Ownership=1, Mews=global→Geo≤2)
- validate.py still shows 57/57 pass after changes
- quick-scan produces structured output for any company in <60 seconds
- SQLite DB replaces TSV with same data

## Stop Conditions
- All P0 items done → good checkpoint. P1 if time permits.
- Same error 3 times → document and skip.
