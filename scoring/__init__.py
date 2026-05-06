#!/usr/bin/env python3
"""
Scoring module — all scoring logic in one place.
Consolidates: DIMS, weights, composite, grades, vetoes, red flags, kill criteria.
"""

DIMS = [
    'Ownership attractiveness',
    'Revenue scale fit',
    'Geographic fit',
    'Tech stack modernity',
    'Customer lock-in',
    'Vertical depth',
    'Integration potential',
    'Growth trajectory',
]

WEIGHTS = [3, 3, 3, 2, 2, 2, 1, 1]
WEIGHT_MAP = dict(zip(DIMS, WEIGHTS))

# --- Composite ---

def compute_composite(dimensions):
    total = sum(WEIGHT_MAP.values())
    score = sum(dimensions.get(d, 0) * WEIGHT_MAP.get(d, 2) for d in DIMS)
    return score / total if total > 0 else 0


def validate_dimensions(dimensions):
    """Check that all DIMS are present and within valid range 1-5."""
    errors = []
    for d in DIMS:
        v = dimensions.get(d)
        if v is None:
            errors.append({'dimension': d, 'error': 'missing'})
        elif not isinstance(v, (int, float)):
            errors.append({'dimension': d, 'error': f'invalid type: {type(v).__name__}'})
        elif v < 1 or v > 5:
            errors.append({'dimension': d, 'error': f'out of range: {v}'})
    return errors


# --- Grades (A-F + ARS 0-100) ---

GRADE_TABLE = [
    (4.5, 5.0, 'A', 'Strong acquisition candidate'),
    (3.5, 4.49, 'B', 'Viable with noted risks'),
    (2.5, 3.49, 'C', 'Significant concerns requiring investigation'),
    (1.5, 2.49, 'D', 'Major risks present'),
    (0.0, 1.49, 'F', 'Critical issues — likely not viable'),
]


def composite_to_readiness(composite):
    if composite is None:
        return None
    return round((max(0.0, min(5.0, composite)) / 5.0) * 100)


def composite_to_grade(composite):
    if composite is None:
        return {'grade': 'N/A', 'description': 'No score available', 'score_100': None}
    for lo, hi, grade, desc in GRADE_TABLE:
        if lo <= composite <= hi:
            return {'grade': grade, 'description': desc, 'score_100': composite_to_readiness(composite)}
    return {'grade': 'F', 'description': 'Critical issues', 'score_100': composite_to_readiness(composite)}


# --- Veto conditions ---

def _has_pe_owner(val):
    low = str(val).lower()
    if 'no pe' in low or 'private; no' in low or 'private,' in low:
        return False
    return any(kw in low for kw in ['pe-backed', 'pe-owned', 'private equity', 'pe)',
        'pollen street', 'hg (majority)', 'ta associates', 'advent international',
        'arcadea', 'marlin equity', 'insight partners', 'bain capital',
        'goldman sachs', 'nonius', 'psg equity'])


def _has_vc_backer(val):
    low = str(val).lower()
    if 'no vc' in low or 'no external' in low:
        return False
    return any(kw in low for kw in ['vc-backed', 'venture capital', 'multi-investor vc',
        'institutional vc', 'vc/growth', 'series a', 'series b', 'series c', 'series d',
        'volta ventures', 'newion', 'kinnevik', 'coatue', 'battery ventures',
        'tiger global', 'growth equity', 'eight roads', 'jigsaw'])


VETOES = [
    (_has_pe_owner, 'ownership', 'Ownership attractiveness', 1, 'PE-backed: not acquirable at SolStein scale'),
    (_has_vc_backer, 'ownership', 'Ownership attractiveness', 2, 'VC-backed: cap table complexity'),
    (lambda v: v == 'US', 'country', 'Geographic fit', 1, 'US-headquartered: outside Benelux thesis'),
    (lambda v: 'acquired' in str(v).lower() and 'door' in str(v).lower(), 'ownership', 'Ownership attractiveness', 1, 'Already acquired'),
    (lambda v: v == 'Off-Market', 'status', 'Ownership attractiveness', 1, 'Off-market: already acquired or PE-owned'),
]


def apply_vetoes(company_info, dimensions):
    changes = []
    for trigger_fn, trigger_field, dim, score, rationale in VETOES:
        value = str(company_info.get(trigger_field, '') or '')
        if trigger_fn(value):
            old = dimensions.get(dim)
            if old != score:
                dimensions[dim] = score
                changes.append({'dimension': dim, 'old_score': old, 'new_score': score, 'rationale': rationale})
    return changes


# --- Red flags ---

RED_FLAGS = [
    {'name': 'customer_concentration', 'severity': 'critical', 'check': lambda d: d.get('Customer lock-in', 5) <= 1,
     'message': 'No customer lock-in — likely high churn'},
    {'name': 'revenue_too_small', 'severity': 'critical', 'check': lambda d: d.get('Revenue scale fit', 3) <= 1,
     'message': 'Revenue too small (<€500K est.)'},
    {'name': 'wrong_geography', 'severity': 'warning', 'check': lambda d: d.get('Geographic fit', 3) <= 1,
     'message': 'Wrong geography — outside Benelux thesis'},
    {'name': 'ownership_blocked', 'severity': 'critical', 'check': lambda d: d.get('Ownership attractiveness', 5) <= 1,
     'message': 'PE-owned or off-market — not acquirable'},
    {'name': 'tech_debt', 'severity': 'warning', 'check': lambda d: d.get('Tech stack modernity', 3) <= 2,
     'message': 'Legacy tech stack — modernization risk'},
    {'name': 'low_growth', 'severity': 'warning', 'check': lambda d: d.get('Growth trajectory', 3) <= 1,
     'message': 'No growth signals — stagnant or declining'},
]


def scan_red_flags(dimensions):
    return [f for f in RED_FLAGS if f['check'](dimensions)]


# --- Kill criteria ---

KILL_CRITERIA = [
    {'name': 'pe_owned', 'condition': lambda d, i: d.get('Ownership attractiveness', 5) <= 1 and 'PE' in str(i.get('ownership', '')),
     'message': 'PE-owned: SolStein cannot outbid PE fund'},
    {'name': 'wrong_market', 'condition': lambda d, i: d.get('Geographic fit', 3) <= 1 and d.get('Revenue scale fit', 3) <= 1,
     'message': 'Wrong geography AND small revenue'},
    {'name': 'no_moat', 'condition': lambda d, i: d.get('Customer lock-in', 5) <= 2 and d.get('Vertical depth', 5) <= 2,
     'message': 'No competitive moat'},
]


def check_kill_criteria(dimensions, info=None):
    if info is None:
        info = {}
    return [k for k in KILL_CRITERIA if k['condition'](dimensions, info)]
