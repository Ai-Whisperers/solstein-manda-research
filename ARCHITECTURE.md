# M&A Research Pipeline — Architecture

## Directory Structure

```
ma-research-pipeline/
├── core/                    ← Foundation layer (no dependencies on other modules)
│   ├── __init__.py
│   ├── config.py            ← All env vars, API keys, paths (Config class)
│   ├── cache.py             ← Persistent disk cache (output/.cache/)
│   └── utils.py             ← Shared helpers: fetch, atomic_json_dump, safe_json_load
│
├── sources/                 ← Data layer (depends on core/)
│   ├── __init__.py          ← Re-exports from scripts/ for backward compatibility
│   ├── enrichment.py        ← Enrichment orchestrator (merges all sources)
│   ├── free.py              ← Free/OSS sources: SEC, yfinance, GLEIF, World Bank, DDG
│   ├── new.py               ← New sources: SIRENE, VIES, Financial Datasets, Companies House
│   ├── plus.py              ← Plus sources: Clearbit, BuiltWith, Crunchbase, Glassdoor, SerpAPI, USPTO
│   └── mcp.py               ← MCP server integrations
│
├── scoring/                 ← Analysis layer (depends on core/)
│   ├── __init__.py          ← DIMS, weights, composite, grades, vetoes, flags, kills
│
├── pipeline/                ← Orchestration layer (depends on sources/ + scoring/)
│   ├── research.py          ← run_pipeline() — ties sources → scoring → report
│   ├── reflect.py           ← Reflection loop for scorecard improvement
│   ├── valuation.py         ← DCF, LBO, comparable company analysis
│   └── crew.py              ← CrewAI multi-agent research
│
├── scripts/                 ← CLI entry points (thin wrappers)
│   ├── research_pipeline.py → pipeline/research.py
│   ├── reflect.py           → pipeline/reflect.py
│   ├── valuation.py         → pipeline/valuation.py
│   ├── research_crew.py     → pipeline/crew.py
│   ├── datasources.py       → Direct enrichment CLI
│   ├── sources_plus.py      → New source integrations
│   ├── batch-score.py       → Batch scorecard generation
│   ├── validate.py          → Validation dashboard
│   ├── track.py             → Experiment tracking (SQLite)
│   └── ...
│
├── tests/                   ← Tests mirror the structure
│   ├── test_scoring.py      → 31 tests for scoring module
│   ├── test_utils.py        → 19 tests for core/utils.py
│   └── test_cache.py        → 13 tests for core/cache.py
│
├── output/                  ← Generated data
│   ├── HORECA/              ← Per-company directories with scorecards
│   └── .cache/              ← Persistent API response cache (7-day TTL)
│
└── .env                     ← API keys (not committed)
```

## Dependency Direction

```
core → sources → scoring → pipeline
(Never circular, never backwards)
```

## Data Flow

```
1. CLI entry point → calls pipeline function
2. pipeline/research.py → sources/enrichment.py → all source modules
3. Each source → core/utils.fetch() with core/cache.py (persistent cache)
4. Enriched data → scoring module → 8-dimension scorecard
5. Scorecard → reflection loop → refined scores
6. Results written atomically to output/HORECA/<company>/
```

## 25 Data Sources

See `output/API_ROADMAP.md` for the complete list and status.
