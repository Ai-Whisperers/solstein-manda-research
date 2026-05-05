#!/usr/bin/env python3
"""
Aggregate all completed company scorecards into the unified JSON and TSV.
Run this after agents have written deep-analysis.md files.
"""

import json, os, re, csv, sys
from datetime import datetime

BASE = os.path.join(os.path.dirname(__file__), '..')
JOHN_JSON = os.path.join(BASE, 'archive', 'john-original', 'horeca_json', 'horeca_data.json')
HORECA_DIR = os.path.join(BASE, 'output', 'HORECA')

DIMENSIONS = [
    'Ownership attractiveness',
    'Revenue scale fit',
    'Geographic fit',
    'Tech stack modernity',
    'Customer lock-in',
    'Vertical depth',
    'Integration potential',
    'Growth trajectory'
]

WEIGHTS = [3, 3, 3, 2, 2, 2, 1, 1]

def load_john():
    with open(JOHN_JSON) as f:
        data = json.load(f)
    result = {}
    folder_map = {}
    for c in data['companies']:
        name = c['company_name']
        folder = name.lower().replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '')
        folder = folder.replace("'", '').replace('&', 'and').replace('--', '-').strip('-')
        folder_map[folder] = name
        sc = c.get('scorecard')
        if sc and sc.get('composite_score') is not None:
            dims = sc.get('dimensions', {})
            result[name] = {
                'composite': sc['composite_score'],
                'dimensions': {k: v['score'] for k, v in dims.items()},
                'confidence': sc.get('confidence_band', ''),
            }
    return result, folder_map

def parse_scorecard(text):
    """Parse 8-dimension scorecard from deep-analysis.md table."""
    scores = {}
    weights_used = {}
    for dim in DIMENSIONS:
        # Match: | N | Dimension | Weight | Score (1-5) | Rationale |
        pattern = r'\|\s*\d+\s*\|\s*' + re.escape(dim) + r'\s*\|\s*(\w+)\s*\|\s*([\d.]+)'
        m = re.search(pattern, text)
        if m:
            weight_str = m.group(1).lower()
            weight_map = {'high': 3, 'medium': 2, 'low': 1}
            weights_used[dim] = weight_map.get(weight_str, 2)
            scores[dim] = float(m.group(2))
    
    # Composite
    comp_match = re.search(r'\*\*Composite\*\*:\s*([\d.]+)\s*/\s*5\.0', text)
    conf_match = re.search(r'\*\*Confidence band\*\*:\s*(.+)', text)
    
    return scores, float(comp_match.group(1)) if comp_match else None, conf_match.group(1).strip() if conf_match else ''

def main():
    john_data, folder_map = load_john()
    print(f"Loaded {len(john_data)} John reference companies")
    
    results_tsv = os.path.join(HORECA_DIR, 'results.tsv')
    fieldnames = ['timestamp','company','experiment_num','ownership','revenue','geo','tech','lockin','vertical','integration','growth','composite','john_composite','error','error_target','kept','confidence','notes']
    
    rows = []
    
    for company_dir in sorted(os.listdir(HORECA_DIR)):
        dpath = os.path.join(HORECA_DIR, company_dir)
        if not os.path.isdir(dpath) or company_dir == 'Data':
            continue
        
        da_path = os.path.join(dpath, 'deep-analysis.md')
        if not os.path.exists(da_path):
            continue
        
        with open(da_path) as f:
            content = f.read()
        
        scores, composite, confidence = parse_scorecard(content)
        if not scores:
            print(f"  SKIP {company_dir}: no scorecard found")
            continue
        
        # Compute error vs John using folder_map
        john_name = folder_map.get(company_dir)
        if not john_name:
            print(f"  SKIP {company_dir}: no John match")
            continue
        
        john = john_data[john_name]
        error = abs(composite - john['composite']) if composite else 999
        
        kept = 'yes' if error <= 0.5 else 'no'
        
        dim_order = ['ownership','revenue','geo','tech','lockin','vertical','integration','growth']
        dim_full = ['Ownership attractiveness','Revenue scale fit','Geographic fit','Tech stack modernity','Customer lock-in','Vertical depth','Integration potential','Growth trajectory']
        
        dim_values = []
        for d in dim_full:
            dim_values.append(str(scores.get(d, '?')))
        
        row = {
            'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M'),
            'company': company_dir,
            'experiment_num': '1',
            'ownership': dim_values[0],
            'revenue': dim_values[1],
            'geo': dim_values[2],
            'tech': dim_values[3],
            'lockin': dim_values[4],
            'vertical': dim_values[5],
            'integration': dim_values[6],
            'growth': dim_values[7],
            'composite': f'{composite:.2f}' if composite else '?',
            'john_composite': f'{john["composite"]:.2f}',
            'error': f'{error:.2f}',
            'error_target': '0.50',
            'kept': kept,
            'confidence': confidence,
            'notes': f'John dims: {john["dimensions"]}' if error > 0.5 else ''
        }
        rows.append(row)
        
        status = '✓' if kept == 'yes' else '✗'
        print(f"  {status} {company_dir:<30} our={composite:.2f} john={john['composite']:.2f} err={error:.2f}")
    
    # Write TSV
    with open(results_tsv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nWrote {len(rows)} results to results.tsv")
    
    passed = sum(1 for r in rows if r['kept'] == 'yes')
    failed = sum(1 for r in rows if r['kept'] == 'no')
    print(f"Passed: {passed}, Failed: {failed}")

if __name__ == '__main__':
    main()
