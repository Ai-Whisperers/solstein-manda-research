#!/usr/bin/env python3
"""New source integrations (SIRENE, VIES, Financial Datasets)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from sources_new import enrich_new_sources as _enrich
enrich_new_sources = _enrich
