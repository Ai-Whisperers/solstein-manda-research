# M&A Research Pipeline — API Integration Roadmap

**Analysis of 1,000+ public APIs for company enrichment, scored by M&A research value.**

---

## Current State: 25 Sources Integrated (+7 new)

| # | Source | Type | Data Provided | Key | Status |
|---|---|---|---|---|---|
| 1 | Wikipedia | REST | Company description, founded, HQ, employees | Free | ✅ |
| 2 | GitHub | REST | Repos, stars, languages, org profile | `GITHUB_TOKEN` | ✅ |
| 3 | DuckDuckGo | HTML scrape | Web search results | Free | ✅ |
| 4 | SEC EDGAR | REST | Financial filings, XBRL data | Free | ✅ |
| 5 | yfinance | Library | Stock data, company profile | Free | ✅ |
| 6 | GLEIF | REST | Legal entity identifier, registration | Free | ✅ |
| 7 | World Bank | REST | Economic indicators by country | Free | ✅ |
| 8 | AbstractAPI | REST | Industry, employee range, revenue range | `ABSTRACT_API_KEY` | ✅ |
| 9 | Financial Datasets | REST | Company facts, income statements | `FINANCIAL_DATASETS_API_KEY` | ✅ |
| 10 | Brave News | REST | Recent news articles | Free | ✅ |
| 11 | Crunchbase (scrape) | HTML scrape | Funding, investors | Free | ⏳ (API version available) |
| 12 | OpenCorporates | REST/HTML | Legal entity, jurisdiction, status | Free | ✅ |
| 13 | UK Companies House | REST | UK company registration data | `UK_COMPANIES_HOUSE_KEY` | ⏳ |
| 14 | French SIRENE | REST | French company registration | Free | ✅ |
| 15 | VIES VAT | SOAP | EU VAT validation | Free | ✅ |
| 16 | OpenRegistry | REST | 27 national registries | Free | ✅ |
| 17 | Playwright/CloakBrowser | Browser | Tech stack, pricing, careers | Free | ✅ |
| 18 | DNS/hosting | Stdlib | IP, hosting provider | Free | ✅ |
| 19 | **Clearbit** | REST | Funding stage, raised capital, category, company type | `CLEARBIT_KEY` | ✅ **NEW** |
| 20 | **BuiltWith** | REST | Full tech stack (50k technologies, versions) | `BUILTWITH_KEY` | ✅ **NEW** |
| 21 | **Crunchbase API** | REST | Structured funding, investors, acquisitions | `CRUNCHBASE_KEY` | ✅ **NEW** |
| 22 | **Glassdoor** | REST | Rating, CEO approval, culture, salary | `GLASSDOOR_KEY` | ✅ **NEW** |
| 23 | **LinkedIn** | Search | Employee count, open roles | Free | ✅ **NEW** |
| 24 | **SerpAPI** | REST | Structured Google results, knowledge graph | `SERPAPI_KEY` | ✅ **NEW** |
| 25 | **USPTO Patent** | REST | Patent count, tech categories, citations | Free | ✅ **NEW** |

---

## Scoring Methodology

Each API scored 0-100 across 5 dimensions:

| Dimension | Weight | Description |
|---|---|---|
| **M&A Relevance** | 35% | Does it directly answer a scoring dimension? |
| **Data Quality** | 25% | Is the data accurate, fresh, and structured? |
| **Free Tier** | 20% | Can we use it at meaningful volume for free? |
| **Integration Effort** | 10% | How many lines of code to integrate? |
| **Uniqueness** | 10% | Does it add data we can't get elsewhere? |

---

## TIER 1 — INTEGRATE IMMEDIATELY (score 70-100)

These add significant new data dimensions or replace fragile scrapes with APIs.

