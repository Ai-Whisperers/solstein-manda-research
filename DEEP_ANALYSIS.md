# M&A Research Pipeline — Deep Analysis & Future Roadmap

**Analyzed**: 2026-05-06 | **Files**: 37 | **Lines**: 5,920 | **Tests**: 63

---

## Current State Assessment

The previous refactor (commit `d739965`) fixed the critical problems:
- ✅ **Architecture clean**: `core → sources/scoring → pipeline → scripts` — zero layer violations
- ✅ **No duplicated files**: All `scripts/` vs `sources/` duplicates deleted
- ✅ **No hardcoded secrets**: GitHub token and LiteLLM key removed from source
- ✅ **Atomic writes everywhere**: No more corrupted JSON on crash
- ✅ **Tests exist**: 63 tests (7.3% ratio, up from 0.6%)
- ✅ **Persistent cache**: API responses cached with 7-day TTL
- ✅ **11 dead files deleted**: ~2,500 lines removed

---

## What's Still Wrong

### 1. Architecture: Good bones, unfinished restructuring

**Problem**: The `pipeline/` directory has the moved logic, but files in `scripts/` ALSO contain the real implementations. The CLI wrappers should be the ONLY code in `scripts/`, but:
- `scripts/datasources.py` (523 lines) — the actual enrichment orchestrator lives here, NOT in `sources/`
- `scripts/free_sources.py` (336 lines) — the actual free sources live here
- `scripts/sources_plus.py` (443 lines) — the actual plus sources live here
- `scripts/sources_new.py` (287 lines) — the actual new sources live here
- `scripts/sources_mcp.py` (212 lines) — the actual MCP sources live here
- `scripts/companies_house.py` (130 lines) — the actual Companies House code lives here

**What should happen**: Move ALL real implementations to `sources/enrichment.py`, `sources/free.py`, `sources/plus.py`, `sources/new.py`, `sources/mcp.py`. Make `scripts/` contain ONLY thin CLI wrappers (5 lines each).

**Why it matters**: Someone grepping for enrichment code finds it in `scripts/` which semantically means "CLI entry points". It's misleading.

### 2. Datasources.py is a monolith (523 lines, #1 largest file)

**Problem**: `scripts/datasources.py` contains:
- Generic fetch utilities (should be in `core/utils.py`)
- Wikipedia integration (should be in `sources/free.py`)
- GitHub integration (should be in `sources/free.py`)
- Brave News (should be in `sources/free.py`)
- Crunchbase HTML scraping (should be in `sources/plus.py`)
- OpenCorporates (should be in `sources/mcp.py`)
- Hosting detection (should be in `sources/free.py`)
- AbstractAPI (should be in `sources/plus.py`)
- The orchestrator function `enrich_company()` (144 lines)

**Fix**: Split into:
- `core/utils.py` — generic fetch utilities
- `sources/free.py` — Wikipedia, GitHub, Brave News, OpenCorporates, Hosting
- `sources/plus.py` — AbstractAPI, Crunchbase (mostly already there)
- `sources/enrichment.py` — the `enrich_company()` orchestrator

### 3. 57 lazy imports inside functions

**Problem**: Imports scattered inside functions. While some are justified (expensive imports like `yfinance`, `crewai`), most are not:
- `import urllib.parse` inside 3 different functions in `sources_plus.py` — should be top-level
- `import csv` inside `reflect_meta.py` — should be top-level
- `import subprocess` in 4 places — should be top-level

**Why it matters**: Every lazy import adds overhead on every function call. CPython caches module imports after first load, but the name lookup still happens. More importantly, it hides the true dependency graph from tools and readers.

### 4. 6 places bypassing Config class

**Problem**: `os.environ.get('ABSTRACT_API_KEY')` etc. are hardcoded in source files instead of going through `core.utils.Config.get()`. 

**Files**:
- `scripts/crewai_config.py:21` — direct `os.environ.get('GITHUB_TOKEN')`
- `scripts/datasources.py:110` — direct `os.environ.get('GITHUB_TOKEN')`
- `scripts/datasources.py:403` — direct `os.environ.get('ABSTRACT_API_KEY')`
- `scripts/sources_new.py:251` — direct `os.environ.get('FINANCIAL_DATASETS_API_KEY')`
- `core/utils.py:118` — direct `os.environ.get('GITHUB_TOKEN')`
- `core/utils.py:144` — direct `os.environ.get('FINANCIAL_DATASETS_API_KEY')`

