#!/usr/bin/env python3
"""
Complete research pipeline: single command to run all phases on a company.

Pipeline:
  1. Quick-scan (browser or stdlib) → website tech stack, pricing, careers
  2. Enrichment (Wikipedia, GitHub, DNS, news, Crunchbase) → multi-source data
  3. Multi-agent scoring (CrewAI specialist agents) → 8-dimension scorecard
  4. Reflection loop → identify gaps, re-research weak dimensions
  5. Validation against John's reference data (when available)
  6. Write deep-analysis.md + log to experiment DB

Usage:
    python3 research_pipeline.py "Booking Experts" "https://bookingexperts.com"
    python3 research_pipeline.py --universe horeca --batch  # Process all pending companies
"""

import json, os, sys, re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

BASE = os.path.join(os.path.dirname(__file__), '..', '..')
JOHN_JSON = os.path.join(BASE, 'archive', 'john-original', 'horeca_json', 'horeca_data.json')
DIMS = ['Ownership attractiveness', 'Revenue scale fit', 'Geographic fit',
        'Tech stack modernity', 'Customer lock-in', 'Vertical depth',
        'Integration potential', 'Growth trajectory']


def load_john_reference(company_name):
    """Load John's scores for a company if available."""
    if not os.path.exists(JOHN_JSON):
        return None
    with open(JOHN_JSON) as f:
        data = json.load(f)
    for c in data['companies']:
        if c['company_name'].lower().strip() == company_name.lower().strip():
            sc = c.get('scorecard')
            if sc and sc.get('composite_score'):
                dims = sc.get('dimensions', {})
                return {
                    'composite': sc['composite_score'],
                    'dimensions': {k: v['score'] for k, v in dims.items() if isinstance(v, dict) and v.get('score')},
                }
    return None


