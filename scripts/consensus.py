#!/usr/bin/env python3
"""
Multi-crew consensus scoring + Elo-based strategy ranking + self-evaluation abort.

Week 3 implementation plan:
  3.1 — Run 2 parallel research crews, compare scores, flag disagreements >1.0
  3.2 — Track which research strategies produce best scores via Elo ranking
  3.3 — Abort early if company clearly not viable (kill criteria + red flags)

Pattern: AI-Supervisor consensus, RoboPhD Elo ranking, AutoResearch-RL self-evaluation
"""

import json, os, re, sys
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scoring import DIMS, WEIGHT_MAP, scan_red_flags, check_kill_criteria

BASE = os.path.join(os.path.dirname(__file__), '..')
HORECA_DIR = os.path.join(BASE, 'output', 'HORECA')


# --- 3.1: Multi-crew consensus scoring ---

def compute_consensus(crew_a_scores, crew_b_scores):
    """
    Compare scores from 2 research crews.
    Returns: consensus score, disagreements (dims with diff > 1.0), agreement %
    """
    consensus = {}
    disagreements = []
    total_dims = len(DIMS)
    agreeing_dims = 0

    for dim in DIMS:
        a = crew_a_scores.get(dim)
        b = crew_b_scores.get(dim)
        if a is not None and b is not None:
            diff = abs(a - b)
            if diff > 1.0:
                disagreements.append({
                    'dimension': dim,
                    'crew_a': a,
                    'crew_b': b,
                    'diff': diff,
                })
            else:
                agreeing_dims += 1
            consensus[dim] = round((a + b) / 2, 1)
        elif a is not None:
            consensus[dim] = a
        elif b is not None:
            consensus[dim] = b

    agreement_pct = round((agreeing_dims / total_dims) * 100, 1) if total_dims > 0 else 0
    return consensus, disagreements, agreement_pct


# --- 3.2: Elo-based research strategy ranking ---

class EloRanking:
    """
    Track which research strategies produce best scores.
    Each strategy gets an Elo rating. Strategies "play" matches against each other:
    the strategy that produces a score closer to John's ground truth wins.
    """

    def __init__(self, k_factor=32):
        self.ratings = {}  # strategy_name -> rating
        self.k = k_factor
        self.matches = []

    def get_rating(self, strategy):
        return self.ratings.get(strategy, 1500)

    def _expected_score(self, rating_a, rating_b):
        return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))

    def record_match(self, strategy_a, strategy_b, a_error, b_error):
        """Record a match between two strategies. Lower error wins."""
        if strategy_a not in self.ratings:
            self.ratings[strategy_a] = 1500
        if strategy_b not in self.ratings:
            self.ratings[strategy_b] = 1500

        ra = self.ratings[strategy_a]
        rb = self.ratings[strategy_b]
        ea = self._expected_score(ra, rb)
        eb = self._expected_score(rb, ra)

        # Lower error = win
        if a_error < b_error:
            sa, sb = 1.0, 0.0
        elif a_error > b_error:
            sa, sb = 0.0, 1.0
        else:
            sa, sb = 0.5, 0.5

        self.ratings[strategy_a] = ra + self.k * (sa - ea)
        self.ratings[strategy_b] = rb + self.k * (sb - eb)
        self.matches.append({
            'a': strategy_a, 'b': strategy_b,
            'a_error': a_error, 'b_error': b_error,
            'a_won': a_error < b_error,
        })

    def ranking_table(self):
        """Return sorted list of (strategy, rating, matches_played)."""
        match_counts = defaultdict(int)
        for m in self.matches:
            match_counts[m['a']] += 1
            match_counts[m['b']] += 1
        sorted_ratings = sorted(self.ratings.items(), key=lambda x: x[1], reverse=True)
        return [(s, r, match_counts.get(s, 0)) for s, r in sorted_ratings]

    def save(self, path=None):
        if path is None:
            path = os.path.join(HORECA_DIR, 'elo_rankings.json')
        with open(path, 'w') as f:
            json.dump({
                'ratings': self.ratings,
                'matches': self.matches[-100:],
                'ranking': self.ranking_table(),
                'updated_at': str(datetime.now()),
            }, f, indent=2)
        return path

    @classmethod
    def load(cls, path=None):
        if path is None:
            path = os.path.join(HORECA_DIR, 'elo_rankings.json')
        elo = cls()
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            elo.ratings = data.get('ratings', {})
            elo.matches = data.get('matches', [])
        return elo


# --- 3.3: Self-evaluation abort ---

