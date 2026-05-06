"""Enrichment orchestrator — runs all sources and merges results into one dict."""
import json, os, sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from core.utils import fetch, fetch_parallel, atomic_json_dump, check_freshness, triangulate_employees
from sources.free import wikipedia_summary, github_org, brave_news, detect_hosting, enrich_free
from sources.plus import abstractapi_enrich, crunchbase_info
from sources.mcp import opencorporates_search


def enrich_company(company_name, domain=None):
    """Enrich company data from 25+ sources. Runs parallel fetches where possible."""
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

    # Step 1: Website scan (needs browser, run first)
    scan = quick_scan(company_name, domain)
    result['website'] = scan
    result['domain'] = scan['domain']
    if scan['website_reachable']:
        result['sources_found'].append('website')
    result['freshness'] = check_freshness(scan.get('scanned_at', ''))

    domain_clean = result['domain'].replace('https://', '').replace('http://', '').split('/')[0]

    # Step 2: Parallel sources
    p_sources = [
        ('dns', lambda: detect_hosting(domain_clean)),
        ('wikipedia', lambda: wikipedia_summary(company_name)),
        ('github', lambda: github_org(company_name)),
        ('opencorporates', lambda: opencorporates_search(company_name)),
        ('news', lambda: brave_news(company_name)),
        ('crunchbase', lambda: crunchbase_info(company_name)),
    ]
    parallel = fetch_parallel(p_sources, max_workers=6)
    for src_name, src_result in parallel.items():
        if src_result:
            result[src_name if src_name != 'dns' else 'hosting'] = src_result
            result['sources_found'].append(src_name)

    # Step 3: Free/OSS sources
    free = enrich_free(company_name)
    for src in free.get('sources_found', []):
        key_map = {'sec_edgar': 'sec_edgar', 'yfinance': 'yfinance',
                   'duckduckgo': 'web_search', 'gleif': 'gleif', 'wikipedia': 'wikipedia'}
        sk = key_map.get(src)
        if sk and free.get(sk):
            result[sk] = free[sk]
            result['sources_found'].append(sk)

    # Step 4: AbstractAPI
    aa = abstractapi_enrich(scan.get('domain', ''))
    if aa:
        result['abstractapi'] = aa
        result['sources_found'].append('abstractapi')

    # Step 5: New sources (Companies House, SIRENE, Financial Datasets)
    try:
        from sources_new import enrich_new_sources
        new = enrich_new_sources(company_name)
        for src in new.get('sources_found', []):
            if src in new and new[src]:
                result[src] = new[src]
                result['sources_found'].append(src)
    except Exception:
        pass

    # Step 6: Plus sources (Clearbit, BuiltWith, Crunchbase API, Glassdoor, LinkedIn, SerpAPI, USPTO)
    try:
        from sources_plus import enrich_plus
        plus = enrich_plus(company_name, result.get('domain'))
        for src in plus.get('sources_found', []):
            if src in plus and plus[src]:
                result[src] = plus[src]
                result['sources_found'].append(src)
    except Exception:
        pass

    # Employee triangulation
    emp = {}
    if result.get('wikipedia'):
        import re
        m = re.search(r'(\d[\d,]*)\s*employees?', result['wikipedia'].get('extract', ''), re.I)
        if m:
            emp['wikipedia'] = int(m.group(1).replace(',', ''))
    gh = result.get('github')
    if gh and gh.get('public_repos'):
        emp['github_repos'] = gh['public_repos']
    result['triangulation']['employees'] = triangulate_employees(emp)

    return result


def format_enrichment_report(data):
    lines = [f"=== Enriched Profile: {data['company']} ==="]
    lines.append(f"Sources found: {len(data['sources_found'])} — {', '.join(data['sources_found'])}")
    f = data.get('freshness', {})
    if f:
        lines.append(f"Freshness: {f.get('note', '')}")
    if data.get('wikipedia'):
        w = data['wikipedia']
        lines.append(f"Wiki: {w.get('description') or w.get('extract', '')[:200]}")
    if data.get('github'):
        g = data['github']
        lines.append(f"GitHub: {g['public_repos']} repos, {g['followers']} followers")
    if data.get('opencorporates'):
        oc = data['opencorporates']
        lines.append(f"Legal: {oc['name']} ({oc.get('jurisdiction', '')})")
    if data.get('news'):
        lines.append(f"News: {len(data['news'])} articles")
    if data.get('crunchbase'):
        lines.append(f"Crunchbase: {data['crunchbase'].get('url', '')}")
    t = data.get('triangulation', {}).get('employees', {})
    if t and t.get('consensus'):
        lines.append(f"Employees: ~{t['consensus']} ({t.get('confidence', '?')})")
    if data.get('website', {}).get('tech_stack'):
        lines.append(f"Tech: {', '.join(data['website']['tech_stack'][:8])}")
    return '\n'.join(lines)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 -m sources.enrichment <company_name> [domain]")
        sys.exit(1)
    name = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else None
    data = enrich_company(name, domain)
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'HORECA')
    folder = name.lower().replace(' ', '-')
    fdir = os.path.join(out_dir, folder)
    os.makedirs(fdir, exist_ok=True)
    path = os.path.join(fdir, 'enriched.json')
    atomic_json_dump(data, path, indent=2)
    print(format_enrichment_report(data))
    print(f"\nSaved: {path}")
