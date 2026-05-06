#!/usr/bin/env python3
"""
PDF report generator — upgrades deal memos from markdown to professional PDF.
Uses pydfy for PDF generation with charts, tables, and branding.

Pattern: pydfy, zipreport, Carbone

Usage:
    python3 report_pdf.py "Booking Experts"
    python3 report_pdf.py --all
"""

import json, os, sys, re, logging
from datetime import datetime

logger = logging.getLogger(__name__)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scoring import DIMS, compute_composite, composite_to_grade, scan_red_flags, check_kill_criteria

BASE = os.path.join(os.path.dirname(__file__), '..')
HORECA_DIR = os.path.join(BASE, 'output', 'HORECA')


def load_company_data(company_name):
    """Load company data from deep-analysis and enriched JSON."""
    folder = company_name.lower().replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '')
    folder = folder.replace("'", '').replace('&', 'and').replace('--', '-').strip('-')
    
    da_path = os.path.join(HORECA_DIR, folder, 'deep-analysis.md')
    en_path = os.path.join(HORECA_DIR, folder, 'enriched.json')
    
    data = {
        'name': company_name,
        'folder': folder,
        'scores': {},
        'sources': [],
        'tech_stack': [],
        'web_search': [],
    }
    
    if os.path.exists(da_path):
        with open(da_path) as f:
            content = f.read()
        # Extract composite
        m = re.search(r'\*\*Composite\*\*:\s*([\d.]+)\s*/\s*5\.0', content)
        if m:
            data['composite'] = float(m.group(1))
        # Extract scores
        for dim in DIMS:
            p = r'\|\s*\d+\s*\|\s*' + re.escape(dim) + r'\s*\|\s*\w+\s*\|\s*([\d.]+)'
            m = re.search(p, content)
            if m:
                data['scores'][dim] = float(m.group(1))
    
    if os.path.exists(en_path):
        with open(en_path) as f:
            en = json.load(f)
        data['sources'] = en.get('sources_found', [])
        tech = en.get('website', {}).get('tech_stack', [])
        data['tech_stack'] = tech if tech else []
        ws = en.get('web_search', [])
        data['web_search'] = ws if ws else []
    
    return data


def generate_pdf(data):
    """Generate PDF report for a company. Returns path to PDF file."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    out_dir = os.path.join(HORECA_DIR, data['folder'])
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, 'deal-report.pdf')
    
    name = data['name']
    comp = data.get('composite', 0)
    grade = composite_to_grade(comp)
    scores = data.get('scores', {})
    
    # Create professional A4 report using matplotlib
    fig = plt.figure(figsize=(8.27, 11.69))  # A4 portrait
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Header
    plt.figtext(0.5, 0.96, f'M&A Deal Report — {name}', ha='center', fontsize=18, weight='bold')
    plt.figtext(0.5, 0.93, f'Generated: {datetime.now().strftime("%Y-%m-%d")} | SolStein M&A Pipeline', 
                ha='center', fontsize=9, color='gray')
    
    # Executive Summary
    plt.figtext(0.08, 0.89, 'Executive Summary', fontsize=13, weight='bold')
    ars = grade.get('score_100', 0)
    plt.figtext(0.08, 0.86, f'Composite Score: {comp:.2f}/5.0  |  Grade: {grade["grade"]}  |  ARS: {ars}/100  |  {grade["description"]}', 
                fontsize=10)
    plt.figtext(0.08, 0.83, f'Data Sources: {len(data.get("sources", []))}  |  Tech Signals: {len(data.get("tech_stack", []))}',
                fontsize=9, color='gray')
    
    # Scorecard chart
    ax_chart = fig.add_axes([0.08, 0.58, 0.84, 0.22])
    dims_short = ['Ownership', 'Revenue', 'Geo', 'Tech', 'Lock-in', 'Vertical', 'Integration', 'Growth']
    vals = [scores.get(d, 0) for d in DIMS]
    colors = ['#4CAF50' if v >= 4 else '#FFC107' if v >= 3 else '#F44336' for v in vals]
    bars = ax_chart.barh(dims_short, vals, color=colors)
    ax_chart.set_xlim(0, 5.5)
    ax_chart.axvline(x=3, color='gray', linestyle='--', alpha=0.3)
    ax_chart.set_xlabel('Score (1-5)')
    for i, v in enumerate(vals):
        ax_chart.text(v + 0.1, i, str(v), va='center')
    
    # Company Details
    plt.figtext(0.08, 0.54, 'Company Details', fontsize=13, weight='bold')
    details = [
        f'Website: bookingexperts.com',
        f'Tech Stack: {", ".join(data.get("tech_stack", [])[:6])}',
        f'GitHub: {data.get("github_repos", 0)} repos',
        f'Pricing: bookingexperts.com/pricing',
    ]
    for i, d in enumerate(details):
        plt.figtext(0.08, 0.51 - i*0.025, d, fontsize=9)
    
    # Score Details
    plt.figtext(0.08, 0.36, 'Dimension Details', fontsize=13, weight='bold')
    dim_descriptions = {
        'Ownership attractiveness': f'Score: {scores.get("Ownership attractiveness", "?")} — 1-5 scale',
        'Revenue scale fit': f'Score: {scores.get("Revenue scale fit", "?")} — 1-5 scale',
        'Geographic fit': f'Score: {scores.get("Geographic fit", "?")} — 1-5 scale',
    }
    for i, (dim, desc) in enumerate(dim_descriptions.items()):
        score = scores.get(dim, '?')
        plt.figtext(0.08, 0.33 - i*0.025, f'{dim}: {desc}', fontsize=9)
    
    # News/Web Search mentions
    ws = data.get('web_search', [])
    if ws:
        plt.figtext(0.08, 0.24, 'Recent Signals', fontsize=13, weight='bold')
        for i, s in enumerate(ws[:3]):
            plt.figtext(0.08, 0.21 - i*0.025, f'• {s["title"][:70]}', fontsize=8)
    
    plt.savefig(pdf_path, dpi=150, bbox_inches='tight', pad_inches=0.3)
    plt.close()
    print(f"  PDF generated: {pdf_path}")
    return pdf_path


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        count = 0
        for d in sorted(os.listdir(HORECA_DIR)):
            if os.path.isdir(os.path.join(HORECA_DIR, d)) and d != 'Data':
                data = load_company_data(d)
                if data.get('composite'):
                    generate_pdf(data)
                    count += 1
        print(f"\nGenerated {count} reports")
    else:
        name = sys.argv[1] if len(sys.argv) > 1 else 'Booking Experts'
        data = load_company_data(name)
        if data.get('composite'):
            generate_pdf(data)
        else:
            print(f"No scorecard found for {name}")
