#!/usr/bin/env python3
"""Enrichment — wraps datasources.py for the new module structure."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from datasources import enrich_company as _enrich_company
enrich_company = _enrich_company
