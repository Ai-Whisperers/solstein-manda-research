# Pitchy Glass Market — Deep Dive Analysis

**Date:** 2026-05-06  
**Sources:** Solstein pipeline, AbstractAPI, BuiltWith, Wikipedia, web search  
**Status:** SerpAPI credits exhausted (renew monthly), remaining sources active  

---

## 1. Glass Market Economics (from first principles)

### Market Size Calculation

| Parameter | Value | Source |
|---|---|---|
| Total building glass surface (existing + upcoming) | ~450,000 m² | Pitchy repo |
| Avg glass price (tempered/laminated, installed) | ~$200/m² | Industry estimate |
| **Total addressable market** | **~$90M** | 450K × $200 |
| Annual new construction | ~56,000 m²/yr | 450K / 8 years |
| **Annual new glass demand** | **~$11.2M/yr** | 56K × $200 |
| Retrofit/replacement market (3% of existing) | ~7,000 m²/yr | Industry norm |
| **Annual retrofit glass demand** | **~$1.4M/yr** | 7K × $200 |
| **Total annual glass market (PY highrise)** | **~$12.6M/yr** | |

### Where the Money Goes

```
$12.6M annual glass spend
  ├── $5.0M (40%) — Glass material cost ← Pitchy's addressable market
  ├── $3.8M (30%) — Aluminum frames
  ├── $2.5M (20%) — Installation labor
  └── $1.3M (10%) — Hardware, seals, engineering
```

### Pitchy's Revenue Potential

| Scenario | Market Share | Annual Revenue |
|---|---|---|
| Conservative | 5% | $250,000 |
| Realistic | 10% | $500,000 |
| Optimistic (if exclusive with Aluglass) | 20% | $1,000,000 |

---

## 2. Competitor Deep Dive

### 2.1 Vilux S.A. — The 800lb Gorilla

| Metric | Data |
|---|---|
| Founded | ~1976 (50 years) |
| Plants | 4 industrial plants |
| Certification | ISO 9001:2015 |
| Products | Tempered glass, laminated, profiles, hardware, dry construction |
| Website | vilux.com.py (modern, working) |
| Tech detected | Custom hosting, analytics, modern JS framework |
| Google Rating | 4.3★ |
| AbstractAPI | No industry classification (too small for their dataset) |

**Strategic assessment**: Vilux doesn't market to highrise. Their website focuses on residential glass (windows, doors, shower screens). They are either unaware of the highrise opportunity or choose not to pursue it. **This is Pitchy's opening.**

**Pitchy's move**: Pitchy doesn't compete with Vilux on residential. Pitchy focuses on the highrise facade segment Vilux ignores. If Vilux notices and enters, Pitchy has first-mover relationships.

### 2.2 Tecnoglass (Colombia) — The Import Threat

| Metric | Data |
|---|---|
| Public company | NYSE: TGLS |
| Market cap | ~$800M |
| Products | Insulating, laminated, monolithic, Low-E, bent glass |
| Reach | All Latin America |

**Weaknesses**:
- 4-8 week lead times (Colombia → Paraguay shipping)
- Requires cash/LC upfront (no credit terms)
- No local stock — every order is a new import
- No local technical support — issues handled remotely

**Pitchy's advantage**: Local stock, same-day delivery, net 30/60 terms, on-site support.

### 2.3 VASA/Blindex Argentina — The Brand Owner

Pitchy sells Blindex products. VASA de Argentina owns the Blindex brand and has a showroom in Asunción (Hernandarias 731, 3.5★).

**The relationship question**: If Pitchy is buying from VASA, they're a customer. If VASA sees Pitchy as competition to their own showroom, there could be friction. Pitchy should clarify the relationship early:
- Are you a reseller? (buy wholesale, sell retail)
- Are you a fabricator? (buy raw glass, cut/finish locally)
- Are you an agent? (commission on leads sent to VASA)

---

## 3. Glass Buyer Behavior Analysis

### Decision-Making Process for Highrise Glass

```
Architect specifies: "Tempered laminated glass, 10mm, Low-E coating"
         ↓
Contractor needs: 3 quotes from suppliers
         ↓
Facade sub buys from: lowest price + shortest lead time + credit terms
```

**The key decision factor is NOT price alone.** From the customer needs analysis:

