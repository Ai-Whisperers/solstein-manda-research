#!/usr/bin/env python3
"""Google Maps company data — imports and enriches the paragu-ai-leads CSV data."""
import csv, json, os, logging
from datetime import datetime
from core.config import Config
from core.cache import cache_get_or_fetch

logger = logging.getLogger(__name__)

LEADS_CSV = os.path.join(Config.BASE, 'data', 'paraguay', 'paraguay_beauty_prioritized.csv')


def load_leads(csv_path=None, priority=None, limit=None):
    """Load leads from CSV. Optionally filter by priority (A/B) and limit."""
    path = csv_path or LEADS_CSV
    if not os.path.exists(path):
        logger.warning("Leads CSV not found: %s", path)
        return []
    leads = []
    with open(path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if priority and row.get('priority', '').upper() != priority.upper():
                continue
            leads.append(row)
            if limit and len(leads) >= limit:
                break
    logger.info("Loaded %d leads from %s", len(leads), path)
    return leads


def lead_to_company_name(lead):
    """Extract a clean company name from a lead row."""
    name = lead.get('name', '').strip()
    # Clean up common suffixes for search
    for suffix in [' S.A.', ' S.R.L.', ' E.A.S.', ' - ', ' – ']:
        name = name.split(suffix)[0] if suffix in name else name
    return name.strip()


def lead_to_domain(lead):
    """Extract or guess domain from a lead row."""
    website = lead.get('website', '').strip()
    if website and website != 'None' and not website.startswith('http'):
        website = 'https://' + website
    return website if website and website != 'None' else None


def maps_to_enrichment_input(lead):
    """Convert a Google Maps lead row to Solstein enrichment input."""
    return {
        'name': lead_to_company_name(lead),
        'domain': lead_to_domain(lead),
        'maps_name': lead.get('name', ''),
        'category': lead.get('category', ''),
        'subcategory': lead.get('subcategory', ''),
        'city': lead.get('city', ''),
        'lat': lead.get('lat', ''),
        'lng': lead.get('lng', ''),
        'phone': lead.get('phone', ''),
        'rating': lead.get('rating'),
        'reviews': lead.get('total_reviews'),
        'maps_types': lead.get('types', ''),
        'priority': lead.get('priority', ''),
        'deep_score': lead.get('deep_score'),
        'address': lead.get('address', ''),
    }


def enrich_lead(lead):
    """Run full Solstein enrichment on a single lead. Returns enriched data."""
    from sources.enrichment import enrich_company
    company_name = lead_to_company_name(lead)
    domain = lead_to_domain(lead)
    result = enrich_company(company_name, domain)
    # Merge Google Maps data on top
    result['maps'] = maps_to_enrichment_input(lead)
    result['sources_found'].append('google_maps')
    return result


def batch_enrich_leads(leads, max_workers=4, limit=None):
    """Enrich a batch of leads using cached results where possible."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    if limit:
        leads = leads[:limit]
    results = []
    total = len(leads)
    print(f"Enriching {total} leads (cached sources will be instant)...")
    with ThreadPoolExecutor(max_workers=max_workers) as exec:
        future_map = {exec.submit(enrich_lead, lead): lead for lead in leads}
        for i, future in enumerate(as_completed(future_map), 1):
            lead = future_map[future]
            try:
                data = future.result()
                src_count = len(data.get('sources_found', []))
                print(f"  [{i}/{total}] {lead.get('name','')[:30]:30s} {src_count} sources")
                results.append(data)
            except Exception as e:
                logger.error("Failed to enrich %s: %s", lead.get('name', ''), e)
                results.append({'company': lead.get('name', ''), 'error': str(e)})
    return results
