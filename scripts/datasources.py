"""
Multi-source company data enrichment. This is now a thin CLI wrapper.
The real implementation lives in sources/enrichment.py.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Backward-compat exports (all real code moved to sources/)
from sources.enrichment import enrich_company, format_enrichment_report
from sources.free import wikipedia_summary, github_org, brave_news, detect_hosting
from sources.plus import crunchbase_info, abstractapi_enrich
from sources.mcp import opencorporates_search
from core.utils import fetch, fetch_parallel, check_freshness, triangulate_employees

# Keep the __main__ for CLI usage
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: datasources.py <company_name> [domain]")
        sys.exit(1)
    name = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else None
    data = enrich_company(name, domain)
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'HORECA')
    folder = name.lower().replace(' ', '-')
    fdir = os.path.join(out_dir, folder)
    os.makedirs(fdir, exist_ok=True)
    from core.utils import atomic_json_dump
    atomic_json_dump(data, os.path.join(fdir, 'enriched.json'), indent=2)
    print(format_enrichment_report(data))
    print(f"\nSaved: {os.path.join(fdir, 'enriched.json')}")
