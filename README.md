# SolStein M&A Research Pipeline

Autonomous M&A target research and scoring system. Given a company name, researches from 25+ public data sources, scores on 8 M&A dimensions, validates against ground truth, and generates investment-grade deal memos.

**Codebase**: 4,841 lines across 3 modules + 25 scripts  
**Universes**: HORECA (73 companies), MEAL_SERVICE (43), AGRO (38)  
**Data sources**: 25+ across browser, free APIs, government registries, and MCP servers  
**Validation**: 57/57 pass, 0 errors  

---

## Architecture

```
pipeline/
├── core/utils.py           # Shared: fetch(), cache, Config, path helpers
├── scoring/                # All scoring logic (135 lines)
│   └── __init__.py         # DIMS, composites, grades, vetoes, red flags, kills
├── sources/                # Data source integrations
│   ├── browser.py          # Playwright browser agent
│   ├── quickscan.py        # Quick-scan v2 (Playwright + stdlib fallback)
│   ├── enrich.py           # Multi-source enrichment
│   ├── free.py             # Free/OSS sources (SEC, yfinance, DDG, GLEIF)
│   ├── mcp.py              # MCP server integrations
│   ├── companies_house.py  # UK Companies House API
│   └── new_sources.py      # SIRENE, VIES, Financial Datasets
├── scripts/                # Pipeline scripts (import from core, scoring, sources)
├── templates/              # Markdown output templates
├── universes/              # CSV universe definitions
└── output/HORECA/          # Research outputs (57 companies)
```

### Import conventions
```python
from core.utils import fetch, Config, cached, folder_from
from scoring import DIMS, compute_composite, composite_to_grade, apply_vetoes
from sources import quick_scan, enrich_company, CompanyBrowser
```

---

## Data Source Layers

### Layer 1: Browser Automation
| Source | Module | Provides |
|---|---|---|
| Playwright browser | `sources/browser.py` | JS rendering, SPA support, tech detection (22 patterns), pricing/careers extraction |
| Cookie dismissal | `sources/browser.py` | 12+ cookie popup selector patterns |
| Stealth mode | `sources/browser.py` | UA rotation, viewport variation, automation detection bypass |

### Layer 2: Multi-Source Enrichment
| Source | Module | Data |
|---|---|---|
| Wikipedia API | `sources/enrich.py` | Company description, founded, HQ, employees, revenue |
| GitHub API | `sources/enrich.py` | Repos, stars, languages, org profile (with auth token: 5K req/hr) |
| DNS/Hosting | `sources/enrich.py` | IP, hosting provider detection (Cloudflare, AWS, GCP) |
| Web search (DDG) | `sources/free.py` | Free web search results, no API key, no rate limits |
| SEC EDGAR | `sources/free.py` | US public company filings, CIK lookup, financials |
| yfinance | `sources/free.py` | Stock profiles — sector, industry, employees, website |
| GLEIF | `sources/free.py` | EU legal entity data, LEI lookup (1.6M+ entities) |
| World Bank | `sources/free.py` | Economic indicators by country |
| Parallel fan-out | `sources/enrich.py` | 6 sources simultaneously via ThreadPool |

### Layer 3: Government Registries
| Source | Module | Coverage | Cost |
|---|---|---|---|
| UK Companies House | `sources/companies_house.py` | 5.4M UK companies, search, officers, filings | Free API key |
| French SIRENE | `sources/new_sources.py` | 25M French companies, SIREN/SIRET lookup | Free (INSEE auth) |
| VIES VAT | `sources/new_sources.py` | EU VAT validation — returns company name/address | Free, no key |

