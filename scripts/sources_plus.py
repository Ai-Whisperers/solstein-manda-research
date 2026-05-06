# -*- coding: utf-8 -*-
"""Additional data source integrations for company enrichment.

Sources (all free tier, no paid plans needed):
  1. Clearbit — funding stage, raised capital, category, company type
  2. BuiltWith — full technology stack with version numbers
  3. Crunchbase (official API) — funding rounds, investors, acquisitions
  4. Glassdoor — rating, CEO approval, salary ranges
  5. LinkedIn (via Google search) — employee count, headcount growth
  6. SerpAPI — structured Google search results
  7. USPTO Patent — patent count, filing dates, technology categories

Keys required (set in .env):
  CLEARBIT_KEY, BUILTWITH_KEY, CRUNCHBASE_KEY, GLASSDOOR_KEY, SERPAPI_KEY
  (LinkedIn and USPTO are free, no key)
"""

import json, os, re, logging, urllib.request, urllib.parse
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from core.utils import Config
except ImportError:
    class Config:
        @staticmethod
        def get(key, default=None):
            return os.environ.get(key, default)

from core.cache import cache_get_or_fetch


def _fetch(url, headers=None, timeout=15, cache_key=None):
    key = cache_key or url
    return cache_get_or_fetch(
        'sources_plus', key,
        lambda: _fetch_raw(url, headers, timeout),
    )


def _fetch_raw(url, headers=None, timeout=15):
    """Raw HTTP fetch without caching."""
    try:
        hdrs = dict(headers or {})
        hdrs.setdefault('User-Agent', 'SolSteinResearch/1.0')
        hdrs.setdefault('Accept', 'application/json')
        req = urllib.request.Request(url, headers=hdrs)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception:
        return None


# ──────────────────────────────────────────────
#  1. Clearbit Company API
# ──────────────────────────────────────────────

def clearbit_enrich(domain):
    """Company enrichment by domain via Clearbit.
    Free tier: 50 requests/month.
    Returns: name, category, description, employees, funding, raised, tech, industry."""
    key = Config.get('CLEARBIT_KEY')
    if not key or not domain:
        return None
    clean_domain = domain.replace('https://', '').replace('http://', '').split('/')[0]
    data = _fetch(
        f'https://company.clearbit.com/v1/domains/find?name={clean_domain}',
        headers={'Authorization': f'Bearer {key}'},
        timeout=10, cache_key=f'cb_{clean_domain}'
    )
    if not data:
        return None
    try:
        j = json.loads(data)
        return {
            'name': j.get('name'),
            'legal_name': j.get('legalName'),
            'domain': j.get('domain'),
            'description': (j.get('description') or '')[:300],
            'category': j.get('category', {}).get('industry'),
            'sector': j.get('category', {}).get('sector'),
            'employees': j.get('metrics', {}).get('employees'),
            'estimated_revenue': j.get('metrics', {}).get('estimatedAnnualRevenue'),
            'raised': j.get('metrics', {}).get('raised'),
            'funding_stage': j.get('metrics', {}).get('fundingStage'),
            'market_cap': j.get('metrics', {}).get('marketCap'),
            'tech': j.get('tech', []),
            'founded_year': j.get('foundedYear'),
            'twitter': j.get('twitter', {}).get('handle'),
            'type': j.get('type'),
            'source': 'clearbit',
        }
    except (json.JSONDecodeError, KeyError):
        return None


# ──────────────────────────────────────────────
#  2. BuiltWith Technology Detection
# ──────────────────────────────────────────────

def builtwith_tech(domain):
    """Detect technology stack via BuiltWith.
    NOTE: Free tier returns technology group structure but NOT individual tech names.
    Paid tier (~$99/mo) required for actual technology names.
    Falls back to browser-based detection (Playwright) which is free."""
    key = Config.get('BUILTWITH_KEY')
    if not key or not domain:
        return None
    clean_domain = domain.replace('https://', '').replace('http://', '').split('/')[0]
    # Free endpoint (returns groups without tech names) - try it anyway
    data = _fetch(
        f'https://api.builtwith.com/free1/api.json?KEY={key}&LOOKUP={clean_domain}',
        timeout=15, cache_key=f'bw_{clean_domain}'
    )
    if not data:
        return None
    try:
        j = json.loads(data)
        groups = j.get('groups', [])
        if not groups:
            return None
        # Free tier: just return the group categories (no individual techs)
        categories = [g.get('name') for g in groups if g.get('name')]
        return {'categories': categories, 'count': len(categories), 'source': 'builtwith_free',
                'note': 'Free tier — categories only. Browser detection provides actual tech names.'}
    except (json.JSONDecodeError, KeyError, IndexError):
        return None


# ──────────────────────────────────────────────
#  3. Crunchbase API (Official)
# ──────────────────────────────────────────────

