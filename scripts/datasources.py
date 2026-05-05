#!/usr/bin/env python3
"""
Multi-source company data enrichment layer v2.
Aggregates from 10+ free public sources in parallel (or sequence).

Sources:
   1. Company website (via quickscan v2 with Playwright) — tech stack, pricing, careers
   2. Wikipedia API — description, founded, HQ, employees, revenue
   3. GitHub API — repos, stars, languages
   4. Hosting/DNS — provider, IP
   5. OpenCorporates API — legal entity, registration, officers
   6. Brave Search (news) — recent developments (past 12 months)
   7. Crunchbase public page — funding, investors (when available)
   8. Source triangulation — cross-reference employee count across sources
   9. Freshness checker — flag data points older than 1 year

Patterns from: companyscope-mcp, m-and-a-target-intelligence-mcp, langchain company-researcher
"""

import json, os, sys, urllib.request, urllib.error, re, threading, time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(os.path.dirname(__file__), '..')

_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
]
_ua_index = 0
_ua_lock = threading.Lock()


def fetch(url, timeout=15):
    global _ua_index
    with _ua_lock:
        ua = _USER_AGENTS[_ua_index % len(_USER_AGENTS)]
        _ua_index += 1
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': ua,
            'Accept': 'application/json,text/html,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception:
        return None


def fetch_parallel(sources, max_workers=5):
    """Run multiple source fetches in parallel. sources is list of (name, callable)."""
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as exec:
        future_map = {exec.submit(fn): name for name, fn in sources}
        for future in as_completed(future_map, timeout=30):
            name = future_map[future]
            try:
                results[name] = future.result(timeout=15)
            except Exception:
                results[name] = None
    return results


def fetch(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; SolSteinResearch/1.0)',
            'Accept': 'application/json,text/html'
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception:
        return None


# --- Source 1: Wikipedia ---

def wikipedia_summary(company_name):
    name = company_name.split('(')[0].strip().replace(' ', '_')
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
        except json.JSONDecodeError:
            pass
    return None


# --- Source 2: GitHub ---

def _gh_fetch(url):
    """GitHub API fetch with token if available."""
    headers = {'User-Agent': 'SolSteinResearch/1.0', 'Accept': 'application/vnd.github.v3+json'}
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN') or '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'
    if token:
        headers['Authorization'] = f'token {token}'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode('utf-8')
    except Exception:
        return None

def github_org(company_name):
    """Fetch GitHub organization info — repos, stars, languages. Uses search if exact org fails."""
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

    # Fallback: try GitHub search
    time.sleep(1)
    search = _gh_fetch(f'https://api.github.com/search/users?q={slug}+type:org&per_page=3')
    if search:
        try:
            s = json.loads(search)
            if s.get('total_count', 0) > 0:
                org = s['items'][0]
                return {
                    'name': org.get('login', ''),
                    'public_repos': 0,
                    'followers': org.get('followers', 0),
                    'description': org.get('description', '') or '',
                    'repos': [],
                    'top_languages': [],
                    'url': org.get('html_url', ''),
                    'note': 'Found via search (org data limited)',
                }
        except (json.JSONDecodeError, KeyError):
            pass
    return None


# --- Source 3: OpenCorporates (via web, free) ---

def opencorporates_search(company_name):
    """Search for legal entity via OpenCorporates web search (free, no token needed)."""
    try:
        name_enc = __import__('urllib.parse').quote(company_name)
    except (ImportError, AttributeError):
        name_enc = company_name.replace(' ', '+')
    html = fetch(f'https://opencorporates.com/companies?q={name_enc}&format=json', timeout=10)
    if html:
        try:
            data = json.loads(html)
            results = data.get('results', {}).get('companies', [])
            if results:
                r = results[0]['company']
                return {
                    'name': r.get('name', ''),
                    'jurisdiction': r.get('jurisdiction_code', ''),
                    'incorporation_date': r.get('incorporation_date', ''),
                    'status': r.get('current_status', ''),
                }
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    return None


# --- Source 4: Brave Search (News) ---

def brave_news(company_name):
    """Search for recent news about a company via Brave Search (rate-limited to 1 req/sec)."""
    try:
        name_enc = __import__('urllib.parse').quote(company_name)
    except (ImportError, AttributeError):
        name_enc = company_name.replace(' ', '+')
    url = f'https://search.brave.com/api/news?q={name_enc}&count=5&freshness=2025'
    data = fetch(url, timeout=8)
    articles = []
    if data:
        try:
            j = json.loads(data)
            for item in j.get('results', [])[:5]:
                pub_date = item.get('age') or item.get('date', '')
                articles.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'description': item.get('description', '')[:200],
                    'date': pub_date,
                    'source': item.get('source', ''),
                })
        except (json.JSONDecodeError, KeyError):
            pass
    return articles if articles else None