**Fix**: Replace with `Config.get('KEY')`. If you ever rename an env var, you change it in ONE place (Config) instead of 6.

### 5. Shebang/logger order inconsistent

**Problem**: 6 library files (not CLI scripts) have `#!/usr/bin/env python3` which is unnecessary for modules meant to be imported. 4 files have `import logging` BEFORE the shebang.

**Files with shebang but shouldn't**:
- `core/utils.py`, `core/cache.py`, `scripts/datasources.py`, `scripts/free_sources.py`, `scripts/sources_plus.py`, `scripts/sources_new.py`, `scripts/companies_house.py`, `scripts/sources_mcp.py`, `scripts/quickscan.py`

**Fix**: Remove shebangs from library files. Only CLI entry points and standalone scripts need them.

### 6. Pipeline/run_pipeline() is 188 lines (#1 largest function)

**Problem**: `pipeline/research.py:51` `run_pipeline()` does everything: quick-scan → enrichment → scoring → reflection → report writing. It's 188 lines and does 5 different things.

**Fix**: Split into:
- `run_pipeline()` — calls stages in sequence (10 lines)
- `_run_quickscan()` — browser/stdlib scan
- `_run_enrichment()` — multi-source enrichment
- `_score_and_reflect()` — scoring + reflection
- `_write_report()` — generate and save scorecard

### 7. No configuration management

**Problem**: Timeouts are hardcoded (10, 15, 30, 60s scattered across files). API endpoints are hardcoded in each source file. There's no centralized configuration for:
- API base URLs
- Default timeouts
- Retry counts
- Rate limits

**Fix**: Add a `core/config.py` with:
```python
class APIConfig:
    TIMEOUT_DEFAULT = 15
    TIMEOUT_SLOW = 60
    RETRY_COUNT = 2
    class Endpoints:
        WIKIPEDIA = "https://en.wikipedia.org/api/rest_v1/page/summary"
        CLEARBIT = "https://company.clearbit.com/v1/domains/find"
        # ...
```

### 8. Test coverage still low (7.3%)

**Problem**: 63 tests for 5,920 lines. Critical modules with ZERO tests:
- `scripts/datasources.py` — 0 tests (core orchestrator!)
- `scripts/sources_plus.py` — 0 tests (7 API integrations)
- `scripts/free_sources.py` — 0 tests (SEC, yfinance, GLEIF)
- `scripts/sources_new.py` — 0 tests (SIRENE, VIES)
- `pipeline/research.py` — 0 tests (end-to-end flow)
- `pipeline/valuation.py` — 0 tests (DCF, LBO)
- `scripts/browser_research.py` — 0 tests (Playwright browser)

**Target**: 150+ tests — test the enrichment orchestrator, each source module (with mocked HTTP), the pipeline flow, and valuation calculations.

---

## Prioritized Action Plan

### Sprint 1: Finish the Restructuring (2 hours)

| # | Task | Files | Lines |
|---|---|---|---|
| 1 | Move datasources.py utilities → `core/utils.py` | 2 | +50/-50 |
| 2 | Move datasources.py Wikipedia, GitHub, etc → `sources/free.py` | 3 | +150/-150 |
| 3 | Move datasources.py AbstractAPI, Crunchbase → `sources/plus.py` | 3 | +100/-100 |
| 4 | Rewrite datasources.py as pure orchestrator (`enrich_company()` only) | 1 | 523→200 |
| 5 | Move `sources/__init__.py` to import from real locations | 1 | ~20 |
| 6 | Rename `scripts/*.py` → rewrite as thin CLI (5 lines each) | 6 | stay same |
| **Result** | Clean split: core/ has utilities, sources/ has implementations, scripts/ has CLIs | | |

### Sprint 2: Configuration Centralization (1 hour)

| # | Task | Files |
|---|---|---|
| 1 | Create `core/config.py` with API endpoints, timeouts, retries | 1 new |
| 2 | Consolidate all 6 `os.environ.get()` bypasses → `Config.get()` | 6 |
| 3 | Add timeout constants, replace magic numbers | 13 |
| **Result** | Change an API URL in one place, not 5 | |

