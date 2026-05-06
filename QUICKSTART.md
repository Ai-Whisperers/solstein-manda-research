# Quickstart

## Prerequisites

```bash
pip install playwright crewai yfinance
python3 -m playwright install chromium
```

## One-Command Research

```bash
cd /data/work/deliverables/ma-research-pipeline

# Research a company
python3 scripts/research_pipeline.py "Booking Experts" "https://bookingexperts.com"

# Validate all results
python3 scripts/validate.py
```

## Validation Dashboard

```bash
python3 scripts/validate.py
```

Output:
```
Composite pass (err≤0.5): 57/57
Grade Distribution: A: 1, B: 3, C: 16, D: 26, F: 11
```

## Quick-Scan

```bash
python3 scripts/quickscan.py "Booking Experts" "https://bookingexperts.com"
```

Shows: title, tech stack, pricing URL, careers URL, page count. Uses Playwright with stdlib fallback.

## Multi-Source Enrichment

```bash
python3 scripts/datasources.py "Booking Experts" "https://bookingexperts.com"
```

Shows: Wikipedia, GitHub, DNS, news, web search, SEC, yfinance, GLEIF, Clearbit, BuiltWith, SerpAPI data.

## Cache Management

```bash
# See what's cached
python3 core/cache.py

# Clear all cache
python3 -c "from core.cache import cache_clear; cache_clear()"

# Clear cache older than 30 days
python3 -c "from core.cache import cache_clear; cache_clear(older_than_days=30)"
```

All API responses are cached in `output/.cache/` with 7-day TTL. Second run on any company: zero API calls.

## Using as a Library

```python
from core.utils import Config, fetch, atomic_json_dump, folder_from
from core.cache import cache_get_or_fetch
from scoring import DIMS, compute_composite, composite_to_grade, apply_vetoes
from sources import quick_scan, enrich_company, CompanyBrowser
from sources.plus import enrich_plus
```

## Environment Variables

Copy `.env.example` to `.env` or export directly:

```bash
# === HIGHLY RECOMMENDED ===
export ABSTRACT_API_KEY=your_key_here    # abstractapi.com (industry, revenue range)
export CLEARBIT_KEY=your_key_here        # dashboard.clearbit.com (funding stage, raised)
export CRUNCHBASE_KEY=your_key_here      # developers.crunchbase.com (funding rounds)
export GLASSDOOR_KEY=your_key_here       # glassdoor.com/developer (ratings, culture)

# Already set (in .env):
# - SERPAPI_KEY: Google search + Knowledge Graph
# - BUILTWITH_KEY: Tech category detection
# - GITHUB_TOKEN: 5,000 req/hr
# - FINANCIAL_DATASETS_API_KEY: US public company financials

# Optional:
export UK_COMPANIES_HOUSE_KEY=<free_from_gov.uk>
```

## Architecture

```
core/       → config, cache, utils        (foundation, no deps)
sources/    → enrichment, free, plus       (data layer, deps on core/)
scoring/    → DIMS, composite, grades      (analysis, deps on core/)
pipeline/   → research, reflect, valuation (orchestration, deps on sources/ + scoring/)
scripts/    → thin CLI wrappers            (just parse args, call pipeline/)
```
