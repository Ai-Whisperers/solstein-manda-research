"""MCP-connected sources: OpenCorporates."""
import json
from core.utils import fetch


def opencorporates_search(company_name):
    """Search for legal entity via OpenCorporates."""
    import urllib.parse
    html = fetch(f'https://opencorporates.com/companies?q={urllib.parse.quote(company_name)}&format=json', timeout=10)
    if not html:
        return None
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
