#!/usr/bin/env python3
"""
Multi-vertical Google Maps scraper for Paraguay.
Scrapes businesses by category across all 17 non-beauty optgroups.
Output: data/paraguay/leads_{vertical}.csv

Usage:
  python3 scripts/paraguay_scrape.py --list              # Show all verticals
  python3 scripts/paraguay_scrape.py --vertical=tech      # Scrape one vertical
  python3 scripts/paraguay_scrape.py --all                # Scrape all verticals
  python3 scripts/paraguay_scrape.py --merge              # Merge all CSVs
  python3 scripts/paraguay_scrape.py --analyze            # Analyze merged data
"""
import sys, os, csv, json, time, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'paraguay')
os.makedirs(OUT_DIR, exist_ok=True)

# Google Maps search queries for each vertical
# Uses Google Maps search via SerpAPI (we have the key)
VERTICALS = {
    # Professional Services
    "lawyers": {
        "queries": ["abogados Asunción Paraguay", "estudio jurídico Asunción", "bufete abogados Paraguay"],
        "builder_vertical": "b2b-professional",
        "interest": "high"
    },
    "accountants": {
        "queries": ["contadores Paraguay", "estudio contable Asunción", "auditoria Paraguay"],
        "builder_vertical": "b2b-professional",
        "interest": "high"
    },
    "insurance": {
        "queries": ["seguros Paraguay", "corredor seguros Asunción"],
        "builder_vertical": "finance-insurance",
        "interest": "high"
    },
    
    # Health/Medical
    "clinics": {
        "queries": ["clínicas médicas Asunción Paraguay", "centro médico Paraguay", "consultorio médico Asunción"],
        "builder_vertical": "health-wellness",
        "interest": "high"
    },
    "dentists": {
        "queries": ["odontología Asunción Paraguay", "dentistas Paraguay", "clínica dental Asunción"],
        "builder_vertical": "health-wellness",
        "interest": "high"
    },
    "veterinarians": {
        "queries": ["veterinarias Asunción Paraguay", "veterinario Paraguay", "clínica veterinaria Asunción"],
        "builder_vertical": "pets-animals",
        "interest": "high"
    },
    
    # Tech/Education
    "tech_companies": {
        "queries": ["empresas tecnología Paraguay", "desarrollo software Paraguay", "TI Paraguay"],
        "builder_vertical": "technology-digital",
        "interest": "high"
    },
    "marketing_agencies": {
        "queries": ["agencias marketing Paraguay", "publicidad Paraguay", "marketing digital Paraguay"],
        "builder_vertical": "technology-digital",
        "interest": "high"
    },
    "coding_schools": {
        "queries": ["cursos programación Paraguay", "bootcamp informática Asunción"],
        "builder_vertical": "education-training",
        "interest": "medium"
    },
    
    # Home Services / Construction
    "construction": {
        "queries": ["constructoras Paraguay", "empresas construcción Asunción", "arquitectos Paraguay"],
        "builder_vertical": "trades-home-services",
        "interest": "high"
    },
    "electricians_plumbers": {
        "queries": ["electricistas Asunción Paraguay", "plomeros Paraguay", "técnicos reparación Asunción"],
        "builder_vertical": "trades-home-services",
        "interest": "medium"
    },
    
    # Automotive
    "auto_repair": {
        "queries": ["talleres mecánicos Asunción Paraguay", "mecánica automotriz Paraguay", "autopartes Paraguay"],
        "builder_vertical": "automotive",
        "interest": "medium"
    },
    
    # Food
    "restaurants": {
        "queries": ["restaurantes Asunción Paraguay", "comida Paraguay", "delivery Paraguay"],
        "builder_vertical": "food-beverage",
        "interest": "medium"
    },
    
    # Creative/Media
    "photographers": {
        "queries": ["fotógrafos Asunción Paraguay", "fotografía profesional Paraguay"],
        "builder_vertical": "portfolio-professional",
        "interest": "medium"
    },
    "video_production": {
        "queries": ["producción audiovisual Paraguay", "videógrafos Asunción", "cine Paraguay"],
        "builder_vertical": "portfolio-professional",
        "interest": "medium"
    },
    
    # Logistics
    "logistics": {
        "queries": ["transporte Paraguay", "logística Paraguay", "fletes Asunción Paraguay"],
        "builder_vertical": "logistics-transport",
        "interest": "medium"
    },
    
    # Tourism
    "tourism": {
        "queries": ["agencias viajes Paraguay", "turismo Paraguay", "hoteles Asunción Paraguay"],
        "builder_vertical": "hospitality-tourism",
        "interest": "low"
    },
}


def list_verticals():
    print("Available verticals for scraping:")
    print()
    for slug, info in sorted(VERTICALS.items()):
        interest = info['interest']
        queries = info['queries']
        print(f"  {slug:25s} [{interest}] {queries[0]}")
    print()
    print("Run: python3 scripts/paraguay_scrape.py --vertical=<slug>")
    print("Run: python3 scripts/paraguay_scrape.py --all")


