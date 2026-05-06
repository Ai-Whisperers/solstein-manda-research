# SolStein M&A Research Pipeline

[![Tests](https://img.shields.io/badge/tests-88%20passing-brightgreen)](#)
[![Python](https://img.shields.io/badge/python-3.12-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](#)
[![Data Sources](https://img.shields.io/badge/sources-25%20integrated-orange)](#)

Autonomous M&A target research and scoring engine. Given a company name, researches from **25+ public data sources**, scores on **8 M&A dimensions** (validated against 57 ground-truth companies), and produces investment-grade scorecards.

```bash
# One command to research any company
python3 scripts/research_pipeline.py "Booking Experts" "https://bookingexperts.com"
```

---

## Quick Start

```bash
pip install playwright crewai yfinance
python3 -m playwright install chromium
cp .env.example .env   # Add your API keys
python3 scripts/research_pipeline.py "Company Name"
```

**No API keys required for basic usage** — Wikipedia, GitHub, SEC EDGAR, GLEIF, Brave News, and web search all work for free.

---

## Architecture

```
core/                    ← Foundation layer (no deps on other modules)
  config.py              ← All API keys, paths, defaults. Single source of truth.
  cache.py               ← Persistent disk cache (7-day TTL, saves API credits)
  utils.py               ← fetch(), atomic_json_dump(), safe_json_load()

sources/                 ← Data layer (depends on core/)
  enrichment.py          ← Orchestrator — runs all sources, merges results
  free.py                ← Wikipedia, GitHub, SEC EDGAR, yfinance, GLEIF, Brave News, DNS
  plus.py                ← Clearbit, BuiltWith, Crunchbase, Glassdoor, SerpAPI, USPTO
  mcp.py                 ← OpenCorporates, MCP server integrations
  __init__.py            ← Backward-compat re-exports

scoring/                 ← Analysis layer (depends on core/)
  __init__.py            ← 8 dimensions, composite, grades, vetoes, red flags, kill criteria

pipeline/                ← Orchestration layer (depends on sources/ + scoring/)
  research.py            ← 5-stage pipeline: scan → enrich → score → reflect → report
  reflect.py             ← Reflection loop for dimension refinement
  valuation.py           ← DCF, LBO, comparable company analysis
  crew.py                ← CrewAI multi-agent research (11 specialist agents)

scripts/                 ← CLI entry points (thin wrappers, 5-10 lines each)
  research_pipeline.py   ← → pipeline/research.run_pipeline()
  datasources.py         ← → sources/enrichment.enrich_company()
  quickscan.py           ← → scripts/quickscan.quick_scan()
  validate.py            ← Validation dashboard
  track.py               ← SQLite experiment tracking
```

**Dependency direction**: `core → sources → scoring → pipeline → scripts` (never circular)

---

## 25+ Data Sources

| Category | Sources | Data Provided |
|---|---|---|
| **Browser** | Playwright/CloakBrowser | Tech stack (22+ patterns), pricing pages, careers, internal links |
| **Free APIs** | Wikipedia, GitHub, SEC EDGAR | Description, financial filings, repos, languages |
| **Financial** | yfinance, Financial Datasets, AbstractAPI | Stock data, income statements, revenue estimates |
| **Legal** | GLEIF, OpenCorporates, VIES, SIRENE, Companies House | Legal entity, registration, VAT validation |
| **Web** | DuckDuckGo, SerpAPI, Brave News | Web search, news, Google Knowledge Graph |
| **Company** | Clearbit, Crunchbase, Glassdoor | Funding stage, investors, ratings, CEO approval |
| **Tech** | BuiltWith | Technology categories (when key available) |
| **People** | LinkedIn (search) | Employee estimates, open roles |
| **IP** | USPTO (via SerpAPI) | Patent search results |
| **Macro** | World Bank | Economic indicators by country |

**Caching**: All API responses are cached to `output/.cache/` with 7-day TTL. Second run = zero API calls, data in milliseconds.

---

## Scoring System

### 8 Dimensions (1-5 scale)

| Dimension | Weight | What It Measures |
|---|---|---|
| Ownership attractiveness | 3× | Founder-owned? PE/VC? Succession gap? |
| Revenue scale fit | 3× | In target ARR range? Profitable? |
| Geographic fit | 3× | Benelux thesis match? |
| Tech stack modernity | 2× | Cloud-native? Modern stack? |
| Customer lock-in | 2× | Long contracts? Deep integrations? |
| Vertical depth | 2× | Clear niche? Defensible? |
| Integration potential | 1× | REST API? Open architecture? |
| Growth trajectory | 1× | Headcount growth? New customers? |

### Grades

| Score | Grade | ARS | Meaning |
|---|---|---|---|
| 4.5-5.0 | A | 90-100 | Strong acquisition candidate |
| 3.5-4.49 | B | 70-89 | Viable with noted risks |
| 2.5-3.49 | C | 50-69 | Significant concerns |
| 1.5-2.49 | D | 30-49 | Major risks present |
| 0-1.49 | F | 0-29 | Critical issues |

### Validation

Scorecards are validated against **57 hand-scored HORECA companies** (John's reference dataset). Current accuracy: **0.0016 average composite error**, **0 dimension-level errors**.

---

## Commands

```bash
# Research a company (full pipeline)
python3 scripts/research_pipeline.py "Booking Experts" "https://bookingexperts.com"

# Quick-scan (browser only)
python3 scripts/quickscan.py "Booking Experts" "https://bookingexperts.com"

# Multi-source enrichment
python3 scripts/datasources.py "Booking Experts" "https://bookingexperts.com"

# Validation dashboard
python3 scripts/validate.py

# Cache management
python3 core/cache.py                               # Show cache stats
python3 -c "from core.cache import cache_clear; cache_clear()"  # Clear all cache
```

---

## Tests

```bash
python3 -m pytest tests/ -v
```

**88 tests** across:
- `test_scoring.py` — composite, grades, vetoes, flags, kill criteria (31 tests)
- `test_utils.py` — safe JSON, folder names, atomic writes, triangulation, freshness (33 tests)
- `test_cache.py` — get/set, TTL, atomicity, stats (13 tests)
- `test_config.py` — env vars, paths, defaults (11 tests)

---

## Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

**Already configured**: AbstractAPI, GitHub token, SerpAPI, BuiltWith, Financial Datasets.

**Free to add** (sign up at each service):
- `CLEARBIT_KEY` — dashboard.clearbit.com (funding stage, raised capital)
- `CRUNCHBASE_KEY` — developers.crunchbase.com (funding rounds, investors)
- `UK_COMPANIES_HOUSE_KEY` — gov.uk (UK company data)

---

## Project Status

**Private repository** — [Ai-Whisperers/solstein-manda-research](https://github.com/Ai-Whisperers/solstein-manda-research)

| Metric | Value |
|---|---|
| Python files | 39 |
| Lines of code | 5,964 |
| Tests | 88 (100% passing) |
| Data sources | 25+ |
| Cache files | 10 (1.2 MB) |
| Validated against | 57 ground-truth companies |
| Architecture violations | 0 |

---

## License

MIT — see [LICENSE](LICENSE).
