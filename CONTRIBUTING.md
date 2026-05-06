# Contributing

## Architecture Rules

```
core/ → sources/ → scoring/ → pipeline/ → scripts/
```

**Never import upward.** `core/` cannot import from `sources/`, `scoring/`, or `pipeline/`. `sources/` cannot import from `pipeline/`.

## Adding a New Data Source

1. Add the integration function in the appropriate file under `sources/`:
   - `free.py` — free/no-key APIs (Wikipedia, GitHub, SEC, etc.)
   - `plus.py` — APIs requiring keys (Clearbit, Crunchbase, etc.)
   - `mcp.py` — MCP server integrations

2. Add the API key to `core/config.py` Config class

3. Wire it into `sources/enrichment.py` (`enrich_company()` function)

4. Add `.env` key to `.env.example`

5. Add tests with mocked HTTP responses

## Code Standards

- **No hardcoded secrets** — every key goes through `Config.get()` in `core/config.py`
- **No bare `except:`** — always catch specific exceptions
- **Atomic writes** — use `atomic_json_dump()` from `core/utils.py`
- **Persistent cache** — use `cache_get_or_fetch()` from `core/cache.py`
- **Tests exist for every module** — add at minimum 5 tests per new source

## Testing

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run a specific test file
python3 -m pytest tests/test_scoring.py -v
```

## Commit Messages

Use conventional commits when possible:
```
feat: add Clearbit company enrichment API
fix: handle None response in github_org
refactor: move fetch_parallel to core/utils.py
test: add 13 cache tests
docs: update QUICKSTART.md with new CLI paths
```