def scrape_vertical(slug):
    """Scrape one vertical using SerpAPI Google Maps search."""
    info = VERTICALS.get(slug)
    if not info:
        print(f"Unknown vertical: {slug}. Use --list to see available.")
        return
    
    from core.config import Config
    from core.cache import cache_get_or_fetch
    import urllib.request, urllib.parse
    
    serp_key = Config.get('SERPAPI_KEY')
    if not serp_key:
        print("SERPAPI_KEY not set. Add to .env")
        return
    
    all_results = []
    seen_names = set()
    
    for query in info['queries']:
        print(f"  Searching: {query}")
        encoded = urllib.parse.quote(f"{query}")
        url = f"https://serpapi.com/search?q={encoded}&api_key={serp_key}&engine=google_maps&type=search&num=20"
        
        data = cache_get_or_fetch('paraguay_maps', slug + '_' + query.replace(' ', '_')[:30], 
            lambda: _fetch_serpapi(url), ttl=7*24*3600)
        
        if not data:
            print(f"    No results")
            continue
        
        results = data.get('local_results', [])
        for r in results:
            name = r.get('title', '').strip()
            if not name or name in seen_names:
                continue
            seen_names.add(name)
            
            phone = r.get('phone', '') or r.get('international_phone', '') or ''
            website = r.get('website', '') or ''
            rating = r.get('rating', '')
            reviews = r.get('reviews', 0)
            address = r.get('address', '') or ''
            lat = r.get('gps_coordinates', {}).get('latitude', '')
            lng = r.get('gps_coordinates', {}).get('longitude', '')
            types = r.get('type', '') or ''
            
            all_results.append({
                'name': name,
                'vertical': slug,
                'category': info['builder_vertical'],
                'city': _extract_city(address),
                'address': address,
                'lat': lat,
                'lng': lng,
                'phone': phone,
                'website': website,
                'rating': rating,
                'total_reviews': reviews,
                'has_website': bool(website),
                'types': types,
            })
    
    # Save to CSV
    path = os.path.join(OUT_DIR, f'leads_{slug}.csv')
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'name', 'vertical', 'category', 'city', 'address',
            'lat', 'lng', 'phone', 'website', 'rating', 'total_reviews',
            'has_website', 'types'
        ])
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"  Saved {len(all_results)} leads to {path}")
    return all_results


def _fetch_serpapi(url):
    import urllib.request, json
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'SolSteinResearch/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"    SerpAPI error: {e}")
        return None


def _extract_city(address):
    if not address:
        return ''
    parts = address.split(',')
    for p in parts:
        p = p.strip()
        if p in ('Asunción', 'Asuncion'): return 'Asunción'
        if 'Ciudad del Este' in p: return 'Ciudad del Este'
        if 'Encarnación' in p: return 'Encarnación'
        if p and len(p) > 3: return p
    return parts[-2].strip() if len(parts) > 1 else parts[0].strip()


def merge_all():
    """Merge all individual vertical CSVs into one master file."""
    all_rows = []
    total = 0
    for f in sorted(os.listdir(OUT_DIR)):
        if f.startswith('leads_') and f.endswith('.csv'):
            path = os.path.join(OUT_DIR, f)
            with open(path, encoding='utf-8') as fh:
                reader = csv.DictReader(fh)
                rows = list(reader)
                slug = f.replace('leads_', '').replace('.csv', '')
                print(f"  {slug:25s} {len(rows):5d} leads")
                all_rows.extend(rows)
                total += len(rows)
    
    path = os.path.join(OUT_DIR, 'paraguay_all_verticals.csv')
    if all_rows:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_rows)
    print(f"\n  TOTAL: {total} leads across {len([f for f in os.listdir(OUT_DIR) if f.startswith('leads_')])} verticals")
    print(f"  Merged: {path}")


def analyze():
    """Analyze the merged data."""
    from collections import Counter
    
    path = os.path.join(OUT_DIR, 'paraguay_all_verticals.csv')
    if not os.path.exists(path):
        path = os.path.join(OUT_DIR, 'paraguay_beauty_prioritized.csv')
    
    if not os.path.exists(path):
        print(f"No merged data at {path}")
        return
    
    with open(path, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    
    print(f"\n{'='*60}")
    print(f"PARAGUAY LEADS ANALYSIS ({len(rows)} total)")
    print(f"{'='*60}")
    
    verticals = Counter(r.get('vertical', r.get('category', 'unknown')) for r in rows)
    print(f"\nVerticals:")
    for v, count in verticals.most_common():
        print(f"  {v:30s} {count:5d}")
    
    cities = Counter(r.get('city', '') for r in rows)
    print(f"\nTop cities:")
    for city, count in cities.most_common(10):
        print(f"  {city:30s} {count}")
    
    no_web = sum(1 for r in rows if r.get('has_website', 'False').lower() != 'true')
    print(f"\nWebsite gap: {no_web}/{len(rows)} ({no_web/len(rows)*100:.0f}%) no website")
    
    rated = [float(r['rating']) for r in rows if r.get('rating') and r['rating']]
    if rated:
        print(f"Avg rating: {sum(rated)/len(rated):.2f}★ ({len(rated)} rated)")
    
    reviewed = [int(r['total_reviews']) for r in rows if r.get('total_reviews') and r['total_reviews'].isdigit()]
    if reviewed:
        print(f"Avg reviews: {sum(reviewed)/len(reviewed):.0f}")
        top_reviewed = sorted([r for r in rows if r.get('total_reviews') and r['total_reviews'].isdigit()],
                            key=lambda x: int(x['total_reviews']), reverse=True)[:10]
        print(f"\nMost reviewed:")
        for r in top_reviewed:
            print(f"  {r.get('name',''):35s} {r.get('vertical',r.get('category','')):20s} {r['total_reviews']} reviews ★{r.get('rating','')}")


if __name__ == '__main__':
    if '--list' in sys.argv:
        list_verticals()
    elif '--all' in sys.argv:
        for slug in VERTICALS:
            print(f"\n--- {slug} ---")
            scrape_vertical(slug)
            time.sleep(1)
        merge_all()
        analyze()
    elif '--merge' in sys.argv:
        merge_all()
    elif '--analyze' in sys.argv:
        analyze()
    else:
        for a in sys.argv[1:]:
            if a.startswith('--vertical='):
                slug = a.split('=')[1]
                scrape_vertical(slug)
                merge_all()
                analyze()
