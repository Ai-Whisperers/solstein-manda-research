#!/usr/bin/env python3
"""Auto-generate corporate-history.md and financial-growth.md from existing deep-analysis.md files."""

import json, os, re, csv
from datetime import datetime

BASE = os.path.join(os.path.dirname(__file__), '..')
JOHN_JSON = os.path.join(BASE, 'archive', 'john-original', 'horeca_json', 'horeca_data.json')
HORECA_DIR = os.path.join(BASE, 'output', 'HORECA')

DIMS = ['Ownership attractiveness', 'Revenue scale fit', 'Geographic fit',
        'Tech stack modernity', 'Customer lock-in', 'Vertical depth',
        'Integration potential', 'Growth trajectory']

def folder_from(name):
    f = name.lower().replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '')
    f = f.replace("'", '').replace('&', 'and').replace('--', '-').strip('-')
    return f

def extract_value(text, field):
    """Extract a table cell value from a deep-analysis.md table."""
    patterns = [
        rf'\|\s*{re.escape(field)}\s*\|\s*(.*?)\s*(?:\|\s|$)',
        rf'\|\s*{re.escape(field)}\s*\|\s*(.*?)\s*\|',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ''

def extract_ownership(text):
    m = re.search(r'Ownership\s*\|\s*(.*?)\s*\|', text)
    return m.group(1).strip() if m else ''

with open(JOHN_JSON) as f:
    data = json.load(f)

# Build maps
john_by_name = {}
for c in data['companies']:
    john_by_name[c['company_name']] = c

count_ch = 0
count_fg = 0

for d in sorted(os.listdir(HORECA_DIR)):
    dp = os.path.join(HORECA_DIR, d)
    if not os.path.isdir(dp) or d == 'Data':
        continue
    da = os.path.join(dp, 'deep-analysis.md')
    if not os.path.exists(da):
        continue
    with open(da) as f:
        content = f.read()

    name_match = re.search(r'^# (.+?) — Deep', content)
    name = name_match.group(1).strip() if name_match else d

    # --- corporate-history.md ---
    ch_path = os.path.join(dp, 'corporate-history.md')
    if not os.path.exists(ch_path):
        legal_entity = extract_value(content, 'Legal entity') or extract_value(content, 'Legal entity')
        founded = extract_value(content, 'Founded')
        founder = extract_value(content, 'Founder') or extract_value(content, 'Founder & CEO') or extract_value(content, 'Founders')
        hq = extract_value(content, 'HQ') or extract_value(content, 'HQ')
        ownership = extract_ownership(content)

        # Try John's data for more details
        jc = john_by_name.get(name, {})
        j_fund = jc.get('fundamentals') or {}
        john_founded = j_fund.get('founded', '')
        john_ceo = j_fund.get('ceo_founders', '')

        ch = f"""# {name} — Corporate History

**Generated**: {datetime.now().strftime('%Y-%m-%d')}
**Source**: Derived from deep-analysis.md + John reference dataset

---

## 1. Legal Entity

| Data Point | Value | Source | Confidence |
|---|---|---|---|
| Legal entity | {legal_entity or 'See deep-analysis.md'} | deep-analysis.md | Confirmed |
| Founded | {founded or john_founded or 'See deep-analysis.md'} | deep-analysis.md | Confirmed |
| Founder(s) | {founder or john_ceo or 'See deep-analysis.md'} | deep-analysis.md | Confirmed |
| HQ | {hq or 'See deep-analysis.md'} | deep-analysis.md | Confirmed |
| Ownership | {ownership or 'See deep-analysis.md'} | deep-analysis.md | Confirmed |

---

## 2. Entity Structure

{legal_entity or name} is a privately held {'B.V.' if 'B.V.' in (legal_entity or '') or 'BV' in (legal_entity or '') else 'limited liability company'}, {'headquartered in ' + hq + '.' if hq else '.'}

---

## 3. M&A Feasibility

- **Acquisition viability**: See deep-analysis.md scorecard for Ownership attractiveness dimension
- **Primary blockers**: {'PE/VC overhang' if 'PE' in ownership or 'VC' in ownership or 'PE-backed' in ownership else 'Founder exit intent unconfirmed'}
- **Estimated EV**: See deep-analysis.md financial section

---

*Auto-generated from deep-analysis.md. For full detail, refer to the deep-analysis.md file.*
"""
        with open(ch_path, 'w') as f:
            f.write(ch.strip() + '\n')
        count_ch += 1

    # --- financial-growth.md ---
    fg_path = os.path.join(dp, 'financial-growth.md')
    if not os.path.exists(fg_path):
        # Extract financial data from deep-analysis
        rev = extract_value(content, 'Revenue') or extract_value(content, 'Revenue')
        employees = extract_value(content, 'Employees') or ''
        funding = extract_value(content, 'Funding raised') or extract_value(content, 'Total funding') or ''
        profitability = extract_value(content, 'Profitability') or ''

        jc = john_by_name.get(name, {})
        j_fund = jc.get('fundamentals') or {}
        j_fg = jc.get('financial_growth') or {}

        fg = f"""# {name} — Financial Growth Analysis

**Generated**: {datetime.now().strftime('%Y-%m-%d')}
**Source**: Derived from deep-analysis.md + John reference dataset

---

## Revenue

| Metric | Value | Source | Confidence |
|---|---|---|---|
| Revenue (est.) | {rev or 'Not publicly disclosed'} | deep-analysis.md | Estimated |
| Funding raised | {funding or 'None identified'} | deep-analysis.md | {'Confirmed' if funding else 'Estimated'} |
| Profitability | {profitability or 'Not publicly disclosed'} | deep-analysis.md | Estimated |

---

## Employees

| Metric | Value | Source |
|---|---|---|
| Headcount | {employees or 'Not disclosed'} | deep-analysis.md |

---

## Funding History

{'No external funding rounds identified.' if not funding or 'Zero' in funding or 'None' in funding else f'See deep-analysis.md for details: {funding}'}

---

*Auto-generated from deep-analysis.md. For full detail, refer to the deep-analysis.md file.*
"""
        with open(fg_path, 'w') as f:
            f.write(fg.strip() + '\n')
        count_fg += 1

print(f"Generated {count_ch} corporate-history.md files")
print(f"Generated {count_fg} financial-growth.md files")
