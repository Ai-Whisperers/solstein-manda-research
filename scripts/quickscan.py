import logging
logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
Quick-scan v2: Browser-powered first-pass data gathering for any company.
Uses Playwright with auto-fallback to stdlib HTTP.

Patterns: browser-use/browser-use, ntegrals/openbrowser, companyscope-mcp

Usage:
    python3 quickscan.py "Booking Experts" "https://bookingexperts.com"
    python3 quickscan.py "Apicbase"
"""

import json, os, re, sys, urllib.request, urllib.error
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(os.path.dirname(__file__), '..')

_HAS_PLAYWRIGHT = False
try:
    from playwright.sync_api import sync_playwright
    _HAS_PLAYWRIGHT = True
except Exception:
            pass


def extract_domain(name):
    name = name.lower().strip()
    name = re.sub(r'[^a-z0-9\s-]', '', name)
    name = re.sub(r'\s+', '', name)
    return f'{name}.com'


class FallbackScanner:
    """Stdlib HTTP fallback when Playwright isn't available."""

    def fetch_url(self, url, timeout=15):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; SolSteinResearch/1.0)',
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception:
            return None

    def scan(self, domain):
        result = {'reachable': False, 'title': '', 'description': '', 'tech_stack': [],
                  'pricing_url': None, 'careers_url': None, 'page_count': 0, 'sources_checked': []}
        html = self.fetch_url(domain)
        result['sources_checked'].append(domain)
        if html:
            result['reachable'] = True
            m = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
            if m:
                result['title'] = m.group(1).strip()[:200]
            m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.DOTALL)
            if m:
                result['description'] = m.group(1).strip()[:300]
            result['tech_stack'] = self._detect_tech(html)
            base = domain.split('//')[1].split('/')[0] if '//' in domain else ''
            links = re.findall(r'href=["\'](https?://[^"\']+)["\']', html)
            result['page_count'] = len(set(l for l in links if base in l))
            for path in ['/pricing', '/careers', '/jobs']:
                h2 = self.fetch_url(domain.rstrip('/') + path, timeout=8)
                if h2:
                    result['sources_checked'].append(domain.rstrip('/') + path)
                    if 'pricing' in path:
                        result['pricing_url'] = domain.rstrip('/') + path
                    if 'careers' in path or 'jobs' in path:
                        result['careers_url'] = domain.rstrip('/') + path
        return result

    def _detect_tech(self, html):
        low = html.lower()
        signals = []
        checks = [('React', r'react'), ('Next.js', r'__next|next\.js'), ('Vue.js', r'vue'),
                  ('Angular', r'angular|ng-'), ('jQuery', r'jquery'), ('Bootstrap', r'bootstrap'),
                  ('Tailwind', r'tailwind'), ('WordPress', r'wp-content'), ('PHP', r'\.php'),
                  ('Python/Django', r'django'), ('Node.js', r'node_modules'),
                  ('Cloudflare', r'cloudflare'), ('Stripe', r'stripe\.com'), ('Mollie', r'mollie'),
                  ('Google Analytics', r'google-analytics')]
        for name, pat in checks:
            if re.search(pat, low):
                signals.append(name)
        return signals


def quick_scan(company_name, domain=None):
    if not domain:
        domain = extract_domain(company_name)
    if not domain.startswith('http'):
        domain = f'https://{domain}'

    result = {
        'company': company_name, 'domain': domain,
        'scanned_at': datetime.now().isoformat(),
        'website_reachable': False, 'title': '', 'description': '',
        'tech_stack': [], 'page_count': 0,
        'pricing': {'found': False, 'tiers': [], 'url': None},
        'careers': {'found': False, 'positions': [], 'url': None},
        'sources_checked': [], 'errors': [], 'method': 'stdlib',
    }

    if _HAS_PLAYWRIGHT:
        try:
            from browser_research import CompanyBrowser
            browser = CompanyBrowser(headless=True, timeout=25000)
            br = browser.research_company(domain)
            browser.close()
            result['website_reachable'] = br['reachable']
            result['title'] = br['title']
            result['description'] = br['description']
            result['tech_stack'] = br['tech_stack']
            result['page_count'] = br['page_count_estimate']
            result['pricing'] = br['pricing']
            result['careers'] = br['careers']
            result['sources_checked'] = br['sources_checked']
            result['method'] = 'playwright'
        except Exception as e:
            result['errors'].append(f'Playwright failed: {e}')

    if not result['website_reachable']:
        fb = FallbackScanner()
        fb_result = fb.scan(domain)
        result['website_reachable'] = fb_result['reachable']
        result['title'] = fb_result['title'] or result['title']
        result['description'] = fb_result['description'] or result['description']
        result['tech_stack'] = fb_result['tech_stack'] or result['tech_stack']
        result['page_count'] = fb_result['page_count'] or result['page_count']
        result['sources_checked'].extend(fb_result['sources_checked'])
        if fb_result['pricing_url'] and not result['pricing'].get('pricing_url'):
            result['pricing'] = {'found': True, 'tiers': [], 'pricing_url': fb_result['pricing_url']}
        if fb_result['careers_url'] and not result['careers'].get('careers_url'):
            result['careers'] = {'found': True, 'positions': [], 'careers_url': fb_result['careers_url']}
        result['method'] = 'stdlib'

    return result


def format_scan_report(scan):
    lines = []
    lines.append(f"=== Quick-Scan: {scan['company']} (method: {scan['method']}) ===")
    lines.append(f"Domain: {scan['domain']}")
    lines.append(f"Reachable: {'Yes' if scan['website_reachable'] else 'No'}")
    if scan['title']:
        lines.append(f"Title: {scan['title']}")
    if scan['description']:
        desc = scan['description'][:200]
        lines.append(f"Description: {desc}...")
    if scan['tech_stack']:
        lines.append(f"Tech stack: {', '.join(scan['tech_stack'][:10])}")
    if scan['pricing']['found']:
        p_url = scan['pricing'].get('pricing_url') or scan['pricing'].get('url', '')
    lines.append(f"Pricing: {p_url} ({len(scan['pricing']['tiers'])} tiers)")
    if scan['careers']['found']:
        c_url = scan['careers'].get('careers_url') or scan['careers'].get('url', '')
        lines.append(f"Careers: {c_url} ({len(scan['careers']['positions'])} positions)")
    lines.append(f"Pages: ~{scan['page_count']} | Sources: {len(scan['sources_checked'])}")
    return '\n'.join(lines)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: quickscan.py <company_name> [domain]")
        sys.exit(1)

    name = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else None
    scan = quick_scan(name, domain)

    out_dir = os.path.join(BASE, 'output', 'HORECA')
    folder = name.lower().replace(' ', '-')
    fdir = os.path.join(out_dir, folder)
    os.makedirs(fdir, exist_ok=True)
    path = os.path.join(fdir, 'quickscan.json')
    with open(path, 'w') as f:
        json.dump(scan, f, indent=2)

    print(format_scan_report(scan))
    print(f"\nSaved: {path}")
