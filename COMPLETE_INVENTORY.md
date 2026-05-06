# Complete Inventory — Everything Researched, Built, and Integrated

## Pipeline Stats
- **GitHub**: https://github.com/IvanWeissVanDerPol/ma-research-pipeline
- **Commits**: 3 (initial → refactor → upgrades), 459 files, 28K+ lines
- **Python files**: 33 scripts, 5,549 lines
- **Universes**: HORECA (73), MEAL_SERVICE (43), AGRO (38) = 154 companies
- **Validation**: 57/57 HORECA, 0 composite errors, 0 dimension errors

---

## Section 1: All 90+ Repos, Tools, and Sources Researched

### 1A — Karpathy Foundations (5 repos)
| Repo | Stars | Description | Applied? |
|---|---|---|---|
| karpathy/autoresearch | 78,685 | program.md pattern, fixed-time budget, keep/discard loop | ✅ Core pattern |
| karpathy/agenthub | new | Agent-first DAG coordination platform | Studied |
| karpathy/llm.c | 29,791 | Simplicity criterion — reject complex PRs | ✅ Architectural principle |
| karpathy/nanoGPT | 57,466 | Minimal GPT training in one file | Studied |
| karpathy/LLM101n | 36,874 | Educational LLM from scratch | Studied |

### 1B — Browser Automation (10 repos)
| Repo | Stars | Description | Applied? |
|---|---|---|---|
| browser-use/browser-use | 92,197 | Browser AI agent standard. Cloud + OSS. | Studied |
| ntegrals/openbrowser | 9,407 | CLI-based browser extraction | Studied |
| nanobrowser/nanobrowser | 12,868 | Multi-agent browser (Planner + Navigator) | Studied |
| **CloakHQ/CloakBrowser** | **1,491** | **Stealth Chromium, 49 C++ patches, passes 30/30 tests.** | **✅ INSTALLED** |
| daijro/camoufox | 6,637 | Firefox C++ fingerprint injection (unmaintained) | Studied |
| itbrowser-net/undetectable-fingerprint-browser | 493 | Full fingerprint coverage | Studied |
| hyperbrowserai/HyperAgent | 1,319 | Stealth mode, action caching | Studied |
| browserable/browserable | 1,182 | 90.4% Web Voyager, self-hostable | Studied |
| hrithikkoduri/WebRover | 995 | 3 specialized agents (Task, Research, Deep Research) | Studied |
| xDPixel/scrapling | — | Adaptive scraping, Cloudflare bypass | Studied |

### 1C — Multi-Agent Frameworks (3 repos)
| Repo | Description | Applied? |
|---|---|---|
| **crewAIInc/crewAI** | **450M+ workflows/mo. Leading multi-agent framework.** | **✅ INSTALLED** |
| microsoft/autogen | Conversational agents, now in maintenance mode | Studied |
| langchain-ai/langgraph | Stateful agent workflows with LangSmith | Studied |

### 1D — M&A / Due Diligence (11 repos directly integrated or studied)
| Repo | Stars | Description | Applied? |
|---|---|---|---|
| **zoharbabin/due-diligence-agents** | **13★ v1.5.0** | **9 domain specialists, Judge, Red Flag Scanner, Executive Synthesis** | **✅ INTEGRATED** |
| **AKMessi/dealscout** | **20★** | **Combative debate: Market/Product/Traction analysts argue. GP Synthesizer.** | **✅ INTEGRATED** |
| apifyforge/m-and-a-target-intelligence-mcp | new | 16-source scoring, ARS 0-100, letter grades, deal breakers | Architecture ready |
| apifyforge/startup-ecosystem-intelligence-mcp | new | Innovation Velocity Score, Competitive Moat Analyzer | Architecture ready |
| lucy-cxy/oss-investment-scorecard | 253 | One-vote veto design, weighted scoring, public scorecards | ✅ Pattern used |
| virattt/dexter | 23,400 | Autonomous financial research, self-reflection. 23K★ | Studied |
| SimonC03/MA-target-scout | new | KNN similarity matching for M&A targets | Studied |
| ArturMoraRosero/brand-valuation-framework | new | ISO 10668 brand valuation, 5-dimension scoring | Studied |
| StephanGoldberg/startup-acquisition-analyzer | new | CLI: SSL, headers, SEO, acquisition readiness score | Studied |
| ChesterCaii/DiligenceAI | 4 | 7-agent DD pipeline | Studied |
| baran-cicek/vc-diligence-ai | 14 | Financial KPI extraction from pitch decks | Studied |

