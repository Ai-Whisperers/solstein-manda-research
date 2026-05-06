#!/usr/bin/env python3
"""
ResearchCoordinator — CrewAI-based multi-agent research crew for M&A target scoring.
Integrates patterns from due-diligence-agents v1.5.0 (9 domains) and DealScout (combative debate).

Agents (9 specialists + validator + synthesis = 11 total):
  - Ownership, Financial, Tech, Market, Legal, Tax, ESG (7 specialist analysts)
  - Debate Moderator, Questions Generator (DealScout pattern)
  - Validator (dd-agents Judge pattern)
  - Synthesizer/GP (dd-agents Executive Synthesis pattern)

Usage:
    from research_crew import ResearchCoordinator
    crew = ResearchCoordinator()
    result = crew.research("Booking Experts", "https://bookingexperts.com")
    print(result['scorecard'])

Patterns: CrewAI, due-diligence-agents v1.5.0, DealScout
"""

import json, os, sys, logging
logger = logging.getLogger(__name__)
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))

from crewai import Agent, Task, Crew, Process, LLM
from scoring import DIMS, WEIGHTS, WEIGHT_MAP, apply_vetoes
from crewai_config import get_llm, get_openai_key, get_openrouter_key, LLM_CONFIGS
from datetime import datetime
from core.utils import safe_json_load

BASE = os.path.join(os.path.dirname(__file__), '..', '..')


def _get_enriched(company_name):
    """Get existing enriched data if available."""
    folder = company_name.lower().replace(' ', '-')
    ep = os.path.join(BASE, 'output', 'HORECA', folder, 'enriched.json')
    data = safe_json_load(ep)
    return data if data else {}


def _make_context(company_name, domain, enriched=None):
    """Build research context string from enriched data."""
    if enriched is None:
        enriched = _get_enriched(company_name)
    ctx = []
    ctx.append(f"Company: {company_name}")
    if domain:
        ctx.append(f"Domain: {domain}")
    w = enriched.get('website', {})
    if w.get('title'):
        ctx.append(f"Website title: {w['title']}")
    if w.get('description'):
        ctx.append(f"Description: {w['description'][:300]}")
    if w.get('tech_stack'):
        ctx.append(f"Tech stack: {', '.join(w['tech_stack'][:10])}")
    if enriched.get('github'):
        g = enriched['github']
        ctx.append(f"GitHub: {g['public_repos']} repos, {g['followers']} followers, langs: {', '.join(g.get('top_languages', [])[:3])}")
    if enriched.get('wikipedia'):
        ctx.append(f"Wikipedia: {enriched['wikipedia']['extract'][:300]}")
    if enriched.get('news'):
        ctx.append(f"News ({len(enriched['news'])} articles)")
    t = enriched.get('triangulation', {}).get('employees', {})
    if t and t.get('consensus'):
        ctx.append(f"Employees: ~{t['consensus']}")
    return '\n'.join(ctx)


