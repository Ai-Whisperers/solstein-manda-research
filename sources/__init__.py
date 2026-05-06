#!/usr/bin/env python3
"""
Source integrations package. Re-exports from scripts/ for backward compatibility.
All real code lives in scripts/ — these are thin aliases.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts'))

from browser_research import CompanyBrowser
from quickscan import quick_scan
from datasources import enrich_company
from free_sources import enrich_free
from sources_mcp import enrich_mcp
from companies_house import lookup_by_name
from sources_new import enrich_new_sources
from sources_plus import enrich_plus
