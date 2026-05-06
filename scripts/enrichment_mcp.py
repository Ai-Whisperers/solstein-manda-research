import logging
logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
MCP-based enrichment pre-pass. Calls external MCP servers for company data.
Integrates with datasources.py as an additional source layer.

Supported MCP servers:
  - m-and-a-target-intelligence (Apify) — 16 sources, $0.045/call
  - startup-ecosystem-intelligence (Apify) — 8 sources VC/innovation focused
  - Bright Data MCP — 200+ web data sources
  - Explorium B2B MCP — company + contact data
"""

import json, os, sys, urllib.request, urllib.error, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(os.path.dirname(__file__), '..')


def call_mcp_via_apify(actor_name, payload, api_token=None):
    """Call an Apify MCP actor via their API. Returns result or None."""
    token = api_token or os.environ.get('APIFY_API_TOKEN')
    if not token:
        return {'error': 'No APIFY_API_TOKEN set. Get one at apify.com.'}

    url = f'https://api.apify.com/v2/acts/{actor_name}/run-sync-get-dataset-items'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {'error': f'HTTP {e.code}: {e.read().decode()[:200]}'}
    except Exception as e:
        return {'error': str(e)}


def enrichment_via_mcp(company_name, domain=None):
    """
    Run MCP-based enrichment. Returns structured dict matching datasources.py format.
    Falls back gracefully if APIs unavailable.
    """
    result = {
        'company': company_name,
        'domain': domain or '',
        'enriched_at': datetime.now().isoformat(),
        'method': 'mcp',
        'mcp_results': {},
        'sources_found': [],
        'errors': [],
        'grade': None,
        'readiness_score': None,
        'deal_breakers': [],
    }

    # Try to get data via Apify M&A target intelligence
    apify_result = call_mcp_via_apify('ryanclinton~m-and-a-target-intelligence-mcp', {
        'company': company_name,
        'domain': domain or '',
    })
    if apify_result and 'error' not in apify_result:
        result['mcp_results']['ma_intelligence'] = apify_result
        result['sources_found'].append('apify_ma_intelligence')
        if isinstance(apify_result, dict):
            result['readiness_score'] = apify_result.get('acquisitionReadinessScore')
            result['grade'] = apify_result.get('grade')
            result['deal_breakers'] = apify_result.get('dealBreakers', [])

    # Startup ecosystem intelligence
    startup_result = call_mcp_via_apify('ryanclinton~startup-ecosystem-intelligence-mcp', {
        'company': company_name,
        'website': domain or '',
    })
    if startup_result and 'error' not in startup_result:
        result['mcp_results']['startup_intelligence'] = startup_result
        result['sources_found'].append('apify_startup_intelligence')

    return result


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'Booking Experts'
    domain = sys.argv[2] if len(sys.argv) > 2 else None
    result = enrichment_via_mcp(name, domain)
    print(json.dumps(result, indent=2))