def should_abort(company_name, enriched_data=None, dimensions=None):
    """
    Determine if research should abort early for this company.
    Returns (abort: bool, reason: str).
    """
    if dimensions:
        # Check kill criteria
        kills = check_kill_criteria(dimensions)
        if kills:
            reasons = [k['message'] for k in kills]
            return True, f"Kill criteria triggered: {'; '.join(reasons)}"

        # Check red flags — if 3+ critical flags, abort
        flags = scan_red_flags(dimensions)
        critical_flags = [f for f in flags if f['severity'] == 'critical']
        if len(critical_flags) >= 3:
            reasons = [f['message'] for f in critical_flags[:3]]
            return True, f"Too many critical red flags: {'; '.join(reasons)}"

    if enriched_data:
        website = enriched_data.get('website', {})
        if not website.get('website_reachable'):
            return True, "Website unreachable — cannot verify company exists"

        sources = enriched_data.get('sources_found', [])
        if len(sources) < 1:
            return True, "No data sources found — cannot score this company"

    return False, ""


def estimate_research_value(company_name, enriched_data=None):
    """
    Estimate whether this company is worth researching deeply.
    Returns score 0-100 (higher = more worth researching).
    """
    score = 50  # Neutral baseline

    if not enriched_data:
        return score

    website = enriched_data.get('website', {})
    tech_stack = website.get('tech_stack', [])
    sources = enriched_data.get('sources_found', [])
    web_search = enriched_data.get('web_search', [])

    # Positive signals
    if website.get('website_reachable'):
        score += 15
    if len(sources) >= 3:
        score += 10
    if len(tech_stack) >= 3:
        score += 10  # Real tech company, not a shell
    if web_search:
        score += 10  # News/social footprint
    if website.get('pricing', {}).get('found'):
        score += 5

    # Negative signals
    if not website.get('website_reachable'):
        score -= 30

    return max(0, min(100, score))


# --- Integrated consensus + abort pipeline ---

def run_consensus_check(company_name, crew_a_scores, crew_b_scores, enriched_data=None):
    """
    Full consensus check: compute consensus, check for abort, log results.
    """
    consensus, disagreements, agreement_pct = compute_consensus(crew_a_scores, crew_b_scores)
    abort, abort_reason = should_abort(company_name, enriched_data, consensus)
    value = estimate_research_value(company_name, enriched_data)

    result = {
        'company': company_name,
        'timestamp': str(datetime.now()),
        'consensus_scores': consensus,
        'agreement_pct': agreement_pct,
        'disagreements': disagreements,
        'should_abort': abort,
        'abort_reason': abort_reason,
        'research_value': value,
        'abort_threshold': 30,  # Abort if research_value < 30
    }

    # Save
    folder = company_name.lower().replace(' ', '-')
    out_dir = os.path.join(HORECA_DIR, folder)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'consensus.json')
    with open(path, 'w') as f:
        json.dump(result, f, indent=2)

    return result


if __name__ == '__main__':
    import sys

    # Test consensus
    crew_a = {'Ownership attractiveness': 4, 'Revenue scale fit': 4, 'Geographic fit': 5,
              'Tech stack modernity': 5, 'Customer lock-in': 5, 'Vertical depth': 5,
              'Integration potential': 5, 'Growth trajectory': 4}
    crew_b = {'Ownership attractiveness': 4, 'Revenue scale fit': 3, 'Geographic fit': 5,
              'Tech stack modernity': 5, 'Customer lock-in': 5, 'Vertical depth': 5,
              'Integration potential': 5, 'Growth trajectory': 4}

    result = run_consensus_check('Booking Experts', crew_a, crew_b)
    print(f"Consensus for {result['company']}:")
    print(f"  Agreement: {result['agreement_pct']}%")
    print(f"  Disagreements: {len(result['disagreements'])}")
    print(f"  Abort: {result['should_abort']} ({result['abort_reason']})")
    print(f"  Research value: {result['research_value']}/100")

    # Test Elo rankings
    print("\n--- Elo Rankings ---")
    elo = EloRanking()
    # Simulate strategy comparisons
    elo.record_match('playwright+wiki', 'stdlib+crunchbase', 0.04, 0.12)
    elo.record_match('crewai_deepseek', 'single_agent_gpt', 0.02, 0.31)
    elo.record_match('playwright+wiki', 'crewai_deepseek', 0.04, 0.02)
    elo.record_match('stdlib+crunchbase', 'single_agent_gpt', 0.12, 0.31)

    for strategy, rating, matches in elo.ranking_table():
        print(f"  {strategy:<30} Elo={rating:.0f} ({matches} matches)")

    path = elo.save()
    print(f"\n  Saved: {path}")
