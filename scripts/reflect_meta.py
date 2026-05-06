import logging
logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
Bilevel Autoresearch outer loop — meta-optimizes the research pipeline.
Reads experiment logs, identifies bottlenecks, generates improvements.
Applies Comparative Reflective Memory — analyzes deltas between our scores and John's.

Pattern from: arXiv 2603.23420 (Bilevel Autoresearch), arXiv 2602.02660 (MARS)

Usage:
    python3 reflect_meta.py                         # Run full meta-analysis
    python3 reflect_meta.py --apply                  # Auto-apply improvements
    python3 reflect_meta.py --report                 # Generate improvement report
"""

import json, os, re, sys
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scoring import DIMS, WEIGHT_MAP
from core.utils import safe_json_load

BASE = os.path.join(os.path.dirname(__file__), '..')
HORECA_DIR = os.path.join(BASE, 'output', 'HORECA')
JOHN_JSON = os.path.join(BASE, 'archive', 'john-original', 'horeca_json', 'horeca_data.json')
RESULTS_TSV = os.path.join(HORECA_DIR, 'results.tsv')


def load_john_reference():
    """Load all John reference scores."""
    data = safe_json_load(JOHN_JSON, {})
    if not data:
        return {}
    result = {}
    for c in data.get('companies', []):
        name = c['company_name']
        sc = c.get('scorecard')
        if sc and sc.get('composite_score'):
            dims = sc.get('dimensions', {})
            result[name] = {
                'composite': sc['composite_score'],
                'dimensions': {k: v['score'] for k, v in dims.items() if isinstance(v, dict) and v.get('score')},
            }
    return result


def load_experiments():
    """Load all experiments from results.tsv."""
    import csv
    experiments = []
    if not os.path.exists(RESULTS_TSV):
        return experiments
    with open(RESULTS_TSV) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            experiments.append(row)
    return experiments


def analyze_errors(john_data, experiments):
    """
    Analyze error patterns across all experiments.
    Returns: which dimensions are hardest, which companies hardest, error trends.
    """
    dim_errors = defaultdict(list)
    company_errors = []

    for exp in experiments:
        company = exp.get('company', '')
        # Find John's data for this company
        john = None
        for jn, jd in john_data.items():
            if company.lower() in jn.lower() or jn.lower() in company.lower():
                john = jd
                break
        if not john:
            continue

        for dim in DIMS:
            col = dim.lower().replace(' ', '_')[:10]
            our_s = exp.get(dim.lower().replace(' ', '_')[:10]) or exp.get(dim.lower().split()[0])
            # Try alternative parsing
            our_val = None
            for k, v in exp.items():
                if dim.lower().startswith(k.lower().replace('_', '')) or k.lower().startswith(dim.lower().split()[0].lower()):
                    try:
                        our_val = float(v)
                    except (ValueError, TypeError):
                        pass
                    break

            john_s = john.get('dimensions', {}).get(dim)
            if our_val is not None and john_s:
                err = abs(our_val - john_s)
                dim_errors[dim].append(err)

        comp_err = float(exp.get('error', 999))
        company_errors.append({'company': company, 'error': comp_err})

    return dim_errors, company_errors


def generate_comparative_reflections(john_data, experiments):
    """
    Comparative Reflective Memory — analyze deltas between our scores and John's.
    Extracts lessons: "we scored X but John scored Y because Z."
    """
    reflections = []

    for exp in experiments[:20]:
        company = exp.get('company', '')
        john = None
        for jn, jd in john_data.items():
            if company.lower() in jn.lower() or jn.lower() in company.lower():
                john = jd
                break
        if not john:
            continue

        # Find which dimensions had the biggest errors
        dim_deltas = []
        for dim in DIMS:
            our_val = None
            for k, v in exp.items():
                if dim.lower().startswith(k.lower().replace('_', '')) or k.lower().startswith(dim.lower().split()[0].lower()):
                    try:
                        our_val = float(v)
                    except (ValueError, TypeError):
                        pass
                    break
            john_s = john.get('dimensions', {}).get(dim)
            if our_val is not None and john_s and our_val != john_s:
                dim_deltas.append({
                    'dimension': dim,
                    'our_score': our_val,
                    'john_score': john_s,
                    'delta': our_val - john_s,
                })

        if dim_deltas:
            reflection = {
                'company': company,
                'john_composite': john['composite'],
                'deltas': dim_deltas,
                'lesson': _derive_lesson(dim_deltas),
            }
            reflections.append(reflection)

    return reflections


def _derive_lesson(deltas):
    """Derive a lesson from dimension deltas."""
    if not deltas:
        return ''
    over = [d for d in deltas if d['delta'] > 0]
    under = [d for d in deltas if d['delta'] < 0]
    parts = []
    if over:
        parts.append(f"Over-scored on: {', '.join(d['dimension'][:15] for d in over[:3])}")
    if under:
        parts.append(f"Under-scored on: {', '.join(d['dimension'][:15] for d in under[:3])}")
    return '; '.join(parts)


def generate_improvement_suggestions(dim_errors):
    """Generate concrete suggestions to improve the research prompts."""
    suggestions = []
    for dim, errs in sorted(dim_errors.items(), key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0, reverse=True):
        if errs:
            avg = sum(errs) / len(errs)
            if avg > 0.5:
                suggestions.append({
                    'dimension': dim,
                    'avg_error': round(avg, 3),
                    'suggestion': _suggestion_for_dim(dim),
                })
    return suggestions


def _suggestion_for_dim(dim):
    """Generate improvement suggestion for a specific dimension."""
    suggestions = {
        'Ownership attractiveness': 'Add check for reseller/distributor entities — they may hold customer relationships separate from IP entity',
        'Revenue scale fit': 'Cross-reference employee count × industry rev/employee + pricing page tiers + customer count',
        'Tech stack modernity': 'Check job postings for tech keywords AND look for mention of legacy systems',
        'Growth trajectory': 'Do NOT conflate HQ headcount changes with overall business growth — international resellers/offices may be growing',
    }
    return suggestions.get(dim, f'Improve research methodology for {dim}')


def run_meta_analysis(apply=False):
    """Run full meta-analysis and optionally apply improvements."""
    john_data = load_john_reference()
    experiments = load_experiments()

    print("=" * 60)
    print("BILEVEL META-ANALYSIS")
    print("=" * 60)

    dim_errors, company_errors = analyze_errors(john_data, experiments)
    print(f"\nAnalyzed {len(experiments)} experiments across {len(john_data)} reference companies")

    print(f"\n--- Dimension Error Analysis ---")
    for dim, errs in sorted(dim_errors.items(), key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0, reverse=True):
        if errs:
            avg = sum(errs) / len(errs)
            mx = max(errs)
            non_zero = sum(1 for e in errs if e > 0)
            print(f"  {dim:<35} avg_err={avg:.3f} max_err={mx:.1f} non_zero={non_zero}")

    print(f"\n--- Comparative Reflections (deltas) ---")
    reflections = generate_comparative_reflections(john_data, experiments)
    for r in reflections[:5]:
        print(f"  {r['company']:<40} lesson: {r['lesson'][:80]}")

    print(f"\n--- Improvement Suggestions ---")
    suggestions = generate_improvement_suggestions(dim_errors)
    for s in suggestions:
        print(f"  [{s['dimension']}] avg_err={s['avg_error']}")
        print(f"    → {s['suggestion']}")

    if apply and suggestions:
        print(f"\n  Would apply {len(suggestions)} improvements (--apply mode)")
        print(f"  Suggestion stored in: {os.path.join(BASE, 'output', 'HORECA', 'meta_improvements.json')}")
        from core.utils import atomic_json_dump
        out = os.path.join(HORECA_DIR, 'meta_improvements.json')
        atomic_json_dump({'suggestions': suggestions, 'reflections': reflections[:10], 'generated_at': str(datetime.now())}, out, indent=2)

    return suggestions, reflections


if __name__ == '__main__':
    apply = '--apply' in sys.argv
    report = '--report' in sys.argv
    run_meta_analysis(apply=apply)
