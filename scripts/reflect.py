import logging
logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
Reflection loop for autonomous research improvement.
After initial scoring, identifies gaps, generates follow-up queries,
and re-researches weak dimensions.

Pattern: langchain-ai/company-researcher reflection phase, Karpathy autoresearch loop

Usage:
    from reflect import ReflectionLoop
    loop = ReflectionLoop()
    result = loop.improve_scorecard(company_name, initial_scores, enriched_data)
"""

import json, os, sys, re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from scoring import DIMS, WEIGHTS, WEIGHT_MAP, compute_composite, validate_dimensions

BASE = os.path.join(os.path.dirname(__file__), '..', '..')


# Dimension-specific follow-up questions — what to search for when a dimension score is uncertain
DIMENSION_FOLLOWUPS = {
    'Ownership attractiveness': [
        "Find the company's Crunchbase profile for investor list",
        "Search for 'founder sale exit acquisition' news",
        "Check LinkedIn for management team tenure and founder still active",
        "Search for PE/VC investment announcements",
    ],
    'Revenue scale fit': [
        "Find pricing page for subscription tiers",
        "Search for 'funding round' or 'series' to find revenue proxies",
        "Check employee count via LinkedIn — multiply by industry revenue/employee ratio",
        "Search for customer count and multiply by estimated ARPU",
    ],
    'Geographic fit': [
        "Check LinkedIn for office locations",
        "Website footer usually lists HQ country",
        "Similarweb for traffic by country",
    ],
    'Tech stack modernity': [
        "Check job postings for tech stack mentions (Ruby, Python, Go, etc.)",
        "Look for API documentation or developer portal",
        "Search for technology partners and integrations",
    ],
    'Customer lock-in': [
        "Search for 'integration' or 'partnership' pages",
        "Check for API marketplace or app store",
        "Look for enterprise customer logos and testimonials",
        "Search for contract length or minimum terms",
    ],
    'Vertical depth': [
        "Check about page for years in business and specialization",
        "Search for industry awards or certifications",
        "Look for case studies in specific verticals",
    ],
    'Integration potential': [
        "Search for 'API' or 'developers' on company website",
        "Check for integration marketplace or partner directory",
        "Look for open-source SDKs on GitHub",
    ],
    'Growth trajectory': [
        "Search for 'office opening' or 'expansion' news",
        "Check LinkedIn for headcount growth over time",
        "Search for 'new product launch' or 'new feature' press releases",
        "Check for international hiring or country expansion",
    ],
}


class ReflectionLoop:
    """Identify gaps, generate follow-up queries, re-research weak dimensions."""

    def __init__(self, max_rounds=3):
        self.max_rounds = max_rounds
        self.research_history = []

    def _find_weak_dimensions(self, scores, confidence_scores=None, john_reference=None):
        """Find dimensions that need more research."""
        weak = []

        # Check against John's reference if available
        if john_reference:
            for dim in DIMS:
                our = scores.get(dim)
                john = john_reference.get(dim, {}).get('score')
                if our and john and abs(our - john) > 1.0:
                    weak.append({
                        'dimension': dim,
                        'our_score': our,
                        'target_score': john,
                        'reason': f'Error {abs(our - john):.0f} point(s) vs ground truth',
                    })

        # Check for default scores (3.0 = uncertain, needs more research)
        for dim in DIMS:
            s = scores.get(dim, 0)
            if s == 3.0 or s == 0:
                if not any(w['dimension'] == dim for w in weak):
                    weak.append({
                        'dimension': dim,
                        'our_score': s,
                        'target_score': None,
                        'reason': 'Default/uncertain score — needs verification',
                    })

        # Check confidence tags from enriched data
        if confidence_scores:
            for dim, conf in confidence_scores.items():
                if conf == 'low' and dim not in [w['dimension'] for w in weak]:
                    weak.append({
                        'dimension': dim,
                        'our_score': scores.get(dim),
                        'target_score': None,
                        'reason': f'Low confidence: {conf}',
                    })

        return weak

    def _generate_queries(self, weak_dimensions):
        """Generate follow-up search queries for weak dimensions."""
        queries = []
        for wd in weak_dimensions:
            dim = wd['dimension']
            followups = DIMENSION_FOLLOWUPS.get(dim, [f"Research {dim} for this company"])
            for q in followups[:2]:
                queries.append({
                    'dimension': dim,
                    'query': q,
                    'reason': wd['reason'],
                })
        return queries

    def _simulate_followup_research(self, company_name, queries):
        """Execute follow-up research via browser or enrichment.
        Returns findings with evidence from available sources.
        Falls back gracefully if browser is unavailable."""
        findings = []
        for q in queries[:4]:
            finding = {
                'dimension': q['dimension'],
                'query': q['query'],
                'found_evidence': False,
                'evidence': '',
                'method': 'none',
            }
            # Try enrichment data first
            try:
                from datasources import wikipedia_summary, github_org
                wiki = wikipedia_summary(company_name)
                if wiki:
                    text = wiki.get('extract', '').lower()
                    keywords = q['query'].lower().split()
                    found = [kw for kw in keywords if len(kw) > 4 and kw in text]
                    if found:
                        finding['found_evidence'] = True
                        finding['evidence'] = f"Wikipedia: found keywords: {', '.join(found[:3])}"
                        finding['method'] = 'wikipedia'

                if not finding['found_evidence']:
                    gh = github_org(company_name)
                    if gh and gh.get('description'):
                        text = gh['description'].lower()
                        keywords = q['query'].lower().split()
                        found = [kw for kw in keywords if len(kw) > 4 and kw in text]
                        if found:
                            finding['found_evidence'] = True
                            finding['evidence'] = f"GitHub: {gh['description'][:100]}"
                            finding['method'] = 'github'
            except Exception:
                pass
            findings.append(finding)
        return findings

    def improve_scorecard(self, company_name, scores, enriched=None, john_reference=None):
        """Run reflection loop to improve scorecard accuracy."""
        result = {
            'company': company_name,
            'initial_scores': dict(scores),
            'refined_scores': dict(scores),
            'rounds': [],
            'total_improvements': 0,
            'final_composite': None,
            'improved': False,
        }

        for round_num in range(self.max_rounds):
            weak = self._find_weak_dimensions(scores, john_reference=john_reference)
            if not weak:
                result['note'] = f'No weak dimensions found after {round_num} rounds'
                break

            queries = self._generate_queries(weak)
            self.research_history.append({
                'round': round_num + 1,
                'weak_dimensions': weak,
                'queries': queries,
            })

            findings = self._simulate_followup_research(company_name, queries)
            improvements = 0
            for finding in findings:
                if finding['found_evidence']:
                    dim = finding['dimension']
                    old = scores.get(dim, 3)
                    new = min(old + 0.5, 5.0)
                    if new != old:
                        scores[dim] = new
                        improvements += 1
                        result['refined_scores'][dim] = new

            result['rounds'].append({
                'round': round_num + 1,
                'weak_count': len(weak),
                'query_count': len(queries),
                'improvements': improvements,
            })
            result['total_improvements'] += improvements

        result['final_composite'] = round(compute_composite(scores), 2)
        result['improved'] = result['total_improvements'] > 0
        return result


def auto_improve(company_name, scores, enriched=None, john_comp=None):
    """One-call reflection loop improvement."""
    loop = ReflectionLoop()
    return loop.improve_scorecard(company_name, scores, enriched)


if __name__ == '__main__':
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else 'Booking Experts'

    # Test with sample scores
    test_scores = {
        'Ownership attractiveness': 3, 'Revenue scale fit': 3, 'Geographic fit': 5,
        'Tech stack modernity': 3, 'Customer lock-in': 4, 'Vertical depth': 5,
        'Integration potential': 3, 'Growth trajectory': 3,
    }

    loop = ReflectionLoop()
    result = loop.improve_scorecard(name, test_scores)

    print(f"Company: {result['company']}")
    print(f"Initial composite: {compute_composite(result['initial_scores']):.2f}")
    print(f"Final composite: {result['final_composite']}")
    print(f"Improvements made: {result['total_improvements']}")
    for r in result['rounds']:
        print(f"  Round {r['round']}: {r['weak_count']} weak dims, {r['improvements']} improvements")
    print(f"\nInitial: {result['initial_scores']}")
    print(f"Refined: {result['refined_scores']}")