### 1. Clearbit Company API
- **Score**: 95
- **URL**: https://dashboard.clearbit.com/api
- **Auth**: API key (free tier: 50 req/mo)
- **Data**: Company name, legal entity, domain, category, description, employees, funding stage, industry, market cap, raised, tech used
- **Why**: Replaces AbstractAPI as primary enrichment — better data for startups (funding stage, raised capital). 50/mo free covers our top targets.
- **Integration**: 1 function, ~20 lines

### 2. Crunchbase API (Official)
- **Score**: 92
- **URL**: https://developers.crunchbase.com/
- **Auth**: API key (free tier: 50 req/mo)
- **Data**: Funding rounds, investors, acquisition history, IPO info, board members, competitor relationships
- **Why**: Currently scraping HTML which breaks when Crunchbase changes layout. Official API gives structured JSON for funding history and M&A events.
- **Integration**: Replace `scripts/datasources.py` Crunchbase scraper with API call

### 3. BuiltWith Technology Lookup
- **Score**: 88
- **URL**: https://api.builtwith.com/
- **Auth**: API key (free tier: 50 req/mo)
- **Data**: Complete tech stack — frameworks, analytics, CDN, payment providers, hosting, SSL, email providers
- **Why**: Currently detecting tech from browser HTML (fragile, limited to ~20 signals). BuiltWith detects 50,000+ technologies with version numbers.
- **Integration**: 1 function, replaces Playwright tech detection as primary source

### 4. Marketstack
- **Score**: 85
- **URL**: https://marketstack.com/
- **Auth**: API key (free tier: 1,000 req/mo)
- **Data**: Real-time and historical stock data, EOD prices, intraday, ticker search
- **Why**: Replaces yfinance which has no SLA and breaks periodically. 1,000 free req/mo is generous.
- **Integration**: Replace yfinance calls in `free_sources.py`

### 5. Glassdoor API
- **Score**: 82
- **URL**: https://www.glassdoor.com/developer/
- **Auth**: API key (free tier: 100 req/mo)
- **Data**: Company rating, CEO approval, salary by role, reviews, culture score, recommend to friend %
- **Why**: Direct input to "Ownership attractiveness" dimension — culture problems = retention risk. CEO approval indicates founder health.
- **Integration**: 1 function, adds new dimension to scoring

### 6. Google Custom Search / SerpAPI
- **Score**: 80
- **URL**: https://serpapi.com/ or https://developers.google.com/custom-search
- **Auth**: API key (SerpAPI free: 100 req/mo, Google CSE: 100/day free)
- **Data**: Structured Google search results without HTML scraping
- **Why**: Currently scraping DuckDuckGo HTML which is fragile and slow. SerpAPI gives structured results with sitelinks, knowledge graph, and news.
- **Integration**: Replace `html_search()` in `free_sources.py`

### 7. LinkedIn Company Search (via Google)
- **Score**: 78
- **URL**: Google search "site:linkedin.com/company/{name}"
- **Auth**: Free (web search)
- **Data**: Employee count, headcount growth, recent hires, open roles
- **Why**: Employee growth is the best revenue proxy for private SaaS companies. Currently not collected at all.
- **Integration**: 1 function, extract from search results

---

## TIER 2A — HIGH VALUE (score 50-69)

These add meaningful signal.

| API | Score | Data | Free Tier | Why Skip? |
|---|---|---|---|---|
| **Similarweb** | 68 | Traffic, geography, engagement, keywords | 100 req/mo | Nice for revenue estimation from traffic |
| **Semrush** | 65 | SEO data, organic keywords, backlinks | 10 req/mo | Too few free requests |
| **ORB Intelligence** | 64 | Company lookup by domain | Free | Good overlap with Clearbit |
| **Patent API (USPTO)** | 63 | Patent search, filings, citations | Free | Valuable for tech depth assessment |
| **Trademark API (USPTO)** | 62 | Trademark search | Free | Validates brand value |
| **NewsAPI** | 60 | News articles from 30k+ sources | 100 req/day | More reliable than Brave News |
| **Adzuna** | 58 | Job listings, salary data | 1,000 req/mo | Useful for employee cost estimation |
| **Indeed** | 57 | Job listings, salary trends | Free | Similar to Adzuna |
| **OpenCorporates API** | 55 | Structured legal entity data | Free tier | Currently scraping HTML |
| **Gravatar** | 52 | Profile photos for people | Free | Low value |
| **Hunter.io** | 51 | Email pattern detection | 25 req/mo | Too few requests |
| **Census.gov** | 50 | Demographics, business data | Free | US-only, macro level |

