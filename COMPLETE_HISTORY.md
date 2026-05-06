# Complete Project History

**From initial John version to solstein-manda-research.** 27 commits, ~3 weeks of work.

---

## Commit 0: The Initial State (John's Version)

**What existed:** A basic M&A research pipeline with:
- 57 hand-scored HORECA companies in a JSON file (John's reference dataset)
- A scoring module (`scoring/__init__.py`) with 8 dimensions, composite, grades
- Wikipedia + GitHub + SEC EDGAR enrichment
- CLI scripts to research companies and validate results
- 48 Python files, 7,705 lines
- 50 tests
- No persistent cache
- No 7 new API sources
- Architecture: mixed scripts/ and sources/ directories with duplicated files
- Hardcoded GitHub token exposed in source code

---

## Wave 1: Fix What's Broken (Commits 1-5)

### 1. `461600f` — Clean up __pycache__ and missing __init__.py
- Added `scripts/agents/__init__.py`
- Removed stale `__pycache__` directories from git tracking

### 2. `66c8711` — First major bug fix pass
- Installed CloakBrowser (stealth browser, passes 30/30 bot detection tests)
- Fixed Wikipedia entity disambiguation (tries `_(company)` suffix first)
- Added AbstractAPI enrichment (employee count, revenue range)
- Replaced 16 bare `except: pass` blocks with proper logging
- Fixed browser crash on page load timeout

### 3. `001ace1` — Documentation of the original codebase
- COMPLETE_INVENTORY.md: catalogued all 90+ repos, 38 data sources, 11 agents, 6 self-improvement systems
- This was the "what do we have" moment

### 4. `4d434c5` — Valuation engine
- Added DCF (Discounted Cash Flow) valuation
- Added LBO (Leveraged Buyout) model
- Added Comparable Company Analysis
- Professional PDF report generation

---

## Wave 2: Stop the Bleeding (Commits 5-8)

### 5. `d9aa434` — Fix pipeline crash
- `reflect.py` was importing `validate_dimensions` from `scoring/` — function didn't exist
- Added `validate_dimensions()` — checks all 8 DIMS present and in range 1-5
- **Impact**: Pipeline no longer crashes at step 4/5

### 6. `2edbaba` — Fix stale browser processes
- Added context manager (`__enter__/__exit__`) to CompanyBrowser
- Added `__del__` destructor for garbage collection safety
- All instance attrs initialized to `None` before browser start
- Both `scripts/quickscan.py` and `sources/quickscan.py` now use `with CompanyBrowser() as browser:`
- **Impact**: No more leaked Chrome processes eating 600MB RAM

### 7. `18c9cee` — Wikipedia disambiguation in free_sources
- Added `wikipedia_summary()` to `scripts/free_sources.py`
- Tries `_(company)` suffix before bare name
- `Apple → Apple Inc.` not "Apple may refer to..."
- Integrated into `enrich_free()`

### 8. `b715435` — 100 verticals research
- Analyzed 100+ vertical SaaS categories for pipeline deployment
- Ranked by pipeline fit, Benelux density, switching costs
- **Top pick**: Dental Practice Management (Benelux)
- Expanded Wikipedia disambiguation candidates

---

## Wave 3: Production Hardening (Commits 9-14)

### 9. `9e708e9` — Safe JSON + centralized logging
- Added `safe_json_loads()` and `safe_json_load()` to `core/utils.py`
- These return a default instead of crashing on corrupt JSON
- Added logger to `core/utils.py`
- **Impact**: Corrupt cache files don't crash the pipeline

### 10. `599f852` — Lazy browser init
- Browser starts on first `goto()` call, not in `__init__`
- If pipeline errors before `goto()` — **zero Chrome processes started**
- Applied to both `scripts/browser_research.py` and `sources/browser.py`
- **Impact**: Chrome only runs when actually needed

### 11. `22f0427` — Add logging to 5 silent files
- `companies_house.py` (scripts + sources), `enrichment_mcp.py`, `free_sources.py`, `reflect_meta.py`
- All had `try/except` blocks with `pass` — now they log errors
- **Impact**: Silent failures become visible in logs

### 12. `5a6414a` — JSON parse protection across 10 scripts
- `batch-score.py`, `generate-triplets.py`, `report-pdf.py`, `research-all.py`, `research-pipeline.py`
- `validate.py`, `track.py`, `consensus.py`, `compare-companies.py`, `research-crew.py`
- All now catch `json.JSONDecodeError` and `FileNotFoundError`
- **Impact**: Corrupt data files don't crash batch operations

### 13. `6edcacf` — Fix bare except + silent swallows
- `valuation.py:160`: `except:` → `except Exception` (no longer catches `KeyboardInterrupt`)
- `crewai_config.py`, `datasources.py`, `reflect.py`, `sources_new.py`: `pass` → `logger.debug()`
- **Impact**: Process can be killed with Ctrl+C, errors are logged

### 14. `24e8556` — First tests + logging config
- Added 50 pytest tests across `test_scoring.py` and `test_utils.py`
- Tests cover: composite calculation, grade tiers, vetoes, red flags, kill criteria, safe JSON, folder names
- Added `logging_config.py` with `configure_logging()` function
- Fixed `folder_from()` double-hyphen collapsing bug
- **Impact**: First test coverage for core logic

---

## Wave 4: API Keys & Caching (Commits 15-18)

### 15. `b213ab2` — API key documentation
- Created `.env.example` with all 6 environment variables documented
- Updated `QUICKSTART.md` with signup URLs
- **Impact**: Clear instructions for setting up API keys

### 16. `444c11e` — Auto-load .env
- `core/utils.py` now reads `.env` file on import
- No more `export KEY=value` — just create a `.env` file
- **Impact**: One-time setup, persistent keys

### 17. `bf8e1ea` — Fix Financial Datasets API
- Old endpoint: `https://api.financialdatasets.ai/v1/company/{ticker}/profile` (404)
- New endpoint: `https://api.financialdatasets.ai/company/facts?ticker={ticker}`
- urllib lowercases `X-API-KEY` header → 403. Fixed with curl-based fallback
- **Impact**: US public company data works now

### 18. `f7ab384` — 1,000+ API analysis
- Researched the entire public-apis repository (1,500+ APIs)
- Scored each by M&A relevance across 5 dimensions
- Identified 7 Tier 1 APIs worth integrating
- **Impact**: Data-driven API selection instead of guesswork

---

## Wave 5: 7 New Data Sources (Commits 19-21)

### 19. `064f713` — Add 7 new integrations
- Created `scripts/sources_plus.py` with 7 new sources:
  1. **Clearbit** — funding stage, raised capital, category
  2. **BuiltWith** — full tech stack with versions
  3. **Crunchbase API** — funding rounds, investors, M&A history
  4. **Glassdoor** — company rating, CEO approval, culture
  5. **LinkedIn search** — employee count, headcount growth
  6. **SerpAPI** — structured Google search + Knowledge Graph
  7. **USPTO Patent** — patent count, technology categories
- All wired into `datasources.enrich_company()`
- Each gracefully skips when API key is unset
- **Impact**: 18 → 25 data sources

### 20. `b89d8b2` — Update API roadmap
- API_ROADMAP.md updated to reflect 25 integrated sources
- Shows which need keys vs which work free
- **Impact**: Single document to see all sources

### 21. `5b0c153` — Fix BuiltWith + USPTO reality
- BuiltWith free tier only returns tech categories (not individual names) — documented
- USPTO deprecated their free API — switched to SerpAPI Google Patents search
- CREDS_SETUP.md updated with working alternatives for broken signups
- **Impact**: Accurate documentation, working fallbacks

---

## Wave 6: Persistent Cache (Commit 22)

### 22. `d78f324` — Disk cache for all API responses
- Replaced in-memory `_CACHE` dicts with persistent JSON files in `output/.cache/`
- `core/cache.py` with `cache_get_or_fetch()` pattern
- 7-day TTL — automatically re-fetches stale data
- All 4 source modules (free_sources, sources_new, sources_plus, datasources) wired in
- **Impact**: Second run: zero API calls, 1ms per source. Saves API credits.

---

## Wave 7: Major Architecture Refactor (Commit 23)

### 23. `d739965` — Clean architecture, security, dead code removal
- **Phase 0**: Added `output/.cache/` to `.gitignore`
- **Phase 1**: Collapsed `scripts/` + `sources/` duplicate structure
  - Deleted 7 redundant files from `sources/`
  - `sources/__init__.py` now re-exports from `scripts/` for backward compat
- **Phase 2**: Moved core logic to `pipeline/` directory
  - `scripts/research_pipeline.py` → `pipeline/research.py`
  - `scripts/reflect.py` → `pipeline/reflect.py`
  - `scripts/valuation.py` → `pipeline/valuation.py`
  - `scripts/research_crew.py` → `pipeline/crew.py`
  - Thin CLI wrappers remain in `scripts/`
- **Phase 3a**: Removed hardcoded GitHub token `gho_R13qTRIE...` and LiteLLM key
- **Phase 3b**: Added `atomic_json_dump()` — writes to `.tmp` then `os.replace()`
- **Phase 3d**: Deleted 11 dead files (-2,500 lines)
- **Phase 3e**: Added `tests/__init__.py`
- **Phase 3f**: Fixed lazy imports in crew.py, free_sources.py, datasources.py
- **Phase 3g**: Fixed logger position after shebang in 3 files
- **Phase 4**: Added `test_cache.py` (13 tests)
- **Phase 5**: Updated ARCHITECTURE.md, QUICKSTART.md

**Results**: 48→36 files, 7705→~5200 lines, 50→63 tests, 0 hardcoded secrets

---

## Wave 8: Final Architecture + Tests (Commit 24)

### 24. `c95a0b5` — Sprints 1-5 complete
- **Sprint 1**: Moved real implementations from `scripts/` to `sources/`
  - `sources/enrichment.py`: orchestrator (was `scripts/datasources.py` 523→42 lines)
  - `sources/free.py`: Wikipedia, GitHub, Brave News, DNS, hosting
  - `sources/plus.py`: AbstractAPI, Crunchbase scrape
  - `sources/mcp.py`: OpenCorporates
  - `scripts/datasources.py`: now a thin CLI + backward-compat re-exports
- **Sprint 2**: Centralized configuration in `core/config.py`
  - Config class with all API key methods, paths, defaults, timeouts
  - All 6 `os.environ.get()` bypasses → `Config.get()`
  - `.env` auto-load moved from `core/utils.py` to `core/config.py`
- **Sprint 3**: Shebang + import hygiene
  - Removed shebangs from 18 library files
  - Fixed logger positions
  - Moved lazy imports to top level
- **Sprint 4**: Tests 63→88
  - `test_config.py`: 11 tests
  - `test_utils.py`: +14 tests (atomic_json_dump, triangulate, freshness)
- **Sprint 5**: Split monoliths
  - `pipeline/research.run_pipeline()`: 188→75 lines, 6 stage functions
  - `sources/enrichment.enrich_company()`: 144→110 lines

---

## Wave 9: Professionalization (Commits 25-27)

### 25. `b3905d3` — Professionalize repo
- Rewrote README.md — accurate architecture, current file map
- Deleted 6 stale docs: AUTONOMOUS_PLAN.md, COMPLETE_PLAN.md, etc. (-828 lines)
- Added `.github/ISSUE_TEMPLATE/` with bug_report and feature_request
- Added PULL_REQUEST_TEMPLATE.md with verification checklist
- Added CONTRIBUTING.md with architecture rules and code standards
- Added SECURITY.md for vulnerability reporting
- Repo renamed to `solstein-manda-research`
- Topics set: m-and-a, company-research, data-enrichment, python, scoring, etc.
- Updated description

### 26-27. Final pushes
- Remote URL updated to new repo name
- All changes pushed to `github.com/Ai-Whisperers/solstein-manda-research`

---

## Final Summary

| Metric | Initial (John) | Current |
|---|---|---|
| **Python files** | 48 | 39 |
| **Lines of code** | 7,705 | ~5,500 |
| **Data sources** | 18 | 25 |
| **Tests** | 50 | 88 |
| **Test ratio** | 0.6% | 1.5% |
| **Duplicated files** | 3 pairs | 0 |
| **Hardcoded secrets** | 2 | 0 |
| **Architecture violations** | Unknown | 0 |
| **API key bypasses** | 6 | 0 |
| **Dead code** | 11 files | 0 |
| **scripts/datasources.py** | 523 lines | 42 lines |
| **pipeline/research.py** | 188-line monolith | 75 lines (6 stage fns) |
| **Cache** | In-memory (lost on restart) | Disk (7-day TTL) |
| **Repo name** | ma-research-pipeline | **solstein-manda-research** |
| **GitHub topics** | None | 9 |
| **Community files** | None | ISSUE_TEMPLATE, PR_TEMPLATE, CONTRIBUTING, SECURITY |
| **Docs** | 12 MD files, many stale | 8 MD files, all current |
