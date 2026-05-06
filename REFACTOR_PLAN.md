# Complete Refactor Plan

Current state: 48 files, 7,705 lines, 25 data sources, works end-to-end.
Target state: Clean architecture, single source tree, testable, maintainable.

---

## Phase 0: Stop the Bleeding (can do anytime, no code changes)

| Action | Why |
|---|---|
| **Revoke `gho_R13qTRIE...`** at github.com/settings/tokens | Hardcoded in `core/utils.py:114`, exposed to everyone who clones |
| **Revoke the LiteLLM key `sk-hermes-litellm-sunstein-2026`** | Same problem, `core/utils.py:118` and `scripts/crewai_config.py:59` |
| **Add `output/.cache/` to `.gitignore`** | Binary cache files shouldn't be committed |

---

## Phase 1: Collapse Duplicate Structure (1 hour)

### Problem
`scripts/` and `sources/` contain 6 pairs of near-identical files. Fixes must be applied twice.

### Current layout:
```
scripts/
  browser_research.py   ─┐ 98% identical
  quickscan.py           ─┤ 100% identical
  datasources.py         ─┤ the real code
  free_sources.py        ─┤ the real code
  sources_new.py         ─┤ the real code
  sources_mcp.py         ─┤ the real code
  companies_house.py     ─┤ 100% identical

sources/
  browser.py             ─┘ 98% identical
  quickscan.py           ─┘ 100% identical
  enrich.py              ─┤ 6-line wrapper → scripts/datasources
  free.py                ─┤ 6-line wrapper → scripts/free_sources
  new_sources.py         ─┤ 6-line wrapper → scripts/sources_new
  mcp.py                 ─┤ 6-line wrapper → scripts/sources_mcp
  companies_house.py     ─┘ 100% identical
  __init__.py            ─┤ re-exports from scripts/... for backward compat
```

### Action:
1. Delete `sources/browser.py` → point `sources/__init__.py` to `scripts/browser_research.py`
2. Delete `sources/quickscan.py` → point to `scripts/quickscan.py`
3. Delete `sources/companies_house.py` → point to `scripts/companies_house.py`
4. Delete the 4 wrapper files (`enrich.py`, `free.py`, `new_sources.py`, `mcp.py`)
5. Rewrite `sources/__init__.py` to just re-export from `scripts/`
6. Update any external import of `sources.browser.CompanyBrowser` to work through the re-export

**Result:** -8 files, -660 lines. One source of truth for every module.

---

## Phase 2: Centralize Architecture (2 hours)

### Problem
Scattered responsibilities — fetch logic in 5 places, config in 3 places, no clear layering.

### Clean Architecture:

```
core/                    ← Foundation layer (no dependencies on other modules)
  __init__.py
  config.py              ← All env vars, API keys, paths. Single source of truth.
  cache.py               ← Persistent disk cache (already exists, just needs config)
  utils.py               ← Shared helpers (JSON, folders, typing)

sources/                 ← Data layer (depends on core/)
  __init__.py            ← Re-exports for backward compat
  browser.py → scripts/browser_research.py   ← 1:1 alias
  quickscan.py → scripts/quickscan.py         ← 1:1 alias
  free.py                ← Merged from scripts/free_sources.py
  new.py                 ← Merged from scripts/sources_new.py
  plus.py                ← Merged from scripts/sources_plus.py
  mcp.py                 ← Merged from scripts/sources_mcp.py
  enrichment.py          ← Merged from scripts/datasources.py (the orchestrator)

scoring/                 ← Analysis layer (depends on core/)
  __init__.py            ← DIMS, composite, grades, vetoes, flags, kills

pipeline/                ← Orchestration layer (depends on sources/ + scoring/)
  research.py            ← run_pipeline() — ties sources → scoring → report
  reflect.py             ← Reflection loop
  crew.py                ← CrewAI multi-agent research
  valuation.py           ← DCF, LBO, comps

scripts/                 ← CLI entry points (thin, just parse args and call pipeline/)
  research_pipeline.py   ← CLI wrapper → pipeline/research.run_pipeline()
  validate.py            ← CLI wrapper → validation logic
  track.py               ← CLI wrapper → experiment tracking
  ... (keep as thin wrappers)

tests/                   ← Tests mirror the structure
  test_core/
  test_scoring/
  test_sources/
  test_pipeline/
```

