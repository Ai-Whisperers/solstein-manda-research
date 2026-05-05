#!/usr/bin/env python3
"""Scoring rubric with veto rules and dimension-level validation."""

DIMS = [
    'Ownership attractiveness',
    'Revenue scale fit',
    'Geographic fit',
    'Tech stack modernity',
    'Customer lock-in',
    'Vertical depth',
    'Integration potential',
    'Growth trajectory'
]

WEIGHTS = [3, 3, 3, 2, 2, 2, 1, 1]
WEIGHT_MAP = dict(zip(DIMS, WEIGHTS))

# Veto conditions: if trigger matches, force dimension score
# Format: (trigger_field, trigger_function, dimension, forced_score, rationale)
# trigger_function(value) returns True if veto should fire
# Using functions instead of patterns to avoid substring false positives (e.g. "PE" matching "Private")

def _has_pe_owner(val):
    """Detect PE ownership — must NOT match 'Private' or 'no PE'."""
    low = val.lower()
    if 'no pe' in low or 'not a pe' in low or 'private; no' in low or 'private,' in low:
        return False
    pe_keywords = [
        'pe-backed', 'pe-owned', 'private equity', 'pe)',
        'pollen street', 'hg (majority)', 'ta associates', 'advent international',
        'arcadea', 'marlin equity', 'insight partners', 'bain capital',
        'goldman sachs', 'nonius', 'psg equity',
    ]
    return any(kw in low for kw in pe_keywords)


def _has_vc_backer(val):
    """Detect VC backing."""
    low = val.lower()
    if 'no vc' in low or 'no external' in low:
        return False
    vc_keywords = [
        'vc-backed', 'venture capital', 'multi-investor vc',
        'institutional vc', 'vc/growth',
        'series a', 'series b', 'series c', 'series d',
        'volta ventures', 'newion', 'kinnevik', 'coatue',
        'battery ventures', 'tiger global', 'growth equity',
        'eight roads', 'jigsaw',
    ]
    return any(kw in low for kw in vc_keywords)


VETOES = [
    # PE ownership → Ownership attractiveness = 1 (not acquirable)
    (_has_pe_owner, 'ownership', 'Ownership attractiveness', 1,
     'PE-backed: not acquirable at SolStein scale'),

    # VC-backed → Ownership attractiveness = 2 (cap table complexity)
    (_has_vc_backer, 'ownership', 'Ownership attractiveness', 2,
     'VC-backed: cap table complexity reduces acquisition feasibility'),

    # US HQ → Geographic fit = 1
    (lambda v: v == 'US', 'country', 'Geographic fit', 1,
     'US-headquartered: outside Benelux thesis geography'),

    # Acquired by strategic → Ownership = 1
    (lambda v: 'acquired' in v.lower() and ('door' in v.lower() or 'dash' in v.lower()), 'ownership', 'Ownership attractiveness', 1,
     'Already acquired: not available for acquisition'),

        # Off-market status → Ownership = 1
    (lambda v: v == 'Off-Market', 'status', 'Ownership attractiveness', 1,
     'Off-market: already acquired or PE-owned'),
]


# --- Red Flag Scanner (from due-diligence-agents pattern) ---

RED_FLAGS = [
    {'name': 'customer_concentration', 'severity': 'critical',
     'check': lambda d: d.get('Customer lock-in', 5) <= 1,
     'message': 'No customer lock-in — likely high churn, no switching costs'},
    {'name': 'revenue_too_small', 'severity': 'critical',
     'check': lambda d: d.get('Revenue scale fit', 3) <= 1,
     'message': 'Revenue too small (<€500K est.) — below minimum target'},
    {'name': 'wrong_geography', 'severity': 'warning',
     'check': lambda d: d.get('Geographic fit', 3) <= 1,
     'message': 'Wrong geography — outside Benelux thesis'},
    {'name': 'ownership_blocked', 'severity': 'critical',
     'check': lambda d: d.get('Ownership attractiveness', 5) <= 1,
     'message': 'PE-owned or off-market — not acquirable'},
    {'name': 'tech_debt', 'severity': 'warning',
     'check': lambda d: d.get('Tech stack modernity', 3) <= 2,
     'message': 'Legacy tech stack — modernization risk'},
    {'name': 'low_growth', 'severity': 'warning',
     'check': lambda d: d.get('Growth trajectory', 3) <= 1,
     'message': 'No growth signals — stagnant or declining'},
]


def scan_red_flags(dimensions):
    """Scan dimensions for red flags. Returns list of active flags."""
    flags = []
    for flag in RED_FLAGS:
        if flag['check'](dimensions):
            flags.append({
                'name': flag['name'],
                'severity': flag['severity'],
                'message': flag['message'],
            })
    return flags


# --- Kill Criteria (from M&A Playbook pattern) ---

KILL_CRITERIA = [
    {'name': 'pe_owned', 'condition': lambda d, i: d.get('Ownership attractiveness', 5) <= 1 and 'PE' in str(i.get('ownership', '')),
     'message': 'PE-owned: SolStein cannot outbid PE fund'},
    {'name': 'wrong_market', 'condition': lambda d, i: d.get('Geographic fit', 3) <= 1 and d.get('Revenue scale fit', 3) <= 1,
     'message': 'Wrong geography AND small revenue — not worth pursuing'},
    {'name': 'no_moat', 'condition': lambda d, i: d.get('Customer lock-in', 5) <= 2 and d.get('Vertical depth', 5) <= 2,
     'message': 'No competitive moat — low lock-in AND shallow vertical depth'},
]


def check_kill_criteria(dimensions, info=None):
    """Check if any kill criteria are met. Returns list of triggered kills."""
    if info is None:
        info = {}
    kills = []
    for criterion in KILL_CRITERIA:
        if criterion['condition'](dimensions, info):
            kills.append({
                'name': criterion['name'],
                'message': criterion['message'],
            })
    return kills


def apply_vetoes(company_info, dimensions):
    """Apply veto rules to dimension scores. Returns list of changes made."""
    changes = []
    for trigger_fn, trigger_field, dim, forced_score, rationale in VETOES:
        value = str(company_info.get(trigger_field, '') or '')
        if trigger_fn(value):
            old_score = dimensions.get(dim)
            if old_score != forced_score:
                dimensions[dim] = forced_score
                changes.append({
                    'dimension': dim,
                    'old_score': old_score,
                    'new_score': forced_score,
                    'rationale': rationale,
                    'trigger': f'{trigger_field}="{value}"'
                })
    return changes


def compute_composite(dimensions):
    """Compute weighted composite from dimension scores."""
    total_w = sum(WEIGHT_MAP.values())
    score = 0
    for d in DIMS:
        s = dimensions.get(d, 0)
        if s is None:
            s = 0
        score += s * WEIGHT_MAP[d]
    return score / total_w if total_w > 0 else 0


def validate_dimensions(our_dims, john_dims, threshold=0.5):
    """Validate dimension-level accuracy. Returns errors list."""
    errors = []
    for dim in DIMS:
        our = our_dims.get(dim)
        john = john_dims.get(dim)
        if our is not None and john is not None:
            err = abs(our - john)
            if err > threshold:
                errors.append({
                    'dimension': dim,
                    'our_score': our,
                    'john_score': john,
                    'error': err
                })
    return errors


def format_veto_report(changes):
    """Format veto changes for display."""
    if not changes:
        return "  No vetoes triggered"
    lines = []
    for c in changes:
        lines.append(f"  VETO: {c['dimension']}: {c['old_score']} → {c['new_score']} ({c['rationale']})")
        lines.append(f"        Trigger: {c['trigger']}")
    return '\n'.join(lines)
