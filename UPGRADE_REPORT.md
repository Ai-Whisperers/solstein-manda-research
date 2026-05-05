# Pipeline Upgrade Report

Built from GitHub research survey of 20+ repos across M&A scoring, company research agents, and agent evaluation frameworks.

## What Was Built (5 P0/P1 items)

### P0.1 — `scripts/rubric.py` (from: apifyforge MCP, lucy-cxy scorecard)
**Veto conditions** that auto-force dimension scores when certain triggers match:
- PE ownership → Ownership = 1 (firing for: Zenchef, Access Group, OrderYOYO, BePOS, etc.)
- VC backing → Ownership = 2 (firing for: Mews, Deliverect, Apicbase, HiJiffy)
- US HQ → Geographic = 1 (firing for: SevenRooms, Revel Systems)
- Off-market → Ownership = 1 (firing for: Horeko, Epos Now)
- Uses function-based detection to avoid false positives (doesn't match "Private" for "PE")

### P0.2 — Dimension-level validation in `validate.py` (from: Karpathy keep/discard loop)
Added dimension-by-dimension error checking to the validation dashboard. Previously: only composite error checked (threshold 0.5). Now: each dimension must be within 1.0 of John's score. Current state: 57/57 pass both levels.

### P0.3 — `scripts/quickscan.py` (from: langchain-ai/company-researcher, trysignalbase pattern)
First-pass data gathering in <10 seconds per company:
- Fetches company website
- Extracts title/description/keywords
- Detects tech stack (React, Python/Django, WordPress, Cloudflare, Mollie, Stripe, etc.)
- Finds pricing + careers pages
- Saves structured JSON for the deep-analysis agent

### P0.4 — `scripts/datasources.py` (from: apifyforge/companyscope-mcp)
Multi-source enrichment layer — 4 free sources no API key needed:
- Website scan (tech stack, description, pricing)
- Wikipedia (company description, employee count, revenue)
- GitHub API (repos, stars, languages)
- DNS/hosting detection
- Extensible to more sources

### P1 — `scripts/track.py` (from: langfuse, judgmentlabs eval patterns)
SQLite experiment tracking replacing flat TSV:
- `track.py init` — create database with experiments + deal_breakers tables
- `track.py report` — full validation report with per-company pass/fail
- `track.py dashboard` — one-line summary
- DB stores: all 8 dimension scores, composite, error, deal breakers, timestamps
- Schema designed for querying: "which agents produce best scores?", "which dimensions have highest error?"

## Research Discovered But Not Built (P2 deferred)

| Pattern | Source | Why Deferred |
|---|---|---|
| KNN similarity search | MA-target-scout | Needs all 57 companies scored (done) but visual output needed. Low marginal value. |
| Agent experiment comparison UI | langfuse/trulens | 3.2K stars, proper dashboard. Overkill for current scale but would replace track.py when we hit 500+ experiments. |
| Multi-agent DAG | agenthub, due-diligence-agents | 4 specialist agents + judge. High value but big implementation scope. |
| LLM-as-judge validation | judgmentlabs | Would replace manual validate.py comparison. Worth doing when we add new universes. |

## Current Pipeline State

```
scripts/
├── rubric.py        # Veto conditions + scoring math + dimension validation
├── quickscan.py     # <10s website scan (tech stack, pricing, description)
├── datasources.py   # Multi-source enrichment (Wikipedia, GitHub, DNS)
├── track.py         # SQLite experiment tracking + deal-breaker detection
├── validate.py      # Dashboard: 57/57 pass, 0 dim errors
├── research-all.py  # Batch verification vs John's ground truth
├── batch-score.py   # Generate scorecards from dimension data
├── generate-triplets.py  # Auto-generate corporate-history + financial-growth
├── aggregate-universe.py # JSON aggregation
└── init-universe.py # Universe creation from CSV

output/HORECA/
├── experiments.db   # SQLite tracking database
├── results.tsv      # (kept for backwards compat)
├── <57 companies>/  # deep-analysis.md + corporate-history.md + financial-growth.md
│                    # + quickscan.json + enriched.json (for researched companies)
└── Data/
    ├── horeca_data.json
    └── horeca_companies.csv
```
