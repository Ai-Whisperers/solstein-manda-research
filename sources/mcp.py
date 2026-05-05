#!/usr/bin/env python3
"""MCP server integrations."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from sources_mcp import enrich_mcp as _enrich_mcp
enrich_mcp = _enrich_mcp