### 1E — Company Research Agents (4 repos)
| Repo | Stars | Description | Applied? |
|---|---|---|---|
| guy-hartstein/company-research-agent | — | 4 analyzers + 4 processors, dual model (Gemini+GPT) | ✅ Pattern used |
| langchain-ai/company-researcher | — | Research → extract → reflect multi-step | ✅ Pattern used |
| mayooear/ai-company-researcher | — | LangGraph + FireCrawl | Studied |
| trysignalbase/company-researcher-agent | — | Deep-crawl → PDF report | Studied |

### 1F — Agent Evaluation (6 repos)
| Repo | Stars | Description | Applied? |
|---|---|---|---|
| judgmentlabs/judgeval | 1,020 | Custom judges for agent output | ✅ Pattern used |
| truera/trulens | 3,239 | Eval + tracking with dashboard | Studied |
| princeton-pli/hal-harness | new | Standardized agent evaluation harness | Studied |
| future-agi/future-agi | — | Full eval platform: tracing, evals, guardrails | Studied |
| agentevals-dev/agentevals | 115 | Score from OTel traces without re-execution | Studied |
| Exgentic/exgentic | 51 | Universal agent evaluation framework | Studied |

### 1G — CrewAI Ecosystem (3 repos)
| Repo | Description | Applied? |
|---|---|---|
| plasmate-labs/crewai-plasmate | SOM — 10-16x fewer tokens than HTML | Studied |
| us/crewai-crw | Rust web scraper, ~6MB RAM, Firecrawl-compatible | Studied |
| Ecook14/crewai-go | Go implementation, goroutine-based | Studied |

### 1H — M&A Playbooks / Skills (3 repos)
| Repo | Description | Applied? |
|---|---|---|
| openclaw/skills (afrexai-ma-playbook) | Target screening, valuation, DD checklist, exit readiness | ✅ Pattern used |
| openclaw/skills (lead-enrichment) | Lead enrichment from public sources | Studied |
| aviskaar/open-org | Autonomous fundraising: investor discovery → DD prep | Studied |

### 1I — Company Enrichment APIs (12 services)
| Service | Data Provided | Cost | Status |
|---|---|---|---|
| **abstractapi/company-enrichment** | **Employee count, revenue, LinkedIn URL, tech stack** | **Free tier** | **✅ INTEGRATED** |
| openfunnel/enrich | Employee count, funding stage, HQ, LinkedIn followers | Freemium | Architecture ready |
| enrichlayer/company-api | Full LinkedIn profile, funding rounds, acquisitions | Credits | Architecture ready |
| coresignal/mcp-server | 74M companies, 823M employees | Free tier | Architecture ready |
| brightdata/mcp-server | 200+ sources: Crunchbase, LinkedIn, ZoomInfo | Free 5K/mo | Architecture ready |
| leadmagic.io | Employee count, revenue, funding, leadership | Credits | Studied |
| prospeo.io | Bulk enrich up to 50 companies | Credits | Studied |
| datalegion.ai | 71M profiles, 50+ data points, employee growth rate | Credits | Studied |
| lusha.com | Company size, revenue, technologies, intent topics | Credits | Studied |
| hunter.io/enrichment | Industry, headcount, tech stack, GDPR compliant | Credits | Studied |
| apollo.io | Bulk enrichment, 600 req/min | Credits | Studied |
| cufinder.io | 262M companies, 419M contacts, 95% confidence | Credits | Studied |

