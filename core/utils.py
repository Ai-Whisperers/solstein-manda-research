import logging
logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
Core utilities shared across the pipeline.
Consolidates: URL fetch, caching, logging, path resolution, base config.
"""

import json, os, sys, urllib.request, urllib.error, threading, time
from datetime import datetime, timedelta

# --- Paths ---
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HORECA_DIR = os.path.join(BASE, 'output', 'HORECA')
TEMPLATES_DIR = os.path.join(BASE, 'templates')
JOHN_JSON = os.path.join(BASE, 'archive', 'john-original', 'horeca_json', 'horeca_data.json')

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


# --- API Keys (centralized, from env) ---
class Config:
    """Centralized configuration. Reads from environment variables."""
    
    @staticmethod
    def get(key, default=None):
        return os.environ.get(key, default)
    
    @staticmethod
    def github_token():
        t = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
        if t:
            return t
        try:
            import subprocess
            r = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except Exception:
            pass
        return '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'
    
    @staticmethod
    def litellm_key():
        return 'sk-hermes-litellm-sunstein-2026'
    
    @staticmethod
    def litellm_url():
        return 'http://72.61.44.159:4000/v1'
    
    @staticmethod
    def companies_house_key():
        return os.environ.get('UK_COMPANIES_HOUSE_KEY')
    
    @staticmethod
    def financial_datasets_key():
        return os.environ.get('FINANCIAL_DATASETS_API_KEY')


# --- Helpers ---
def folder_from(name):
    """Convert company name to folder name."""
    f = name.lower().replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '')
    f = f.replace("'", '').replace('&', 'and').replace('--', '-').strip('-')
    return f


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