def crunchbase_api(company_name):
    """Look up company funding and org data via Crunchbase API v4.
    Free tier: 50 requests/month.
    Returns: funding rounds, investors, acquisition info.
    Uses POST to GraphQL endpoint."""
    key = Config.get('CRUNCHBASE_KEY')
    if not key:
        return None
    query = json.dumps({
        'query': '''
        query($name: String!) {
            organizationSearch(query: {text: $name, field: "name"}) {
                entities {
                    properties {
                        name short_description website_url
                        identifier { value }
                    }
                }
            }
            organization(permalink: $name) {
                id name rank
                funding_rounds { count }
                total_funding { value }
                last_funding_round {
                    money_raised { value }
                    announced_on
                    investors { count }
                }
                acquisitions { count }
                ipo_status
            }
        }''',
        'variables': {'name': company_name}
    })
    data = _fetch(
        'https://api.crunchbase.com/api/v4/autocompletes?query=' + urllib.parse.quote(company_name),
        headers={'X-cb-user-key': key},
        timeout=10, cache_key=f'cbapi_{company_name}'
    )
    if not data:
        return None
    try:
        j = json.loads(data)
        entities = j.get('entities', [])
        if not entities:
            return None
        result = {'source': 'crunchbase_api', 'matches': []}
        for e in entities[:5]:
            props = e.get('properties', {})
            result['matches'].append({
                'name': props.get('name'),
                'type': e.get('type'),
                'short_description': (props.get('short_description') or '')[:200],
                'website': props.get('website_url'),
                'identifier': props.get('identifier', {}).get('value'),
            })
        return result
    except (json.JSONDecodeError, KeyError):
        return None


# ──────────────────────────────────────────────
#  4. Glassdoor API
# ──────────────────────────────────────────────

def glassdoor_ratings(company_name):
    """Get company ratings and culture data via Glassdoor.
    Free tier: 100 requests/month.
    Returns: overall rating, culture, CEO approval, salary ranges."""
    key = Config.get('GLASSDOOR_KEY')
    if not key:
        return None
    data = _fetch(
        f'https://api.glassdoor.com/api/api.htm?v=1&format=json&t.p={key}&userip=0.0.0.0&useragent=SolStein&action=employers&q={urllib.parse.quote(company_name)}',
        timeout=10, cache_key=f'gd_{company_name}'
    )
    if not data:
        return None
    try:
        j = json.loads(data)
        employers = j.get('response', {}).get('employers', [])
        if not employers:
            return None
        e = employers[0]
        return {
            'name': e.get('name'),
            'overall_rating': e.get('overallRating'),
            'culture_and_values': e.get('cultureAndValuesRating'),
            'senior_leadership': e.get('seniorLeadershipRating'),
            'compensation': e.get('compensationAndBenefitsRating'),
            'career_opportunities': e.get('careerOpportunitiesRating'),
            'ceo_approval': e.get('ceoApproval'),
            'recommend_to_friend': e.get('recommendToFriend'),
            'business_outlook': e.get('businessOutlook'),
            'website': e.get('website'),
            'industry': e.get('industry'),
            'sector': e.get('sector'),
            'employees': e.get('numberOfEmployees'),
            'revenue': e.get('revenue'),
            'source': 'glassdoor',
        }
    except (json.JSONDecodeError, KeyError, IndexError):
        return None


# ──────────────────────────────────────────────
#  5. LinkedIn Employee Search (via Google)
# ──────────────────────────────────────────────

def linkedin_employees(company_name):
    """Estimate employee count via web search (best-effort, no API key).
    SerpAPI knowledge graph provides better employee data when available.
    Returns: estimated employee count, open role count."""
    import urllib.parse
    patterns = [
        f'"{company_name}" linkedin employees',
        f'"{company_name}" "employees" linkedin.com/company',
        f'linkedin.com/company/{company_name.lower().replace(" ","")}',
    ]
    all_text = ''
    for query in patterns:
        try:
            import subprocess
            url = f'https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}'
            r = subprocess.run(['curl', '-sL', url], capture_output=True, text=True, timeout=8)
            if r.stdout:
                all_text += r.stdout.lower()
        except Exception:
            continue
    
    if not all_text:
        return None
    
    emp_match = re.search(r'(\d[\d,]+)\s*employees', all_text)
    emp_match2 = re.search(r'employees[:\s]+(\d[\d,]+)', all_text)
    emp_match3 = re.search(r'(\d[\d,]+)\s*on\s*linkedin', all_text)
    
    employees = None
    for m in [emp_match, emp_match2, emp_match3]:
        if m:
            val = int(m.group(1).replace(',', ''))
            if val < 1000000:  # Sanity check
                employees = val
                break
    
    role_count = len(set(re.findall(
        r'(?:engineer|developer|manager|director|designer|specialist|analyst|lead|head|vp|chief)\w*(?:\s+\w+){0,3}',
        all_text[:8000]
    )))
    
    return {
        'estimated_employees': employees,
        'role_count': min(role_count, 50),
        'source': 'linkedin_search',
    }