### Sprint 3: Shebang + Import Hygiene (30 min)

| # | Task |
|---|---|
| 1 | Remove shebangs from 8 library files |
| 2 | Fix 4 files with logger before shebang |
| 3 | Move 10 obvious lazy imports to top level (urllib.parse, csv, subprocess, re) |

### Sprint 4: Test Coverage (4 hours)

| # | Module | Current | Target |
|---|---|---|---|
| 1 | `scripts/datasources.py` | 0 | 20 |
| 2 | `scripts/sources_plus.py` | 0 | 15 |
| 3 | `scripts/free_sources.py` | 0 | 10 |
| 4 | `pipeline/research.py` | 0 | 10 |
| 5 | `pipeline/valuation.py` | 0 | 10 |
| 6 | `scripts/browser_research.py` | 0 | 5 |
| **Result** | 63 → 133 tests | | |

### Sprint 5: Split Monolith Functions (1 hour)

| # | Function | Current lines | Target |
|---|---|---|---|
| 1 | `datasources.enrich_company()` | 144 | split into 4 helpers |
| 2 | `pipeline/research.run_pipeline()` | 188 | split into 5 stage functions |
| 3 | `pipeline/crew._create_agents()` | 93 | simplify |
| 4 | `scripts/track.generate_report()` | 91 | refactor |

---

## Long-Term Practices

### Do:

| Practice | Why |
|---|---|
| **One module = one responsibility** | `datasources.py` does 7 things → split |
| **Config in one place** | Every env var read goes through `Config.get()` |
| **CLI scripts are 5 lines** | Import + parse args + call library function |
| **Test with mocks** | Mock HTTP responses for deterministic tests |
| **Type hints on public functions** | `def enrich_company(name: str, domain: Optional[str] = None) -> dict` |
| **Atomic writes** | Use `atomic_json_dump()` for every file write |
| **Lazy imports only for expensive deps** | `yfinance`, `crewai` OK. `urllib.parse`, `csv`, `re` → always top-level |

### Don't:

| Practice | Why |
|---|---|
| **Hardcoded API URLs in source files** | Change API version = search-and-replace across 5 files |
| **Shebangs on library files** | Confuses tools, implies the file is executable |
| **Env var reads outside Config** | Rename a key = update 6 files instead of 1 |
| **Direct json.dump(..., open(...))** | Crash mid-write = corrupted file |
| **Monolith functions >100 lines** | Can't test, can't understand, can't change safely |

---

## Architectural Vision (After Sprints 1-5)

```
core/
  config.py     ← ALL configuration (timeouts, endpoints, env vars)
  cache.py      ← Persistent disk cache
  utils.py      ← fetch(), atomic_json_dump(), safe_json_load()

sources/
  enrichment.py ← enrich_company() — pure orchestrator (calls other sources)
  free.py       ← Wikipedia, GitHub, SEC, yfinance, GLEIF, Brave News, DDG
  plus.py       ← Clearbit, BuiltWith, Crunchbase, Glassdoor, SerpAPI, USPTO
  new.py        ← SIRENE, VIES, Financial Datasets, Companies House
  mcp.py        ← MCP server integrations
  browser.py    ← CompanyBrowser, tech detection

scoring/        ← DIMS, composite, grades, vetoes, flags, kills

pipeline/
  research.py   ← run_pipeline() — calls stages (each < 30 lines)
  reflect.py    ← Reflection loop
  valuation.py  ← DCF, LBO, comps
  crew.py       ← CrewAI multi-agent

scripts/        ← ONLY 5-line CLI wrappers
  research_pipeline.py → "import run_pipeline; run_pipeline()"
  datasources.py       → "import enrich_company; enrich_company()"
  valuation.py         → "import valuation_summary; valuation_summary()"
  quickscan.py         → "import quick_scan; quick_scan()"
  ...

tests/
  test_core/     ← tests for config, cache, utils
  test_sources/  ← tests for enrichment, free, plus (mocked HTTP)
  test_scoring/  ← tests for DIMS, composite, grades (63 existing)
  test_pipeline/ ← tests for research, valuation, crew
```

---

**Next:** Want me to execute Sprint 1 (finish the restructuring)? It's the highest impact — turns `scripts/` into actual entry points and `sources/` into the real module. About 2 hours.
