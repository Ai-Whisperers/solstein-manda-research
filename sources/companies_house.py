
import logging
logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
UK Companies House API integration.
Free API key at: https://developer.company-information.service.gov.uk/
Rate limit: 600 req/5min with key. 5.4M companies available.
Bulk data: Free monthly CSV snapshots.

Endpoints:
  - Company search
  - Company profile
  - Officers
  - Filing history
  - Persons of Significant Control (PSC)
"""

import json, os, sys, base64
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(os.path.dirname(__file__), "..")

_API_KEY = os.environ.get("UK_COMPANIES_HOUSE_KEY")
_API_CACHE = {}


def _fetch(endpoint, params=None):
    """Fetch from Companies House API. Uses API key if available."""
    key = _API_KEY
    if not key:
        return None
    
    url = f"https://api.company-information.service.gov.uk{endpoint}"
    if params:
        qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
        url += f"?{qs}"
    
    cache_key = url
    if cache_key in _API_CACHE:
        return _API_CACHE[cache_key]
    
    try:
        auth = base64.b64encode(f"{key}:".encode()).decode()
        req = urllib.request.Request(url, headers={
            "Authorization": f"Basic {auth}",
            "User-Agent": "SolSteinResearch/1.0",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            _API_CACHE[cache_key] = data
            return data
    except Exception:
        return None


def search_companies(query):
    """Search for companies by name."""
    import urllib.parse
    return _fetch("/search/companies", {"q": query})


def get_company(company_number):
    """Get detailed company profile."""
    return _fetch(f"/company/{company_number}")


def get_officers(company_number):
    """Get company officers/directors."""
    return _fetch(f"/company/{company_number}/officers")


def get_filing_history(company_number):
    """Get company filing history."""
    return _fetch(f"/company/{company_number}/filing-history")


def get_psc(company_number):
    """Get Persons of Significant Control."""
    return _fetch(f"/company/{company_number}/persons-with-significant-control")


def lookup_by_name(company_name):
    """Full company lookup by name. Returns structured profile."""
    search = search_companies(company_name)
    if not search or not search.get("items"):
        return None
    
    items = search["items"]
    results = []
    for item in items[:3]:
        num = item.get("company_number", "")
        profile = get_company(num) if num else None
        results.append({
            "name": item.get("title", ""),
            "number": num,
            "status": item.get("company_status", ""),
            "type": item.get("company_type", ""),
            "incorporated": item.get("date_of_creation", ""),
            "address": item.get("address", {}),
            "officers": get_officers(num) if num else None,
            "filings": get_filing_history(num) if num else None,
        })
    
    return {
        "company": company_name,
        "total_results": search.get("total_results", 0),
        "results": results,
        "source": "uk_companies_house",
    }


if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "Booking Experts"
    
    if _API_KEY:
        result = lookup_by_name(name)
        if result:
            print(f"Found {result['total_results']} results for {name}")
            for r in result["results"]:
                print(f"  {r['name']} ({r['number']}) - {r['status']}")
        else:
            print(f"No results for {name}")
    else:
        print("No UK_COMPANIES_HOUSE_KEY set.")
        print("Get a free key at: https://developer.company-information.service.gov.uk/")
        print("Then: export UK_COMPANIES_HOUSE_KEY=your_key_here")
