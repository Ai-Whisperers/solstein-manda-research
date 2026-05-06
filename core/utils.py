"""
Core utilities shared across the pipeline.
Consolidates: URL fetch, parallel fetch, atomic writes, JSON safety, folder names.
"""
import json, os, sys, urllib.request, urllib.error, threading, time, logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)
from core.config import Config

# --- Paths (centralized in Config) ---
BASE = Config.BASE
HORECA_DIR = Config.HORECA_DIR
JOHN_JSON = Config.JOHN_JSON

# --- Caching ---
_CACHE = {}
_CACHE_TTL = 3600  # 1 hour default
_CACHE_LOCK = threading.Lock()


def cached(ttl=None):
    """Decorator: cache function results with TTL in seconds."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            with _CACHE_LOCK:
                if key in _CACHE:
                    entry = _CACHE[key]
                    if (datetime.now() - entry['time']).seconds < (ttl or _CACHE_TTL):
                        return entry['data']
            result = func(*args, **kwargs)
            with _CACHE_LOCK:
                _CACHE[key] = {'data': result, 'time': datetime.now()}
            return result
        return wrapper
    return decorator


def clear_cache():
    with _CACHE_LOCK:
        _CACHE.clear()


# --- User-Agent rotation ---
_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
]
_ua_index = 0
_ua_lock = threading.Lock()


def fetch(url, timeout=15, headers=None):
    """Fetch URL with rotating user-agent and caching."""
    global _ua_index
    with _ua_lock:
        ua = _USER_AGENTS[_ua_index % len(_USER_AGENTS)]
        _ua_index += 1
    
    req_headers = {
        'User-Agent': ua,
        'Accept': 'application/json,text/html,*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    if headers:
        req_headers.update(headers)
    
    try:
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception:
        return None


def fetch_parallel(items, max_workers=5):
    """Run multiple fetches in parallel. items = [(name, callable), ...]"""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as exec:
        future_map = {exec.submit(fn): name for name, fn in items}
        for future in as_completed(future_map, timeout=30):
            name = future_map[future]
            try:
                results[name] = future.result(timeout=15)
            except Exception:
                results[name] = None
    return results


# Config is now in core/config.py, imported at top of file.


# --- Helpers ---

def atomic_json_dump(data, path, **kwargs):
    """Write JSON atomically: write to .tmp then os.replace.
    Prevents corrupted files on crash mid-write."""
    tmp = path + '.tmp'
    try:
        with open(tmp, 'w') as f:
            json.dump(data, f, **kwargs)
        os.replace(tmp, path)
    except (OSError, TypeError) as e:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def triangulate_employees(sources):
    """Cross-reference employee counts from multiple sources. Returns consensus + flags."""
    values = {k: v for k, v in sources.items() if v}
    if len(values) >= 2:
        vals = list(values.values())
        avg = sum(vals) / len(vals)
        max_diff = max(vals) - min(vals)
        if max_diff / max(avg, 1) > 0.5:
            return {'consensus': round(avg), 'sources': values, 'confidence': 'low',
                    'note': f'Disagreement: difference of {max_diff}'}
        return {'consensus': round(avg), 'sources': values, 'confidence': 'high',
                'note': f'Consistent across {len(values)} sources'}
    elif len(values) == 1:
        src, val = next(iter(values.items()))
        return {'consensus': val, 'sources': values, 'confidence': 'low', 'note': f'Single source: {src}'}
    return {'consensus': None, 'sources': {}, 'confidence': 'none', 'note': 'No data'}


def check_freshness(scan_date_str):
    """Check if a scan date is fresh (within 90 days)."""
    if not scan_date_str:
        return {'fresh': False, 'days_old': None, 'note': 'No date available'}
    try:
        scan_date = datetime.fromisoformat(str(scan_date_str))
        delta = datetime.now() - scan_date
        if delta.days > 365:
            return {'fresh': False, 'days_old': delta.days, 'note': f'Stale: {delta.days} days old'}
        elif delta.days > 90:
            return {'fresh': False, 'days_old': delta.days, 'note': f'Aging: {delta.days} days old'}
        return {'fresh': True, 'days_old': delta.days, 'note': f'Fresh: {delta.days} days ago'}
    except (ValueError, TypeError):
        return {'fresh': False, 'days_old': None, 'note': 'Invalid date format'}


def folder_from(name):
    """Convert company name to folder name."""
    f = name.lower().replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '')
    f = f.replace("'", '').replace('&', 'and')
    while '--' in f:
        f = f.replace('--', '-')
    return f.strip('-')


def safe_json_loads(text, default=None):
    """Parse JSON safely, return default on failure."""
    if text is None:
        return default
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError, TypeError):
        return default


def safe_json_load(filepath, default=None):
    """Read and parse JSON file safely, return default on failure."""
    try:
        with open(filepath) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError, OSError):
        return default


def load_john_reference():
    """Load John's reference scores."""
    import json
    if not os.path.exists(JOHN_JSON):
        return {}
    data = safe_json_load(JOHN_JSON, {})
    result = {}
    folder_map = {}
    for c in data['companies']:
        name = c['company_name']
        folder = folder_from(name)
        folder_map[folder] = name
        sc = c.get('scorecard')
        if sc and sc.get('composite_score') is not None:
            dims_raw = sc.get('dimensions', {})
            dims = {}
            from scoring import DIMS
            for d in DIMS:
                v = dims_raw.get(d, {})
                dims[d] = v.get('score') if isinstance(v, dict) else v
            result[name] = {'composite': sc['composite_score'], 'dims': dims}
    return result, folder_map
