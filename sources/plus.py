"""Plus sources: AbstractAPI, Crunchbase scrape (from datasources.py), plus the 7 from sources_plus.py."""
import json, re
from core.utils import fetch
from core.config import Config

# ──────────────────────────────────────────────
#  AbstractAPI (was in scripts/datasources.py)
# ──────────────────────────────────────────────

def abstractapi_enrich(domain):
    """Company enrichment by domain via AbstractAPI."""
    api_key = Config.get('ABSTRACT_API_KEY')
    if not api_key or not domain:
        return None
    import urllib.parse
    clean_domain = domain.replace('https://', '').replace('http://', '').split('/')[0]
    data = fetch(
        f'https://companyenrichment.abstractapi.com/v2/?api_key={api_key}&domain={clean_domain}',
        timeout=10
    )
    if not data:
        return None
    try:
        j = json.loads(data)
        return {
            'employee_count': j.get('employee_count'),
            'employee_range': j.get('employee_range'),
            'annual_revenue': j.get('annual_revenue'),
            'revenue_range': j.get('revenue_range'),
            'industry': j.get('industry'),
            'linkedin_url': j.get('linkedin_url'),
            'type': j.get('type'),
            'ticker': j.get('ticker'),
            'founded_year': j.get('year_founded'),
            'technologies': j.get('technologies', []),
        }
    except (json.JSONDecodeError, KeyError):
        return None

# ──────────────────────────────────────────────
#  Crunchbase HTML scrape (was in scripts/datasources.py)
# ──────────────────────────────────────────────

def crunchbase_info(company_name):
    """Scrape Crunchbase public page for funding/investor data."""
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

# ──────────────────────────────────────────────
#  Wrapper for scripts/sources_plus (the 7 new APIs)
# ──────────────────────────────────────────────

def enrich_plus(company_name, domain=None):
    """Run all 7 plus sources via scripts/sources_plus."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
    from sources_plus import enrich_plus as _ep
    return _ep(company_name, domain)