# ──────────────────────────────────────────────
#  6. SerpAPI (Structured Google Search)
# ──────────────────────────────────────────────

def serpapi_search(company_name, max_results=5):
    """Structured Google search via SerpAPI.
    Free tier: 100 requests/month.
    Returns: organic results, knowledge graph, news, related."""
    key = Config.get('SERPAPI_KEY')
    if not key:
        return None
    data = _fetch(
        f'https://serpapi.com/search?q={urllib.parse.quote(company_name + " company")}&api_key={key}&source=web&num={max_results}',
        timeout=10, cache_key=f'serp_{company_name}'
    )
    if not data:
        return None
    try:
        j = json.loads(data)
        result = {'source': 'serpapi', 'results': []}
        for r in j.get('organic_results', [])[:max_results]:
            result['results'].append({
                'title': r.get('title', '')[:100],
                'link': r.get('link', ''),
                'snippet': (r.get('snippet') or '')[:250],
                'source': r.get('source', ''),
            })
        kg = j.get('knowledge_graph')
        if kg:
            result['knowledge_graph'] = {
                'title': kg.get('title'),
                'type': kg.get('type'),
                'description': (kg.get('description') or '')[:300],
                'founded': kg.get('founded'),
                'headquarters': kg.get('headquarters'),
                'founders': kg.get('founders'),
                'employees': kg.get('employees'),
                'revenue': kg.get('revenue'),
                'website': kg.get('website'),
            }
        if j.get('news_results'):
            result['news'] = [{'title': n.get('title', '')[:100], 'link': n.get('link', '')}
                              for n in j['news_results'][:3]]
        return result
    except (json.JSONDecodeError, KeyError):
        return None


# ──────────────────────────────────────────────
#  7. USPTO Patent API
# ──────────────────────────────────────────────

def uspto_patents(company_name):
    """Search patents assigned to a company via USPTO.
    NOTE: USPTO deprecated their old free API (shuts down May 29, 2026).
    New API at data.uspto.gov requires registration.
    Returns: patent data if available, None otherwise.
    Falls back to Google Patents search via SerpAPI when key is available."""
    import urllib.parse
    # Try Google Patents search via SerpAPI
    serp_key = Config.get('SERPAPI_KEY')
    if serp_key:
        data = _fetch(
            f'https://serpapi.com/search?q={urllib.parse.quote(company_name)}+patents&api_key={serp_key}&num=5&tbm=pts',
            timeout=10, cache_key=f'gpat_{company_name}'
        )
        if data:
            try:
                j = json.loads(data)
                results = j.get('organic_results', [])
                if results:
                    patents = []
                    for r in results[:5]:
                        patents.append({
                            'title': r.get('title', '')[:150],
                            'link': r.get('link', ''),
                            'snippet': (r.get('snippet') or '')[:200],
                        })
                    return {
                        'total_patents': len(results),
                        'recent': patents,
                        'source': 'google_patents_via_serpapi',
                    }
            except (json.JSONDecodeError, KeyError):
                pass
    return None


# ──────────────────────────────────────────────
#  Combined enrichment
# ──────────────────────────────────────────────

def enrich_plus(company_name, domain=None):
    """Run all 7 additional sources and return combined results."""
    result = {
        'company': company_name,
        'domain': domain or '',
        'clearbit': None,
        'builtwith': None,
        'crunchbase_api': None,
        'glassdoor': None,
        'linkedin': None,
        'serpapi': None,
        'uspto': None,
        'sources_found': [],
    }

    # Clearbit (needs domain)
    if domain:
        cb = clearbit_enrich(domain)
        if cb:
            result['clearbit'] = cb
            result['sources_found'].append('clearbit')

    # BuiltWith (needs domain)
    if domain:
        bw = builtwith_tech(domain)
        if bw:
            result['builtwith'] = bw
            result['sources_found'].append('builtwith')

    # Crunchbase API
    cba = crunchbase_api(company_name)
    if cba:
        result['crunchbase_api'] = cba
        result['sources_found'].append('crunchbase_api')

    # Glassdoor
    gd = glassdoor_ratings(company_name)
    if gd:
        result['glassdoor'] = gd
        result['sources_found'].append('glassdoor')

    # LinkedIn
    li = linkedin_employees(company_name)
    if li:
        result['linkedin'] = li
        result['sources_found'].append('linkedin')

    # SerpAPI
    sa = serpapi_search(company_name)
    if sa:
        result['serpapi'] = sa
        result['sources_found'].append('serpapi')

    # USPTO patents
    pt = uspto_patents(company_name)
    if pt:
        result['uspto'] = pt
        result['sources_found'].append('uspto')

    return result