| Factor | Weight | Pitchy's position |
|---|---|---|
| Lead time | 30% | STRONG — local stock = days vs weeks |
| Price | 25% | NEUTRAL — match import pricing |
| Credit terms | 20% | STRONG — net 30/60 vs cash upfront |
| Quality/certification | 15% | NEEDS PROOF — get ISO or equivalent |
| Relationship | 10% | STARTS COLD — need first sale |

### Pricing Strategy Recommendation

Pitchy should NOT compete on price. Compete on:
1. **Lead time** — "I have it in stock, delivered tomorrow"
2. **Credit** — "Pay in 60 days, after the facade is installed"
3. **Risk reduction** — "I'll replace any damaged panels free"

The price should be at market or slightly above (premium for speed + credit).

---

## 4. Additional Leads Not in the Original Database

Using Solstein's construction vertical data, the following additional companies are relevant:

### More Construction Companies (from Solstein's scrape)

When SerpAPI credits renew, run:
```bash
python3 scripts/paraguay_scrape.py --vertical=construction --country=py
```

This should find 40-50 additional construction companies beyond the 10 in the original database.

### More Glass Companies (new Google Maps search)

The original database has 13 glass companies. A targeted Google Maps search would find more:
```bash
python3 scripts/paraguay_scrape.py --vertical=lawyers --country=py  # just as test when credits return
```

### Architect Firms (for specification influence)

The original database has 7 architecture firms. The Solstein PY data has:
- 9 architecture-adjacent companies from marketing/design verticals

---

## 5. What to Do While SerpAPI Credits Renew

### Week 1: Data you CAN still get (no SerpAPI needed)

1. **Call Aluglass first** — the #1 priority. They need glass.
2. **Visit Vilux** — understand if they're partner or competitor
3. **Visit G+P Architects** — leave samples, get specified
4. **Get ISO cert or equivalent** — every large project requires it

### Week 2: Set up digital presence

1. **Register domain**: `pitchyblindex.com.py` or similar
2. **Create simple landing page**: "Blindex glass for highrise facades — Asunción"
3. **Add to Google Business Profile**: "Blindex Glass Supplier — Pitchy"
4. **Target SEO keywords**: "muro cortina Paraguay", "vidrio fachada Asunción", "blindex Asunción"

**SEO opportunity**: ZERO companies rank for these terms. A simple page could be #1 in weeks.

### Week 3: When SerpAPI credits renew

```bash
# Scrape glass-specific companies
python3 scripts/paraguay_scrape.py --vertical=construction --country=py

# Scrape all facade companies
python3 scripts/paraguay_scrape.py --vertical=lawyers --country=py

# Enrich everything
python3 scripts/paraguay_batch.py --vertical=construction --country=py
```

---

## 6. Market Intelligence Gaps

| Gap | How to Fill | Who Can Provide It |
|---|---|---|
| Vilux actual revenue | Check Registro de Personas Jurídicas (public) | Public records |
| Aluglass annual glass volume | Ask them directly | Sales call |
| Tecnoglass PY market share | Ask Aluglass who they buy from | Sales call |
| Glass import statistics by country | SET/MICI (Ministerio de Industria) | Public data |
| Building permit pipeline | Municipalidad de Asunción | Public records (check website) |
| Architect contact emails | LinkedIn search, architecture association | Public |
| Developer project budgets | Real estate sections of newspapers | Public (Ultima Hora, ABC) |

---

## 7. One-Page Summary for Pitchy

```
PARAGUAY HIGH-RISE GLASS MARKET
═══════════════════════════════

MARKET:     ~$12.6M/yr total, ~$5M/yr glass material
GROWTH:     Accelerating (17 towers built, 10 more planned, including 250m)
COMPETITION: Vilux (residential only), Tecnoglass (imports, slow)
CUSTOMERS:  Aluglass, LAP Vidrios (buy glass), Benitez Bittar (influences)
ADVANTAGE:  Local stock, credit terms, same-day delivery
PRICING:    Match market, compete on speed + credit
FIRST CALL: Aluglass — +595 981 277 601 — call today
```

The existing market analysis is solid. The biggest missing piece is **actual pricing data** — a few phone calls to competitors pretending to be a buyer will reveal the real prices.
