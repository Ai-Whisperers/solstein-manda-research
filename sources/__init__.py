#!/usr/bin/env python3
"""
Source integrations package. Each module provides company data from one source.
All functions return structured dict or None.
"""

from .browser import CompanyBrowser
from .quickscan import quick_scan
from .enrich import enrich_company
from .free import enrich_free
from .mcp import enrich_mcp
from .companies_house import lookup_by_name
from .new_sources import enrich_new_sources
