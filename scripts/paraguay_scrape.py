#!/usr/bin/env python3
"""
Multi-vertical, multi-country Google Maps scraper.
Scrapes businesses by vertical × location via SerpAPI.
Output: data/{country}/leads_{vertical}.csv

Usage:
  python3 scripts/paraguay_scrape.py --list                     # Show verticals
  python3 scripts/paraguay_scrape.py --vertical=tech             # Scrape PY tech
  python3 scripts/paraguay_scrape.py --vertical=tech --country=ar  # Scrape AR tech
  python3 scripts/paraguay_scrape.py --country=py --all          # All PY verticals
  python3 scripts/paraguay_scrape.py --country=ar --all          # All AR verticals
  python3 scripts/paraguay_scrape.py --merge                     # Merge all CSVs
  python3 scripts/paraguay_scrape.py --analyze --country=ar      # Analyze AR data
"""
import sys, os, csv, json, time, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# ─── Countries ───
COUNTRIES = {
    "py": {"name": "Paraguay",     "lang": "es", "currency": "PYG", "phone": "+595"},
    "ar": {"name": "Argentina",    "lang": "es", "currency": "ARS", "phone": "+54"},
    "br": {"name": "Brazil",       "lang": "pt", "currency": "BRL", "phone": "+55"},
    "uy": {"name": "Uruguay",      "lang": "es", "currency": "UYU", "phone": "+598"},
    "cl": {"name": "Chile",        "lang": "es", "currency": "CLP", "phone": "+56"},
    "pe": {"name": "Peru",         "lang": "es", "currency": "PEN", "phone": "+51"},
    "co": {"name": "Colombia",     "lang": "es", "currency": "COP", "phone": "+57"},
    "mx": {"name": "Mexico",       "lang": "es", "currency": "MXN", "phone": "+52"},
}

# Google Maps search queries for each vertical
# Each query is a template: {location} is replaced with the country's capital + country name
# Location templates — replaces {loc} with the country's main city
LOCATIONS = {
    "py": "Asunción Paraguay",
    "ar": "Buenos Aires Argentina",
    "br": "São Paulo Brasil",
    "uy": "Montevideo Uruguay",
    "cl": "Santiago Chile",
    "pe": "Lima Peru",
    "co": "Bogotá Colombia",
    "mx": "Ciudad de México México",
}

