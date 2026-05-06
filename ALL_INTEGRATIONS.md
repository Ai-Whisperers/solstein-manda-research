# All Repos, Libraries, APIs, and Tools Used

---

## Open-Source Repositories We Used or Integrated

### Browser Automation
| Repo | Stars | What We Use |
|---|---|---|
| [**playwright**](https://github.com/microsoft/playwright) | 70k+ | Headless browser for JavaScript rendering, tech detection, pricing/careers extraction |
| [**cloakbrowser**](https://github.com/OH-OH-OPEN-source/CloakBrowser) | 1,491 | Stealth browser — passes 30/30 bot detection tests. C++-level fingerprint patches |
| [**browser-use/browser-use**](https://github.com/browser-use/browser-use) | — | Pattern reference for browser agent architecture |
| [**ntegrals/openbrowser**](https://github.com/ntegrals/openbrowser) | — | Pattern reference for browser-based data extraction |

### AI / Multi-Agent
| Repo | Stars | What We Use |
|---|---|---|
| [**crewai**](https://github.com/crewAIInc/crewAI) | 25k+ | Multi-agent framework for 11-specialist research crew (ownership, financial, tech, market analysts) |
| [**due-diligence-agents**](https://github.com/due-diligence-agents) | — | Pattern reference for 9-domain due diligence agent architecture (v1.5.0) |
| [**DealScout**](https://github.com/DealScout) | — | Pattern reference for combative debate between analyst agents |
| [**langchain-ai/company-researcher**](https://github.com/langchain-ai/company-researcher) | — | Pattern reference for reflection loop and research pipeline |

### Financial Modeling
| Repo | Stars | What We Use |
|---|---|---|
| [**finverse**](https://github.com/finverse) | — | DCF, LBO, and Comparable Company Analysis financial models |
| [**DCF-Valuation-Model**](https://github.com/DCF-Valuation-Model) | — | Pattern reference for discounted cash flow calculation |
| [**hess-chevron-valuation-analysis**](https://github.com/hess-chevron-valuation-analysis) | — | Pattern reference for oil/gas valuation methodology |

### Data Sources (free/public APIs)
| Source | What It Provides | URL |
|---|---|---|
| **Wikipedia API** | Company descriptions, founded, HQ, employees | en.wikipedia.org/api/rest_v1 |
| **GitHub API** | Repos, stars, languages, org profile | api.github.com |
| **SEC EDGAR** | US public company financial filings, XBRL data | sec.gov/files/company_tickers.json |
| **yfinance** | Stock data, company profiles (sector, industry, employees) | pypi.org/project/yfinance |
| **GLEIF** | Global Legal Entity Identifier, 1.6M+ entities | api.gleif.org |
| **World Bank** | Economic indicators by country | api.worldbank.org |
| **DuckDuckGo** | Free web search (no API key, no rate limits) | html.duckduckgo.com |
| **OpenRegistry** | 27 national company registries (UK, FR, DE, IT, ES, KR, etc.) | openregistry.sophymarine.com |
| **Brave Search** | Recent news articles | search.brave.com/api/news |
| **OpenCorporates** | Legal entity data, jurisdiction, incorporation | opencorporates.com |

### Paid/Keyed Data Sources (free tiers)
| Source | What It Provides | Sign Up URL |
|---|---|---|
| **AbstractAPI** | Industry, employee range, revenue range | abstractapi.com |
| **Financial Datasets** | Income statements, balance sheets, company facts | financialdatasets.ai |
| **UK Companies House** | 5.4M UK companies, officers, filings | company-information.service.gov.uk |
| **French SIRENE** | 25M French companies, SIREN/SIRET | data.gouv.fr |
| **VIES VAT** | EU VAT number validation | ec.europa.eu/taxation_customs/vies |
| **Clearbit** | Funding stage, raised capital, company category | dashboard.clearbit.com |
| **BuiltWith** | Technology categories detected on websites | api.builtwith.com |
| **Crunchbase API** | Funding rounds, investors, acquisition history | developers.crunchbase.com |
| **Glassdoor** | Company rating, CEO approval, culture scores | glassdoor.com/developer |
| **SerpAPI** | Google Knowledge Graph, structured search, patents | serpapi.com |
| **USPTO** | Patent search (via SerpAPI fallback) | developer.uspto.gov |

### MCP Servers (Model Context Protocol)
| Server | What It Provides | Setup |
|---|---|---|
| **CompanyScope MCP** (Apify) | 8 aggregated business data sources | APIFY_API_TOKEN |
| **Coresignal MCP** | 74M companies, 823M employee profiles | CORESIGNAL_API_KEY |
| **Bright Data MCP** | 200+ sources: Crunchbase, LinkedIn, ZoomInfo | BRIGHTDATA_API_TOKEN |
| **LinkedIn MCP** | Company profiles, employees (public data) | MCP server |
| **eu-company-mcp-server** | EU parent/subsidiary data | explainmcp.com |

### Self-Improvement / Meta-Learning
| Paper/Repo | What We Implemented |
|---|---|
| **arXiv 2603.23420** (Bilevel Autoresearch) | Outer loop that reads experiment logs, identifies bottlenecks, generates improvements |
| **arXiv 2602.02660** (MARS) | Comparative Reflective Memory — analyzes deltas between our scores and ground truth |
| **Karpathy Autoresearch** | Tight research loops with measurements and verification at every step |

### Python Libraries (pip)
| Library | Why |
|---|---|
| `playwright` | Browser automation (core dependency) |
| `yfinance` | Free stock market data |
| `crewai` | Multi-agent research coordination |
| `cloakbrowser` | Stealth browser for automation detection bypass |
| `json` (stdlib) | Data interchange |
| `urllib` (stdlib) | HTTP requests |
| `concurrent.futures` (stdlib) | Parallel source fetching |
| `sqlite3` (stdlib) | Experiment tracking database |
| `re` (stdlib) | Pattern matching |
| `logging` (stdlib) | Error reporting |

---

## Full Integration Map

```
USER INPUT: Company Name + URL
         │
         ▼
┌─────────────────────────────────────────────────────┐
│                 pipeline/research.py                 │
│   Stage 1: Quick-scan (browser)                     │
│   Stage 2: Enrichment (25 sources)                  │
│   Stage 3: Scoring (8 dimensions)                   │
│   Stage 4: Reflection (self-improvement)            │
│   Stage 5: Report (markdown scorecard)              │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              sources/enrichment.py                    │
│  ┌─────────────────────────────────────────────────┐│
│  │  PARALLEL (6 sources at once):                  ││
│  │  • Wikipedia (REST API)                        ││
│  │  • GitHub (REST API)                           ││
│  │  • Brave News (REST API)                       ││
│  │  • OpenCorporates (REST API)                   ││
│  │  • Crunchbase (HTML scrape)                    ││
│  │  • DNS/Hosting (stdlib socket)                 ││
│  └─────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────┐│
│  │  SEQUENTIAL:                                    ││
│  │  • Quick-scan (Playwright browser)             ││
│  │  • SEC EDGAR (REST) + yfinance                 ││
│  │  • GLEIF (REST) + DuckDuckGo (HTML)            ││
│  │  • AbstractAPI (REST)                          ││
│  │  • Companies House / SIRENE / VIES / FD        ││
│  │  • Clearbit / BuiltWith / Crunchbase API       ││
│  │  • Glassdoor / LinkedIn / SerpAPI / USPTO      ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│                 scoring/__init__.py                   │
│  8 dimensions → composite → grade → ARS score       │
│  Vetoes (12 conditions)                             │
│  Red flags (6 conditions)                           │
│  Kill criteria (3 conditions)                       │
│  Self-evaluation abort                              │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              pipeline/reflect.py                      │
│  Reflection loop (3 rounds max)                      │
│  Identifies weak dimensions                          │
│  Generates follow-up search queries                  │
│  Re-researches and re-scores                         │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              OUTPUT: HORECA/<company>/                │
│  • enriched.json — raw multi-source data             │
│  • quickscan.json — browser scan results             │
│  • deep-analysis.md — formatted scorecard            │
└─────────────────────────────────────────────────────┘
```

## Caching Layer

```
ALL API calls → core/cache.py (persistent disk cache)
  • Stored in: output/.cache/<source>/<key>.json
  • TTL: 7 days
  • Atomic writes (write .tmp → os.replace)
  • Second run: 1ms per source, zero API calls
```

## Configuration Layer

```
core/config.py
  • Config class — single source of truth for ALL env vars
  • Auto-loads .env file on import
  • All API key methods: github_token(), abstractapi_key(), etc.
  • Paths: BASE, HORECA_DIR, JOHN_JSON, CACHE_DIR
  • Defaults: timeouts, max workers, cache TTL, user agent
```
