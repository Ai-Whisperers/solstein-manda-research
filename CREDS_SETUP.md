# API Key Setup Guide

Sign up at each URL, get your free API key, add to `.env`.

---

## 1. Clearbit — Company enrichment (funding, category, employees)

**URL**: https://dashboard.clearbit.com/signup  
**Free tier**: 50 requests/month  
**Data**: Company name, description, category, employees, estimated revenue, **funding stage**, **raised capital**, **tech used**

**Setup:**
1. Go to https://dashboard.clearbit.com/signup
2. Sign up with email
3. Go to https://dashboard.clearbit.com/api
4. Copy your API key
5. In `.env`: `CLEARBIT_KEY=paste_it_here`

**If Clearbit doesn't work:** ✅ SerpAPI key is already working — gives knowledge graph (CEO, founders, HQ, ratings) for well-known companies

---

## 2. BuiltWith — Tech stack detection

**URL**: https://api.builtwith.com/  
**Free tier**: 50 requests/month  
**Data returned**: Technology category groups only (e.g. "Analytics", "JavaScript", "CDN") — NOT individual technology names  
**⚠️ Limitation**: The free tier does NOT return specific technologies like "React", "Google Analytics", etc. Paid tier (~$99/mo) required for that.

**Setup:**
1. Go to https://api.builtwith.com/ (click "Get Your Free API Key")
2. Sign up with email
3. Check your email for the API key
4. In `.env`: `BUILTWITH_KEY=paste_it_here`

**If BuiltWith free tier isn't useful enough:** ✅ We already detect 20+ technologies via Playwright browser (React, Vue, jQuery, WordPress, PHP, Stripe, etc.) at no cost. This is more useful than BuiltWith's free tier.

---

## 3. Crunchbase — Funding rounds, investors, M&A history

**URL**: https://developers.crunchbase.com/  
**Free tier**: 50 requests/month  
**Data**: Funding rounds (series, dates, amounts), investors, acquisition history, IPO info, board members

**Setup:**
1. Go to https://developers.crunchbase.com/ — create an account
2. If that doesn't work, try https://www.crunchbase.com/ → login → settings → API
3. In `.env`: `CRUNCHBASE_KEY=paste_it_here`

**If Crunchbase won't give you a free key:** ✅ We already scrape Crunchbase HTML as a fallback (works, just less structured). SerpAPI also returns some funding data through Google Knowledge Graph.

---

## 4. Glassdoor — Company ratings, culture, CEO approval

**URL**: https://www.glassdoor.com/developer/  
**⚠️ Problem**: This page returns 404. Glassdoor may have shut down their free developer program.

**Alternatives (already working):**

| Alternative | What you get | Status |
|---|---|---|
| **SerpAPI** (key already set) | Google Knowledge Graph: rating, review count, CEO name, founders, headquarters, founded date | ✅ Works now |
| **Wikipedia** (free, no key) | Company description, founded, HQ, industry | ✅ Works now |
| **Glassdoor scrape** (free, no key) | Company rating if page is publicly accessible | ⏳ Possible |

**If you somehow get a Glassdoor API key:**
In `.env`: `GLASSDOOR_KEY=paste_it_here` — the code supports it if you find a working signup

---

## 5. SerpAPI — Google search results (structured) ✅ Already set

**URL**: https://serpapi.com/  
**Free tier**: 100 searches/month  
**Data**: Structured Google search results, **Knowledge Graph** (CEO, founders, founded date, HQ, ratings for well-known companies), **Google Patents**, news results, related companies

**Already configured.** SerpAPI key is set and working. This is our most valuable new source — it replaces:
- ❌ DuckDuckGo HTML scraping (slow, fragile) → ✅ SerpAPI (structured, fast)
- ❌ USPTO patent API (deprecated) → ✅ SerpAPI Google Patents search
- ❌ Manual founder/CEO research → ✅ Knowledge Graph

**Your key**: `1010c29b0ed4a4d390667eddbdbd26246cf7ae185e6815b29edc80690b96049f` (already in `.env`)

---

## 6. BuiltWith — Already set (from above)

**Your key**: `e34d2c7e-ff3d-4a33-9c7f-0bb6a725d56a` (already in `.env`)

---

## Already configured (these work right now):

| Key | Status | Data |
|---|---|---|
| `ABSTRACT_API_KEY` | ✅ Set | Industry, employee range, founded year |
| `GITHUB_TOKEN` | ✅ Set | 5,000 req/hr GitHub API |
| `FINANCIAL_DATASETS_API_KEY` | ✅ Set | Company facts, financial statements |
| `SERPAPI_KEY` | ✅ Set | Google search, Knowledge Graph, Patents |
| `BUILTWITH_KEY` | ✅ Set | Tech category groups |

## Free, no key needed (work immediately):

| Source | Data |
|---|---|
| **LinkedIn** (search-based) | Employee count, open roles |
| **Wikipedia** | Company descriptions, founded, HQ |
| **SEC EDGAR** | Public company financial filings |
| **GLEIF** | Legal entity identifiers (global) |
| **OpenRegistry** | 27 national company registries |
| **French SIRENE** | French company registration |
| **VIES VAT** | EU VAT number validation |
| **World Bank** | Country economic indicators |
| **Brave News** | Recent news articles |
| **SerpAPI Google Patents** | Patent search results |
| **Playwright browser** | Tech stack, pricing, careers, internal links |

---

## Quick test after setting keys:

```bash
cd /data/work/deliverables/ma-research-pipeline
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from datasources import enrich_company
data = enrich_company('Booking.com')
srcs = data.get('sources_found', [])
print(f'Active sources ({len(srcs)}): {srcs}')
"
```

With all keys set, expect: `15+ sources including clearbit, builtwith, abstractapi, serpapi, linkedin, github, wikipedia, gleif`

Without extra keys, expect: `~12 sources including serpapi, builtwith (categories), linkedin, wikipedia, github, gleif, abstractapi`
