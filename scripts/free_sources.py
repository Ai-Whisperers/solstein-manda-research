import logging
logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
Free data source integrations for company enrichment.

Sources (all free, no API key needed):
  1. SEC EDGAR — US public company filings, financial data
  2. yfinance — Stock market data, company profiles
  3. DuckDuckGo — Web search (no API key)
  4. OpenRegistry — 27 national company registries (free tier)
  5. EU company data — GLEIF, VAT, parent/subsidiary via eu-company-mcp-server
  6. World Bank — Economic indicators by country

Pattern: public-apis (300K★), openpublicapis.com, explainmcp.com
"""

import json, os, sys, urllib.request, urllib.error, re, time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(os.path.dirname(__file__), '..')

_CACHE = {}
_CACHE_TTL = 3600  # 1 hour


def _fetch(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'SolSteinResearch/1.0 (research@solstein.com)',
            'Accept': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception:
        return None


def _cached_fetch(url, timeout=15, cache_key=None):
    """Fetch with caching to avoid hitting rate limits."""
    key = cache_key or url
    if key in _CACHE:
        entry = _CACHE[key]
        if datetime.now() - entry['time'] < timedelta(seconds=_CACHE_TTL):
            return entry['data']
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'SolSteinResearch/1.0 (research@solstein.com)',
            'Accept': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode('utf-8', errors='replace')
            _CACHE[key] = {'data': data, 'time': datetime.now()}
            return data
    except Exception:
        return None


# --- Source 0: Wikipedia (free, no API key) ---

def wikipedia_summary(company_name):
    """Fetch Wikipedia article summary with entity disambiguation.
    Tries '(company)' suffix first to avoid disambiguation pages (e.g. 'Apple (company)' not 'Apple')."""
    base = company_name.split('(')[0].strip()
    safe = base.replace(' ', '_')
    candidates = [f"{safe}_(company)", safe, f"{safe}_(software)", f"{safe}_(website)",
                  f"{safe}_(software_company)", f"{safe}_(technology_company)"]
    for name in candidates:
        data = _fetch(f'https://en.wikipedia.org/api/rest_v1/page/summary/{name}')
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


# --- Source 1: SEC EDGAR (free, no API key) ---

def sec_company_search(company_name):
    """Search SEC EDGAR for a company by name. Returns CIK and basic info."""
    data = _cached_fetch('https://www.sec.gov/files/company_tickers.json', cache_key='sec_tickers')
    if not data:
        return None
    try:
        tickers = json.loads(data)
        results = []
        name_lower = company_name.lower()
        for cik_str, info in tickers.items():
            if name_lower in info.get('title', '').lower():
                results.append({
                    'cik': str(info['cik_str']).zfill(10),
                    'name': info['title'],
                    'ticker': info['ticker'],
                })
        return results[:5] if results else None
    except (json.JSONDecodeError, KeyError):
        return None


def sec_company_facts(cik):
    """Get XBRL financial facts for a company by CIK."""
    data = _cached_fetch(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',
                         cache_key=f'sec_facts_{cik}')
    if not data:
        return None
    try:
        facts = json.loads(data)
        result = {'name': facts.get('entityName', ''), 'cik': cik}
        # Extract key financial metrics
        us_gaap = facts.get('facts', {}).get('us-gaap', {})
        for metric in ['RevenueFromContractWithCustomerExcludingAssessedTax',
                       'OperatingIncomeLoss', 'NetIncomeLoss',
                       'Assets', 'Liabilities', 'StockholdersEquity',
                       'EmployeeRelatedExpenses', 'SalesRevenueNet']:
            if metric in us_gaap:
                vals = us_gaap[metric].get('units', {}).get('USD', [])
                if vals:
                    result[metric] = vals[-3:]  # Last 3 values
        return result
    except (json.JSONDecodeError, KeyError):
        return None


# --- Source 2: yfinance for stock data (free, no API key) ---

def yfinance_profile(ticker):
    """Get company profile from Yahoo Finance via yfinance library."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            'name': info.get('longBusinessSummary', '')[:300],
            'sector': info.get('sector', ''),
            'industry': info.get('industry', ''),
            'employees': info.get('fullTimeEmployees'),
            'website': info.get('website', ''),
            'country': info.get('country', ''),
            'city': info.get('city', ''),
        }
    except Exception:
        return None


# --- Source 3: HTML scraper for web search (free, no API key) ---

def html_search(query, max_results=5):
    """Search via HTML scraping of search engines. Falls back across multiple engines."""
    results = []
    import urllib.parse as urlparse
    encoded = urlparse.quote(query)

    # Try Google HTML
    urls_to_try = [
        f'https://html.duckduckgo.com/html/?q={encoded}',
    ]

    for url in urls_to_try:
        data = _cached_fetch(url, timeout=10, cache_key=f'html_{query}')
        if not data:
            continue

        # Extract result links from DDG HTML format
        found = re.findall(
            r'<a[^>]*class="result__a"[^>]*href="(//[^"]+)"[^>]*>(.*?)</a>',
            data, re.DOTALL
        )

        for redirect_url, text in found[:max_results]:
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            if not clean_text or len(clean_text) < 5:
                continue
            # Decode DDG redirect URL to real URL
            real_url = redirect_url
            m = re.search(r'uddg=(https?%3A[^&]+)', redirect_url)
            if m:
                real_url = urlparse.unquote(m.group(1))
            results.append({
                'url': real_url,
                'title': clean_text[:100],
            })

        if results:
            break

    return results if results else None


