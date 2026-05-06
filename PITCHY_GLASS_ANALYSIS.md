# Pitchy's Glass Market — Solstein M&A Analysis

**Generated:** 2026-05-06  
**Source repo:** github.com/Ai-Whisperers/pitchy-glass-market-paraguay  
**Pipeline:** Solstein M&A Research (25 data sources)  

---

## What the Pitchy Repo Already Has (Excellent)

The existing market intelligence is **comprehensive and actionable**:

| Asset | What it contains |
|---|---|
| **27 buildings** analyzed | 17 existing + 10 upcoming towers, heights, floor counts, estimated glass surface |
| **25+ leads** with phone numbers | Facade installers, contractors, developers, architects, hardware stores |
| **13 glass companies** mapped | Competitors + potential customers, with ratings, websites, product lines |
| **5 customer types** with detailed needs analysis | What each type buys, their pain points, how to win them |
| **Competitive positioning** | Where Pitchy fits vs imports (Tecnoglass) vs local (Vilux) |
| **Action plan with call scripts** | Day-by-day outreach plan with phone numbers and talking points |

**Estimated glass demand**: 450,000 m² across existing + upcoming towers  
**Annual market**: ~56,000 m²/year of glass facade  

---

## What Solstein Adds

Without SerpAPI credits (exhausted from Chile scraping), Solstein's remaining active sources:

| Source | Data It Can Still Provide |
|---|---|
| **AbstractAPI** | Industry classification, company type (still working) |
| **BuiltWith** | Technology categories (still working) |
| **LinkedIn search** | Employee estimates, role counts (still working) |
| **Web search** | News, web presence (via DuckDuckGo) |
| **Wikipedia** | Company descriptions (only for well-known companies) |
| **DNS/Hosting** | Hosting provider, IP |
| **Google Maps (local data)** | Phone, rating, review count for 7,788 PY companies |

---

## Solstein Scored Analysis of Pitchy's Market

### Market Size Scoring

| Factor | Score (1-5) | Rationale |
|---|---|---|
| Total addressable market | 4 | 450,000 m² glass, ~$90M at $200/m² |
| Growth trajectory | 5 | PY construction boom accelerating (250m tower planned) |
| Competitive intensity | 3 | Vilux dominant but not focused on highrise; imports unreliable |
| Customer availability | 5 | 25+ leads with phone numbers already identified |
| Digital maturity | 2 | Most competitors have basic websites, no SEO, no funnels |
| **Composite** | **3.8/5.0 (Grade B)** | Strong market with clear entry point |

### Lead Quality Scoring (by Customer Type)

| Customer Type | Score | Best Lead | Why |
|---|---|---|---|
| Facade installers | **5/5** | Aluglass (4.5★, 34 yrs) | Explicitly buys glass for facades, needs supply |
| General contractors | **4/5** | Benitez Bittar (4.6★) | Built tallest PY tower, influences glass purchases |
| Glass manufacturers | **3/5** | Glasstex (4.2★, 4 locations) | Could buy or compete — needs investigation |
| Developers | **3/5** | EYDISA (4.5★, multiple projects) | Specifies glass, but through contractors |
| Architects | **2/5** | G+P Architects (4.7★) | Influences spec but doesn't buy |
| Hardware stores | **3/5** | Ferrex (6 locations) | Distribution channel for retail |

### Digital Presence Analysis of Lead Companies

| Company | Has Website | Tech Detected | SEO Opportunity |
|---|---|---|---|
| Aluglass | ✅ Yes | WordPress | Low — site exists but basic |
| LAP Vidrios | ✅ Yes | — | Low |
| Vilux | ✅ Yes | Modern | Medium — biggest player with good site |
| Glasstex | ✅ Yes | — | Low |
| Benitez Bittar | ✅ Yes | — | Low |
| EYDISA | ✅ Yes | — | Low |
| TECINCI | ✅ Yes | — | Low |
| Ferrex | ✅ Yes | — | Medium — has app "FIX" |

---

## Strategic Recommendations

### 1. Immediate Actions (from Pitchy repo data)

The existing action plan is correct. Prioritize:
1. **Aluglass** (+595 981 277 601) — call today, they need glass
2. **LAP Vidrios** (+595 972 243 520) — same profile
3. **Benitez Bittar** (+595 971 775 000) — reference account

### 2. Solstein-Identified Opportunities

**Digital gap**: None of the 10 glass/construction companies have strong SEO for "muro cortina Paraguay" or "vidrio fachada Asunción". A simple landing page with those keywords would capture inbound leads that currently don't exist in the market.

**Partner strategy**: Vilux (50 years, ISO 9001, 4 plants) doesn't market to highrise. Pitchy could be their highrise facade division — Pitchy sells Blindex products, Vilux provides installation. Pitchy pays Vilux a referral fee.

**Import replacement**: Tecnoglass (Colombia) is the current highrise supplier but has 4-8 week lead times and requires cash upfront. Pitchy's advantage: local stock, net 30 terms, same-day delivery.

### 3. Pipeline Integration

The existing lead database can be imported into the Solstein pipeline:
```bash
# Convert Pitchy's leads to CSV format and enrich
python3 scripts/paraguay_batch.py --vertical=construction --country=py

# Run Solstein scoring on glass industry specifically
python3 scripts/research_pipeline.py "Aluglass" "https://aluglass.com.py"
```

### 4. Market Intelligence Gaps to Fill

| Gap | How to Fill | Priority |
|---|---|---|
| Actual glass pricing in PY market | Call competitors asking for quotes | High |
| Vilux production capacity | Visit their plant in Fernando de la Mora | Medium |
| Tecnoglass PY market share | Ask Aluglass who they currently buy from | High |
| Building permit pipeline | Check Municipalidad de Asunción public records | Medium |
| Glass import statistics | SET/MICI trade data | Low |

---

## Pipeline Status

**SerpAPI credits**: 0/100 remaining (exhausted by Chile scraping — renews monthly)  
**Active sources**: AbstractAPI, BuiltWith, LinkedIn, DuckDuckGo, Wikipedia, GitHub, GLEIF  
**To re-enable SerpAPI**: Upgrade at serpapi.com (starts at $50/mo for 5,000 searches)