VERTICALS = {
    # Professional Services
    "lawyers": {
        "queries": ["abogados {loc}", "estudio jurídico {loc}", "bufete abogados {loc}"],
        "builder_vertical": "b2b-professional",
        "interest": "high"
    },
    "accountants": {
        "queries": ["contadores {loc}", "estudio contable {loc}", "auditoria {loc}"],
        "builder_vertical": "b2b-professional",
        "interest": "high"
    },
    "insurance": {
        "queries": ["seguros {loc}", "corredor seguros {loc}"],
        "builder_vertical": "finance-insurance",
        "interest": "high"
    },
    
    # Health/Medical
    "clinics": {
        "queries": ["clínicas médicas {loc}", "centro médico {loc}", "consultorio médico {loc}"],
        "builder_vertical": "health-wellness",
        "interest": "high"
    },
    "dentists": {
        "queries": ["odontología {loc}", "dentistas {loc}", "clínica dental {loc}"],
        "builder_vertical": "health-wellness",
        "interest": "high"
    },
    "veterinarians": {
        "queries": ["veterinarias {loc}", "veterinario {loc}", "clínica veterinaria {loc}"],
        "builder_vertical": "pets-animals",
        "interest": "high"
    },
    
    # Tech/Education
    "tech_companies": {
        "queries": ["empresas tecnología {loc}", "desarrollo software {loc}", "TI {loc}"],
        "builder_vertical": "technology-digital",
        "interest": "high"
    },
    "marketing_agencies": {
        "queries": ["agencias marketing {loc}", "publicidad {loc}", "marketing digital {loc}"],
        "builder_vertical": "technology-digital",
        "interest": "high"
    },
    "coding_schools": {
        "queries": ["cursos programación {loc}", "bootcamp informática {loc}"],
        "builder_vertical": "education-training",
        "interest": "medium"
    },
    
    # Home Services / Construction
    "construction": {
        "queries": ["constructoras {loc}", "empresas construcción {loc}", "arquitectos {loc}"],
        "builder_vertical": "trades-home-services",
        "interest": "high"
    },
    "electricians_plumbers": {
        "queries": ["electricistas {loc}", "plomeros {loc}", "técnicos reparación {loc}"],
        "builder_vertical": "trades-home-services",
        "interest": "medium"
    },
    
    # Automotive
    "auto_repair": {
        "queries": ["talleres mecánicos {loc}", "mecánica automotriz {loc}", "autopartes {loc}"],
        "builder_vertical": "automotive",
        "interest": "medium"
    },
    
    # Food
    "restaurants": {
        "queries": ["restaurantes {loc}", "comida {loc}", "delivery {loc}"],
        "builder_vertical": "food-beverage",
        "interest": "medium"
    },
    
    # Creative/Media
    "photographers": {
        "queries": ["fotógrafos {loc}", "fotografía profesional {loc}"],
        "builder_vertical": "portfolio-professional",
        "interest": "medium"
    },
    "video_production": {
        "queries": ["producción audiovisual {loc}", "videógrafos {loc}", "cine {loc}"],
        "builder_vertical": "portfolio-professional",
        "interest": "medium"
    },
    
    # Logistics
    "logistics": {
        "queries": ["transporte {loc}", "logística {loc}", "fletes {loc}"],
        "builder_vertical": "logistics-transport",
        "interest": "medium"
    },
    
    # Tourism
    "tourism": {
        "queries": ["agencias viajes {loc}", "turismo {loc}", "hoteles {loc}"],
        "builder_vertical": "hospitality-tourism",
        "interest": "low"
    },

    # Brazil-specific (Portuguese queries)
    "clinics_br": {
        "queries": ["clínicas médicas {loc}", "consultório médico {loc}"],
        "builder_vertical": "health-wellness",
        "interest": "high",
        "lang": "pt"
    },
    "tech_br": {
        "queries": ["empresas tecnologia {loc}", "desenvolvimento software {loc}"],
        "builder_vertical": "technology-digital",
        "interest": "high",
        "lang": "pt"
    },
}


def _get_out_dir(country="py"):
    d = os.path.join(DATA_DIR, country)
    os.makedirs(d, exist_ok=True)
    return d


def _resolve_queries(info, country="py"):
    """Replace {loc} placeholder with actual location for the country."""
    loc = LOCATIONS.get(country, "Asunción Paraguay")
    return [q.replace("{loc}", loc) for q in info.get('queries', [])]


def list_verticals():
    print("Available verticals for scraping:")
    print()
    for slug, info in sorted(VERTICALS.items()):
        interest = info['interest']
        queries = info['queries']
        print(f"  {slug:25s} [{interest}] {queries[0]}")
    print()
    print("Multi-country: add --country=ar, --country=br, --country=uy, etc.")
    print("Run: python3 scripts/paraguay_scrape.py --vertical=<slug> --country=ar")


def scrape_vertical(slug, country="py"):
    """Scrape one vertical for a specific country using SerpAPI Google Maps."""
    info = VERTICALS.get(slug)
    if not info:
        print(f"Unknown vertical: {slug}. Use --list to see available.")
        return None
    
    from core.config import Config
    from core.cache import cache_get_or_fetch
    import urllib.request, urllib.parse
    
    serp_key = Config.get('SERPAPI_KEY')
    if not serp_key:
        print("SERPAPI_KEY not set. Add to .env")
        return None
    
    queries = _resolve_queries(info, country)
    out_dir = _get_out_dir(country)
    country_name = COUNTRIES.get(country, {}).get('name', country.upper())
    
    all_results = []
    seen_names = set()
    
    for query in queries:
        print(f"  [{country_name}] Searching: {query}")
        encoded = urllib.parse.quote(query)
        url = f"https://serpapi.com/search?q={encoded}&api_key={serp_key}&engine=google_maps&type=search&num=20"
        
        data = cache_get_or_fetch(f'maps_{country}', slug + '_' + query.replace(' ', '_')[:30], 
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
            
            all_results.append({
                'name': name,
                'country': country,
                'vertical': slug,
                'category': info['builder_vertical'],
                'city': _extract_city(r.get('address', '') or ''),
                'address': (r.get('address', '') or ''),
                'lat': (r.get('gps_coordinates', {}) or {}).get('latitude', ''),
                'lng': (r.get('gps_coordinates', {}) or {}).get('longitude', ''),
                'phone': (r.get('phone', '') or r.get('international_phone', '') or ''),
                'website': (r.get('website', '') or ''),
                'rating': r.get('rating', ''),
                'total_reviews': r.get('reviews', 0),
                'has_website': bool(r.get('website', '')),
                'types': (r.get('type', '') or ''),
            })
    
    # Save to country-specific CSV
    path = os.path.join(out_dir, f'leads_{slug}.csv')
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'name', 'country', 'vertical', 'category', 'city', 'address',
            'lat', 'lng', 'phone', 'website', 'rating', 'total_reviews',
            'has_website', 'types'
        ])
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"  Saved {len(all_results)} [{country_name}] leads to {path}")
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