# --- Source 4: OpenRegistry (27 national registries, free) ---

def openregistry_lookup(company_name, jurisdiction=None):
    """Look up company in national registries via OpenRegistry MCP.
    Free tier: 20 requests/min per IP. Covers 27 registries.
    """
    encoded = urllib.parse.quote(company_name)
    url = f'https://openregistry.sophymarine.com/mcp?q={encoded}'
    if jurisdiction:
        url += f'&jurisdiction={jurisdiction}'
    data = _cached_fetch(url, timeout=20, cache_key=f'or_{company_name}')
    if data:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            pass
    return None


# --- Source 5: EU company data (GLEIF, free, no key) ---

def gleif_search(company_name):
    """Search GLEIF (Global Legal Entity Identifier Foundation) for legal entities.
    1.6M+ EU companies. Completely free."""
    encoded = urllib.parse.quote(company_name)
    url = f'https://api.gleif.org/api/v1/lei-records?filter[entity.legalName]={encoded}&page[size]=3'
    data = _cached_fetch(url, cache_key=f'gleif_{company_name}')
    if not data:
        return None
    try:
        j = json.loads(data)
        entities = []
        for item in j.get('data', []):
            attrs = item.get('attributes', {})
            entities.append({
                'name': attrs.get('entity', {}).get('legalName', {}).get('name', ''),
                'lei': attrs.get('lei', ''),
                'status': attrs.get('entity', {}).get('legalForm', {}).get('name', ''),
                'jurisdiction': attrs.get('entity', {}).get('jurisdiction', ''),
                'registration': attrs.get('registration', {}).get('initialRegistrationDate', ''),
            })
        return entities if entities else None
    except (json.JSONDecodeError, KeyError):
        return None


# --- Source 6: World Bank data (free, no key) ---

def worldbank_country_data(country_code):
    """Get economic indicators for a country from World Bank."""
    url = f'http://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD;NY.GDP.MKTP.KD.ZG;SL.UEM.TOTL.ZS?format=json&per_page=10'
    data = _cached_fetch(url, cache_key=f'wb_{country_code}')
    if not data:
        return None
    try:
        j = json.loads(data)
        result = {}
        for item in j[1] if len(j) > 1 else []:
            indicator = item.get('indicator', {}).get('id', '')
            value = item.get('value')
            year = item.get('date', '')
            if value and indicator:
                if indicator not in result:
                    result[indicator] = {}
                result[indicator][year] = value
        return result if result else None
    except (json.JSONDecodeError, KeyError, IndexError):
        return None


# --- Combined enrichment function ---

def enrich_free(company_name, domain=None, ticker=None, country=None):
    """Run all free data sources and return combined results."""
    result = {
        'company': company_name,
        'domain': domain or '',
        'enriched_at': datetime.now().isoformat(),
        'wikipedia': None,
        'sec': None,
        'yfinance': None,
        'web_search': None,
        'openregistry': None,
        'gleif': None,
        'worldbank': None,
        'sources_found': [],
    }

    # Wikipedia (free, no key)
    wiki = wikipedia_summary(company_name)
    if wiki:
        result['wikipedia'] = wiki
        result['sources_found'].append('wikipedia')

    # SEC EDGAR (free, no key)
    sec_results = sec_company_search(company_name)
    if sec_results:
        result['sec'] = sec_results
        result['sources_found'].append('sec_edgar')
        # Get financial facts for first match
        cik = sec_results[0]['cik']
        facts = sec_company_facts(cik)
        if facts:
            result['sec_facts'] = facts

    # yfinance (free, no key)
    if ticker:
        profile = yfinance_profile(ticker)
        if profile:
            result['yfinance'] = profile
            result['sources_found'].append('yfinance')

    # DuckDuckGo search (free, no key)
    search_results = html_search(f'{company_name} company funding news')
    if search_results:
        result['web_search'] = search_results
        result['sources_found'].append('duckduckgo')

    # OpenRegistry (free, 27 registries)
    or_result = openregistry_lookup(company_name)
    if or_result:
        result['openregistry'] = or_result
        result['sources_found'].append('openregistry')

    # GLEIF (free, 1.6M+ entities)
    gleif = gleif_search(company_name)
    if gleif:
        result['gleif'] = gleif
        result['sources_found'].append('gleif')

    return result


if __name__ == '__main__':
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else 'Booking Experts'
    result = enrich_free(name)

    print(f"Company: {result['company']}")
    print(f"Sources found: {result['sources_found']}")
    if result.get('wikipedia'):
        print(f"  Wiki: {result['wikipedia']['title']} — {result['wikipedia']['description']}")
    if result.get('sec'):
        for r in result['sec']:
            print(f"  SEC: {r['name']} ({r['ticker']}) CIK={r['cik']}")
    if result.get('gleif'):
        for e in result['gleif'][:2]:
            print(f"  GLEIF: {e['name']} ({e['lei']})")
    if result.get('web_search'):
        for s in result['web_search'][:3]:
            print(f"  DDG: {s['title'][:60]}")