class ResearchCoordinator:
    """Orchestrates multi-agent company research."""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self._create_agents()

    def _create_agents(self):
        llm_default = get_llm('cheap')
        llm_validator = get_llm('openai_best')

        self.ownership_agent = Agent(
            role='Ownership & Governance Analyst',
            goal='Analyze company ownership structure, cap table, and founder situation',
            backstory='You specialize in tracing corporate ownership, identifying PE/VC involvement, and assessing founder exit readiness.',
            llm=llm_default,
            verbose=self.verbose,
        )

        self.financial_agent = Agent(
            role='Financial & Revenue Analyst',
            goal='Assess revenue scale, growth trajectory, and capital efficiency from public signals',
            backstory='You estimate private company financials from public signals: headcount, pricing, funding history, customer count.',
            llm=llm_default,
            verbose=self.verbose,
        )

        self.tech_agent = Agent(
            role='Technology & Product Analyst',
            goal='Evaluate tech stack modernity, integration capabilities, and product depth',
            backstory='You assess software companies by their technology choices, API openness, and product architecture.',
            llm=llm_default,
            verbose=self.verbose,
        )

        self.market_agent = Agent(
            role='Market Position Analyst',
            goal='Analyze geographic presence, customer lock-in, competitive position, and vertical depth',
            backstory='You map market landscapes, assess competitive moats, and evaluate customer switching costs.',
            llm=llm_default,
            verbose=self.verbose,
        )

        self.validator_agent = Agent(
            role='Research Validator',
            goal='Cross-reference all claims, flag unsupported assertions, and ensure source citations',
            backstory='You are a meticulous fact-checker. Every score must cite a specific source. Unsupported claims are flagged.',
            llm=llm_validator,
            verbose=self.verbose,
        )

        # Extended agents (from due-diligence-agents 9-domain pattern)
        self.legal_agent = Agent(
            role='Legal & Regulatory Analyst',
            goal='Assess legal structure, IP ownership, regulatory exposure, and compliance risks',
            backstory='You evaluate corporate legal structure, IP portfolios, data privacy compliance, and regulatory risks for acquisition targets.',
            llm=llm_default,
            verbose=self.verbose,
        )

        self.tax_agent = Agent(
            role='Tax & Structuring Analyst',
            goal='Evaluate tax structure, jurisdiction risks, and deal structuring implications',
            backstory='You analyze tax implications of cross-border acquisitions, holding structures, and potential tax liabilities.',
            llm=llm_default,
            verbose=self.verbose,
        )

        self.esg_agent = Agent(
            role='ESG & Sustainability Analyst',
            goal='Assess environmental, social, and governance factors affecting acquisition value',
            backstory='You evaluate ESG maturity, sustainability practices, and governance quality as they impact deal risk and valuation.',
            llm=llm_default,
            verbose=self.verbose,
        )

        # DealScout-pattern debate agents
        self.debate_moderator = Agent(
            role='Debate Moderator',
            goal='Force analysts to argue their positions and detect contradictions',
            backstory='You are an instigator. You force the Market, Product, and Financial analysts to defend their conclusions and challenge each other\'s assumptions.',
            llm=llm_default,
            verbose=self.verbose,
        )

        self.questions_generator = Agent(
            role='Questions Generator',
            goal='Generate hard-hitting questions that challenge the investment thesis',
            backstory='You are a devil\'s advocate. You generate 8-12 critical questions across Market, Product, Traction, and Team categories that must be answered before any investment decision.',
            llm=llm_default,
            verbose=self.verbose,
        )

        # dd-agents Executive Synthesis (GP Agent)
        self.synthesizer = Agent(
            role='Synthesizer (GP)',
            goal='Read all analyst reports, debate transcript, and critical questions. Produce final investment verdict.',
            backstory='You are the General Partner making the final decision. You synthesize all perspectives, weigh evidence, and produce a clear Pass/Invest recommendation with rationale.',
            llm=llm_best,
            verbose=self.verbose,
        )

    def _run_analyst(self, agent, task_desc, context):
        task = Task(
            description=task_desc,
            expected_output='A JSON object with: score (1-5), rationale, source_cited, confidence (high/medium/low)',
            agent=agent,
            context=[{'description': context, 'expected_output': 'Research context'}],
        )
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=self.verbose)
        result = crew.kickoff()
        return str(result)

    def _parse_score(self, raw):
        """Extract numeric score from agent output."""
        m = re.search(r'"score"\s*:\s*([\d.]+)', raw)
        if m:
            return float(m.group(1))
        m = re.search(r'score[:\s]+([\d.]+)', raw, re.I)
        if m:
            return float(m.group(1))
        return None

    def research(self, company_name, domain=None, enriched=None):
        """Run full research crew. Returns scorecard dict."""
        if enriched is None:
            enriched = _get_enriched(company_name)
        if not enriched:
            try:
                from datasources import enrich_company
                enriched = enrich_company(company_name, domain)
            except Exception:
                enriched = {'website': {'tech_stack': []}, 'sources_found': []}

        context = _make_context(company_name, domain, enriched)

        dimension_agents = [
            ('Ownership attractiveness', self.ownership_agent,
             'Analyze the ownership structure of this company. Is it founder-owned? PE-backed? VC-backed? '
             'Is there a succession plan? What is the deal structure complexity? Score 1-5.'),
            ('Revenue scale fit', self.financial_agent,
             'Estimate the company revenue scale from public signals. Consider: employee count × industry benchmarks, '
             'pricing page analysis, customer count, funding history. Is it in the €1-15M target range? Score 1-5.'),
            ('Geographic fit', self.market_agent,
             'Where is this company based? What is its primary market? Is it Benelux-focused or global? Score 1-5.'),
            ('Tech stack modernity', self.tech_agent,
             'Assess the technology stack. Is it cloud-native? Modern frameworks? Open API? '
             'Any legacy technology (PHP, ASP.NET, on-premise)? Score 1-5.'),
            ('Customer lock-in', self.market_agent,
             'How sticky are the customers? Long contracts? Deep integrations? High switching costs? Score 1-5.'),
            ('Vertical depth', self.market_agent,
             'How deep is this company in its vertical? Years of domain expertise? Niche specialization? Score 1-5.'),
            ('Integration potential', self.tech_agent,
             'Does this company have an open API? Integration marketplace? Partner ecosystem? Score 1-5.'),
            ('Growth trajectory', self.financial_agent,
             'Is the company growing? Headcount trends? New products? Geographic expansion? Customer growth? Score 1-5.'),
        ]

        scores = {}
        rationales = {}
        for dim, agent, prompt in dimension_agents:
            result = self._run_analyst(agent, f"Score {dim} for {company_name}\n\nResearch context:\n{context}\n\n{prompt}", context)
            score = self._parse_score(result)
            if score:
                scores[dim] = score
                rationales[dim] = result[:200]
            else:
                scores[dim] = 3
                rationales[dim] = f"Unable to determine from context. Default: 3. Raw: {result[:100]}"

        # Validate
        validation = self._run_analyst(self.validator_agent,
            f"Validate the following scorecard for {company_name}:\n{json.dumps(scores, indent=2)}\n"
            f"Check: are any scores unsupported? Are there contradictions? Suggest adjustments.",
            context)

        # Apply vetoes
        info = {
            'ownership': str(enriched.get('crunchbase', {}).get('description', '')),
            'country': '',
            'status': '',
        }
        veto_changes = apply_vetoes(info, scores)

        # Compute composite
        composite = sum(scores.get(d, 3) * WEIGHT_MAP.get(d, 2) for d in DIMS) / sum(WEIGHT_MAP.values())

        return {
            'company': company_name,
            'domain': domain,
            'researched_at': datetime.now().isoformat(),
            'dimensions': {d: {'score': scores.get(d, 3), 'rationale': rationales.get(d, '')} for d in DIMS},
            'composite': round(composite, 2),
            'veto_changes': veto_changes,
            'validation': validation[:300],
            'sources_count': len(enriched.get('sources_found', [])),
        }


if __name__ == '__main__':
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else 'Booking Experts'
    domain = sys.argv[2] if len(sys.argv) > 2 else None
    coord = ResearchCoordinator(verbose=True)
    result = coord.research(name, domain)

    print(f"\n=== Research Result: {result['company']} ===")
    print(f"Composite: {result['composite']}/5.0")
    for d in DIMS:
        v = result['dimensions'].get(d, {})
        print(f"  {d:<35} {v.get('score', '?'):<5} {v.get('rationale', '')[:80]}")
    if result['veto_changes']:
        print(f"\nVetoes applied: {len(result['veto_changes'])}")
    print(f"Sources: {result['sources_count']}")
