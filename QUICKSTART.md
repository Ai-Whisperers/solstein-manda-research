# Quickstart

## Prerequisites

```bash
pip install playwright crewai yfinance
python3 -m playwright install chromium
```

## One-Command Research

```bash
cd /data/work/deliverables/john-pipeline

# Research a company
python3 scripts/research_pipeline.py "Booking Experts" "https://bookingexperts.com"

# Validate all results
python3 scripts/validate.py

# Generate all deal memos
python3 scripts/deal_memo.py --all
```

## Validation Dashboard

```bash
python3 scripts/validate.py
```

Output:
```
Composite pass (err≤0.5): 57/57
Dimension-level pass: ✓ PASS
Grade Distribution: A: 1, B: 3, C: 16, D: 26, F: 11
Top: Booking Experts (A, 92/100 ARS)
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

Shows: Wikipedia, GitHub, DNS, news, web search, SEC, yfinance, GLEIF data.

## Tracking

```bash
python3 scripts/track.py dashboard   # One-line summary
python3 scripts/track.py report      # Full report
```

## Meta-Analysis

```bash
python3 scripts/reflect_meta.py      # Find improvement opportunities
```

## Using as a Library

```python
from core.utils import Config, fetch, folder_from
from scoring import DIMS, compute_composite, composite_to_grade, apply_vetoes
from sources import quick_scan, enrich_company, CompanyBrowser
```

## Environment Variables

```bash
# Optional (for additional sources):
export UK_COMPANIES_HOUSE_KEY=<free_from_gov.uk>
export FINANCIAL_DATASETS_API_KEY=<free_from_financialdatasets.ai>

# Already configured:
# - GitHub token: auto-detected
# - LiteLLM proxy: 72.61.44.159:4000
# - OpenRegistry: free, no key needed
```
