# API Key Setup Guide

Go to each URL, sign up, get your free API key, paste into `.env`.

---

## 1. Clearbit — Company enrichment

1. Go to https://dashboard.clearbit.com/signup
2. Sign up with email
3. Go to https://dashboard.clearbit.com/api
4. Copy your API key
5. In `.env`: `CLEARBIT_KEY=paste_it_here`

---

## 2. BuiltWith — Tech stack detection

1. Go to https://api.builtwith.com/ (click "Get Your Free API Key")
2. Sign up with email
3. Check your email for the API key
4. In `.env`: `BUILTWITH_KEY=paste_it_here`
5. ⚠️ Free tier only returns tech categories (not specific tech names). Paid tier needed for full data. Browser detection works better for free.

---

## 3. Crunchbase — Funding, investors, M&A

1. Go to https://developers.crunchbase.com/ — try signing up
2. If that doesn't work, try https://www.crunchbase.com/ → login → settings → API
3. In `.env`: `CRUNCHBASE_KEY=paste_it_here`
4. ⚠️ If Crunchbase doesn't approve your free key, we fall back to HTML scraping which still works

---

## 4. Glassdoor — Company ratings, culture, CEO approval

1. Glassdoor's developer program at https://www.glassdoor.com/developer/ was unreliable (404 when tested)
2. Alternative: We use SerpAPI (Google Knowledge Graph) which returns ratings, CEO, founders, and headquarters for well-known companies
3. If you find a working Glassdoor signup link, paste the key in `.env`: `GLASSDOOR_KEY=paste_it_here`

---

## 5. SerpAPI — Google search results (structured)

1. Go to https://serpapi.com/
2. Sign up (free tier: 100 searches/month)
3. Go to your dashboard, find your API key
4. In `.env`: `SERPAPI_KEY=paste_it_here`

---

## Already configured (these work right now):

| Key | Status |
|---|---|
| `ABSTRACT_API_KEY` | ✅ Already set |
| `GITHUB_TOKEN` | ✅ Already set |
| `FINANCIAL_DATASETS_API_KEY` | ✅ Already set |

## Free, no key needed (work immediately):

| Source | Data |
|---|---|
| LinkedIn | Employee count, open roles |
| USPTO | Patents assigned to company |
| Wikipedia | Company descriptions |
| SEC EDGAR | Public company filings |
| GLEIF | Legal entity identifiers |

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

Expected output with all keys: `Active sources (15+): ['website', 'dns', 'wikipedia', 'github', 'web_search', 'gleif', 'abstractapi', 'clearbit', 'builtwith', 'crunchbase_api', 'glassdoor', 'linkedin', 'serpapi', 'uspto']`
