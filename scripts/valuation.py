#!/usr/bin/env python3
"""CLI wrapper for pipeline/valuation.py."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pipeline.valuation import valuation_summary

if __name__ == '__main__':
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'AAPL'
    result = valuation_summary(ticker)
    print(f"Valuation summary for {ticker}:")
    for k, v in result.items():
        print(f"  {k}: {v}")
