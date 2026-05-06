import logging
logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
MCP server integrations for company data enrichment.
Each source is a standalone function that returns structured data or None.

Sources:
  1. Coresignal — 74M companies, 823M employees, 399M jobs (MCP, free tier)
  2. Bright Data — 200+ data sources including Crunchbase, LinkedIn (MCP, free tier 5K/mo)
  3. CompanyScope — 8 sources aggregated (Apify, 25 free calls/day)
  4. OpenRegistry — 27 national registries, real-time government data (free, no key)
  
Pattern: apifyforge MCP servers, coresignal MCP, Bright Data MCP
"""

import json, os, sys, urllib.request, urllib.error, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(os.path.dirname(__file__), '..')

_CACHE = {}
_CACHE_TTL = 3600


def _fetch(url, headers=None, timeout=20, cache_key=None):
    key = cache_key or url
    if key in _CACHE:
        entry = _CACHE[key]
        if (datetime.now() - entry['time']).seconds < _CACHE_TTL:
            return entry['data']
    try:
        req = urllib.request.Request(url, headers=headers or {
            'User-Agent': 'SolSteinResearch/1.0',
            'Accept': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode('utf-8', errors='replace')
            _CACHE[key] = {'data': data, 'time': datetime.now()}
            return data
    except Exception:
        return None


# --- Source 1: Coresignal (MCP, free tier) ---

def coresignal_company(company_name, api_key=None):
    """Search Coresignal's 74M company records. Requires API key from coresignal.com."""
    key = api_key or os.environ.get('CORESIGNAL_API_KEY')
    if not key:
        return None
    data = _fetch(
        f'https://mcp.coresignal.com/mcp?company={company_name}&apikey={key}',
        timeout=20, cache_key=f'coresignal_{company_name}'
    )
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            pass
    return None


# --- Source 2: Bright Data MCP (200+ sources, free tier 5K/mo) ---

def brightdata_crunchbase(company_name, api_token=None):
    """Get Crunchbase data via Bright Data's web data API. Free tier: 5K requests/month."""
    token = api_token or os.environ.get('BRIGHTDATA_API_TOKEN')
    if not token:
        return {'error': 'No BRIGHTDATA_API_TOKEN set. Get one at brightdata.com'}
    # Bright Data's MCP endpoint for Crunchbase
    payload = json.dumps({'company': company_name}).encode()
    url = 'https://api.brightdata.com/mcp/web_data_crunchbase_company'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}


def brightdata_linkedin(company_name, api_token=None):
    """Get LinkedIn company data via Bright Data."""
    token = api_token or os.environ.get('BRIGHTDATA_API_TOKEN')
    if not token:
        return {'error': 'No BRIGHTDATA_API_TOKEN'}
    payload = json.dumps({'company': company_name}).encode()
    url = 'https://api.brightdata.com/mcp/web_data_linkedin_company'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}


# --- Source 3: CompanyScope (Apify, 8 sources, 25 free calls/day) ---

def companyscope_lookup(company_name, api_token=None):
    """CompanyScope — 8 sources: Wikipedia, SEC, GitHub, OpenCorporates, RDAP, DNS, social, careers.
    Free tier: 25 calls/day on Apify."""
    token = api_token or os.environ.get('APIFY_API_TOKEN')
    if not token:
        return {'error': 'No APIFY_API_TOKEN set. Get one at apify.com.'}
    payload = json.dumps({'company': company_name}).encode()
    url = 'https://api.apify.com/v2/acts/stewyboy1990~companyscope-mcp/run-sync-get-dataset-items'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {'error': str(e)}


# --- Source 4: OpenRegistry (27 national registries, free, no key) ---

def openregistry_search(company_name, jurisdiction=None):
    """OpenRegistry — 27 national company registries. Free: 20 req/min per IP. No API key."""
    import urllib.parse
    encoded = urllib.parse.quote(company_name)
    url = f'https://openregistry.sophymarine.com/mcp?q={encoded}'
    if jurisdiction:
        url += f'&jurisdiction={jurisdiction}'
    data = _fetch(url, timeout=20, cache_key=f'openreg_{company_name}')
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            pass
    return {'error': 'No data returned'}


# --- Combined MCP enrichment ---

def enrich_mcp(company_name, domain=None):
    """Run all MCP sources with available API keys. Returns combined results."""
    result = {
        'company': company_name,
        'domain': domain or '',
        'enriched_at': datetime.now().isoformat(),
        'sources_found': [],
    }

    # Try OpenRegistry (free, no key needed)
    try:
        or_data = openregistry_search(company_name)
        if or_data and 'error' not in or_data:
            result['openregistry'] = or_data
            result['sources_found'].append('openregistry')
    except Exception:
            pass

    # Try CompanyScope (if APIFY_API_TOKEN set)
    if os.environ.get('APIFY_API_TOKEN'):
        try:
            cs = companyscope_lookup(company_name)
            if cs and 'error' not in cs:
                result['companyscope'] = cs
                result['sources_found'].append('companyscope')
        except Exception:
            pass

    # Try Coresignal (if CORESIGNAL_API_KEY set)
    if os.environ.get('CORESIGNAL_API_KEY'):
        try:
            cs = coresignal_company(company_name)
            if cs:
                result['coresignal'] = cs
                result['sources_found'].append('coresignal')
        except Exception:
            pass

    return result


def format_mcp_report(data):
    """Format MCP enrichment results."""
    lines = []
    lines.append(f"=== MCP Enrichment: {data['company']} ===")
    lines.append(f"Sources: {', '.join(data['sources_found']) if data['sources_found'] else 'None (API keys needed)'}")
    if data.get('openregistry'):
        lines.append(f"  OpenRegistry: 27 national registries queried")
    if data.get('companyscope'):
        lines.append(f"  CompanyScope: 8 sources aggregated")
    if data.get('coresignal'):
        lines.append(f"  Coresignal: company data found")
    if not data['sources_found']:
        lines.append(f"\n  To enable more sources, set these env vars:")
        lines.append(f"  - APIFY_API_TOKEN (for CompanyScope + M&A intelligence)")
        lines.append(f"  - CORESIGNAL_API_KEY (for 74M company records)")
        lines.append(f"  - BRIGHTDATA_API_TOKEN (for Crunchbase + LinkedIn)")
    return '\n'.join(lines)


if __name__ == '__main__':
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else 'Booking Experts'
    result = enrich_mcp(name)
    print(format_mcp_report(result))