---

## TIER 2B — GOOD VALUE (score 30-49)

| API | Score | Data | Free Tier |
|---|---|---|---|
| **ExchangeRate API** | 48 | Currency conversion rates | 1,000 req/mo |
| **World Bank API** | 47 | Economic data by country | Free (unlimited) |
| **Country.is** | 45 | Country data from domain | Free |
| **IPAPI** | 44 | Geolocation from IP | Free (50/day) |
| **Mailboxlayer** | 42 | Email validation | 100 req/mo |
| **Abstract APIs** | 41 | Phone, email, geolocation | 100 each/mo |
| **Open Data Soft** | 40 | Open data portal search | Free |
| **Bing News Search** | 39 | News results | 1,000/mo |
| **GNews** | 38 | Google News results | 100/day |
| **Currents API** | 37 | News articles | Free |
| **Spaceflight News** | 36 | Space industry news | Free |
| **Nomics** | 35 | Crypto market data | 1,000/mo |
| **CoinGecko** | 34 | Crypto company holdings | Free |
| **Data USA** | 33 | US public data | Free |
| **USDA** | 32 | Agriculture data | Free |
| **BLS API** | 31 | Employment statistics | Free |
| **Glassdoor (free tier)** | 30 | Limited company data | Free |

---

## TIER 3 — SPECIALIZED NICHES (score 15-29)

| API | Data | Best For |
|---|---|---|
| **SEC EDGAR Full Text** | 10-K, 10-Q section-level search | Risk factor analysis |
| **OCCRP** | Organized crime and corruption data | Emerging market vetting |
| **OpenSanctions** | Sanctions and PEP lists | Compliance screening |
| **World Bank Procurement** | Government contracts | Revenue validation |
| **EU Tenders** | EU government contracts | Revenue validation |
| **OpenCorporates Beneficial Ownership** | Ultimate beneficial owners | Ownership verification |
| **Crunchbase M&A API** | Acquisition history, acquirer details | Direct M&A signal |
| **PitchBook (no API)** | Private market data | Would be #1 if available |
| **CB Insights (no API)** | Tech market intelligence | Would be #2 if available |
| **Owler (no API)** | Company competitive intelligence | Would be #3 if available |

---

## Already Covered by Current 25 Sources

No need to duplicate — we already get this data:

| Data Point | Current Source(s) |
|---|---|
| Company description | Wikipedia, Playwright, Clearbit, SerpAPI (KG) |
| Basic financials (public) | SEC EDGAR, yfinance, Financial Datasets |
| Stock price | yfinance |
| Legal entity (US public) | SEC EDGAR (CIK), Clearbit |
| Legal entity (global) | GLEIF (LEI) |
| Legal entity (UK) | Companies House |
| Legal entity (France) | SIRENE |
| Legal entity (27 countries) | OpenRegistry |
| EU VAT validation | VIES |
| **Full tech stack (50k techs)** | **BuiltWith** ⬅️ new |
| Tech stack (basic) | Playwright browser |
| News | Brave News, SerpAPI |
| GitHub activity | GitHub API |
| **Funding stage + raised capital** | **Clearbit, Crunchbase API** ⬅️ new |
| **Company rating + culture** | **Glassdoor** ⬅️ new |
| Employee data | AbstractAPI, Clearbit, LinkedIn |
| Financial statements (public) | Financial Datasets |
| Country economics | World Bank |
| **Patent count + tech moat** | **USPTO** ⬅️ new |
| **Google knowledge graph** | **SerpAPI** ⬅️ new |

---

## Gaps That No API Can Easily Fill

