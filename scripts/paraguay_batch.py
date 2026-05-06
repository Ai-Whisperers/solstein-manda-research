#!/usr/bin/env python3
"""Batch enrichment of Paraguay leads from Google Maps CSV.
Usage:
  python3 scripts/paraguay_batch.py --priority A --limit 10    # Test 10 leads
  python3 scripts/paraguay_batch.py --priority A --limit 1000  # Enrich top 1,000
  python3 scripts/paraguay_batch.py --vertical=tech --limit 20 # Scrape+enrich a vertical
  python3 scripts/paraguay_batch.py --analyze                  # Analyze saved results
"""
import sys, os, json, csv, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import scripts.quickscan as qs
qs._HAS_PLAYWRIGHT = False

from sources.maps import load_leads, enrich_lead
from core.cache import cache_stats
from scoring import DIMS, compute_composite, composite_to_grade


def run_enrichment(args):
    priority = args.get('priority', 'A')
    limit = args.get('limit')
    vertical = args.get('vertical')
    
    if vertical:
        # Scrape + enrich a specific vertical
        print(f"\nScraping vertical: {vertical}")
        from paraguay_scrape import scrape_vertical, merge_all
        scrape_vertical(vertical)
        merge_all()
        # Load from the vertical CSV
        vertical_csv = os.path.join(os.path.dirname(__file__), '..', 'data', 'paraguay', f'leads_{vertical}.csv')
        leads = load_leads(csv_path=vertical_csv, limit=limit)
    else:
        leads = load_leads(priority=priority, limit=limit)
    
    leads = load_leads(priority=priority, limit=limit)
    if not leads:
        print("No leads found. Check data/paraguay/paraguay_beauty_prioritized.csv")
        return
    
    print(f"\nEnriching {len(leads)} Priority {priority} leads...")
    print(f"{'='*60}")
    
    results = []
    errors = 0
    start = time.time()
    
    for i, lead in enumerate(leads, 1):
        try:
            data = enrich_lead(lead)
            srcs = data.get('sources_found', [])
            score_data(data, lead)
            results.append(data)
            
            elapsed = time.time() - start
            avg = elapsed / i
            remaining = avg * (len(leads) - i)
            print(f"  [{i}/{len(leads)}] {lead['name'][:25]:25s} {len(srcs)} srcs | "
                  f"maps={data.get('maps',{}).get('rating','')}★ | "
                  f"ETA: {remaining/60:.1f}min", flush=True)
        except Exception as e:
            errors += 1
            print(f"  [{i}/{len(leads)}] ERROR: {lead['name']}: {e}", flush=True)
    
    total_time = time.time() - start
    print(f"\n{'='*60}")
    print(f"Completed: {len(results)} leads in {total_time/60:.1f}min ({errors} errors)")
    
    # Save results
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'paraguay')
    os.makedirs(out_dir, exist_ok=True)
    
    out_path = os.path.join(out_dir, f'enriched_priority_{priority.lower()}.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Saved: {out_path}")
    
    # Save CSV summary
    csv_path = os.path.join(out_dir, f'enriched_priority_{priority.lower()}.csv')
    save_csv_summary(results, csv_path)
    print(f"Saved: {csv_path}")
    
    # Cache stats
    cs = cache_stats()
    print(f"Cache: {cs['total_files']} files, {cs['total_size_kb']} KB")


def score_data(data, lead):
    """Apply scoring to enriched lead data."""
    scores = {d: 3 for d in DIMS}
    m = data.get('maps', {})
    
    # Google rating = proxy for customer satisfaction
    try:
        rating = float(m.get('rating', 0) or 0)
        if rating >= 4.5: scores['Customer lock-in'] = 4
        elif rating >= 4.0: scores['Customer lock-in'] = 3
    except: pass
    
    # Review count = proxy for business size
    try:
        reviews = int(m.get('reviews', 0) or 0)
        if reviews >= 200: scores['Revenue scale fit'] = 3
        elif reviews >= 50: scores['Revenue scale fit'] = 2
    except: pass
    
    # Digital presence = suggests tech adoption
    has_web = str(m.get('has_website', 'False'))
    if has_web == 'True':
        scores['Tech stack modernity'] = 3
        scores['Integration potential'] = 3
    
    # More Solstein sources = more digital footprint
    src_count = len(data.get('sources_found', []))
    if src_count >= 5: scores['Tech stack modernity'] = 4
    
    comp = compute_composite(scores)
    grade = composite_to_grade(comp)
    
    data['scoring'] = {
        'scores': scores,
        'composite': round(comp, 2),
        'grade': grade['grade'],
        'ars': grade['score_100'],
    }


def save_csv_summary(results, path):
    """Save a flat CSV with key fields from enriched results."""
    fields = [
        'company', 'maps_category', 'maps_city', 'maps_rating', 'maps_reviews',
        'has_website', 'sources_count',
        'composite', 'grade', 'ars',
        'abstractapi_industry', 'serpapi_results', 'linkedin_employees',
        'github_repos', 'wiki_title',
    ]
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for r in results:
            m = r.get('maps', {})
            s = r.get('scoring', {})
            writer.writerow([
                r.get('company', ''),
                m.get('category', ''),
                m.get('city', ''),
                m.get('rating', ''),
                m.get('reviews', ''),
                m.get('has_website', False),
                len(r.get('sources_found', [])),
                s.get('composite', ''),
                s.get('grade', ''),
                s.get('ars', ''),
                r.get('abstractapi', {}).get('industry', ''),
                len(r.get('serpapi', {}).get('results', [])) if r.get('serpapi') else 0,
                r.get('linkedin', {}).get('estimated_employees', ''),
                r.get('github', {}).get('public_repos', 0) if r.get('github') else 0,
                r.get('wikipedia', {}).get('title', '') if r.get('wikipedia') else '',
            ])


def run_analysis(args):
    """Analyze previously saved enrichment results."""
    import json
    from collections import Counter
    
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'paraguay')
    
    for priority in ['A', 'B']:
        path = os.path.join(out_dir, f'enriched_priority_{priority.lower()}.json')
        if not os.path.exists(path):
            print(f"No results for Priority {priority} at {path}")
            continue
        
        with open(path) as f:
            results = json.load(f)
        
        print(f"\n{'='*60}")
        print(f"PRIORITY {priority} ANALYSIS ({len(results)} leads)")
        print(f"{'='*60}")
        
        # Source coverage
        src_counter = Counter()
        for r in results:
            for s in r.get('sources_found', []):
                src_counter[s] += 1
        print(f"\nSource coverage:")
        for src, count in src_counter.most_common(10):
            print(f"  {src:20s} {count:4d}/{len(results)} ({count/len(results)*100:.0f}%)")
        
        # Score distribution
        composites = [r.get('scoring', {}).get('composite', 0) for r in results if r.get('scoring')]
        grades = Counter(r.get('scoring', {}).get('grade', '') for r in results if r.get('scoring'))
        if composites:
            print(f"\nScoring:")
            print(f"  Avg composite: {sum(composites)/len(composites):.2f}")
            print(f"  Grade distribution: {dict(grades)}")
        
        # Top categories
        cats = Counter(r.get('maps', {}).get('category', '') for r in results)
        print(f"\nTop categories:")
        for cat, count in cats.most_common(10):
            print(f"  {cat:20s} {count}")
        
        # Cities
        cities = Counter(r.get('maps', {}).get('city', '') for r in results)
        print(f"\nTop cities:")
        for city, count in cities.most_common(10):
            print(f"  {city:20s} {count}")


if __name__ == '__main__':
    args = {'priority': 'A', 'limit': None, 'analyze': False, 'vertical': None}
    for a in sys.argv[1:]:
        if a.startswith('--priority='): args['priority'] = a.split('=')[1]
        elif a.startswith('--limit='): args['limit'] = int(a.split('=')[1])
        elif a.startswith('--vertical='): args['vertical'] = a.split('=')[1]
        elif a == '--analyze': args['analyze'] = True
    
    if args['analyze']:
        run_analysis(args)
    else:
        run_enrichment(args)
