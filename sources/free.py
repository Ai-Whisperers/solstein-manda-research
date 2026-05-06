"""Free/OSS data sources: Wikipedia, GitHub, SEC, yfinance, DDG, GLEIF, Brave News, DNS, World Bank."""
import json, os, re, time, socket
from datetime import datetime

from core.utils import fetch, safe_json_loads
from core.config import Config

# ──────────────────────────────────────────────
#  Wikipedia
# ──────────────────────────────────────────────

def wikipedia_summary(company_name):
    base = company_name.split('(')[0].strip().replace(' ', '_')
    candidates = [f"{base}_(company)", base, f"{base}_(software)", f"{base}_(website)",
                  f"{base}_(software_company)", f"{base}_(technology_company)"]
    for name in candidates:
        data = fetch(f'https://en.wikipedia.org/api/rest_v1/page/summary/{name}')
        if data:
            try:
                j = json.loads(data)
                if j.get('extract') and 'may refer to' not in j.get('extract', ''):
                    return {
                        'title': j.get('title', ''),
                        'description': j.get('description', ''),
                        'extract': j.get('extract', '')[:800],
                        'url': f"https://en.wikipedia.org/wiki/{name}",
                    }
            except (json.JSONDecodeError, KeyError):
                continue
    return None

# ──────────────────────────────────────────────
#  GitHub
# ──────────────────────────────────────────────

import urllib.request as _urllib_request

def _gh_fetch(url):
    headers = {'User-Agent': 'SolSteinResearch/1.0', 'Accept': 'application/vnd.github.v3+json'}
    token = Config.github_token()
    if token:
        headers['Authorization'] = f'token {token}'
    try:
        req = _urllib_request.Request(url, headers=headers)
        with _urllib_request.urlopen(req, timeout=10) as resp:
            return resp.read().decode('utf-8')
    except Exception:
        return None

def github_org(company_name):
    slug = company_name.lower().replace(' ', '').replace('-', '').replace('.', '').replace("'", '')
    data = _gh_fetch(f'https://api.github.com/orgs/{slug}')
    if data:
        try:
            org = json.loads(data)
            if org.get('login'):
                repos_data = fetch(org['repos_url'] + '?per_page=10&sort=updated')
                repos = json.loads(repos_data) if repos_data else []
                lang_stats = {}
                for r in repos[:10]:
                    l = r.get('language')
                    if l:
                        lang_stats[l] = lang_stats.get(l, 0) + 1
                return {
                    'name': org.get('name', ''),
                    'public_repos': org.get('public_repos', 0),
                    'followers': org.get('followers', 0),
                    'description': org.get('description', ''),
                    'repos': [{'name': r['name'], 'stars': r.get('stargazers_count', 0),
                              'language': r.get('language', '')} for r in repos[:5]],
                    'top_languages': sorted(lang_stats, key=lang_stats.get, reverse=True)[:5],
                    'url': org.get('html_url', ''),
                }
        except (json.JSONDecodeError, KeyError):
            pass
    time.sleep(1)
    search = _gh_fetch(f'https://api.github.com/search/users?q={slug}+type:org&per_page=3')
    if search:
        try:
            s = json.loads(search)
            if s.get('total_count', 0) > 0:
                org = s['items'][0]
                return {
                    'name': org.get('login', ''),
                    'public_repos': 0, 'followers': org.get('followers', 0),
                    'description': org.get('description', '') or '',
                    'repos': [], 'top_languages': [],
                    'url': org.get('html_url', ''),
                    'note': 'Found via search (org data limited)',
                }
        except (json.JSONDecodeError, KeyError):
            pass
    return None

# ──────────────────────────────────────────────
#  Brave News
# ──────────────────────────────────────────────

def brave_news(company_name):
    import urllib.parse
    url = f'https://search.brave.com/api/news?q={urllib.parse.quote(company_name)}&count=5&freshness=2025'
    data = fetch(url, timeout=8)
    if not data:
        return None
    try:
        j = json.loads(data)
        articles = []
        for item in j.get('results', [])[:5]:
            articles.append({
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'description': item.get('description', '')[:200],
                'date': item.get('age') or item.get('date', ''),
                'source': item.get('source', ''),
            })
        return articles if articles else None
    except (json.JSONDecodeError, KeyError):
        return None

# ──────────────────────────────────────────────
#  DNS / Hosting
# ──────────────────────────────────────────────

def detect_hosting(domain):
    result = {'hosting': None, 'ip': None}
    try:
        ip = socket.gethostbyname(domain)
        result['ip'] = ip
        if ip.startswith('104.') or ip.startswith('172.'):
            result['hosting'] = 'Cloudflare'
        elif ip.startswith('52.') or ip.startswith('54.'):
            result['hosting'] = 'AWS'
        elif ip.startswith('34.') or ip.startswith('35.'):
            result['hosting'] = 'Google Cloud'
        elif ip.startswith('13.'):
            result['hosting'] = 'AWS (us-east)'
    except Exception:
        pass
    return result

# ──────────────────────────────────────────────
#  Combined enrichment (wraps scripts/free_sources)
# ──────────────────────────────────────────────

def enrich_free(company_name, domain=None, ticker=None, country=None):
    """Run all free data sources from scripts/free_sources."""
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', 'scripts'))
    from free_sources import enrich_free as _ef
    return _ef(company_name, domain, ticker, country)
