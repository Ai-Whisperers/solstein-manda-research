#!/usr/bin/env python3
"""
Compare SolStein pipeline output against John's original data.
Usage: python compare-companies.py <universe> [--company <name>]

Without --company, compares all companies in the universe.
"""

import json, os, sys, re, textwrap

sys.path.insert(0, os.path.dirname(__file__))

UNIVERSES = {
    'horeca': {
        'john_json': os.path.join(os.path.dirname(__file__), '..', 'archive', 'john-original', 'HORECA_IT.zip'),
        'pipeline_json': os.path.join(os.path.dirname(__file__), '..', 'output', 'HORECA', 'Data', 'horeca_data.json'),
    }
}

def extract_john_scores(zip_path):
    """Extract scorecard data from John's JSON inside the zip."""
    import zipfile
    z = zipfile.ZipFile(zip_path)
    json_files = [n for n in z.namelist() if n.endswith('horeca_data.json')]
    if not json_files:
        return {}
    with z.open(json_files[0]) as f:
        data = json.load(f)
    result = {}
    for c in data.get('companies', []):
        name = c.get('company_name', '')
        sc = c.get('scorecard')
        if sc and sc.get('composite_score') is not None:
            result[name] = {
                'composite': sc['composite_score'],
                'dimensions': sc.get('dimensions', {}),
                'confidence': sc.get('confidence_band', ''),
                'fundamentals': {
                    'revenue': c.get('fundamentals', {}).get('revenue', ''),
                    'employees': c.get('fundamentals', {}).get('employees', ''),
                    'ownership': c.get('fundamentals', {}).get('ownership', ''),
                }
            }
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: compare-companies.py <universe>")
        print("Universes: " + ", ".join(UNIVERSES.keys()))
        sys.exit(1)

    universe = sys.argv[1]
    if universe not in UNIVERSES:
        print(f"Unknown universe: {universe}")
        sys.exit(1)

    cfg = UNIVERSES[universe]
    
    # Extract from John's zip
    john_data = extract_john_scores(cfg['john_json'])
    
    print(f"=== Comparison: {universe.upper()} Universe ===")
    print(f"John's companies with scores: {len(john_data)}")
    print()
    
    if john_data:
        # Show top 10 by score from John's data
        sorted_john = sorted(john_data.items(), key=lambda x: x[1]['composite'], reverse=True)
        print("Top 10 by John's composite score:")
        print(f"{'Company':<25} {'Score':<8} {'Confidence':<15} {'Revenue':<25} {'Ownership'}")
        print("-"*80)
        for name, data in sorted_john[:10]:
            rev = data['fundamentals'].get('revenue', '')[:24]
            own = data['fundamentals'].get('ownership', '')[:20]
            print(f"{name:<25} {data['composite']:<8.2f} {data['confidence']:<15} {rev:<25} {own}")
        print()
        
        # Show distribution
        tiers = {'1.0-1.9': 0, '2.0-2.9': 0, '3.0-3.9': 0, '4.0-4.9': 0, '5.0': 0}
        for name, data in john_data.items():
            s = data['composite']
            if s < 2: tiers['1.0-1.9'] += 1
            elif s < 3: tiers['2.0-2.9'] += 1
            elif s < 4: tiers['3.0-3.9'] += 1
            elif s < 5: tiers['4.0-4.9'] += 1
            else: tiers['5.0'] += 1
        print("Score distribution:")
        for k, v in tiers.items():
            bar = '#' * v
            print(f"  {k}: {v:3d} {bar}")
        print()
        print(f"Average composite: {sum(d['composite'] for d in john_data.values())/len(john_data):.2f}")


if __name__ == '__main__':
    main()
