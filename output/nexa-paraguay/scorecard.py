#!/usr/bin/env python3
"""Solstein M&A Scorecard for Nexa Paraguay."""
import json, os
from datetime import datetime

company = 'Nexa Paraguay'
vertical = 'Relocation & Residency Services'
DIMS = [
    'Ownership attractiveness', 'Revenue scale fit', 'Geographic fit',
    'Tech stack modernity', 'Customer lock-in', 'Vertical depth',
    'Integration potential', 'Growth trajectory',
]
WEIGHTS = [3, 3, 3, 2, 2, 2, 1, 1]

dimensions = {
    'Ownership attractiveness': {
        'score': 4, 'weight': 3,
        'rationale': 'Private service business. No PE/VC — clean cap table, fully acquirable. Owned/operated by ParaguAI team (Ivan). No complex structures or institutional investors.',
        'risk_factors': []
    },
    'Revenue scale fit': {
        'score': 3, 'weight': 3,
        'rationale': 'Programs $2,900-6,900+. Fixed-fee + add-ons (land purchase, 12-month accounting). Boutique scale — below typical PE $5M+ EBITDA threshold, but clear path via volume.',
        'risk_factors': ['Revenue unverified — no public financials', 'Client volume appears limited']
    },
    'Geographic fit': {
        'score': 5, 'weight': 3,
        'rationale': 'Paraguay-based, Paraguay-focused. Perfect alignment with Ai-Whisperers Paraguay strategy. Strong local govt/bank/notary relationships.',
        'risk_factors': []
    },
    'Tech stack modernity': {
        'score': 4, 'weight': 2,
        'rationale': 'Next.js 16 + Tailwind v4 + React 19 + TS 5. Modern stack. 4-locale i18n. HubSpot/Mailchimp/GA4. 111 responsive images. SEO-optimized. WhatsApp lead capture.',
        'risk_factors': ['Pages Router (not App Router)', 'No headless CMS — content in JSON files']
    },
    'Customer lock-in': {
        'score': 3, 'weight': 2,
        'rationale': '8-12 week process creates high switching costs mid-process. Investor Program has 12-month recurring engagement. But low stickiness after engagement completes.',
        'risk_factors': ['One-time relationship for most clients', 'Competitive market']
    },
    'Vertical depth': {
        'score': 3, 'weight': 2,
        'rationale': 'Narrow but deep: 9 services across 4 programs covering full relocation stack. Benelux specialization edge.',
        'risk_factors': ['Single-vertical risk', 'Limited differentiation from competitors']
    },
    'Integration potential': {
        'score': 5, 'weight': 1,
        'rationale': 'Already on Ai-Whisperers stack: client-kit, CI/CD, ParaguAI infra. Golden Visa cross-referral, builder landing pages, WhatsApp automation, HubSpot CRM — all directly applicable.',
        'risk_factors': []
    },
    'Growth trajectory': {
        'score': 4, 'weight': 1,
        'rationale': 'Growing Paraguay relocation demand (tax refugees, digital nomads). 200+ families served. Scale via content, paid ads, Benelux partner network, AI lead qualification.',
        'risk_factors': ['Growth metrics unverified', 'Macro-dependent (tax policy, political stability)']
    }
}

total_weight = sum(WEIGHTS)
composite = sum(dimensions[d]['score'] * dimensions[d]['weight'] for d in DIMS) / total_weight

GRADE_TABLE = [
    (4.5, 5.0, 'A', 'Strong acquisition candidate'),
    (3.5, 4.49, 'B', 'Viable with noted risks'),
    (2.5, 3.49, 'C', 'Significant concerns requiring investigation'),
    (1.5, 2.49, 'D', 'Major risks present'),
    (0.0, 1.49, 'F', 'Critical issues — likely not viable'),
]
for lo, hi, grade, desc in GRADE_TABLE:
    if lo <= composite <= hi:
        grade_obj = {'grade': grade, 'description': desc, 'score_100': round((composite / 5.0) * 100)}
        break

result = {
    'company': company,
    'vertical': vertical,
    'analyzed_at': datetime.now().isoformat(),
    'veto_checks': {'pe_owned': False, 'vc_backed': False, 'us_headquartered': False,
                    'already_acquired': False, 'off_market': False},
    'veto_triggered': False,
    'dimensions': dimensions,
    'composite_score': round(composite, 2),
    'grade': grade_obj['grade'],
    'grade_description': grade_obj['description'],
    'readiness_score_100': grade_obj['score_100'],
}

print(json.dumps(result, indent=2, ensure_ascii=False))
