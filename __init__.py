"""
SolStein M&A Research Pipeline — Unified API.

Import anything from here:
    from pipeline import (
        # Scoring
        DIMS, compute_composite, composite_to_grade, apply_vetoes,
        scan_red_flags, check_kill_criteria,
        
        # Core
        fetch, cached, Config, folder_from,
        
        # Sources
        quick_scan, enrich_company, enrich_free, enrich_mcp,
        
        # Data
        load_john_reference,
    )
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Core
from core.utils import fetch, cached, Config, folder_from, load_john_reference, clear_cache

# Scoring
from scoring import (
    DIMS, WEIGHTS, WEIGHT_MAP,
    compute_composite, composite_to_grade, composite_to_readiness,
    apply_vetoes, scan_red_flags, check_kill_criteria,
)

# Sources
from sources import quick_scan, enrich_company, enrich_free, enrich_mcp, CompanyBrowser

# Allow direct script execution
__all__ = [
    'DIMS', 'WEIGHTS', 'WEIGHT_MAP',
    'compute_composite', 'composite_to_grade', 'composite_to_readiness',
    'apply_vetoes', 'scan_red_flags', 'check_kill_criteria',
    'fetch', 'cached', 'Config', 'folder_from', 'load_john_reference', 'clear_cache',
    'quick_scan', 'enrich_company', 'enrich_free', 'enrich_mcp', 'CompanyBrowser',
]
