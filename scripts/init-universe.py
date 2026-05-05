#!/usr/bin/env python3
"""
Initialize a new universe for the SolStein M&A Research Pipeline.

Usage:
    python3 init-universe.py <name> <csv_path>

The CSV must have columns: name,category,country,description
"""

import csv, json, os, sys
from datetime import datetime

def main():
    if len(sys.argv) < 2:
        print("Usage: init-universe.py <name> [csv_path]")
        print("  If csv_path omitted, reads from universes/<name>.csv")
        sys.exit(1)

    name = sys.argv[1]
    if len(sys.argv) >= 3:
        csv_path = sys.argv[2]
    else:
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'universes', f'{name}.csv')

    if not os.path.exists(csv_path):
        print(f"ERROR: CSV not found: {csv_path}")
        sys.exit(1)

    base_dir = os.path.join(os.path.dirname(__file__), '..', 'output', name.upper())
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'Data'), exist_ok=True)

    # Read CSV
    companies = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append(row)

    # Create company folders
    for c in companies:
        folder_name = c['name'].lower().replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '')
        c['folder'] = folder_name
        company_dir = os.path.join(base_dir, folder_name)
        os.makedirs(company_dir, exist_ok=True)
        # Create stub company info file
        with open(os.path.join(company_dir, f'{folder_name}.md'), 'w') as f:
            f.write(f"""# {c['name']}

- **Category**: {c['category']}
- **Country**: {c['country']}
- **Description**: {c['description']}
- **Status**: Pending
- **Research date**: —
""")

    # Generate JSON skeleton
    metadata = {
        "total": len(companies),
        "source_directory": base_dir,
        "generated_date": datetime.now().strftime("%Y-%m-%d"),
        "by_status": {"Pending": len(companies)}
    }

    data = {
        "metadata": metadata,
        "companies": [{
            "company_name": c['name'],
            "folder": c['folder'],
            "country": c['country'],
            "category": c['category'],
            "status": "Pending",
            "scorecard": None,
            "fundamentals": None,
            "history": None,
            "financial_growth": None,
            "research_date": None,
            "has_deep_analysis": False,
            "has_corporate_history": False,
            "has_financial_growth": False
        } for c in companies]
    }

    json_path = os.path.join(base_dir, 'Data', f'{name}_data.json')
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

    # CSV for easy viewing
    csv_out_path = os.path.join(base_dir, 'Data', f'{name}_companies.csv')
    with open(csv_out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name','category','country','description','folder','status'])
        writer.writeheader()
        for c in companies:
            writer.writerow(c)

    print(f"Initialized universe '{name}' with {len(companies)} companies")
    print(f"  Output: {base_dir}")
    print(f"  JSON:   {json_path}")
    print(f"  CSV:    {csv_out_path}")

if __name__ == '__main__':
    main()