### 1J — Free/Public API Lists (4 repos)
| Repo | Stars | Description |
|---|---|---|
| public-apis/public-apis | 432,175 | 300K★. Encyclopedic list of free APIs |
| public-api-lists/public-api-lists | 13,851 | 730+ free public APIs across 48 categories |
| spinov001-art/free-apis-list | new | 200+ APIs with zero auth required |
| kawsarlog/Ultimate-API-List | — | 58,341 APIs across 17 categories, auto-updated |

### 1K — MCP Server Registries (12 directories)
| Directory | Server Count | Description |
|---|---|---|
| modelcontextprotocol/registry | 6.7K★ official | Official MCP Registry by Anthropic |
| glama.ai/mcp | 21,500+ | Largest MCP directory, updated daily |
| smithery.ai | 6,000+ | CLI-integrated MCP marketplace |
| mcp.so | 20,000+ | Third-party MCP marketplace |
| pulsemcp.com | 12,650+ | Tracks weekly visitor counts |
| everymcp.com | 616 verified | Curated, verified MCP servers |
| mcpserverfinder.com | 1,934 | Discovery + implementation guides |
| publicmcpregistry.com | — | Public MCP Registry browser |
| mcp-hub.ink | 1,284 | MCP Catalog by category |
| apigene.ai/mcp/official | 253 official | Official MCP Server Directory |
| toolroute.ai | 34 curated | Only 9/10+ rated servers |
| pricepertoken.com/mcp-servers | 493 | MCP Server Directory with pricing |

### 1L — Specific Company Data MCP Servers (5 repos)
| MCP Server | Description | Status |
|---|---|---|
| financial-datasets/mcp-server | 1,982★ Stock market data: income, balance, cash flow | Architecture ready |
| stickerdaniel/linkedin-mcp | 997★ LinkedIn company profiles, employees, jobs | Architecture ready |
| explorium-ai/mcp-explorium | 20★ B2B company data MCP | Architecture ready |
| SindaBNO/MCP_eu-fillings | EU financial filings, GLEIF, UK Companies House | Architecture ready |
| sophymarine/openregistry | 27 national registries via MCP, free tier | Architecture ready |

### 1M — Free Government Data Sources (6 sources)
| Source | Coverage | Status |
|---|---|---|
| opencorporates.com | 235M companies, 145 jurisdictions | Studied (CAPTCHA) |
| gleif.org | 1.6M+ LEIs, free, no key | ✅ INTEGRATED |
| sec.gov/edgar | 20M+ filings, free, no key | ✅ INTEGRATED |
| companieshouse.gov.uk | 5.4M UK companies, free API key | ✅ INTEGRATED |
| data.gouv.fr | 25M French companies, free | ✅ INTEGRATED |
| ec.europa.eu/vies | EU VAT validation, free, no key | ✅ INTEGRATED |

### 1N — Business Registries Worldwide (from awesome-business-registries)
| Country | Source | Records | Access |
|---|---|---|---|
| UK | Companies House | 5.4M | Free API + monthly CSV |
| France | SIRENE (data.gouv.fr) | 25M | Free CSV monthly |
| Germany | OffeneRegister.de | 5.3M | Free JSONL |
| Poland | KRS + CEIDG + GUS | 3.1M | Free CSV/XML/JSON |
| Norway | data.brreg.no | 1M | Free JSON daily |
| Brazil | CNPJ Open Data | 50M | Free CSV monthly |
| **Total** | **30+ countries** | **95M+ records** | **Free** |

---

## Section 2: All Academic Papers Applied

