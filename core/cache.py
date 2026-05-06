"""Persistent disk-backed cache for API responses.
All 25 sources share this cache. Once fetched, data is stored forever
(or until TTL expires). This eliminates repeated API calls across runs.

Cache location: output/.cache/<source>/<cache_key>.json
"""

import json, os, time, logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output', '.cache')
DEFAULT_TTL = 7 * 24 * 3600  # 7 days in seconds


def _ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def cache_get(source, key):
    """Get cached response for a source+key. Returns parsed JSON or None."""
    cache_path = os.path.join(CACHE_DIR, source, f'{key}.json')
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path) as f:
            entry = json.load(f)
        # Check TTL
        cached_time = entry.get('_cached_at', 0)
        ttl = entry.get('_ttl', DEFAULT_TTL)
        if time.time() - cached_time > ttl:
            os.remove(cache_path)
            return None
        logger.debug("Cache HIT: %s/%s (age: %.1fh)", source, key, (time.time() - cached_time) / 3600)
        return entry.get('data')
    except (json.JSONDecodeError, OSError, KeyError):
        return None


def cache_set(source, key, data, ttl=None):
    """Store a response in the cache."""
    cache_path = os.path.join(CACHE_DIR, source, f'{key}.json')
    _ensure_dir(cache_path)
    entry = {
        '_cached_at': time.time(),
        '_ttl': ttl or DEFAULT_TTL,
        '_source': source,
        '_key': key,
        'data': data,
    }
    try:
        tmp = cache_path + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(entry, f, indent=2)
        os.replace(tmp, cache_path)
        logger.debug("Cache SET: %s/%s", source, key)
    except OSError as e:
        logger.warning("Cache write failed: %s/%s — %s", source, key, e)


def cache_get_or_fetch(source, key, fetch_fn, ttl=None):
    """Get from cache or call fetch_fn, cache the result, return it."""
    cached = cache_get(source, key)
    if cached is not None:
        return cached
    data = fetch_fn()
    if data is not None:
        cache_set(source, key, data, ttl)
    return data


def cache_stats():
    """Return summary of what's in the cache."""
    if not os.path.exists(CACHE_DIR):
        return {'total_files': 0, 'sources': {}, 'total_size_kb': 0}
    total = 0
    total_size = 0
    source_counts = {}
    for root, dirs, files in os.walk(CACHE_DIR):
        for f in files:
            if f.endswith('.json'):
                total += 1
                rel = os.path.relpath(root, CACHE_DIR)
                source_counts[rel] = source_counts.get(rel, 0) + 1
                total_size += os.path.getsize(os.path.join(root, f))
    return {
        'total_files': total,
        'sources': source_counts,
        'total_size_kb': round(total_size / 1024, 1),
    }


def cache_clear(source=None, older_than_days=None):
    """Clear cache. If source given, clear only that source.
    If older_than_days given, clear only entries older than N days."""
    if not os.path.exists(CACHE_DIR):
        return
    for root, dirs, files in os.walk(CACHE_DIR):
        for f in files:
            if f.endswith('.json'):
                fpath = os.path.join(root, f)
                rel = os.path.relpath(root, CACHE_DIR)
                if source and source != rel:
                    continue
                if older_than_days:
                    age = time.time() - os.path.getmtime(fpath)
                    if age < older_than_days * 86400:
                        continue
                os.remove(fpath)
    logger.info("Cache cleared: source=%s, older_than=%s days", source or 'all', older_than_days or 'any')


if __name__ == '__main__':
    stats = cache_stats()
    print(f"Cache directory: {CACHE_DIR}")
    print(f"Total cached files: {stats['total_files']}")
    print(f"Total size: {stats['total_size_kb']} KB")
    for source, count in sorted(stats['sources'].items()):
        print(f"  {source}: {count} files")
