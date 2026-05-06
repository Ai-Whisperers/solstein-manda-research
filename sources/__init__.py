"""
Source integrations package. Each module provides company data from one domain.
Layer: data sources, depends on core/.
"""
from sources.enrichment import enrich_company, format_enrichment_report
from sources.free import enrich_free, wikipedia_summary, github_org, brave_news, detect_hosting
from sources.plus import enrich_plus, abstractapi_enrich, crunchbase_info
from sources.mcp import opencorporates_search
from scripts.browser_research import CompanyBrowser
from scripts.quickscan import quick_scan
from scripts.sources_mcp import enrich_mcp
from scripts.companies_house import lookup_by_name
from scripts.sources_new import enrich_new_sources
