#!/usr/bin/env python3
"""
Grade tiers and score normalization for M&A pipeline.
Maps our 1-5 composite to Acquisition Readiness Score (0-100) and letter grades.
Pattern from: m-and-a-target-intelligence-mcp, oss-investment-scorecard
"""

# Grade thresholds: composite score (1-5 scale) -> letter grade
GRADE_TABLE = [
    (4.5, 5.0, 'A', 'Strong acquisition candidate'),
    (3.5, 4.49, 'B', 'Viable with noted risks'),
    (2.5, 3.49, 'C', 'Significant concerns requiring investigation'),
    (1.5, 2.49, 'D', 'Major risks present'),
    (0.0, 1.49, 'F', 'Critical issues — likely not viable'),
]


def composite_to_readiness_score(composite):
    """Map our 1-5 composite to 0-100 Acquisition Readiness Score."""
    if composite is None:
        return None
    composite = max(0.0, min(5.0, composite))
    return round((composite / 5.0) * 100)


def composite_to_grade(composite):
    """Map composite score to letter grade + description."""
    if composite is None:
        return {'grade': 'N/A', 'description': 'No score available', 'score_100': None}
    for lo, hi, grade, desc in GRADE_TABLE:
        if lo <= composite <= hi:
            return {
                'grade': grade,
                'description': desc,
                'score_100': composite_to_readiness_score(composite),
            }
    return {'grade': 'F', 'description': 'Critical issues', 'score_100': composite_to_readiness_score(composite)}


def format_grade_badge(grade_info):
    """Return colored/emoji badge for a grade."""
    badges = {
        'A': '🟢 A — Strong acquisition candidate',
        'B': '🟡 B — Viable with noted risks',
        'C': '🟠 C — Significant concerns',
        'D': '🔴 D — Major risks present',
        'F': '⚫ F — Critical issues, not viable',
        'N/A': '⚪ N/A — No score',
    }
    return badges.get(grade_info.get('grade', 'N/A'), grade_info.get('grade', 'N/A'))