### Action:
1. Move `scripts/datasources.py` enrichment logic → `sources/enrichment.py`
2. Move `scripts/research_pipeline.py` logic → `pipeline/research.py`
3. Move `scripts/reflect.py` → `pipeline/reflect.py`
4. Move `scripts/valuation.py` → `pipeline/valuation.py`
5. Move `scripts/research_crew.py` → `pipeline/crew.py`
6. Rewrite `scripts/research_pipeline.py` as a thin CLI wrapper (5 lines)
7. Move `scripts/crewai_config.py` → `core/config.py` (add to existing Config class)
8. Centralize all API key reading into `core/config.py`:
   - `Config.abstractapi_key()`, `Config.github_token()`, etc.
   - No more `os.environ.get('KEY')` scattered across 5 files
9. Centralize all fetch logic into `core/utils.py`:
   - `fetch()` with caching (currently duplicated in 5 files)
   - `fetch_parallel()` 
   - `fetch_with_auth()` for APIs needing special headers

**Result:** Clear dependency direction: `core → sources → scoring → pipeline`. Never circular.

---

## Phase 3: Fix Every Code Smell (3 hours)

### 3a. Security (30 min)
| File | Issue | Fix |
|---|---|---|
| `core/utils.py:114` | Hardcoded GitHub token | Remove, use env var only |
| `core/utils.py:118` | Hardcoded LiteLLM key | Remove, use env var only |
| `scripts/crewai_config.py:59` | Hardcoded LiteLLM key (duplicate) | Remove |

### 3b. Atomic File Writes (30 min)
All files that do `json.dump(data, open(path, 'w'))` should instead:
```python
tmp = path + '.tmp'
with open(tmp, 'w') as f:
    json.dump(data, f)
os.replace(tmp, path)  # Atomic on Linux
```

Files to fix (from `grep -rn "json.dump\|open(.*'w'"`):
- `scripts/report_pdf.py`, `scripts/research_pipeline.py`, `scripts/batch-score.py`, `scripts/datasources.py` (__main__), `scripts/quickscan.py` (__main__), `scripts/track.py`, `scripts/consensus.py`, `scripts/reflect_meta.py`, `core/cache.py`

### 3c. Atomic Cache Writes (15 min)
`core/cache.py` already has the issue: `cache_set` writes directly to the cache file. Fix: write to `.tmp` then `os.replace()`.

### 3d. Remove Dead Code (30 min)
Files that are NEVER imported — decide: archive or delete?

| File | Lines | Decision |
|---|---|---|
| `scripts/deal_memo.py` | 156 | 🗑️ Delete (obsolete — report_pdf.py does this) |
| `scripts/track.py` | 298 | Keep — useful CLI tool, just never imported |
| `scripts/reflect_meta.py` | 240 | Keep — useful standalone analysis |
| `scripts/init-universe.py` | 103 | 🗑️ Delete (one-time setup script) |
| `scripts/aggregate-universe.py` | 88 | 🗑️ Delete (obsolete) |
| `scripts/research-all.py` | 152 | 🗑️ Delete (superseded by validate.py + batch-score.py) |
| `scripts/report_pdf.py` | 168 | Keep — useful CLI tool |
| `scripts/generate-triplets.py` | 168 | 🗑️ Delete (one-off data generation) |
| `scripts/consensus.py` | 275 | 🗑️ Delete (Elo ranking was experimental, never integrated) |
| `scripts/compare-companies.py` | 97 | 🗑️ Delete (one-off analysis) |
| `scripts/batch-score.py` | 107 | Keep — batch generation of scorecards |
| `scripts/validate.py` | 154 | Keep — validation dashboard |
| `scripts/grades.py` | 50 | 🗑️ Delete (superseded by scoring/__init__.py) |
| `scripts/enrichment_mcp.py` | 90 | 🗑️ Delete (superseded by sources_mcp.py) |
| `logging_config.py` | 24 | 🗑️ Delete (never imported, configure_logging() in core/utils.py) |
| `test_latam.py` | 108 | Keep — LATAM validation |
| `test_latam_batch.py` | 112 | Keep — LATAM validation |
| `scripts/rubric.py` | 197 | 🗑️ Delete (superseded by scoring/__init__.py) |

**Result:** -2,500 lines of dead code. ~16 fewer files.

### 3e. Add Missing `__init__.py` (5 min)
```
tests/__init__.py  ← MISSING (pytest can work without it, but good practice)
```

