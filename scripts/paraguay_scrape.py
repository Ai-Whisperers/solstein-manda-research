#!/usr/bin/env python3
"""
Multi-vertical, multi-country Google Maps scraper — v2.
Scrapes businesses by vertical × location via SerpAPI with pagination,
multi-city coverage, and deep dedup.

Output: data/{country}/leads_{vertical}.csv

Usage:
  python3 scripts/paraguay_scrape.py --list                          # Show verticals
  python3 scripts/paraguay_scrape.py --vertical=tech --country=py    # Scrape PY tech
  python3 scripts/paraguay_scrape.py --country=py --all              # All PY verticals
  python3 scripts/paraguay_scrape.py --country=ar --all              # All AR verticals
  python3 scripts/paraguay_scrape.py --country=py --deep=lawyers     # Deep scrape lawyers with pagination
  python3 scripts/paraguay_scrape.py --merge --country=py            # Merge PY CSVs
  python3 scripts/paraguay_scrape.py --analyze --country=py          # Analyze PY data
  python3 scripts/paraguay_scrape.py --all-countries --vertical=tech # Scrape tech in ALL countries
"""
import sys, os, csv, json, time, re, urllib.request, urllib.parse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import Config
from core.cache import cache_get_or_fetch

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
SERP_KEY = Config.get('SERPAPI_KEY')

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

# ─── Cities per country (for nationwide coverage) ───
CITIES = {
    "py": ["Asunción", "Ciudad del Este", "Encarnación", "San Lorenzo", "Luque",
           "Capiatá", "Lambaré", "Fernando de la Mora", "Mariano Roque Alonso",
           "Hernandarias", "Presidente Franco", "Caaguazú", "Coronel Oviedo",
           "Pedro Juan Caballero", "Concepción", "Villarrica", "Pilar", "Caacupé"],
    "ar": ["Buenos Aires", "Córdoba", "Rosario", "Mendoza", "La Plata",
           "San Miguel de Tucumán", "Mar del Plata", "Salta", "Santa Fe",
           "Corrientes", "Bahía Blanca", "Posadas", "Resistencia", "Santiago del Estero"],
    "br": ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Brasília", "Salvador",
           "Fortaleza", "Curitiba", "Manaus", "Recife", "Porto Alegre",
           "Belém", "Goiânia", "Guarulhos", "Campinas", "São Luís"],
    "uy": ["Montevideo", "Salto", "Paysandú", "Ciudad de la Costa", "Las Piedras",
           "Rivera", "Maldonado", "Tacuarembó", "Melo", "Mercedes"],
    "cl": ["Santiago", "Valparaíso", "Concepción", "La Serena", "Antofagasta",
           "Temuco", "Rancagua", "Talca", "Arica", "Iquique", "Puerto Montt"],
    "pe": ["Lima", "Arequipa", "Trujillo", "Chiclayo", "Piura",
           "Cusco", "Huancayo", "Iquitos", "Tacna", "Juliaca"],
    "co": ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena",
           "Cúcuta", "Bucaramanga", "Pereira", "Santa Marta", "Ibagué"],
    "mx": ["Ciudad de México", "Guadalajara", "Monterrey", "Puebla", "Tijuana",
           "León", "Querétaro", "Juárez", "Zapopan", "Mérida"],
}