def merge_all(country=None):
    """Merge all individual vertical CSVs into one master file per country."""
    from collections import Counter
    countries = [country] if country else list(COUNTRIES.keys())
    
    for c in countries:
        out_dir = _get_out_dir(c)
        all_rows = []
        total = 0
        files_found = 0
        
        for f in sorted(os.listdir(out_dir)):
            if f.startswith('leads_') and f.endswith('.csv'):
                path = os.path.join(out_dir, f)
                with open(path, encoding='utf-8') as fh:
                    reader = csv.DictReader(fh)
                    rows = list(reader)
                    slug = f.replace('leads_', '').replace('.csv', '')
                    print(f"  [{c}] {slug:25s} {len(rows):5d} leads")
                    all_rows.extend(rows)
                    total += len(rows)
                    files_found += 1
        
        if all_rows:
            path = os.path.join(out_dir, 'all_verticals.csv')
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
                writer.writeheader()
                writer.writerows(all_rows)
            print(f"  [{c}] TOTAL: {total} leads across {files_found} verticals → {path}")


def analyze(country=None):
    """Analyze leads data for a specific country."""
    from collections import Counter
    
    if country:
        paths_to_try = [
            os.path.join(DATA_DIR, country, 'all_verticals.csv'),
        ]
    else:
        # Check all countries
        for c in COUNTRIES:
            analyze(c)
        return
    
    path = None
    for p in paths_to_try:
        if os.path.exists(p):
            path = p
            break
    
    if not path:
        print(f"No data for {country}. Scrape some verticals first.")
        return
    
    with open(path, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    
    country_name = COUNTRIES.get(country, {}).get('name', country.upper())
    print(f"\n{'='*60}")
    print(f"{country_name} LEADS ANALYSIS ({len(rows)} total)")
    print(f"{'='*60}")
    
    verticals = Counter(r.get('vertical', 'unknown') for r in rows)
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
    
    reviewed = [int(r['total_reviews']) for r in rows if r.get('total_reviews') and str(r['total_reviews']).isdigit()]
    if reviewed:
        print(f"Avg reviews: {sum(reviewed)/len(reviewed):.0f}")
        top_reviewed = sorted([r for r in rows if r.get('total_reviews') and str(r['total_reviews']).isdigit()],
                            key=lambda x: int(x['total_reviews']), reverse=True)[:10]
        print(f"\nMost reviewed:")
        for r in top_reviewed:
            print(f"  {r.get('name',''):35s} {r.get('vertical',''):20s} {r['total_reviews']} reviews ★{r.get('rating','')}")


if __name__ == '__main__':
    country = 'py'
    for a in sys.argv[1:]:
        if a.startswith('--country='):
            country = a.split('=')[1]
    
    if '--list' in sys.argv:
        list_verticals()
    elif '--all' in sys.argv:
        for slug in VERTICALS:
            print(f"\n--- {slug} [{country}] ---")
            scrape_vertical(slug, country=country)
            time.sleep(1)
        merge_all(country=country)
        analyze(country=country)
    elif '--merge' in sys.argv:
        merge_all(country=country)
    elif '--analyze' in sys.argv:
        analyze(country=country)
    else:
        for a in sys.argv[1:]:
            if a.startswith('--vertical='):
                slug = a.split('=')[1]
                scrape_vertical(slug, country=country)
                merge_all(country=country)
                analyze(country=country)