### 3f. Standardize Lazy Imports (20 min)
50 lazy imports. Most are legit (avoid circular imports, expensive modules like yfinance/crewai).
But some should be top-level:
- `import re` in `scripts/research_crew.py:186` and `scripts/track.py:180` → move to top
- `import urllib.parse` in `scripts/free_sources.py:147` → move to top (used in 3 functions)
- `import socket` in `scripts/datasources.py:246` → move to top

### 3g. Standardize Logger Position (15 min)
Multiple files have `logger = logging.getLogger(__name__)` AFTER the shebang/docstring but BEFORE the `#!/usr/bin/env python3` line, which is wrong:
- `scripts/datasources.py`: line 1 is `import logging`, line 2 is `logger = ...`, THEN line 3 is `#!/usr/bin/env python3`
- `scripts/reflect.py`: same pattern
- `scripts/free_sources.py`: same pattern (was already this way before our edits)
- `scripts/sources_new.py`: same pattern

Fix: `#!/usr/bin/env python3` must always be line 1.

---

## Phase 4: Test Coverage (4 hours)

### Current: 50 tests for 7,705 lines (0.6%)
### Target: 200+ tests for 5,200 lines (4%) — realistic for a pipeline

### Must-have test targets:

| Module | Existing Tests | Needed | What to Test |
|---|---|---|---|
| `core/cache.py` | 0 | 10 | cache_get/set, TTL expiry, cache_stats, concurrent access |
| `core/utils.py` | 19 | 5 | fetch(), Config.get(), env auto-load |
| `scoring/__init__.py` | 31 | 0 | Already well-tested |
| `sources/free_sources.py` | 0 | 5 | SEC EDGAR parsing, yfinance calls, GLEIF |
| `sources/sources_new.py` | 0 | 5 | SIRENE, VIES, Financial Datasets, Companies House |
| `sources/sources_plus.py` | 0 | 10 | Each of 7 APIs (with mock HTTP), enrich_plus() |
| `sources/datasources.py` | 0 | 15 | enrich_company(), fetch(), fetch_parallel(), triangulation |
| `pipeline/research.py` | 0 | 5 | End-to-end pipeline run |
| `pipeline/valuation.py` | 0 | 5 | DCF, LBO, comps calculations |

### Testing approach:
- Use `unittest.mock.patch` to mock HTTP requests — no real API calls in tests
- Use `tempfile` for cache tests — no filesystem pollution
- Test with realistic but fake company data (fixtures in `tests/fixtures/`)

---

## Phase 5: Documentation (1 hour)

### Current: 8 markdown files (ARCHITECTURE.md, QUICKSTART.md, etc.) — most are outdated.
### Fix:
1. Update `ARCHITECTURE.md` to reflect actual structure after refactor
2. Update `QUICKSTART.md` with new CLI paths
3. Add docstrings to all public API functions in core/ and sources/
4. Add type hints to all new code

---

## Summary

| Phase | Hours | Files Changed | Lines Removed | Risk |
|---|---|---|---|---|
| 0: Stop bleeding | 0.1 | 0 | 0 | None |
| 1: Collapse duplicates | 1 | 14 files deleted | -660 | Low (backward compat via __init__.py) |
| 2: Centralize architecture | 2 | 20 files moved/renamed | 0 | Medium (import path changes) |
| 3: Fix code smells | 3 | 30 files | -2,500 | Low |
| 4: Test coverage | 4 | +5 test files | 0 | None (new code only) |
| 5: Documentation | 1 | 3 markdown files | -5 outdated | None |
| **Total** | **~11 hours** | | **~3,160 fewer lines, 48→30 files** | |

## Architectural Principles Going Forward

1. **One direction of dependency**: `core → sources → scoring → pipeline` (never the other way)
2. **No duplicated code**: if you need it in two places, put it in core/
3. **All config in one place**: `core/config.py` is the ONLY file that reads env vars
4. **All HTTP in one place**: `core/utils.fetch()` with caching is the ONLY fetch function
5. **CLI scripts are thin**: parse args → call pipeline function → print results
6. **Test what matters**: scoring, enrichment orchestration, cache behavior
7. **Atomic writes everywhere**: `write to .tmp → os.replace()` for every file
8. **No secrets in source**: every key comes from `.env`, no hardcoded fallbacks

---

Want me to execute this plan in order? Phase 0 and Phase 1 can be done in under an hour.
