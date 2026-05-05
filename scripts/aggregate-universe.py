#!/usr/bin/env python3
"""
Aggregate all company deep-analyses into a single JSON file (matching John's format).
Usage: python aggregate-universe.py <universe>
"""

import json, os, sys, re
from datetime import datetime

def main():
    if len(sys.argv) < 2:
        print("Usage: aggregate-universe.py <universe>")
        sys.exit(1)

    universe = sys.argv[1].upper()
    base_dir = os.path.join(os.path.dirname(__file__), '..', 'output', universe)
    data_dir = os.path.join(base_dir, 'Data')
    os.makedirs(data_dir, exist_ok=True)

    companies = []
    for d in sorted(os.listdir(base_dir)):
        dpath = os.path.join(base_dir, d)
        if not os.path.isdir(dpath) or d == 'Data':
            continue
        
        company = {
            'company_name': d,
            'folder': d,
            'country': '',
            'category': '',
            'status': 'Pending',
            'scorecard': None,
            'fundamentals': None,
            'history': None,
            'financial_growth': None,
            'research_date': None,
            'has_deep_analysis': False,
            'has_corporate_history': False,
            'has_financial_growth': False
        }

        # Check for deep analysis
        da_path = os.path.join(dpath, 'deep-analysis.md')
        if os.path.exists(da_path):
            company['has_deep_analysis'] = True
            company['status'] = 'Researched'
            # Parse score from the document
            with open(da_path) as f:
                content = f.read()
            score_match = re.search(r'\*\*Composite\*\*:\s*([\d.]+)\s*/\s*5\.0', content)
            if score_match:
                company['composite_score'] = float(score_match.group(1))

        ch_path = os.path.join(dpath, 'corporate-history.md')
        if os.path.exists(ch_path):
            company['has_corporate_history'] = True

        fg_path = os.path.join(dpath, 'financial-growth.md')
        if os.path.exists(fg_path):
            company['has_financial_growth'] = True

        companies.append(company)

    metadata = {
        'total': len(companies),
        'source_directory': base_dir,
        'generated_date': datetime.now().strftime("%Y-%m-%d"),
        'by_status': {}
    }
    for c in companies:
        s = c['status']
        metadata['by_status'][s] = metadata['by_status'].get(s, 0) + 1

    output = {
        'metadata': metadata,
        'companies': companies
    }

    json_path = os.path.join(data_dir, f'{universe.lower()}_data.json')
    with open(json_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Aggregated {len(companies)} companies in universe '{universe}'")
    print(f"  Statuses: {metadata['by_status']}")
    print(f"  JSON: {json_path}")

if __name__ == '__main__':
    main()