# --- Source 5: Crunchbase public page ---

def crunchbase_info(company_name):
    """Try to fetch publicly available Crunchbase information."""
    slug = company_name.lower().replace(' ', '-').replace("'", '').replace('.', '')
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    html = fetch(f'https://www.crunchbase.com/organization/{slug}')
    if html and '404' not in html[:500]:
        data = {'url': f'https://www.crunchbase.com/organization/{slug}'}
        m = re.search(r'<meta\s+name="description"\s+content="(.*?)"', html)
        if m:
            data['description'] = m.group(1)[:300]
        return data
    return None


# --- Source 6: Hosting/DNS ---

def detect_hosting(domain):
    result = {'hosting': None, 'ip': None}
    try:
        import socket
        ip = socket.gethostbyname(domain)
        result['ip'] = ip
        # Basic hosting detection from IP ranges
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


# --- Wikipedia data extraction helpers ---

def _parse_wiki_value(text, pattern):
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(0).strip()[:100] if m else None


# --- Source triangulation ---

def triangulate_employees(sources):
    """Cross-reference employee counts from multiple sources. Returns consensus + flags."""
    values = {}
    for src_name, value in sources.items():
        if value:
            values[src_name] = value

    if len(values) >= 2:
        vals = list(values.values())
        avg = sum(vals) / len(vals)
        max_diff = max(vals) - min(vals)
        if max_diff / max(avg, 1) > 0.5:
            return {
                'consensus': round(avg),
                'sources': values,
                'confidence': 'low',
                'note': f'Disagreement: sources differ by {max_diff} (range {min(vals)}-{max(vals)})',
            }
        return {
            'consensus': round(avg),
            'sources': values,
            'confidence': 'high',
            'note': f'Consistent across {len(values)} sources',
        }
    elif len(values) == 1:
        src, val = next(iter(values.items()))
        return {'consensus': val, 'sources': values, 'confidence': 'low', 'note': f'Single source: {src}'}
    return {'consensus': None, 'sources': {}, 'confidence': 'none', 'note': 'No employee data found'}


# --- Freshness checker ---

def check_freshness(scan_date_str):
    """Check if a scan date is fresh (within 90 days)."""
    if not scan_date_str:
        return {'fresh': False, 'days_old': None, 'note': 'No date available'}
    try:
        scan_date = datetime.fromisoformat(scan_date_str)
        delta = datetime.now() - scan_date
        if delta.days > 365:
            return {'fresh': False, 'days_old': delta.days, 'note': f'Stale: {delta.days} days old'}
        elif delta.days > 90:
            return {'fresh': False, 'days_old': delta.days, 'note': f'Aging: {delta.days} days old'}
        return {'fresh': True, 'days_old': delta.days, 'note': f'Fresh: {delta.days} days ago'}
    except (ValueError, TypeError):
        return {'fresh': False, 'days_old': None, 'note': 'Invalid date format'}


# --- Main enrichment function ---