# ─── Vertical definitions with search queries ───
# Each entry has: queries (list of search strings), builder_vertical (mapping),
# interest (high/medium/low), min_reviews (filter out businesses with fewer reviews)
VERTICALS = {
    # ── Professional Services ──
    "lawyers": {
        "queries": ["abogados", "estudio jurídico", "bufete abogados", "consultoría legal", "despacho abogados"],
        "builder_vertical": "b2b-professional",
        "interest": "high", "min_reviews": 3
    },
    "accountants": {
        "queries": ["contadores", "estudio contable", "auditoria", "contabilidad", "asesoría fiscal"],
        "builder_vertical": "b2b-professional",
        "interest": "high", "min_reviews": 3
    },
    "insurance": {
        "queries": ["seguros", "corredor seguros", "compañía seguros", "productor seguros"],
        "builder_vertical": "finance-insurance",
        "interest": "high", "min_reviews": 3
    },
    "notaries": {
        "queries": ["escribanos", "escribanía", "notaría"],
        "builder_vertical": "b2b-professional",
        "interest": "medium", "min_reviews": 2
    },
    "real_estate": {
        "queries": ["inmobiliarias", "corredor inmobiliario", "bienes raíces", "agencia inmobiliaria"],
        "builder_vertical": "real-estate-relocation",
        "interest": "high", "min_reviews": 3
    },

    # ── Health/Medical ──
    "clinics": {
        "queries": ["clínica médica", "centro médico", "consultorio médico", "policlínico", "centro de salud"],
        "builder_vertical": "health-wellness",
        "interest": "high", "min_reviews": 5
    },
    "dentists": {
        "queries": ["odontólogo", "dentista", "clínica dental", "consultorio odontológico"],
        "builder_vertical": "health-wellness",
        "interest": "high", "min_reviews": 5
    },
    "veterinarians": {
        "queries": ["veterinaria", "clínica veterinaria", "veterinario", "hospital veterinario"],
        "builder_vertical": "pets-animals",
        "interest": "high", "min_reviews": 5
    },
    "pharmacies": {
        "queries": ["farmacia", "droguería", "farmacéutica"],
        "builder_vertical": "health-wellness",
        "interest": "medium", "min_reviews": 5
    },
    "opticians": {
        "queries": ["óptica", "centro óptico", "laboratorio óptico"],
        "builder_vertical": "health-wellness",
        "interest": "medium", "min_reviews": 2
    },
    "psychologists": {
        "queries": ["psicólogo", "psicoterapia", "consultorio psicológico", "psiquiatra"],
        "builder_vertical": "health-wellness",
        "interest": "medium", "min_reviews": 3
    },

    # ── Tech/Education ──
    "tech_companies": {
        "queries": ["empresa tecnología", "desarrollo software", "TI informática",
                     "soluciones tecnológicas", "sistemas informáticos"],
        "builder_vertical": "technology-digital",
        "interest": "high", "min_reviews": 2
    },
    "marketing_agencies": {
        "queries": ["agencia marketing", "publicidad", "marketing digital",
                     "agencia publicidad", "diseño web"],
        "builder_vertical": "technology-digital",
        "interest": "high", "min_reviews": 3
    },
    "coding_schools": {
        "queries": ["curso programación", "bootcamp informática", "escuela tecnología",
                     "academia programación", "curso desarrollo web"],
        "builder_vertical": "education-training",
        "interest": "medium", "min_reviews": 2
    },
    "language_schools": {
        "queries": ["escuela idiomas", "curso inglés", "academia idiomas",
                     "instituto idiomas", "curso portugués"],
        "builder_vertical": "education-training",
        "interest": "medium", "min_reviews": 3
    },

    # ── Home Services / Construction ──
    "construction": {
        "queries": ["constructora", "empresa construcción", "arquitecto",
                     "ingeniero civil", "desarrolladora inmobiliaria"],
        "builder_vertical": "trades-home-services",
        "interest": "high", "min_reviews": 3
    },
    "electricians_plumbers": {
        "queries": ["electricista", "plomero", "técnico reparación", "servicio técnico",
                     "mantenimiento hogar", "cerrajero"],
        "builder_vertical": "trades-home-services",
        "interest": "medium", "min_reviews": 2
    },
    "remodeling": {
        "queries": ["remodelación", "reforma hogar", "diseño interior",
                     "decoración hogar", "ampliación casa"],
        "builder_vertical": "trades-home-services",
        "interest": "medium", "min_reviews": 2
    },

    # ── Automotive ──
    "auto_repair": {
        "queries": ["taller mecánico", "mecánica automotriz", "autopartes",
                     "servicio automotriz", "chapista pintura"],
        "builder_vertical": "automotive",
        "interest": "medium", "min_reviews": 3
    },
    "car_dealers": {
        "queries": ["concesionaria autos", "venta autos", "automotora",
                     "usados autos", "importadora autos"],
        "builder_vertical": "automotive",
        "interest": "medium", "min_reviews": 3
    },
    "motorcycle_shops": {
        "queries": ["taller motos", "venta motos", "motos repuestos", "concesionaria motos"],
        "builder_vertical": "automotive",
        "interest": "low", "min_reviews": 2
    },
    "tire_shops": {
        "queries": ["neumáticos", "llantas", "gomería", "centro llantas"],
        "builder_vertical": "automotive",
        "interest": "low", "min_reviews": 2
    },

    # ── Food/Restaurants ──
    "restaurants": {
        "queries": ["restaurante", "comida", "parrilla", "comida rápida", "pizzeria"],
        "builder_vertical": "food-beverage",
        "interest": "medium", "min_reviews": 10
    },
    "cafes": {
        "queries": ["cafetería", "café", "heladería", "panadería", "pastelería"],
        "builder_vertical": "food-beverage",
        "interest": "medium", "min_reviews": 5
    },
    "delivery": {
        "queries": ["delivery comida", "envío domicilio", "comida para llevar", "viandas"],
        "builder_vertical": "food-beverage",
        "interest": "medium", "min_reviews": 3
    },
    "catering": {
        "queries": ["catering", "servicio gastronómico", "bufet", "eventos gastronomía"],
        "builder_vertical": "food-beverage",
        "interest": "medium", "min_reviews": 3
    },

    # ── Creative/Media ──
    "photographers": {
        "queries": ["fotógrafo", "fotografía profesional", "fotografía bodas", "fotografía eventos"],
        "builder_vertical": "portfolio-professional",
        "interest": "medium", "min_reviews": 3
    },
    "video_production": {
        "queries": ["producción audiovisual", "videógrafo", "cine", "productora audiovisual"],
        "builder_vertical": "portfolio-professional",
        "interest": "medium", "min_reviews": 3
    },
    "graphic_design": {
        "queries": ["diseñador gráfico", "diseño gráfico", "diseño branding", "identidad corporativa"],
        "builder_vertical": "portfolio-professional",
        "interest": "medium", "min_reviews": 2
    },

    # ── Ecommerce/Retail ──
    "clothing_stores": {
        "queries": ["tienda ropa", "indumentaria", "boutique", "moda", "ropa mujer"],
        "builder_vertical": "retail-local",
        "interest": "medium", "min_reviews": 5
    },
    "electronics_stores": {
        "queries": ["tienda electrónica", "electrodomésticos", "tecnología", "celulares", "informática"],
        "builder_vertical": "retail-local",
        "interest": "medium", "min_reviews": 5
    },

    # ── Logistics ──
    "logistics": {
        "queries": ["transporte", "logística", "fletes", "mensajería", "courier"],
        "builder_vertical": "logistics-transport",
        "interest": "medium", "min_reviews": 3
    },
    "storage": {
        "queries": ["depósito", "almacenamiento", "guardamuebles", "bodega"],
        "builder_vertical": "logistics-transport",
        "interest": "low", "min_reviews": 2
    },

    # ── Tourism/Hospitality ──
    "travel_agencies": {
        "queries": ["agencia viajes", "turismo", "operador turístico", "paquetes turísticos"],
        "builder_vertical": "hospitality-tourism",
        "interest": "medium", "min_reviews": 3
    },
    "hotels": {
        "queries": ["hotel", "hospedaje", "alojamiento", "hostal"],
        "builder_vertical": "hospitality-tourism",
        "interest": "medium", "min_reviews": 10
    },

    # ── Agriculture/Agribusiness (PY specific) ──
    "agribusiness": {
        "queries": ["agropecuaria", "campo", "agrícola", "ganadería", "agronegocios"],
        "builder_vertical": "agriculture",
        "interest": "medium", "min_reviews": 2
    },
    "farm_supplies": {
        "queries": ["insumos agropecuarios", "veterinaria campo", "fertilizantes", "semillas"],
        "builder_vertical": "agriculture",
        "interest": "medium", "min_reviews": 2
    },

    # ── Legal/Compliance (high value) ──
    "immigration_lawyers": {
        "queries": ["abogado inmigración", "abogado extranjería", "migraciones"],
        "builder_vertical": "b2b-professional",
        "interest": "high", "min_reviews": 2
    },
    "corporate_lawyers": {
        "queries": ["abogado corporativo", "abogado empresarial", "derecho comercial",
                     "abogado societario"],
        "builder_vertical": "b2b-professional",
        "interest": "high", "min_reviews": 2
    },
}