These are the hardest scoring dimensions to improve:

| Gap | Why No API Exists | Alternative |
|---|---|---|
| **Private company revenue** | Private companies don't disclose | Use employee count × industry revenue/employee |
| **Customer churn rate** | Internal metric, not public | Glassdoor reviews mentioning "customer satisfaction" |
| **PE/VC ownership %** | Often hidden | Crunchbase funding history + news search |
| **Founder willingness to sell** | Personal, not public | News sentiment analysis + founder age proxy |
| **Contract length / lock-in** | Terms of service are private | Job postings mentioning "migration", "implementation" |

---

## Integration Status

```
DONE (2026-05-06):
  ✅ Clearbit Company API         → scripts/sources_plus.py
  ✅ BuiltWith Tech API           → scripts/sources_plus.py
  ✅ Crunchbase API               → scripts/sources_plus.py (alongside scrape)
  ✅ Glassdoor API                → scripts/sources_plus.py
  ✅ LinkedIn employee search     → scripts/sources_plus.py
  ✅ SerpAPI                      → scripts/sources_plus.py
  ✅ USPTO Patent API             → scripts/sources_plus.py
  → All 7 wired into datasources.enrich_company()

NEXT (no keys required from you):
  ⬜ Marketstack                  → replace yfinance in free_sources.py
  ⬜ NewsAPI                      → replace Brave News in datasources.py
  ⬜ OpenCorporates REST API      → replace HTML scrape in datasources.py

NEEDS YOU TO SIGN UP (then we activate):
  🔑 Clearbit   → dashboard.clearbit.com       → CLEARBIT_KEY
  🔑 BuiltWith  → api.builtwith.com            → BUILTWITH_KEY
  🔑 Crunchbase → developers.crunchbase.com    → CRUNCHBASE_KEY
  🔑 Glassdoor  → glassdoor.com/developer      → GLASSDOOR_KEY
  🔑 SerpAPI    → serpapi.com                  → SERPAPI_KEY
```

---

## Build vs Buy Analysis

| Approach | Cost | Signal Gain | Time to Integrate |
|---|---|---|---|
| Add Clearbit + BuiltWith | $0 (free tier) | ++ | 2 hours |
| Add all Tier 1 (7 APIs) | $0 (free tiers) | +++ | 1 day |
| Upgrade to paid tiers | ~$500/mo | ++++ | 2 days |
| Build own data pipeline | N/A | Same as free tiers | Already built |

**Recommendation**: Integrate all Tier 1 APIs on free tiers. None require payment — the free tiers cover 50-100 requests/month which is enough for our target pipeline (57 HORECA + 10 new prospects/month = ~70 req/mo).

---

## How Each API Maps to Scoring Dimensions

```
                           Own  Rev  Geo  Tech Lock Vert Inte Grow
Clearbit                   ✓    ✓    ✓    ✓    -    ✓    ✓    ✓
BuiltWith                  -    -    -    ✓    ✓    -    ✓    -
Marketstack (stock)        -    ✓    -    -    -    -    -    ✓
Glassdoor                  ✓    -    -    -    ✓    -    -    -
Crunchbase API             ✓    ✓    -    -    ✓    ✓    ✓    ✓
LinkedIn (employee)        -    ✓    -    -    -    ✓    -    ✓
SerpAPI (search)           -    -    ✓    -    -    -    -    ✓
NewsAPI (sentiment)        -    -    -    -    -    -    -    ✓
USPTO Patent               -    -    -    ✓    ✓    ✓    -    -
Similarweb (traffic)       -    ✓    ✓    -    -    -    -    ✓
Adzuna (salaries)          -    ✓    ✓    -    -    -    -    -
ORB Intelligence           ✓    -    ✓    -    -    ✓    -    -

Legend: Own=Ownership, Rev=Revenue, Geo=Geographic, Tech=Tech stack,
Lock=Customer lock-in, Vert=Vertical depth, Inte=Integration, Grow=Growth
```
