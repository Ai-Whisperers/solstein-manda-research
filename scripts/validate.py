#!/usr/bin/env python3
"""Validation dashboard: one-command pass/fail across all dimensions and composites."""

import json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scoring import composite_to_grade, composite_to_readiness

BASE = os.path.join(os.path.dirname(__file__), '..')
JOHN_JSON = os.path.join(BASE, 'archive', 'john-original', 'horeca_json', 'horeca_data.json')
HORECA_DIR = os.path.join(BASE, 'output', 'HORECA')

WEIGHTS = [3, 3, 3, 2, 2, 2, 1, 1]
DIMS = ['Ownership attractiveness', 'Revenue scale fit', 'Geographic fit',
        'Tech stack modernity', 'Customer lock-in', 'Vertical depth',
        'Integration potential', 'Growth trajectory']

with open(JOHN_JSON) as f:
    data = json.load(f)

john_map = {}
folder_map = {}
for c in data['companies']:
    name = c['company_name']
    folder = name.lower().replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '')
    folder = folder.replace("'", '').replace('&', 'and').replace('--', '-').strip('-')
    folder_map[folder] = name
    sc = c.get('scorecard')
    if sc and sc.get('composite_score') is not None:
        dims_raw = sc.get('dimensions', {})
        dims = {}
        for d in DIMS:
            v = dims_raw.get(d, {})
            if isinstance(v, dict):
                dims[d] = v.get('score')
            else:
                dims[d] = v
        john_map[name] = {'composite': sc['composite_score'], 'dims': dims}

results = []
for d in sorted(os.listdir(HORECA_DIR)):
    dp = os.path.join(HORECA_DIR, d)
    if not os.path.isdir(dp) or d == 'Data':
        continue
    jn = folder_map.get(d)
    if not jn:
        continue
    
    da = os.path.join(dp, 'deep-analysis.md')
    if not os.path.exists(da):
        continue
    with open(da) as f:
        content = f.read()
    
    comp_match = re.search(r'\*\*Composite\*\*:\s*([\d.]+)\s*/\s*5\.0', content)
    our_comp = float(comp_match.group(1)) if comp_match else None
    
    john = john_map.get(jn, {})
    jc = john.get('composite')
    jd = john.get('dims', {})
    
    comp_err = abs(our_comp - jc) if our_comp and jc else 999
    
    dim_errs = {}
    for dim in DIMS:
        our_s = None
        pattern = r'\|\s*\d+\s*\|\s*' + re.escape(dim) + r'\s*\|\s*\w+\s*\|\s*([\d.]+)'
        m = re.search(pattern, content)
        if m:
            our_s = float(m.group(1))
        john_s = jd.get(dim)
        if our_s and john_s:
            dim_errs[dim] = abs(our_s - john_s)
    
    results.append({
        'folder': d,
        'name': jn,
        'our_comp': our_comp,
        'john_comp': jc,
        'comp_err': comp_err,
        'comp_pass': comp_err <= 0.5 if comp_err != 999 else False,
        'dim_errs': dim_errs,
    })

print("=" * 70)
print("HORECA VALIDATION DASHBOARD")
print("=" * 70)
print(f"\nTotal companies: {len(results)}")
print(f"Composite pass (err≤0.5): {sum(1 for r in results if r['comp_pass'])}/{len(results)}")
avg_err = sum(r['comp_err'] for r in results) / len(results)
print(f"Average composite error: {avg_err:.4f}")
print(f"Max composite error: {max(r['comp_err'] for r in results):.4f}")
print(f"Min composite error: {min(r['comp_err'] for r in results):.4f}")

print(f"\n{'Dimension':<35} {'Avg Err':<10} {'Max Err':<10} {'Err > 0':<10} {'Err > 1.0':<10}")
print("-" * 75)
for dim in DIMS:
    errs = [r['dim_errs'].get(dim, 0) for r in results if dim in r['dim_errs']]
    if errs:
        avg = sum(errs) / len(errs)
        mx = max(errs)
        non_zero = sum(1 for e in errs if e > 0)
        gt_one = sum(1 for e in errs if e > 1.0)
        print(f"{dim:<35} {avg:<10.4f} {mx:<10.1f} {non_zero:<10} {gt_one:<10}")

# Dimension-level pass/fail
dim_pass = True
for r in results:
    for dim, err in r['dim_errs'].items():
        if err > 1.0:
            dim_pass = False
            print(f"\n  DIM FAIL: {r['folder']:<40} {dim:<30} err={err:.1f}")
print(f"\nDimension-level pass (all err ≤1.0): {'✓ PASS' if dim_pass else '✗ FAIL'}")

# Grade distribution
print(f"\n{'Grade Distribution':<20} {'Count':<8} {'Score Range'}")
print("-" * 45)
grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
for r in results:
    g = composite_to_grade(r['our_comp'])
    grade_counts[g['grade']] = grade_counts.get(g['grade'], 0) + 1
for g in ['A', 'B', 'C', 'D', 'F']:
    bar = '█' * grade_counts.get(g, 0)
    print(f"  {g:<20} {grade_counts.get(g, 0):<8} {bar}")

print(f"\nTop 10 by Acquisition Readiness Score (0-100):")
sorted_r = sorted(results, key=lambda x: x['our_comp'] or 0, reverse=True)
print(f"  {'Company':<40} {'Score':<8} {'ARS':<8} {'Grade':<6}")
for r in sorted_r[:10]:
    if r['our_comp']:
        g = composite_to_grade(r['our_comp'])
        ars = g['score_100']
        print(f"  {r['folder']:<40} {r['our_comp']:<8.2f} {ars:<8} {g['grade']:<6}")

print(f"\nFailed companies (comp err > 0.5):")
for r in results:
    if not r['comp_pass']:
        dim_details = ', '.join(f"{d[:15]}={e}" for d, e in r['dim_errs'].items() if e > 0.5)
        print(f"  ✗ {r['folder']:<40} comp_err={r['comp_err']:.2f} ({dim_details})")

print(f"\nScore distribution:")
dist = {'4.0-5.0': 0, '3.0-3.9': 0, '2.0-2.9': 0, '1.0-1.9': 0}
for r in results:
    c = r['our_comp']
    if c and c >= 4: dist['4.0-5.0'] += 1
    elif c and c >= 3: dist['3.0-3.9'] += 1
    elif c and c >= 2: dist['2.0-2.9'] += 1
    elif c: dist['1.0-1.9'] += 1
for k, v in dist.items():
    bar = '█' * v
    print(f"  {k}: {v:3d} {bar}")