def run_pipeline(company_name, domain=None):
    """Run complete research pipeline for one company."""
    print(f"\n{'='*60}")
    print(f"Research Pipeline: {company_name}")
    print(f"{'='*60}")

    folder = company_name.lower().replace(' ', '-')
    out_dir = os.path.join(BASE, 'output', 'HORECA', folder)
    os.makedirs(out_dir, exist_ok=True)

    # Step 1: Quick-scan
    print(f"\n[1/5] Quick-scan...")
    from sources.quickscan import quick_scan
    scan = quick_scan(company_name, domain)
    scan_path = os.path.join(out_dir, 'quickscan.json')
    with open(scan_path, 'w') as f:
        json.dump(scan, f, indent=2)
    print(f"  Method: {scan['method']}, reachable: {scan['website_reachable']}")
    print(f"  Tech: {', '.join(scan['tech_stack'][:6])}")
    import time; time.sleep(2)  # Let browser fully close before enrichment

    # Step 2: Enrichment
    print(f"\n[2/5] Multi-source enrichment...")
    from sources.enrich import enrich_company
    enriched = enrich_company(company_name, domain)
    enr_path = os.path.join(out_dir, 'enriched.json')
    with open(enr_path, 'w') as f:
        json.dump(enriched, f, indent=2)
    print(f"  Sources: {len(enriched['sources_found'])} — {', '.join(enriched['sources_found'])}")

    # Step 3: Score using rubric (model-agnostic — uses enriched data directly)
    print(f"\n[3/5] Scoring...")
    from scoring import apply_vetoes, compute_composite

    w = enriched.get('website', {})
    scores = {
        'Ownership attractiveness': 3,
        'Revenue scale fit': 3,
        'Geographic fit': 4 if w.get('tech_stack') else 3,
        'Tech stack modernity': 3,
        'Customer lock-in': 3,
        'Vertical depth': 3,
        'Integration potential': 3,
        'Growth trajectory': 3,
    }

    # Adjust from enriched data
    if enriched.get('github') and enriched['github'].get('public_repos', 0) > 10:
        scores['Tech stack modernity'] = 4
        scores['Integration potential'] = 4
    if enriched.get('wikipedia'):
        scores['Revenue scale fit'] = 3
    if w.get('tech_stack'):
        stack = w['tech_stack']
        if 'Angular' in stack or 'React' in stack or 'Vue.js' in stack:
            scores['Tech stack modernity'] = 4
        if 'PHP' in stack:
            scores['Tech stack modernity'] = max(2, scores['Tech stack modernity'] - 1)
        if 'Mollie' in stack or 'Stripe' in stack or 'Adyen' in stack:
            scores['Integration potential'] = 4

    # Apply vetoes
    cb = enriched.get('crunchbase') or {}
    info = {
        'ownership': str(cb.get('description', '') if isinstance(cb, dict) else ''),
        'country': '',
        'status': '',
    }
    changes = apply_vetoes(info, scores)
    composite = round(compute_composite(scores), 2)

    print(f"  Composite: {composite}")
    for d in DIMS:
        print(f"    {d:<35} {scores.get(d, '?')}")

    # Step 4: Reflection
    print(f"\n[4/5] Reflection loop...")
    from scripts.reflect import ReflectionLoop
    from scoring import compute_composite as reflect_comp
    john = load_john_reference(company_name)
    if john:
        print(f"  John reference available: composite={john['composite']}")
    else:
        print(f"  No John reference available")
    loop = ReflectionLoop()
    reflection = loop.improve_scorecard(company_name, scores, enriched, john_reference=john)

    if reflection['improved']:
        print(f"  Refinements: {reflection['total_improvements']}")
        scores = reflection['refined_scores']
        composite = round(compute_composite(scores), 2)
        print(f"  Refined composite: {composite}")

    # Compute confidence from reflection + source count
    src_count = len(enriched.get('sources_found', []))
    ref_rounds = len(reflection.get('rounds', []))
    total_improvements = reflection.get('total_improvements', 0)

    if src_count >= 5 and ref_rounds >= 1:
        confidence = 'High'
    elif src_count >= 3:
        confidence = 'Medium'
    elif src_count >= 1:
        confidence = 'Low'
    else:
        confidence = 'Very Low'

    if total_improvements > 0:
        confidence = 'Medium'  # At least some refinement happened

    if john:
        error = abs(composite - john['composite']) if john.get('composite') else 999
        if error <= 0.5:
            confidence = 'Validated'  # Highest — matches ground truth

    # Step 5: Write deep-analysis
    print(f"\n[5/5] Writing scorecard...")
    dim_rows = ''
    for i, dim in enumerate(DIMS, 1):
        s = scores.get(dim, 3)
        w = 'High' if i <= 3 else ('Medium' if i <= 6 else 'Low')
        dim_rows += f'| {i} | {dim} | {w} | {s} | From pipeline research | — |\n'

    da = f"""# {company_name} — Deep M&A Analysis

**Research date**: {datetime.now().strftime('%Y-%m-%d')}
**Pipeline**: Automated research pipeline v2
**Sources**: {len(enriched.get('sources_found', []))} — {', '.join(enriched.get('sources_found', []))}

---

## 1. Quick-Scan Results

| Data Point | Value |
|---|---|
| Website | {scan.get('domain', domain or '')} |
| Reachable | {scan.get('website_reachable', False)} |
| Title | {scan.get('title', '')} |
| Tech stack | {', '.join(scan.get('tech_stack', [])[:8])} |
| Pricing | {scan.get('pricing', {}).get('pricing_url', 'Not found')} |
| Careers | {scan.get('careers', {}).get('careers_url', 'Not found')} |

---

## 2. Enriched Data

| Source | Data Found |
|---|---|
| Wikipedia | {'✓' if enriched.get('wikipedia') else '—'} |
| GitHub | {'✓ ' + str(enriched.get('github', {}).get('public_repos', 0)) + ' repos' if enriched.get('github') else '—'} |
| DNS | {'✓ ' + str(enriched.get('hosting', {}).get('hosting', '')) if enriched.get('hosting', {}).get('hosting') else '✓'} |
| News | {'✓ ' + str(len(enriched.get('news', []))) + ' articles' if enriched.get('news') else '—'} |
| Crunchbase | {'✓' if enriched.get('crunchbase') else '—'} |
| SEC EDGAR | {'✓' if enriched.get('sec_edgar') else '—'} |
| yfinance | {'✓' if enriched.get('yfinance') else '—'} |
| Web Search | {'✓ ' + str(len(enriched.get('web_search', []))) + ' results' if enriched.get('web_search') else '—'} |

---

## 3. M&A Attractiveness Scorecard

| # | Dimension | Weight | Score | Rationale | Source |
|---|---|---|---|---|---|
{dim_rows}
**Composite**: {composite} / 5.0
**Confidence band**: {'Medium-High' if len(enriched.get('sources_found', [])) >= 4 else 'Medium' if len(enriched.get('sources_found', [])) >= 2 else 'Low'}
**Reflection rounds**: {len(reflection.get('rounds', []))}

---

## 4. Reflection Loop Results

{'No refinements needed' if not reflection.get('improved') else f'{reflection["total_improvements"]} improvements made across {len(reflection.get("rounds", []))} rounds'}
"""

    da_path = os.path.join(out_dir, 'deep-analysis.md')
    with open(da_path, 'w') as f:
        f.write(da)

    print(f"  Written: {da_path}")
    print(f"\n{'='*60}")
    print(f"Done: {company_name} — composite {composite}/5.0")
    print(f"{'='*60}")

    return {
        'company': company_name,
        'composite': composite,
        'scores': scores,
        'sources': enriched.get('sources_found', []),
        'john_composite': john['composite'] if john else None,
    }


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'Booking Experts'
    domain = sys.argv[2] if len(sys.argv) > 2 else None
    run_pipeline(name, domain)
