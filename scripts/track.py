#!/usr/bin/env python3
"""
Experiment tracking database + deal-breaker detection + unified validation.
Replaces the flat results.tsv with a proper SQLite database.

Usage:
    python3 track.py init              # Create/init the database
    python3 track.py log <args>        # Log an experiment result
    python3 track.py report            # Print full validation report
    python3 track.py dashboard         # Print dashboard summary
"""

import json, os, re, sqlite3, sys, csv
from datetime import datetime

BASE = os.path.join(os.path.dirname(__file__), '..')
DB_PATH = os.path.join(BASE, 'output', 'HORECA', 'experiments.db')
JOHN_JSON = os.path.join(BASE, 'archive', 'john-original', 'horeca_json', 'horeca_data.json')
HORECA_DIR = os.path.join(BASE, 'output', 'HORECA')

DIMS = ['Ownership attractiveness', 'Revenue scale fit', 'Geographic fit',
        'Tech stack modernity', 'Customer lock-in', 'Vertical depth',
        'Integration potential', 'Growth trajectory']
DIM_SHORT = ['ownership', 'revenue', 'geo', 'tech', 'lockin', 'vertical', 'integration', 'growth']
WEIGHTS = [3, 3, 3, 2, 2, 2, 1, 1]

SCHEMA = '''
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    company TEXT NOT NULL,
    universe TEXT NOT NULL DEFAULT 'HORECA',
    experiment_num INTEGER NOT NULL DEFAULT 1,
    ownership REAL, revenue REAL, geo REAL, tech REAL,
    lockin REAL, vertical REAL, integration REAL, growth REAL,
    composite REAL,
    john_composite REAL,
    composite_error REAL,
    dim_max_error REAL,
    deal_breakers TEXT,
    kept INTEGER NOT NULL DEFAULT 0,
    confidence TEXT,
    notes TEXT,
    UNIQUE(company, experiment_num)
);

CREATE TABLE IF NOT EXISTS deal_breakers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    breaker_type TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'warning',
    detected_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_experiments_company ON experiments(company);
CREATE INDEX IF NOT EXISTS idx_experiments_composite_error ON experiments(composite_error);
'''


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_PATH}")


def detect_deal_breakers(company_info, dimensions, john_composite=None):
    """Detect deal breakers from company data + dimension scores."""
    breakers = []
    own = dimensions.get('Ownership attractiveness', 5)
    rev = dimensions.get('Revenue scale fit', 3)
    geo = dimensions.get('Geographic fit', 3)
    
    # PE-owned → not acquirable
    if own <= 1:
        breakers.append(('ownership_blocker', 'PE-owned or off-market: not acquirable at SolStein scale', 'critical'))
    
    # Revenue too small
    if rev <= 1:
        breakers.append(('revenue_too_small', 'Revenue fit score 1: ARR likely below €500K', 'warning'))
    
    # Wrong geography
    if geo <= 1:
        breakers.append(('wrong_geography', 'Geographic fit score 1: outside Benelux thesis', 'warning'))
    
    # Composite is low overall
    if john_composite and john_composite < 2.0:
        breakers.append(('low_quality', f'John composite score {john_composite:.1f}: low overall attractiveness', 'info'))
    
    return breakers