# ═══════════════════════════════════════════════
#  CORE FUNCTIONS
# ═══════════════════════════════════════════════

def _get_out_dir(country="py"):
    d = os.path.join(DATA_DIR, country)
    os.makedirs(d, exist_ok=True)
    return d


def _resolve_queries(info):
    return info.get('queries', [])


def _fetch_serpapi(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'SolSteinResearch/1.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f"    SerpAPI HTTP {e.code}: {body}")
        return None
    except Exception as e:
        print(f"    SerpAPI error: {e}")
        return None


def _extract_city(address, country="py"):
    """Extract city name from Google Maps address."""
    if not address:
        return ''
    parts = [p.strip() for p in address.split(',')]
    # Known PY cities
    py_cities = {'Asunción', 'Asuncion', 'Ciudad del Este', 'Encarnación', 'Encarnacion',
                 'San Lorenzo', 'Luque', 'Capiatá', 'Capiatá', 'Lambaré',
                 'Fernando de la Mora', 'Mariano Roque Alonso'}
    # Known AR cities
    ar_cities = {'Buenos Aires', 'CABA', 'Córdoba', 'Rosario', 'Mendoza', 'La Plata'}
    known = py_cities | ar_cities
    
    for p in parts:
        p = p.strip()
        if p in known:
            return p
        if any(city in p for city in known):
            return p
    # Return the second-to-last part (usually the city)
    for p in reversed(parts):
        p = p.strip()
        if len(p) > 3 and not any(x in p.lower() for x in ['paraguay', 'argentina', 'brasil', 'uruguay', 'chile', 'peru', 'colombia', 'mexico']):
            return p
    return parts[-2].strip() if len(parts) > 1 else parts[0].strip()


def _parse_serpapi_result(r, slug, info, country):
    """Parse a single SerpAPI result into our format."""
    name = r.get('title', '').strip()
    if not name:
        return None
    
    gps = r.get('gps_coordinates', {}) or {}
    address = (r.get('address', '') or '')
    phone = (r.get('phone', '') or r.get('international_phone', '') or '')
    website = (r.get('website', '') or '')
    rating = r.get('rating', '')
    reviews = r.get('reviews', 0) or 0
    
    return {
        'name': name,
        'country': country,
        'vertical': slug,
        'category': info['builder_vertical'],
        'city': _extract_city(address, country),
        'address': address,
        'lat': gps.get('latitude', ''),
        'lng': gps.get('longitude', ''),
        'phone': phone,
        'website': website,
        'rating': rating,
        'total_reviews': reviews,
        'has_website': bool(website),
        'types': (r.get('type', '') or ''),
    }


def _search_serpapi_maps(query, country, page=0):
    """Search Google Maps via SerpAPI. Supports pagination via 'start' parameter."""
    encoded = urllib.parse.quote(query)
    num = 20  # Max per page
    start = page * num
    url = (f"https://serpapi.com/search?q={encoded}&api_key={SERP_KEY}"
           f"&engine=google_maps&type=search&num={num}&start={start}")
    return _fetch_serpapi(url)


# ═══════════════════════════════════════════════
#  SCRAPING FUNCTIONS
# ═══════════════════════════════════════════════

def scrape_vertical(slug, country="py", max_pages=3, deep=False):
    """
    Scrape one vertical for a specific country using SerpAPI Google Maps.
    
    Args:
        slug: Vertical slug from VERTICALS dict
        country: Country code (py, ar, br, etc.)
        max_pages: Number of SerpAPI pages to fetch (20 results each)
        deep: If True, scrape ALL cities for the country (not just capital)
    """
    info = VERTICALS.get(slug)
    if not info:
        print(f"Unknown vertical: {slug}")
        return None
    if not SERP_KEY:
        print("SERPAPI_KEY not set")
        return None

    queries = _resolve_queries(info)
    out_dir = _get_out_dir(country)
    country_name = COUNTRIES.get(country, {}).get('name', country.upper())
    
    # Determine which cities to scrape
    cities_to_scrape = CITIES.get(country, ["Asunción"]) if deep else CITIES.get(country, [CITIES.get(country, ["Asunción"])[0]])
    if not deep:
        cities_to_scrape = [cities_to_scrape[0]]  # Just the first (capital)
    
    all_results = []
    seen_names = set()
    total_api_calls = 0
    
    print(f"\n  [{country_name}] Scraping: {slug} ({len(cities_to_scrape)} cities, {len(queries)} queries)")
    
    for city in cities_to_scrape:
        for query_template in queries:
            query = f"{query_template} {city} {country_name}"
            
            for page in range(max_pages):
                cache_key = f"{slug}_{country}_{city}_{query_template[:20]}_p{page}"
                cache_key = re.sub(r'[^a-zA-Z0-9_]', '_', cache_key)[:50]
                
                data = cache_get_or_fetch(
                    f'maps_{country}', cache_key,
                    lambda q=query, p=page, c=country: _search_serpapi_maps(q, c, p),
                    ttl=7*24*3600
                )
                total_api_calls += 1
                
                if not data:
                    break
                
                results = data.get('local_results', [])
                if not results:
                    break
                
                new_count = 0
                for r in results:
                    entry = _parse_serpapi_result(r, slug, info, country)
                    if not entry:
                        continue
                    
                    name = entry['name']
                    if name in seen_names:
                        continue
                    
                    # Filter by minimum reviews
                    min_rev = info.get('min_reviews', 0)
                    try:
                        reviews = int(entry['total_reviews'])
                    except (ValueError, TypeError):
                        reviews = 0
                    if min_rev > 0 and reviews < min_rev:
                        continue
                    
                    seen_names.add(name)
                    all_results.append(entry)
                    new_count += 1
                
                if new_count == 0:
                    break  # No new unique results on this page
                
                if page < max_pages - 1:
                    time.sleep(0.5)  # Rate limit between pages
    
    # Save results
    path = os.path.join(out_dir, f'leads_{slug}.csv')
    fieldnames = ['name', 'country', 'vertical', 'category', 'city', 'address',
                  'lat', 'lng', 'phone', 'website', 'rating', 'total_reviews',
                  'has_website', 'types']
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"  [{country_name}] {slug}: {len(all_results)} leads from {len(cities_to_scrape)} cities, {total_api_calls} API calls → {path}")
    return all_results