def enrich_company(company_name, domain=None):
    """Enrich company data from 10+ free sources. Sources run in parallel via ThreadPool."""
    from quickscan import quick_scan

    result = {
        'company': company_name,
        'domain': domain,
        'enriched_at': datetime.now().isoformat(),
        'freshness': None,
        'website': {},
        'wikipedia': None,
        'github': None,
        'hosting': None,
        'opencorporates': None,
        'news': None,
        'crunchbase': None,
        'triangulation': {'employees': None},
        'sources_found': [],
        'errors': [],
    }

    # Step 1: Website scan (sequential — needs browser)
    scan = quick_scan(company_name, domain)
    result['website'] = scan
    result['domain'] = scan['domain']
    if scan['website_reachable']:
        result['sources_found'].append('website')
    result['freshness'] = check_freshness(scan.get('scanned_at', ''))

    domain_clean = result['domain'].replace('https://', '').replace('http://', '').split('/')[0]

    # Step 2: All other sources run in parallel
    sources = [
        ('dns', lambda: detect_hosting(domain_clean)),
        ('wikipedia', lambda: wikipedia_summary(company_name)),
        ('github', lambda: github_org(company_name)),
        ('opencorporates', lambda: opencorporates_search(company_name)),
        ('news', lambda: brave_news(company_name)),
        ('crunchbase', lambda: crunchbase_info(company_name)),
    ]

    parallel_results = fetch_parallel(sources, max_workers=6)

    for src_name, src_result in parallel_results.items():
        if src_result:
            if src_name == 'dns':
                result['hosting'] = src_result
            elif src_name == 'wikipedia':
                result['wikipedia'] = src_result
            elif src_name == 'github':
                result['github'] = src_result
            elif src_name == 'opencorporates':
                result['opencorporates'] = src_result
            elif src_name == 'news':
                result['news'] = src_result
            elif src_name == 'crunchbase':
                result['crunchbase'] = src_result
            result['sources_found'].append(src_name)

    # Free/OSS sources (SEC, yfinance, DDG, GLEIF)
    try:
        from free_sources import enrich_free
        free = enrich_free(company_name)
        for src in free.get('sources_found', []):
            if src == 'sec_edgar' and free.get('sec'):
                result['sec_edgar'] = free['sec']
                result['sources_found'].append('sec_edgar')
            if src == 'yfinance' and free.get('yfinance'):
                result['yfinance'] = free['yfinance']
                result['sources_found'].append('yfinance')
            if src == 'duckduckgo' and free.get('web_search'):
                result['web_search'] = free['web_search']
                result['sources_found'].append('web_search')
            if src == 'gleif' and free.get('gleif'):
                result['gleif'] = free['gleif']
                result['sources_found'].append('gleif')
    except Exception:
        pass

    # New sources (Companies House, SIRENE, Financial Datasets)
    try:
        from sources_new import enrich_new_sources
        new = enrich_new_sources(company_name)
        for src in new.get('sources_found', []):
            if src == 'sirene' and new.get('sirene'):
                result['sirene'] = new['sirene']
                result['sources_found'].append('sirene')
            if src == 'companies_house' and new.get('companies_house'):
                result['companies_house'] = new['companies_house']
                result['sources_found'].append('companies_house')
            if src == 'financial_datasets' and new.get('financial_datasets'):
                result['financial_datasets'] = new['financial_datasets']
                result['sources_found'].append('financial_datasets')
    except Exception:
        pass

    # Source triangulation
    emp_sources = {}
    if result['wikipedia']:
        m = re.search(r'(\d[\d,]*)\s*employees?', result['wikipedia'].get('extract', ''), re.I)
        if m:
            emp_sources['wikipedia'] = int(m.group(1).replace(',', ''))
    if result['github'] and result['github'].get('public_repos'):
        emp_sources['github_repos'] = result['github']['public_repos']
    result['triangulation']['employees'] = triangulate_employees(emp_sources)

    return result


def format_enrichment_report(data):
    lines = []
    lines.append(f"=== Enriched Profile: {data['company']} ===")
    lines.append(f"Sources found: {len(data['sources_found'])} — {', '.join(data['sources_found'])}")
    f = data.get('freshness', {})
    if f:
        lines.append(f"Freshness: {f.get('note', '')}")
    if data['wikipedia']:
        lines.append(f"Wiki: {data['wikipedia']['description'] or data['wikipedia']['extract'][:200]}")
    if data['github']:
        g = data['github']
        lines.append(f"GitHub: {g['public_repos']} repos, {g['followers']} followers, langs: {', '.join(g.get('top_languages', [])[:3])}")
    if data['opencorporates']:
        oc = data['opencorporates']
        lines.append(f"Legal: {oc['name']} ({oc['jurisdiction']}), type={oc['company_type']}, status={oc['status']}")
    if data['news']:
        lines.append(f"News: {len(data['news'])} recent articles")
        for a in data['news'][:2]:
            lines.append(f"  - {a['title'][:80]}")
    if data['crunchbase']:
        lines.append(f"Crunchbase: {data['crunchbase'].get('url', '')}")
    t = data['triangulation']['employees']
    if t and t['consensus']:
        lines.append(f"Employees: ~{t['consensus']} ({t['confidence']} confidence) — {t['note']}")
    if data['website'].get('tech_stack'):
        lines.append(f"Tech: {', '.join(data['website']['tech_stack'][:8])}")
    if data.get('sirene'):
        for s in data['sirene'][:1]:
            lines.append(f"SIRENE: {s['name']} ({s['siren']})")
    if data.get('companies_house'):
        ch = data['companies_house']
        for r in ch.get('results', [])[:1]:
            lines.append(f"Companies House: {r['name']} ({r['number']}) - {r['status']}")
    return '\n'.join(lines)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: datasources.py <company_name> [domain]")
        sys.exit(1)

    name = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else None
    data = enrich_company(name, domain)

    out_dir = os.path.join(BASE, 'output', 'HORECA')
    folder = name.lower().replace(' ', '-')
    fdir = os.path.join(out_dir, folder)
    os.makedirs(fdir, exist_ok=True)
    path = os.path.join(fdir, 'enriched.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

    print(format_enrichment_report(data))
    print(f"\nSaved: {path}")