### Layer 4: MCP Servers
| Source | Module | Data | Cost |
|---|---|---|---|
| OpenRegistry | `sources/mcp.py` | 27 national registries (UK, FR, DE, IT, ES, PL, KR, CA, US) | Free (20 req/min) |
| Coresignal | `sources/mcp.py` | 74M companies, 823M employees | Free tier |
| Bright Data | `sources/mcp.py` | 200+ sources: Crunchbase, LinkedIn, ZoomInfo | Free (5K req/mo) |
| CompanyScope | `sources/mcp.py` | 8 sources aggregated | Free (25 calls/day) |
| Financial Datasets | `sources/new_sources.py` | Income statements, balance sheets, stock data | Free API key |

---

## Scoring System

### 8 Dimensions (1-5 scale)
| Dimension | Weight | What It Measures |
|---|---|---|
| Ownership attractiveness | 3x | Founder-owned? PE/VC? Succession gap? |
| Revenue scale fit | 3x | In target ARR range? Profitable? |
| Geographic fit | 3x | Primary market matches thesis? |
| Tech stack modernity | 2x | Cloud-native? Modern stack? |
| Customer lock-in | 2x | Long contracts? Deep integrations? |
| Vertical depth | 2x | Clear niche? Defensible position? |
| Integration potential | 1x | REST API? Open architecture? |
| Growth trajectory | 1x | Headcount growth? New customers? |

### Grade Tiers
| Score | Grade | ARS (0-100) | Meaning |
|---|---|---|---|
| 4.5-5.0 | A | 90-100 | Strong acquisition candidate |
| 3.5-4.49 | B | 70-89 | Viable with noted risks |
| 2.5-3.49 | C | 50-69 | Significant concerns |
| 1.5-2.49 | D | 30-49 | Major risks present |
| 0-1.49 | F | 0-29 | Critical issues — not viable |

### Auto-Vetoes (12 conditions)
- PE ownership → Ownership = 1
- VC backing → Ownership = 2
- US HQ → Geographic = 1
- Off-market → Ownership = 1

### Red Flag Scanner (6 conditions)
- Customer concentration, revenue too small, wrong geography, ownership blocked, legacy tech, no growth

### Kill Criteria (3 conditions)
- PE-owned: SolStein cannot compete with PE funds
- Wrong market: wrong geography AND small revenue
- No moat: low lock-in AND shallow vertical depth

---

## Self-Improvement Systems

### Reflection Loop
After initial scoring, identifies weak dimensions (score = 3.0 or high uncertainty), generates targeted follow-up search queries, re-researches, re-scores. Up to 3 rounds per company.

### Bilevel Meta-Analysis
Reads all experiment logs, ranks dimensions by error rate, generates improvement suggestions. Finds patterns like "we over-score Geographic fit on US companies" and suggests prompt fixes.

### Multi-Crew Consensus
Runs 2 parallel research crews, compares scores, flags disagreements >1.0. Elo-rankings track which research strategies produce most accurate scores vs ground truth.

### Self-Evaluation Abort
Checks kill criteria + red flags + research value estimation → aborts non-viable targets before wasting research budget.

---

## Quick Reference

```bash
# Run research on one company
python3 scripts/research_pipeline.py "Company Name" "https://company.com"

# Validate all results against ground truth
python3 scripts/validate.py

# Generate deal memos for all scored companies
python3 scripts/deal_memo.py --all

# Track experiments
python3 scripts/track.py dashboard
python3 scripts/track.py report

# Quick-scan a website
python3 scripts/quickscan.py "Company Name" "https://company.com"

# Multi-source enrichment
python3 scripts/datasources.py "Company Name" "https://company.com"

# Bilevel meta-analysis (find improvement opportunities)
python3 scripts/reflect_meta.py --report

# Import as library
python3 -c "
from core.utils import Config, fetch
from scoring import DIMS, compute_composite, composite_to_grade
from sources import quick_scan, enrich_company
"
```

---

## To Activate Additional Sources

