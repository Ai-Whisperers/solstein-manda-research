# Autoresearch Learnings — HORECA Universe

## What Autoresearch Taught Us About Scoring

### Hardest Dimensions to Score via Desk Research

**1. Revenue scale fit** — The hardest dimension to score accurately. John's ARR estimates are often wide bands (€2-10M for unTill). Private companies don't disclose financials in NL/BE. Best proxies: headcount × industry rev/employee ratio, pricing page analysis, customer count × estimated ARPU.

**2. Ownership attractiveness** — Easy when the answer is "no PE/VC" (score 4-5). Hard to distinguish between "founder-owned" and "founder-owned with hidden family complexity." The unTill case showed 15 reseller entities that weren't visible from the dev entity alone — required digging through the reseller directory page.

**3. Growth trajectory** — The most subjective dimension. John scored unTill's growth 4/5 (seeing Air/Payments launches positively). We scored it 2/5 (focusing on NL headcount decline). Both views are defensible. Growth trajectory requires understanding *which metrics matter* for the specific business model.

### Easiest Dimensions

**4. Geographic fit** — Trivial. HQ address, web traffic by country, LinkedIn office locations. Always score 1 (wrong geography) or 5 (perfect) or 2-3 (US-headquartered with EU ops).

**5. Integration potential** — Also easy. Public API documentation, integration marketplace page, job postings for integration engineers. Score 5 if open API exists, 2-3 if no API found, 1 if claimed but no evidence.

**6. Vertical depth** — Years in market + niche focus. 25+ years exclusively in hospitality = 5. 5-year-old generalist software = 2.

### What We Got Wrong (and Fixed)

| Company | Dimension | Our Initial | John's | What We Missed |
|---|---|---|---|---|
| unTill | Ownership | 4 | 3 | 15 independent reseller entities = significant deal complexity |
| unTill | Revenue | 4 | 3 | ARR band is €2-10M (5× spread), not €5-10M |
| unTill | Tech | 4 | 3 | PHP/ASP.NET backend is legacy, not "cloud-native transition" |
| unTill | Growth | 2 | 4 | NL headcount decline ≠ business decline; 15-country reseller expansion + new products are real growth signals |
| Deliverect | Geographic | 4 | 2 | HQ moved to NY, primary market shifted to North America |
| Mews | Geographic | 5 | 2 | Global company in 85 countries is not a "Benelux fit" |
| Zenchef | Vertical | 4 | 5 | 15+ years, full-stack reservation/payments/CRM platform |

### Methodology Improvements for Next Time

1. **Check reseller/partner pages** before scoring ownership — unTill's resellers page revealed 15 entities we'd miss otherwise
2. **Check tech stack via job postings** — job descriptions reveal language/framework choices better than marketing pages
3. **Don't conflate NL headcount with global business** — NL dev entity shrinkage may reflect offshoring, not decline
4. **Geographic fit is about primary market, not HQ location** — Mews is Amsterdam HQ but operates globally, making it a poor Benelux-specific fit
5. **Revenue estimates need ±50% confidence bands** — desk research alone cannot reliably estimate private company ARR
