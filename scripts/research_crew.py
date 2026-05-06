#!/usr/bin/env python3
"""CLI wrapper for pipeline/crew.py."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pipeline.crew import ResearchCoordinator

if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'Booking Experts'
    domain = sys.argv[2] if len(sys.argv) > 2 else None
    crew = ResearchCoordinator()
    result = crew.research(name, domain)
    print(f"Research complete for {name}")
    print(result.get('scorecard', {}))