def scrape_all_verticals(country="py", max_pages=2, deep=False):
    """Scrape all verticals for a country."""
    total = 0
    for slug in VERTICALS:
        print(f"\n{'='*50}")
        result = scrape_vertical(slug, country, max_pages=max_pages, deep=deep)
        if result:
            total += len(result)
        # Rate limiting between verticals
        time.sleep(2)
    print(f"\n{'='*50}")
    print(f"TOTAL: {total} leads across {len(VERTICALS)} verticals in {country.upper()}")
    return total


# ═══════════════════════════════════════════════
#  MERGE & ANALYZE
# ═══════════════════════════════════════════════

def merge_all(country=None):
    """Merge all vertical CSVs into one master file per country."""
    countries = [country] if country else list(COUNTRIES.keys())
    
    for c in countries:
        out_dir = _get_out_dir(c)
        all_rows = []
        total = 0
        files_found = 0
        
        for f in sorted(os.listdir(out_dir)):
            if f.startswith('leads_') and f.endswith('.csv'):
                path = os.path.join(out_dir, f)
                try:
                    with open(path, encoding='utf-8') as fh:
                        reader = csv.DictReader(fh)
                        rows = list(reader)
                except Exception:
                    continue
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
    """Analyze leads data for a specific country or all countries."""
    from collections import Counter, defaultdict
    
    if not country:
        for c in COUNTRIES:
            analyze(c)
        return
    
    paths_to_try = [
        os.path.join(DATA_DIR, country, 'all_verticals.csv'),
    ]
    path = next((p for p in paths_to_try if os.path.exists(p)), None)
    
    if not path:
        print(f"No data for {country}.")
        return
    
    with open(path, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    
    country_name = COUNTRIES.get(country, {}).get('name', country.upper())
    print(f"\n{'='*60}")
    print(f"{country_name} — {len(rows)} leads")
    print(f"{'='*60}")
    
    # Verticals
    verts = Counter(r.get('vertical', 'unknown') for r in rows)
    print(f"\nVerticals:")
    for v, count in verts.most_common(30):
        print(f"  {v:30s} {count:5d}")
    
    # Cities
    cities = Counter(r.get('city', '') for r in rows if r.get('city'))
    print(f"\nCities ({len(cities)}):")
    for city, count in cities.most_common(15):
        print(f"  {city:30s} {count}")
    
    # Website gap
    no_web = sum(1 for r in rows if r.get('has_website', 'False').lower() != 'true')
    print(f"\nWebsite gap: {no_web}/{len(rows)} ({no_web/len(rows)*100:.0f}%)")
    
    # Ratings
    rated = [float(r['rating']) for r in rows if r.get('rating') and r['rating']]
    if rated:
        print(f"Avg rating: {sum(rated)/len(rated):.2f}★")
    
    # Top reviewed
    reviewed_rows = [r for r in rows if r.get('total_reviews') and str(r['total_reviews']).isdigit()]
    if reviewed_rows:
        reviewed_rows.sort(key=lambda x: int(x['total_reviews']), reverse=True)
        print(f"\nTop 15 most reviewed:")
        for r in reviewed_rows[:15]:
            print(f"  {r.get('name',''):40s} {r.get('vertical',''):20s} {r['total_reviews']:>6s} reviews ★{r.get('rating','')}")


# ═══════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════

def list_verticals():
    print(f"Available verticals ({len(VERTICALS)}):")
    print()
    for slug, info in sorted(VERTICALS.items()):
        interest = info['interest']
        queries = info['queries']
        print(f"  {slug:30s} [{interest}] {queries[0]}")
    print()
    print(f"Countries ({len(COUNTRIES)}): {', '.join(COUNTRIES.keys())}")
    print()
    print("")
    print("Modes:")
    print("  --vertical=<slug>        Scrape one vertical (capital city only — ~5 API calls)")
    print("  --deep=<slug>            Deep scrape: all cities, 3 pages (~50 API calls per country)")
    print("  --all                    Scrape ALL verticals (capital only — ~150 API calls)")
    print("  --light                  Scrape ALL verticals (1 query each — ~40 API calls)")
    print("  --country=ar --all --deep Deep all verticals for Argentina (~1,500 API calls)")
    print("")
    print("Examples:")
    print("  python3 scripts/paraguay_scrape.py --light --country=py   (40 calls)")
    print("  python3 scripts/paraguay_scrape.py --deep=tech --country=ar  (50 calls)")
    print("  python3 scripts/paraguay_scrape.py --deep=lawyers --country=cl (50 calls)")
    print("  python3 scripts/paraguay_scrape.py --vertical=tech --country=py  (5 calls)")


if __name__ == '__main__':
    country = 'py'
    deep = False
    max_pages = 2
    vertical = None
    all_countries = False
    
    for a in sys.argv[1:]:
        if a.startswith('--country='): country = a.split('=')[1]
        elif a.startswith('--vertical='): vertical = a.split('=')[1]
        elif a.startswith('--deep='): vertical = a.split('=')[1]; deep = True; max_pages = 5
        elif a == '--deep': deep = True; max_pages = 5
        elif a == '--all-countries': all_countries = True
    
    if '--list' in sys.argv:
        list_verticals()
    elif all_countries and vertical:
        for c in COUNTRIES:
            print(f"\n{'#'*60}")
            print(f"# {COUNTRIES[c]['name']}")
            print(f"{'#'*60}")
            scrape_vertical(vertical, c, max_pages=1)
    elif '--light' in sys.argv:
        # Light mode: 1 query per vertical, 1 city, 1 page (saves SerpAPI credits)
        for slug in VERTICALS:
            scrape_vertical(slug, country, max_pages=1, deep=False)
            time.sleep(0.5)
        merge_all(country=country)
        analyze(country=country)
    elif '--all' in sys.argv:
        if deep:
            scrape_all_verticals(country, max_pages=5, deep=True)
        else:
            scrape_all_verticals(country, max_pages=2, deep=False)
        merge_all(country=country)
        analyze(country=country)
    elif '--merge' in sys.argv:
        merge_all(country=country)
    elif '--analyze' in sys.argv:
        analyze(country=country)
    elif vertical:
        scrape_vertical(vertical, country, max_pages=max_pages, deep=deep)
        merge_all(country=country)
        analyze(country=country)
    else:
        list_verticals()
