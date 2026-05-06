#!/usr/bin/env python3
"""CLI wrapper for pipeline/reflect.py."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pipeline.reflect import ReflectionLoop, auto_improve

if __name__ == '__main__':
    from pipeline.reflect import compute_composite
    name = sys.argv[1] if len(sys.argv) > 1 else 'Booking Experts'
    test_scores = {
        'Ownership attractiveness': 3, 'Revenue scale fit': 3, 'Geographic fit': 5,
        'Tech stack modernity': 3, 'Customer lock-in': 4, 'Vertical depth': 5,
        'Integration potential': 3, 'Growth trajectory': 3,
    }
    loop = ReflectionLoop()
    result = loop.improve_scorecard(name, test_scores)
    print(f"Company: {result['company']}")
    print(f"Initial composite: {compute_composite(result['initial_scores']):.2f}")
    print(f"Final composite: {result['final_composite']}")
    print(f"Improvements made: {result['total_improvements']}")
    for r in result['rounds']:
        print(f"  Round {r['round']}: {r['weak_count']} weak dims, {r['improvements']} improvements")
