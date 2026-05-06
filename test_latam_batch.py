#!/usr/bin/env python3
"""
Batch test pipeline on multiple LATAM companies across different sectors.
Validates that the pipeline works on diverse geographies, sectors, and company types.
"""

import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from datasources import enrich_company
from scoring import DIMS, compute_composite, composite_to_grade, apply_vetoes, scan_red_flags

# LATAM companies across sectors: fintech, ecommerce, SaaS, logistics, health, energy
companies = [
    # Fintech / Payments
    {"name": "StoneCo", "domain": "https://www.stone.co", "ticker": "STNE", "sector": "Fintech", "country": "BR"},
    {"name": "MercadoLibre", "domain": "https://www.mercadolibre.com", "ticker": "MELI", "sector": "Ecommerce", "country": "AR"},
    {"name": "Nubank", "domain": "https://nubank.com.br", "ticker": "NU", "sector": "Fintech", "country": "BR"},
    {"name": "Globant", "domain": "https://www.globant.com", "ticker": "GLOB", "sector": "Tech Services", "country": "AR"},
    {"name": "Despegar", "domain": "https://www.despegar.com", "ticker": "DESP", "sector": "Travel", "country": "AR"},
    {"name": "Biomelab", "domain": "https://biomelab.com", "ticker": None, "sector": "Health", "country": "PY"},
    {"name": "Ualabee", "domain": "https://ualabee.com", "ticker": None, "sector": "Mobility", "country": "AR"},
]

results = []

print("=" * 80)
print("LATAM BATCH TEST — 7 Companies Across 6 Sectors")
print("=" * 80)

for i, co in enumerate(companies, 1):
    print(f"\n[{i}/{len(companies)}] {co['name']} ({co['sector']}, {co['country']})")
    print("-" * 60)
    
    try:
        # Enrichment
        data = enrich_company(co['name'], co['domain'])
        src = data.get('sources_found', [])
        tech = data.get('website', {}).get('tech_stack', [])
        ws = data.get('web_search', [])
        
        # Score based on enrichment signals
        geo_score = 1 if co['country'] != 'NL' else 5
        if co['country'] in ('AR', 'BR', 'PY'):
            geo_score = 1
        
        scores = {
            'Ownership attractiveness': 2,
            'Revenue scale fit': 2,
            'Geographic fit': geo_score,
            'Tech stack modernity': 4 if len(tech) >= 3 else 3,
            'Customer lock-in': 3,
            'Vertical depth': 3,
            'Integration potential': 3,
            'Growth trajectory': 3,
        }
        
        # Adjust based on signals
        if len(src) >= 4:
            scores['Revenue scale fit'] = 3
        if len(tech) >= 5:
            scores['Tech stack modernity'] = 5
        if ws and len(ws) >= 3:
            scores['Growth trajectory'] = 4
        
        info = {'ownership': '', 'country': co['country'], 'status': ''}
        changes = apply_vetoes(info, scores)
        comp = compute_composite(scores)
        grade = composite_to_grade(comp)
        flags = scan_red_flags(scores)
        
        print(f"  Sources: {len(src)} — {', '.join(src[:5])}")
        print(f"  Tech: {', '.join(tech[:4]) if tech else 'none'}")
        print(f"  News: {len(ws) if ws else 0}")
        print(f"  Score: {comp:.2f}/5.0 | Grade: {grade['grade']} | ARS: {grade['score_100']}/100 | Flags: {len(flags)}")
        
        results.append({
            'name': co['name'],
            'sector': co['sector'],
            'country': co['country'],
            'sources': len(src),
            'tech_signals': len(tech),
            'news': len(ws) if ws else 0,
            'composite': comp,
            'grade': grade['grade'],
            'ars': grade['score_100'],
            'flags': len(flags),
        })
        
        time.sleep(1)  # Rate limit politeness
        
    except Exception as e:
        print(f"  ERROR: {e}")
        results.append({'name': co['name'], 'sector': co['sector'], 'country': co['country'],
                        'sources': 0, 'tech_signals': 0, 'news': 0, 'composite': 0, 'grade': 'F', 'ars': 0, 'flags': 0})

print("\n" + "=" * 80)
print("BATCH RESULTS SUMMARY")
print("=" * 80)
print(f"\n{'Company':<20} {'Sector':<15} {'Country':<5} {'Src':<4} {'Tech':<5} {'News':<5} {'Score':<7} {'Grade':<6} {'ARS':<5}")
print("-" * 80)
for r in results:
    print(f"{r['name']:<20} {r['sector']:<15} {r['country']:<5} {r['sources']:<4} {r['tech_signals']:<5} {r['news']:<5} {r['composite']:<7.2f} {r['grade']:<6} {r['ars']:<5}")

print(f"\nTotal companies tested: {len(results)}")
print(f"Average sources found: {sum(r['sources'] for r in results)/len(results):.1f}")
print(f"Average composite: {sum(r['composite'] for r in results)/len(results):.2f}/5.0")
print(f"Average ARS: {sum(r['ars'] for r in results)/len(results):.0f}/100")
print(f"Companies with news: {sum(1 for r in results if r['news'] > 0)}/{len(results)}")
print(f"Companies with tech detected: {sum(1 for r in results if r['tech_signals'] > 0)}/{len(results)}")
