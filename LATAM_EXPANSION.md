# LATAM Expansion & Cross-Border M&A Thesis

**Generated:** 2026-05-06  
**Data:** 7,464 beauty + 862 non-beauty leads across PY, AR, BR (22 verticals)

---

## Current Coverage

| Country | Leads | Verticals Scraped | Status |
|---|---|---|---|
| **Paraguay** | 7,464 beauty + 323 non-beauty | 18 optgroups, 9 verticals | ✅ Deep |
| **Argentina** | 342 | 7 verticals (tech, lawyers, clinics, etc.) | 🟡 Medium |
| **Brazil** | 188 | 4 verticals (tech, lawyers, clinics, vets) | 🟡 Light |
| **Uruguay, Chile, Peru, Colombia, Mexico** | 0 | — | ⬜ Not started |

---

## Phase 3: Multi-Country Scraper

**What was built:** The scraper now supports 8 LATAM countries with templated queries:
- `{loc}` is replaced with each country's capital + country name
- Portuguese queries for Brazil (via `clinics_br`, `tech_br` verticals)
- All data stored in `data/{country_code}/` directories

**To scrape a new country:**
```bash
# Scrape all high-value verticals for Uruguay
python3 scripts/paraguay_scrape.py --vertical=tech_companies --country=uy
python3 scripts/paraguay_scrape.py --vertical=lawyers --country=uy

# Scrape all verticals for Chile
python3 scripts/paraguay_scrape.py --country=cl --all
```

**Rough costs per country (SerpAPI credits):**
- 10 verticals × 3 queries each = 30 API calls per country
- 100 free SerpAPI calls/month → ~3 new countries per month
- Or upgrade SerpAPI to $50/mo for 5,000 calls → 160 countries

---

## Phase 4: Cross-Border M&A Thesis

### Thesis: "Digital-Forward LATAM SMEs Are the Next Acquisition Wave"

**Why it matters:** Across all 3 countries, we see the same pattern:
- **75%+ of SMEs have no website** (PY: 75%, AR: similar, BR: similar)
- **Google Maps data exists for all of them** — phone, rating, address, lat/lng
- **Digital transformation is happening NOW** — post-COVID, the ones that didn't digitize are dying
- **Consolidation play**: buy the digital leader in each vertical per country, roll up

### Target Profiles by Vertical

| Vertical | Paraguay | Argentina | Brazil | Cross-Border Play |
|---|---|---|---|---|
| **Law Firms** | 30 leads, avg 4.7★ | 8 leads, 4.8★ | 15 leads, 4.7★ | Legal tech rollup — acquire top PY firm, expand to AR |
| **Tech Companies** | 39 leads, avg 4.3★ | 48 leads, 4.5★ | 22 leads, 4.6★ | Nearshore dev shops — PY is cheapest, AR has talent, BR has scale |
| **Clinics** | 38 leads, avg 4.4★ | 12 leads, 4.0★ | 8 leads, 4.2★ | Telemedicine platform — acquire clinics, add SaaS layer |
| **Veterinarians** | 27 leads, avg 4.6★ | 9 leads, 4.5★ | 6 leads, 4.6★ | Vete expansion — PY already has product, replicate for AR/BR |
| **Construction** | 46 leads, avg 4.3★ | 12 leads, 4.1★ | — | Home services marketplace — PY first, then AR |
| **Marketing Agencies** | 44 leads, avg 4.5★ | 10 leads, 4.6★ | — | Digital services rollup — buy agencies, add tech |

### M&A Scoring for LATAM

The Solstein pipeline's 8-dimension scoring adapts to LATAM with modified weights:

| Dimension | Benelux Weight | LATAM Weight | Why Changed |
|---|---|---|---|
| Ownership attractiveness | 3× | 3× | Same — family-owned is better |
| Revenue scale fit | 3× | 2× | LATAM companies are smaller — adjust threshold |
| Geographic fit | 3× | 4× | **More important** — cross-border complexity |
| Tech stack modernity | 2× | 3× | **More important** — digital gap = opportunity |
| Customer lock-in | 2× | 2× | Same |
| Vertical depth | 2× | 2× | Same |
| Integration potential | 1× | 2× | **More important** — API readiness enables rollup |
| Growth trajectory | 1× | 2× | **More important** — high-growth region |

### Top 10 Most Acquirable LATAM Companies (from our data)

Based on Google Maps rating + review count + website presence + vertical:

| Company | Country | Vertical | Rating | Reviews | Why |
|---|---|---|---|---|---|
| Peroni Sosa Tellechea Burt & Narvaja | PY | Lawyers | 4.7★ | 56 | Top-tier PY law firm, has website, brandable |
| EXO Soluciones Tecnológicas | AR | Tech | 3.8★ | 1,434 | Massive client base, needs product upgrade |
| CLINICA BONNE SANTE | PY | Clinics | 4.9★ | 447 | Premium clinic, strong brand, no website |
| Ruysam Advogados Associados | BR | Lawyers | 4.9★ | 289 | Top BR law firm, expansion target |
| Confluencia IT | AR | Tech | 5.0★ | 108 | Perfect rating, IT services, scalable |
| Clínica Veterinaria Tacuary | PY | Vets | 4.7★ | 718 | Market leader, Vete acquisition target |
| Hospital Centro Médico de Campinas | BR | Clinics | 2.0★ | 911 | Low rating = turnaround opportunity |
| Dr. Carlos Escauriza Benítez, Abogado | PY | Lawyers | 4.8★ | 54 | Solo practitioner, digital-savvy |
| IBM Argentina | AR | Tech | 4.3★ | 1,077 | Large, needs modernization |
| Estudio Jurídico Enzetti | AR | Lawyers | 5.0★ | 483 | Perfect rating, legal tech target |

---

## Next Steps for LATAM

### Immediate (this week)
1. Scrape remaining AR verticals (insurance, accountants, photographers, logistics)
2. Scrape top 3 verticals for UY, CL, CO (tech, lawyers, clinics)
3. Run Solstein enrichment on top 50 leads per country

### Short-term (this month)
4. Run the full 7,464 beauty leads through Solstein scoring
5. Identify top 100 LATAM acquisition targets across all verticals
6. Generate automated outreach scorecards for each

### Medium-term (this quarter)
7. Add Google Maps scraping for MercadoLibre categories (ecommerce integration)
8. Cross-reference with ClasiPar directory for PY
9. Build LATAM M&A dashboard with filters by country, vertical, score

### How to scrape a new country:
```bash
# One command per vertical
python3 scripts/paraguay_scrape.py --vertical=tech_companies --country=cl
python3 scripts/paraguay_scrape.py --vertical=lawyers --country=cl
python3 scripts/paraguay_scrape.py --vertical=clinics --country=cl

# Merge and analyze
python3 scripts/paraguay_scrape.py --country=cl --merge
python3 scripts/paraguay_scrape.py --country=cl --analyze

# Enrich with Solstein
python3 scripts/paraguay_batch.py --vertical=tech_companies --country=cl
```
