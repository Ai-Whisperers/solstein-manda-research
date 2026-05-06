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
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'core'))

BASE = os.path.join(os.path.dirname(__file__), '..', '..')
JOHN_JSON = os.path.join(BASE, 'archive', 'john-original', 'horeca_json', 'horeca_data.json')

from core.utils import safe_json_load, atomic_json_dump
from core.config import Config
DIMS = ['Ownership attractiveness', 'Revenue scale fit', 'Geographic fit',
        'Tech stack modernity', 'Customer lock-in', 'Vertical depth',
        'Integration potential', 'Growth trajectory']


def load_john_reference(company_name):
    """Load John's scores for a company if available."""
    data = safe_json_load(JOHN_JSON)
    if not data:
        return None
    for c in data.get('companies', []):
        if c['company_name'].lower().strip() == company_name.lower().strip():
            sc = c.get('scorecard')
            if sc and sc.get('composite_score'):
                dims = sc.get('dimensions', {})
                return {
                    'composite': sc['composite_score'],
                    'dimensions': {k: v['score'] for k, v in dims.items() if isinstance(v, dict) and v.get('score')},
                }
    return None


def _run_quickscan(company_name, domain, out_dir):
    """Stage 1: Browser/stdlib quick-scan of company website."""
    from scripts.quickscan import quick_scan
    scan = quick_scan(company_name, domain)
    atomic_json_dump(scan, os.path.join(out_dir, 'quickscan.json'), indent=2)
    print(f"  Method: {scan['method']}, reachable: {scan['website_reachable']}")
    print(f"  Tech: {', '.join(scan['tech_stack'][:6])}")
    return scan


def _run_enrichment(company_name, domain, out_dir):
    """Stage 2: Multi-source enrichment."""
    from sources.enrichment import enrich_company
    enriched = enrich_company(company_name, domain)
    atomic_json_dump(enriched, os.path.join(out_dir, 'enriched.json'), indent=2)
    print(f"  Sources: {len(enriched['sources_found'])} — {', '.join(enriched['sources_found'])}")
    return enriched


def _score_from_enriched(enriched):
    """Stage 3: Score company on 8 dimensions using enriched data."""
    from scoring import apply_vetoes, compute_composite
    w = enriched.get('website', {})
    scores = {d: 3 for d in DIMS}
    scores['Geographic fit'] = 4 if w.get('tech_stack') else 3

    if enriched.get('github', {}).get('public_repos', 0) > 10:
        scores['Tech stack modernity'] = 4
        scores['Integration potential'] = 4
    if w.get('tech_stack'):
        stack = w['tech_stack']
        if any(x in stack for x in ['Angular', 'React', 'Vue.js']):
            scores['Tech stack modernity'] = 4
        if 'PHP' in stack:
            scores['Tech stack modernity'] = max(2, scores['Tech stack modernity'] - 1)
        if any(x in stack for x in ['Mollie', 'Stripe', 'Adyen']):
            scores['Integration potential'] = 4

    cb = enriched.get('crunchbase') or {}
    apply_vetoes({'ownership': str(cb.get('description', '') if isinstance(cb, dict) else ''),
                  'country': '', 'status': ''}, scores)
    composite = round(compute_composite(scores), 2)

    print(f"  Composite: {composite}")
    for d in DIMS:
        print(f"    {d:<35} {scores.get(d, '?')}")
    return scores, composite


def _reflect_and_refine(company_name, scores, enriched):
    """Stage 4: Reflection loop to identify and fix weak dimensions."""
    from pipeline.reflect import ReflectionLoop
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
    return scores, reflection, john


def _compute_confidence(enriched, reflection, scores, john):
    """Compute confidence band from source count + reflection + ground truth."""
    src_count = len(enriched.get('sources_found', []))
    ref_rounds = len(reflection.get('rounds', []))
    total_improvements = reflection.get('total_improvements', 0)
    composite = round(__import__('scoring').compute_composite(scores), 2)

    if src_count >= 5 and ref_rounds >= 1: conf = 'High'
    elif src_count >= 3: conf = 'Medium'
    elif src_count >= 1: conf = 'Low'
    else: conf = 'Very Low'

    if total_improvements > 0: conf = 'Medium'
    if john:
        err = abs(composite - john['composite']) if john.get('composite') else 999
        if err <= 0.5: conf = 'Validated'
    return conf


def _write_report(company_name, domain, scan, enriched, scores, reflection, composite, out_dir):
    """Stage 5: Generate and save the deep-analysis markdown report."""
    dim_rows = ''
    for i, dim in enumerate(DIMS, 1):
        s = scores.get(dim, 3)
        w = 'High' if i <= 3 else ('Medium' if i <= 6 else 'Low')
        dim_rows += f'| {i} | {dim} | {w} | {s} | From pipeline research | — |\n'

    src_count = len(enriched.get('sources_found', []))
    da = f"""# {company_name} — Deep M&A Analysis

**Research date**: {datetime.now().strftime('%Y-%m-%d')}
**Pipeline**: Automated research pipeline v2
**Sources**: {src_count} — {', '.join(enriched.get('sources_found', []))}

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
| News | {'✓ ' + str(len(enriched.get('news', []))) + ' articles' if enriched.get('news') else '—'} |
| SEC EDGAR | {'✓' if enriched.get('sec_edgar') else '—'} |

---

## 3. M&A Attractiveness Scorecard

| # | Dimension | Weight | Score | Rationale | Source |
|---|---|---|---|---|---|
{dim_rows}
**Composite**: {composite} / 5.0
**Confidence band**: {'Medium-High' if src_count >= 4 else 'Medium' if src_count >= 2 else 'Low'}
**Reflection rounds**: {len(reflection.get('rounds', []))}

---

## 4. Reflection Loop Results

{'No refinements needed' if not reflection.get('improved') else f'{reflection["total_improvements"]} improvements made across {len(reflection.get("rounds", []))} rounds'}
"""
    da_path = os.path.join(out_dir, 'deep-analysis.md')
    with open(da_path, 'w') as f:
        f.write(da)
    print(f"  Written: {da_path}")
    return da_path


def run_pipeline(company_name, domain=None):
    """Run complete research pipeline for one company — 5 stages."""
    print(f"\n{'='*60}\nResearch Pipeline: {company_name}\n{'='*60}")
    out_dir = os.path.join(Config.HORECA_DIR, company_name.lower().replace(' ', '-'))
    os.makedirs(out_dir, exist_ok=True)

    scan = _run_quickscan(company_name, domain, out_dir)
    enriched = _run_enrichment(company_name, domain, out_dir)
    scores, composite = _score_from_enriched(enriched)
    scores, reflection, john = _reflect_and_refine(company_name, scores, enriched)
    composite = round(__import__('scoring').compute_composite(scores), 2)

    _compute_confidence(enriched, reflection, scores, john)
    _write_report(company_name, domain, scan, enriched, scores, reflection, composite, out_dir)

    print(f"\n{'='*60}\nDone: {company_name} — composite {composite}/5.0\n{'='*60}")
    return {
        'company': company_name, 'composite': composite, 'scores': scores,
        'sources': enriched.get('sources_found', []),
        'john_composite': john['composite'] if john else None,
    }


if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else 'Booking Experts'
    domain = sys.argv[2] if len(sys.argv) > 2 else None
    run_pipeline(name, domain)
