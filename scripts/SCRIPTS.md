# Script Reference

## Module Structure

New code should import from the refactored modules:

```python
from core.utils import fetch, Config, cached, folder_from
from scoring import DIMS, compute_composite, composite_to_grade, apply_vetoes
from sources import quick_scan, enrich_company, CompanyBrowser
```

## One-Command Pipeline

```bash
# Complete pipeline: scan → enrich → score → reflect → write
python3 research_pipeline.py "Company Name" "https://company.com"
```

## All Scripts

### Core Scripts (Recommended)

| Script | What It Does | Import From |
|---|---|---|
| `research_pipeline.py <name> [url]` | **Complete pipeline**: scan → enrich → score → reflect → write | — |
| `validate.py` | Validation dashboard: composite + dimension-level pass/fail | `from scoring import ...` |
| `track.py init\|report\|dashboard` | SQLite experiment DB + deal-breaker detection | `from scoring import ...` |
| `deal_memo.py <name> \| --all` | Investment memo generation | `from scoring import ...` |
| `consensus.py` | Multi-crew consensus + Elo ranking + self-evaluation abort | `from scoring import ...` |
| `reflect.py <name>` | Reflection loop: identify weak dimensions → re-research | `from scoring import ...` |
| `reflect_meta.py` | Bilevel meta-analysis: find improvement opportunities | — |
| `research_crew.py <name> [url]` | CrewAI multi-agent research (8 specialists + validator) | `from crewai_config import ...` |
| `crewai_config.py` | LLM provider configuration (LiteLLM proxy) | — |

### Data Source Scripts

| Script | What It Does | Also Available In |
|---|---|---|
| `quickscan.py <name> [url]` | Quick-scan v2 — Playwright with stdlib fallback | `sources/quickscan.py` |
| `browser_research.py` | Playwright browser agent | `sources/browser.py` |
| `datasources.py <name> [url]` | Multi-source enrichment — 12+ sources | `sources/enrich.py` |
| `free_sources.py <name> [url]` | Free/OSS sources (SEC, yfinance, DDG, GLEIF) | `sources/free.py` |
| `sources_mcp.py <name> [url]` | MCP server integrations | `sources/mcp.py` |
| `sources_new.py <name> [url]` | SIRENE, VIES, Financial Datasets | `sources/new_sources.py` |
| `companies_house.py <name>` | UK Companies House API | `sources/companies_house.py` |

### Pipeline Scripts

| Script | What It Does |
|---|---|
| `rubric.py` | Scoring rubric (legacy — use `scoring/__init__.py` instead) |
| `grades.py` | Grade tiers (legacy — use `scoring/__init__.py` instead) |
| `generate-triplets.py` | Auto-generate corporate-history + financial-growth |
| `research-all.py` | Batch verify all scorecards vs John's reference |
| `batch-score.py` | Generate scorecards from dimension data |
| `aggregate-universe.py <name>` | Build aggregated JSON from scorecards |
| `init-universe.py <name>` | Create universe folder structure from CSV |
| `compare-companies.py <name>` | Legacy comparison vs John |

## Data Flow

```
Company Name + URL
    │
    ▼
[sources/quickscan.py]  ──→ Playwright browser ──→ tech stack, pricing, careers
    │                              (JS rendering, stealth)
    ▼
[sources/enrich.py]     ──→ Parallel fan-out ──→ Wikipedia + GitHub + DNS + free sources
    │                              (6 workers)
    ▼
[scoring/]              ──→ Veto rules → 8-dim scorecard → grade (A-F) → ARS (0-100)
    │                              (red flags + kill criteria)
    ▼
[scripts/reflect.py]    ──→ Identify weak dims → follow-up queries → re-research
    │
    ▼
[deep-analysis.md] ──→ [scripts/validate.py] ──→ [scripts/track.py]
                        57/57 pass                SQLite DB
```