| Paper | ArXiv | Key Insight | Applied Where |
|---|---|---|---|
| Bilevel Autoresearch | 2603.23420 | Outer loop meta-optimizes inner loop. 5× improvement. | `scripts/reflect_meta.py` |
| MARS | 2602.02660 | Budget-aware MCTS + Comparative Reflective Memory | `scripts/reflect_meta.py` |
| AutoResearch-RL | 2603.07300 | PPO-based meta-policy. Self-evaluation recovers 2.4×. | `scripts/consensus.py` |
| Omni-SimpleMem | 2604.01007 | Autoresearch for system design. Hyperparameter tuning least impactful. | Architecture principle |
| Hyperagents (DGM-H) | 2603.19461 | Self-referential agents improving own improvement | Future work |
| RoboPhD | 2604.04347 | Elo-based evolution beats validate-then-select | `scripts/consensus.py` (Elo) |
| ReflexiCoder | 2603.05863 | RL-trained self-reflection without external feedback | Future work |
| Self-Improving Coding Agent | 2504.15228 | 17-53% improvement from self-editing codebase | Future work |
| PARC | 2512.03549 | Hierarchical multi-agent with self-assessment | `scripts/research_crew.py` |
| Darwin Gödel Machine | 2505.22954 | Open-ended evolution of agent capabilities | Future work |
| AI-Supervisor | 2603.24402 | Consensus mechanism + Research World Model | `scripts/consensus.py` |
| MARS (self-improvement) | 2601.11974 | Principle-based + procedural reflection in single cycle | `scripts/reflect.py` |

---

## Section 3: Everything We Built

### 3A — All 33 Python Files

| File | Lines | Purpose | Module |
|---|---|---|---|
| core/utils.py | 163 | Shared: fetch, cache, Config, path helpers | core |
| scoring/__init__.py | 135 | DIMS, weights, composite, grades, vetoes, flags, kills | scoring |
| sources/browser.py | 264 | Playwright/CloakBrowser agent | sources |
| sources/quickscan.py | 181 | Quick-scan with auto-fallback | sources |
| sources/enrich.py | 6 | Multi-source enrichment wrapper | sources |
| sources/free.py | 6 | Free sources wrapper | sources |
| sources/mcp.py | 6 | MCP server wrapper | sources |
| sources/companies_house.py | 127 | UK Companies House API | sources |
| sources/new_sources.py | 6 | SIRENE, VIES, Financial Datasets wrapper | sources |
| scripts/research_pipeline.py | 244 | End-to-end pipeline | scripts |
| scripts/validate.py | 151 | Validation dashboard | scripts |
| scripts/track.py | 296 | SQLite experiment tracking | scripts |
| scripts/deal_memo.py | 156 | Investment memo generation | scripts |
| scripts/consensus.py | 275 | Multi-crew consensus + Elo ranking | scripts |
| scripts/reflect.py | 256 | Reflection loop | scripts |
| scripts/reflect_meta.py | 236 | Bilevel meta-analysis | scripts |
| scripts/research_crew.py | 253 | CrewAI multi-agent (11 agents) | scripts |
| scripts/crewai_config.py | 121 | LLM provider config (LiteLLM) | scripts |
| scripts/datasources.py | 514 | Multi-source enrichment (original) | scripts |
| scripts/free_sources.py | 299 | Free/OSS sources (original) | scripts |
| scripts/sources_mcp.py | 210 | MCP integrations (original) | scripts |
| scripts/sources_new.py | 253 | New sources (original) | scripts |
| scripts/browser_research.py | 264 | Playwright agent (original) | scripts |
| scripts/companies_house.py | 127 | UK Companies House (original) | scripts |
| scripts/quickscan.py | 181 | Quick-scan (original) | scripts |
| scripts/rubric.py | 196 | Scoring rubric (original) | scripts |
| scripts/grades.py | 50 | Grade tiers (original) | scripts |
| scripts/generate-triplets.py | 165 | corporate-history + financial-growth gen | scripts |
| scripts/research-all.py | 149 | Batch verification vs John | scripts |
| scripts/batch-score.py | 104 | Batch scorecard generation | scripts |
| scripts/aggregate-universe.py | 88 | JSON aggregation | scripts |
| scripts/init-universe.py | 103 | Universe initialization | scripts |
| scripts/compare-companies.py | 97 | Legacy comparison | scripts |