```bash
# Free API keys (register at each service):
export UK_COMPANIES_HOUSE_KEY=<from companieshouse.gov.uk>
export FINANCIAL_DATASETS_API_KEY=<from financialdatasets.ai>
export APIFY_API_TOKEN=<from apify.com>        # For CompanyScope + M&A intelligence
export CORESIGNAL_API_KEY=<from coresignal.com>  # For 74M company records
export BRIGHTDATA_API_TOKEN=<from brightdata.com> # For 200+ data sources

# Already configured:
# - GitHub token: auto-detected from gh CLI
# - LiteLLM proxy: auto-detected at 72.61.44.159:4000
```

---

## File Map

### Core (shared utilities)
| File | Lines | Purpose |
|---|---|---|
| `core/utils.py` | 163 | fetch(), cache, Config, path helpers, load_john_reference |

### Scoring
| File | Lines | Purpose |
|---|---|---|
| `scoring/__init__.py` | 135 | DIMS, weights, composite, grades, vetoes, red flags, kill criteria |

### Sources (data integrations)
| File | Lines | Purpose |
|---|---|---|
| `sources/browser.py` | 264 | Playwright browser agent |
| `sources/quickscan.py` | 181 | Quick-scan v2 with auto-fallback |
| `sources/enrich.py` | 6 | Multi-source enrichment |
| `sources/free.py` | 6 | Free/OSS sources |
| `sources/mcp.py` | 6 | MCP server integrations |
| `sources/companies_house.py` | 127 | UK Companies House API |
| `sources/new_sources.py` | 6 | SIRENE, VIES, Financial Datasets |

### Scripts (pipeline orchestration)
| Script | Lines | Purpose |
|---|---|---|
| `scripts/research_pipeline.py` | 244 | End-to-end research pipeline |
| `scripts/validate.py` | 151 | Validation dashboard |
| `scripts/track.py` | 296 | SQLite experiment tracking |
| `scripts/deal_memo.py` | 156 | Deal memo generation |
| `scripts/consensus.py` | 275 | Multi-crew consensus + Elo ranking |
| `scripts/reflect.py` | 256 | Reflection loop for dimension refinement |
| `scripts/reflect_meta.py` | 236 | Bilevel meta-analysis |
| `scripts/research_crew.py` | 253 | CrewAI multi-agent research |
| `scripts/crewai_config.py` | 121 | LLM provider config (LiteLLM proxy) |
| `scripts/datasources.py` | 480 | Multi-source enrichment (original) |
| `scripts/free_sources.py` | 299 | Free/OSS sources (original) |
| `scripts/sources_mcp.py` | 210 | MCP server integrations (original) |
| `scripts/sources_new.py` | 253 | New source integrations (original) |
| `scripts/browser_research.py` | 264 | Playwright browser (original) |
| `scripts/companies_house.py` | 127 | UK Companies House (original) |
| `scripts/quickscan.py` | 181 | Quick-scan (original) |
| `scripts/rubric.py` | 196 | Scoring rubric (original) |
| `scripts/grades.py` | 50 | Grade tiers (original) |
| `scripts/generate-triplets.py` | 165 | corporate-history + financial-growth gen |
| `scripts/research-all.py` | 149 | Batch verification vs John |
| `scripts/batch-score.py` | 104 | Batch scorecard generation |
| `scripts/aggregate-universe.py` | 88 | JSON aggregation |
| `scripts/init-universe.py` | 103 | Universe initialization |
| `scripts/compare-companies.py` | 97 | Legacy comparison |

### Outputs
| Output | Count | Location |
|---|---|---|
| Deep analysis | 57 | `output/HORECA/*/deep-analysis.md` |
| Corporate history | 57 | `output/HORECA/*/corporate-history.md` |
| Financial growth | 57 | `output/HORECA/*/financial-growth.md` |
| Deal memos | 57 | `output/HORECA/*/deal-memo.md` |
| Experiment log | 57 | `output/HORECA/results.tsv` |
| SQLite database | 50 entries | `output/HORECA/experiments.db` |
| Elo rankings | 4 strategies | `output/HORECA/elo_rankings.json` |
| Aggregated JSON | 57 companies | `output/HORECA/Data/horeca_data.json` |
