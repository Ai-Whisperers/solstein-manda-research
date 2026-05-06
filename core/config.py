"""Centralized configuration. All env vars, API keys, paths, and defaults in one place."""
import os

# Auto-load .env on import when running as script
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                _k, _v = _k.strip(), _v.strip().strip("'\"")
                if _k and not os.environ.get(_k):
                    os.environ[_k] = _v


class Config:
    """All configuration — env vars, paths, defaults. Single source of truth."""

    # ─── Generic ───
    @staticmethod
    def get(key, default=None):
        return os.environ.get(key, default)

    # ─── API Keys ───
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
        return None

    @staticmethod
    def abstractapi_key():
        return os.environ.get('ABSTRACT_API_KEY')

    @staticmethod
    def clearbit_key():
        return os.environ.get('CLEARBIT_KEY')

    @staticmethod
    def builtwith_key():
        return os.environ.get('BUILTWITH_KEY')

    @staticmethod
    def crunchbase_key():
        return os.environ.get('CRUNCHBASE_KEY')

    @staticmethod
    def glassdoor_key():
        return os.environ.get('GLASSDOOR_KEY')

    @staticmethod
    def serpapi_key():
        return os.environ.get('SERPAPI_KEY')

    @staticmethod
    def litellm_key():
        return os.environ.get('LITELLM_KEY')

    @staticmethod
    def litellm_url():
        return os.environ.get('LITELLM_URL') or 'http://72.61.44.159:4000/v1'

    @staticmethod
    def companies_house_key():
        return os.environ.get('UK_COMPANIES_HOUSE_KEY')

    @staticmethod
    def financial_datasets_key():
        return os.environ.get('FINANCIAL_DATASETS_API_KEY')

    # ─── Paths ───
    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    HORECA_DIR = os.path.join(BASE, 'output', 'HORECA')
    JOHN_JSON = os.path.join(BASE, 'archive', 'john-original', 'horeca_json', 'horeca_data.json')
    CACHE_DIR = os.path.join(BASE, 'output', '.cache')

    # ─── Defaults / Timeouts ───
    TIMEOUT_DEFAULT = 15
    TIMEOUT_SLOW = 60
    TIMEOUT_FAST = 10
    MAX_WORKERS = 6
    CACHE_TTL = 7 * 24 * 3600  # 7 days
    USER_AGENT = 'SolSteinResearch/1.0'