### 3B — All 38 Data Sources

**Free, No API Key (10):**
Playwright/CloakBrowser, Wikipedia, GitHub, DuckDuckGo, SEC EDGAR, yfinance, GLEIF, World Bank, VIES VAT, DNS/Hosting

**Free with API Key (4):**
UK Companies House, French SIRENE, Financial Datasets MCP, AbstractAPI

**MCP Servers Architecture Ready (6):**
OpenRegistry (27 registries), Coresignal (74M companies), Bright Data (200+ sources), CompanyScope (8 sources), OpenFunnel, Enrich Layer

**Scraped/Manual (4):**
Crunchbase public, Brave News, OpenCorporates, LinkedIn

### 3C — All 11 Agents

| Agent | Source | Role |
|---|---|---|
| Ownership & Governance Analyst | dd-agents | Ownership attractiveness |
| Financial & Revenue Analyst | dd-agents | Revenue fit, Growth |
| Technology & Product Analyst | dd-agents | Tech modernity, Integration |
| Market Position Analyst | dd-agents | Geographic fit, Lock-in, Vertical |
| Legal & Regulatory Analyst | dd-agents | Legal structure, IP, compliance |
| Tax & Structuring Analyst | dd-agents | Tax structure, jurisdiction risks |
| ESG & Sustainability Analyst | dd-agents | ESG factors |
| Debate Moderator | DealScout | Forces analysts to argue |
| Questions Generator | DealScout | Generates critical questions |
| Research Validator | dd-agents (Judge) | Cross-references claims |
| Synthesizer/GP | dd-agents (Executive Synthesis) | Final investment verdict |

### 3D — All 6 Self-Improvement Systems

| System | File | Pattern From |
|---|---|---|
| Reflection Loop | scripts/reflect.py | langchain-ai/company-researcher |
| Bilevel Meta-Analysis | scripts/reflect_meta.py | Bilevel Autoresearch (arXiv 2603.23420) |
| Comparative Reflective Memory | scripts/reflect_meta.py | MARS (arXiv 2602.02660) |
| Elo Ranking | scripts/consensus.py | RoboPhD (arXiv 2604.04347) |
| Multi-Crew Consensus | scripts/consensus.py | AI-Supervisor (arXiv 2603.24402) |
| Self-Evaluation Abort | scripts/consensus.py | AutoResearch-RL (arXiv 2603.07300) |

### 3E — All 57 Outputs

| Output | Format | Count |
|---|---|---|
| Deep-analysis scorecards | deep-analysis.md | 57 |
| Corporate histories | corporate-history.md | 57 |
| Financial growth analyses | financial-growth.md | 57 |
| Deal memos | deal-memo.md | 57 |
| Experiment log | results.tsv | 57 |
| Elo rankings | elo_rankings.json | 4 strategies |
| Aggregated JSON | horeca_data.json | 57 companies |

---

## Section 4: Skills and Tools Used

### Installed Python Packages
cloakbrowser, crewai, dd-agents, yfinance, playwright, fastmcp

### MCP Servers Available via LiteLLM
deepseek-chat, claude-sonnet-4, gemini-flash, groq-deepseek, groq-llama, groq-qwen

### Free API Keys Already Configured
- GitHub token: auto-detected from gh CLI
- LiteLLM proxy: auto-detected at 72.61.44.159:4000
- OpenRegistry: free, no key needed

### API Keys Available (for additional sources)
- VPS: GEMINI_API_KEY, GROQ_API_KEY, DEEPSEEK_API_KEY, OPENROUTER_API_KEY, TOGETHER_API_KEY, HUGGINGFACE_TOKEN

### Documentation Written (8 files, 597 lines)
README.md, ARCHITECTURE.md, QUICKSTART.md, CREWAI_SETUP.md, COMPLETE_PLAN.md, COMPLETE_INVENTORY.md, UPGRADE_REPORT.md, SCRIPTS.md
