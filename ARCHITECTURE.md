# Architecture

## Module Structure

```
pipeline/
│
├── core/                          # Shared infrastructure
│   ├── __init__.py
│   └── utils.py                   # fetch(), cached(), Config, path helpers
│       ├── fetch(url)             # HTTP GET with rotating user-agents
│       ├── fetch_parallel(items)  # ThreadPool-based parallel fetches
│       ├── cached(ttl)            # Decorator: cache function results
│       ├── Config class           # Centralized API keys from env
│       │   ├── github_token()
│       │   ├── litellm_key()
│       │   ├── companies_house_key()
│       │   └── financial_datasets_key()
│       ├── folder_from(name)      # Company name → folder name
│       └── load_john_reference()  # Ground truth data loader
│
├── scoring/                       # Scoring system
│   └── __init__.py                # All scoring in one place
│       ├── DIMS, WEIGHTS          # 8 dimensions + weights
│       ├── compute_composite()    # Weighted average 1-5
│       ├── composite_to_grade()   # 1-5 → Grade A-F + ARS 0-100
│       ├── apply_vetoes()         # 12 auto-veto conditions
│       ├── scan_red_flags()       # 6 warning conditions
│       └── check_kill_criteria()  # 3 auto-reject conditions
│
├── sources/                       # Data source integrations
│   ├── __init__.py                # Unified exports
│   ├── browser.py                 # Playwright browser automation
│   ├── quickscan.py               # Quick website scan (Playwright + fallback)
│   ├── enrich.py                  # Multi-source enrichment (wrapper)
│   ├── free.py                    # Free/OSS sources (wrapper)
│   ├── mcp.py                     # MCP server integrations (wrapper)
│   ├── companies_house.py         # UK Companies House API
│   └── new_sources.py             # SIRENE, VIES, Financial Datasets
│
├── scripts/                       # Pipeline scripts
│   ├── research_pipeline.py       # End-to-end: scan → enrich → score → reflect → write
│   ├── validate.py                # Validation dashboard
│   ├── track.py                   # SQLite experiment tracking
│   ├── deal_memo.py               # Investment memo generation
│   ├── consensus.py               # Multi-crew consensus + Elo ranking
│   ├── reflect.py                 # Reflection loop for weak dims
│   ├── reflect_meta.py            # Bilevel outer-loop meta-analysis
│   ├── research_crew.py           # CrewAI multi-agent research (8 agents)
│   ├── crewai_config.py           # LLM provider config
│   └── ... (legacy entrypoints)
│
├── templates/                     # Markdown output templates
├── universes/                     # Universe CSVs (horeca, meal-service, agro)
└── output/HORECA/                 # Research outputs
```

## Data Flow

```
Company Name + URL
    │
    ▼
[sources/quickscan.py]  ──→ Playwright browser ──→ tech stack, pricing, careers
    │                              (JS rendering, stealth mode, cookie dismissal)
    ▼
[sources/enrich.py]     ──→ Parallel fan-out (6 sources) ──→ Wikipedia, GitHub, DNS
    │                              (ThreadPool with 6 workers)
    ▼
[sources/free.py]       ──→ Free sources ──→ SEC EDGAR, yfinance, DDG search, GLEIF
    │                              (zero cost, no API keys)
    ▼
[scoring/]              ──→ Veto rules applied ──→ 8-dimension scorecard
    │                              (12 veto conditions, 6 red flags, 3 kill criteria)
    ▼
[scripts/reflect.py]    ──→ Reflection loop ──→ Identify gaps → generate queries → re-research
    │                              (up to 3 rounds, targets weak dimensions)
    ▼
[deep-analysis.md]      ──→ [scripts/validate.py] ──→ [scripts/track.py]
                             57/57 pass                    SQLite DB
```

## Import Graph

```
core/utils.py            # No dependencies on other pipeline modules
    ↑
scoring/__init__.py      # No dependencies on other pipeline modules
    ↑
sources/*.py             # May import from core.utils
    ↑
scripts/*.py             # Import from core, scoring, sources
```

## Key Design Decisions

1. **core/utils.py as single shared module** — fetch, cache, UA rotation, Config, path helpers all in one place. Every script that needs HTTP, caching, or config imports from here.

2. **scoring/ as single source of truth** — DIMS, weights, composite, grades, vetos, flags, kills all in one file. Eliminated the previous split between rubric.py and grades.py which had overlapping logic.

3. **sources/ for all data integrations** — each data source is a module with a focused purpose. `__init__.py` provides clean imports. Original scripts in `scripts/` still work for backward compatibility.

4. **No circular dependencies** — core → scoring → sources → scripts forms a clean dependency chain with no cycles.

5. **Backward compatible** — old scripts in `scripts/` still work. New code should import from `core`, `scoring`, `sources`.