def log_experiment(company, dims, john_comp, experiment_num=1, confidence='', notes=''):
    """Log a single experiment result."""
    conn = sqlite3.connect(DB_PATH)
    
    comp = sum(dims[d] * w for d, w in zip(DIMS, WEIGHTS)) / sum(WEIGHTS)
    comp_err = abs(comp - john_comp) if john_comp else 999
    dim_errs = []
    
    # Read John's dims for comparison
    from rubric import apply_vetoes
    john_data = _load_john()
    if company in john_data:
        jd = john_data[company].get('dims', {})
        dim_errs = [abs(dims.get(d, 0) - jd.get(d, 0)) for d in DIMS]
    
    dim_max = max(dim_errs) if dim_errs else 0
    kept = 1 if comp_err <= 0.5 and dim_max <= 1.0 else 0
    
    # Detect deal breakers
    info = {'ownership': '', 'country': '', 'status': ''}
    breakers = detect_deal_breakers(info, dims)
    
    conn.execute('''
        INSERT OR REPLACE INTO experiments
        (timestamp, company, experiment_num, ownership, revenue, geo, tech,
         lockin, vertical, integration, growth, composite, john_composite,
         composite_error, dim_max_error, deal_breakers, kept, confidence, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(), company, experiment_num,
        dims.get('Ownership attractiveness'), dims.get('Revenue scale fit'),
        dims.get('Geographic fit'), dims.get('Tech stack modernity'),
        dims.get('Customer lock-in'), dims.get('Vertical depth'),
        dims.get('Integration potential'), dims.get('Growth trajectory'),
        round(comp, 2), round(john_comp, 2) if john_comp else None,
        round(comp_err, 4), round(dim_max, 2),
        json.dumps(breakers) if breakers else None,
        kept, confidence, notes
    ))
    
    conn.commit()
    conn.close()
    return comp_err <= 0.5 and dim_max <= 1.0


def _load_john():
    """Load John's reference data."""
    result = {}
    folder_map = {}
    with open(JOHN_JSON) as f:
        data = json.load(f)
    for c in data['companies']:
        name = c['company_name']
        folder = name.lower().replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '')
        folder = folder.replace("'", '').replace('&', 'and').replace('--', '-').strip('-')
        folder_map[folder] = name
        sc = c.get('scorecard')
        if sc and sc.get('composite_score') is not None:
            dims_raw = sc.get('dimensions', {})
            dims = {}
            for d in DIMS:
                v = dims_raw.get(d, {})
                dims[d] = v.get('score') if isinstance(v, dict) else v
            result[name] = {'composite': sc['composite_score'], 'dims': dims}
    return result, folder_map


def generate_report():
    """Generate comprehensive report from database + current scorecards."""
    john_data, folder_map = _load_john()
    conn = sqlite3.connect(DB_PATH)
    
    total = 0
    comp_pass = 0
    dim_pass = 0
    all_breakers = []
    
    for d in sorted(os.listdir(HORECA_DIR)):
        dp = os.path.join(HORECA_DIR, d)
        if not os.path.isdir(dp) or d == 'Data':
            continue
        jn = folder_map.get(d)
        if not jn:
            continue
        
        da = os.path.join(dp, 'deep-analysis.md')
        if not os.path.exists(da):
            continue
        with open(da) as f:
            content = f.read()
        
        comp_match = re.search(r'\*\*Composite\*\*:\s*([\d.]+)\s*/\s*5\.0', content)
        our_comp = float(comp_match.group(1)) if comp_match else None
        
        john = john_data.get(jn, {})
        jc = john.get('composite')
        jd = john.get('dims', {})
        
        comp_err = abs(our_comp - jc) if our_comp and jc else 999
        
        dim_errs = {}
        for dim in DIMS:
            pattern = r'\|\s*\d+\s*\|\s*' + re.escape(dim) + r'\s*\|\s*\w+\s*\|\s*([\d.]+)'
            m = re.search(pattern, content)
            our_s = float(m.group(1)) if m else None
            john_s = jd.get(dim)
            if our_s is not None and john_s is not None:
                dim_errs[dim] = abs(our_s - john_s)
        
        comp_ok = comp_err <= 0.5
        dim_ok = all(e <= 1.0 for e in dim_errs.values()) if dim_errs else True
        
        total += 1
        if comp_ok:
            comp_pass += 1
        if dim_ok:
            dim_pass += 1
        
        if not comp_ok or not dim_ok:
            print(f"  FAIL: {jn:<40} comp_err={comp_err:.2f} dim_max={max(dim_errs.values()) if dim_errs else 0:.1f}")
        
        # Log to DB if not already
        existing = conn.execute('SELECT COUNT(*) FROM experiments WHERE company=?', (jn,)).fetchone()[0]
        if existing == 0:
            our_dims = {}
            for dim in DIMS:
                pattern = r'\|\s*\d+\s*\|\s*' + re.escape(dim) + r'\s*\|\s*\w+\s*\|\s*([\d.]+)'
                m = re.search(pattern, content)
                if m:
                    our_dims[dim] = float(m.group(1))
            if our_dims and len(our_dims) >= 8 and jc:
                log_experiment(jn, our_dims, jc)
    
    conn.close()
    
    print(f"\n{'='*60}")
    print("FINAL VALIDATION REPORT")
    print(f"{'='*60}")
    print(f"Total: {total}")
    print(f"Composite pass (err≤0.5): {comp_pass}/{total}")
    print(f"Dimension pass (all err≤1.0): {dim_pass}/{total}")
    
    # Summary stats from DB
    conn = sqlite3.connect(DB_PATH)
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total,
            ROUND(AVG(composite_error), 4) as avg_err,
            ROUND(MAX(composite_error), 4) as max_err,
            ROUND(MIN(composite_error), 4) as min_err,
            SUM(kept) as passed
        FROM experiments
    ''').fetchone()
    conn.close()
    
    if stats:
        print(f"\nDB stats: {stats[0]} experiments, avg_err={stats[1]}, max_err={stats[2]}, passed={stats[3]}")
    
    print(f"\nDeal breakers detected: {len(all_breakers)}")


def print_dashboard():
    """Compact one-line dashboard."""
    conn = sqlite3.connect(DB_PATH)
    
    total = conn.execute('SELECT COUNT(*) FROM experiments').fetchone()[0]
    passed = conn.execute('SELECT COUNT(*) FROM experiments WHERE kept=1').fetchone()[0]
    avg_err = conn.execute('SELECT ROUND(AVG(composite_error), 4) FROM experiments').fetchone()[0]
    max_err = conn.execute('SELECT ROUND(MAX(composite_error), 4) FROM experiments').fetchone()[0]
    
    top = conn.execute('''
        SELECT company, composite, john_composite, composite_error
        FROM experiments ORDER BY composite DESC LIMIT 5
    ''').fetchall()
    
    worst = conn.execute('''
        SELECT company, composite, john_composite, composite_error
        FROM experiments ORDER BY composite_error DESC LIMIT 3
    ''').fetchall()
    
    conn.close()
    
    print(f"[DB] {total} experiments | {passed} passed | avg_err={avg_err} | max_err={max_err}")
    print(f"[Top 5] " + ', '.join(f"{r[0]}={r[1]}" for r in top))
    if worst and worst[0][3] > 0:
        print(f"[Worst] " + ', '.join(f"{r[0]} err={r[3]}" for r in worst))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: track.py <init|report|dashboard>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == 'init':
        init_db()
    elif cmd == 'report':
        generate_report()
    elif cmd == 'dashboard':
        print_dashboard()
    else:
        print(f"Unknown command: {cmd}")
