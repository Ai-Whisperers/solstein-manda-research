#!/usr/bin/env python3
"""CLI wrapper for pipeline/research.py. Run: python3 scripts/research_pipeline.py <company> [domain]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pipeline.research import run_pipeline

if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'Booking Experts'
    domain = sys.argv[2] if len(sys.argv) > 2 else None
    run_pipeline(name, domain)
