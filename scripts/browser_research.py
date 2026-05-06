"""
Browser-powered company research module.
Uses Playwright to render JavaScript, handle SPAs, and extract structured data.
Pattern from: browser-use/browser-use, ntegrals/openbrowser

Usage:
    from browser_research import CompanyBrowser
    browser = CompanyBrowser()
    data = browser.research_company("https://bookingexperts.com")
    print(data['tech_stack'])
    browser.close()
"""

import re, json, time, logging
logger = logging.getLogger(__name__)

try:
    import cloakbrowser
    _has_cloak = True
except ImportError:
    _has_cloak = False

if not _has_cloak:
    from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout


class CompanyBrowser:
    """Playwright-based browser agent for company research."""

    _ua_pool = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    ]
    _ua_index = 0

    def __init__(self, headless=True, timeout=30000):
        self._cloak = _has_cloak
        self._headless = headless
        self.timeout = timeout
        # All browser resources start as None — lazily initialized on first use
        self.browser = None
        self.context = None
        self.page = None
        self.play = None

    def _ensure_browser(self):
        """Start browser on first use. This allows __init__ to be safe — if browser
        creation fails, cleanup via __exit__/__del__ works because all attrs exist."""
        if self.browser is not None:
            return
        if self._cloak:
            logger.info("Using CloakBrowser (stealth mode)")
            import cloakbrowser
            self.browser = cloakbrowser.launch(headless=self._headless)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
        else:
            self.play = sync_playwright().start()
            self.browser = self.play.chromium.launch(
                headless=self._headless,
                args=['--disable-blink-features=AutomationControlled',
                      '--no-sandbox', '--disable-dev-shm-usage']
            )
            ua = CompanyBrowser._ua_pool[CompanyBrowser._ua_index % len(CompanyBrowser._ua_pool)]
            CompanyBrowser._ua_index += 1
            self.context = self.browser.new_context(
                user_agent=ua,
                viewport={'width': 1280, 'height': 800},
                locale='en-US',
                extra_http_headers={'Accept-Language': 'en-US,en;q=0.9'},
            )
            self.page = self.context.new_page()

    def _dismiss_cookies(self):
        """Try to dismiss common cookie consent popups."""
        try:
            # Common cookie accept button selectors
            selectors = [
                'button:has-text("Accept")', 'button:has-text("Accept All")',
                'button:has-text("I agree")', 'button:has-text("Got it")',
                'button:has-text("Allow")', 'button:has-text("Allow All")',
                'button:has-text("OK")', '#cookies-accept', '.cookie-accept',
                '[aria-label*="cookie" i]', '[data-testid="cookie-accept"]',
                'button:has-text("Consent")',
            ]
            for sel in selectors:
                try:
                    btn = self.page.query_selector(sel)
                    if btn and btn.is_visible():
                        btn.click()
                        self.page.wait_for_timeout(500)
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def goto(self, url, wait_until='domcontentloaded'):
        self._ensure_browser()
        try:
            self.page.goto(url, wait_until=wait_until, timeout=self.timeout)
            self.page.wait_for_load_state('networkidle', timeout=10000)
            self._dismiss_cookies()
            return True
        except Exception:
            return False

    def get_text(self):
        return self.page.inner_text('body') if self.page else ''

    def get_html(self):
        return self.page.content() if self.page else ''

    def get_title(self):
        return self.page.title() if self.page else ''

    def extract_meta(self):
        meta = {'title': self.get_title(), 'description': '', 'keywords': ''}
        try:
            desc = self.page.query_selector('meta[name="description"]')
            if desc:
                meta['description'] = desc.get_attribute('content') or ''
            kw = self.page.query_selector('meta[name="keywords"]')
            if kw:
                meta['keywords'] = kw.get_attribute('content') or ''
        except Exception:
            pass
        return meta

    def detect_tech_stack(self):
        """Detect technology stack from rendered page."""
        html = self.get_html().lower()
        signals = []
        checks = [
            ('React', r'react(\.|\-)'), ('Next.js', r'__next|next\.js'),
            ('Vue.js', r'vue(\.|\-)'), ('Angular', r'angular|ng-'),
            ('jQuery', r'jquery'), ('Bootstrap', r'bootstrap'),
            ('Tailwind', r'tailwind'), ('WordPress', r'wp-content|wp-includes'),
            ('Ruby/Rails', r'rails|\.rb'), ('PHP', r'\.php'),
            ('Python/Django', r'django|csrfmiddleware|python'),
            ('Node.js', r'node_modules|express\.js'),
            ('Go', r'golang|\.go'), ('Java', r'java\.js|spring'),
            ('Cloudflare', r'cloudflare|__cfduid'),
            ('Google Analytics', r'google-analytics|gtag'),
            ('Stripe', r'stripe\.com'), ('Mollie', r'mollie'),
            ('Adyen', r'adyen'), ('Hotjar', r'hotjar'),
            ('Intercom', r'intercom'), ('HubSpot', r'hs-analytics'),
            ('Shopify', r'shopify'), ('WooCommerce', r'woocommerce'),
        ]
        for name, pattern in checks:
            if re.search(pattern, html):
                signals.append(name)
        return signals

    def find_links(self, pattern=None):
        links = []
        try:
            for a in self.page.query_selector_all('a[href]'):
                href = a.get_attribute('href') or ''
                text = (a.inner_text() or '').strip()[:80]
                if pattern and pattern.lower() not in href.lower() and pattern.lower() not in text.lower():
                    continue
                links.append({'href': href, 'text': text})
        except Exception:
            pass
        return links

    def extract_pricing(self):
        """Navigate to pricing page and extract tiers."""
        pricing_urls = ['/pricing', '/plans', '/pricing-plans', '/subscription']
        data = {'found': False, 'tiers': [], 'pricing_url': None}
        for path in pricing_urls:
            url = self.page.url.rstrip('/') + path
            if self.goto(url, wait_until='domcontentloaded'):
                data['found'] = True
                data['pricing_url'] = url
                text = self.get_text()[:3000]
                prices = re.findall(r'[€$£]\s*[\d,]+(?:\.\d{2})?(?:\s*/\s*(?:mo|month|year|yr))?', text)
                data['tiers'] = prices[:10]
                break
        return data

    def extract_careers(self):
        """Navigate to careers page and extract open positions."""
        career_urls = ['/careers', '/jobs', '/about-us#jobs', '/join-us']
        data = {'found': False, 'positions': [], 'careers_url': None}
        for path in career_urls:
            url = self.page.url.rstrip('/') + path
            if self.goto(url, wait_until='domcontentloaded'):
                data['found'] = True
                data['careers_url'] = url
                text = self.get_text()[:5000]
                roles = re.findall(r'(?:Engineer|Developer|Designer|Manager|Analyst|Specialist|Lead|Head|Director|VP|CTO|CEO)\w*(?:\s+\w+){0,5}', text)
                data['positions'] = list(set(roles))[:20]
                break
        return data

    def count_internal_links(self):
        base = self.page.url.split('//')[1].split('/')[0] if '//' in self.page.url else ''
        links = set()
        try:
            for a in self.page.query_selector_all('a[href]'):
                href = a.get_attribute('href') or ''
                if base in href:
                    links.add(href.split('//')[1] if '//' in href else href)
        except Exception:
            pass
        return len(links)

    def screenshot(self, path='screenshot.png'):
        try:
            self.page.screenshot(path=path, full_page=True)
            return path
        except Exception:
            return None

    def research_company(self, url):
        """Full company research in one call. Returns structured dict."""
        result = {
            'url': url,
            'reachable': False,
            'title': '',
            'description': '',
            'tech_stack': [],
            'pricing': {'found': False, 'tiers': [], 'pricing_url': None},
            'careers': {'found': False, 'positions': [], 'careers_url': None},
            'page_count_estimate': 0,
            'sources_checked': [],
        }

        if not self.goto(url):
            return result

        result['reachable'] = True
        meta = self.extract_meta()
        result['title'] = meta['title']
        result['description'] = meta['description']
        result['tech_stack'] = self.detect_tech_stack()
        result['page_count_estimate'] = self.count_internal_links()
        result['sources_checked'].append(url)

        # Try about page for description
        about_url = url.rstrip('/') + '/about'
        if self.goto(about_url, wait_until='domcontentloaded'):
            about_text = self.get_text()[:1000]
            if len(about_text) > len(result['description']):
                result['description'] = about_text[:500]
            result['sources_checked'].append(about_url)

        # Extract pricing
        result['pricing'] = self.extract_pricing()

        # Extract careers
        result['careers'] = self.extract_careers()

        return result

    def close(self):
        try:
            if self.page:
                self.page.close()
        except Exception:
            pass
        try:
            if self.context:
                self.context.close()
        except Exception:
            pass
        try:
            if self.browser:
                self.browser.close()
        except Exception:
            pass
        try:
            if getattr(self, 'play', None):
                self.play.stop()
        except Exception:
            pass

    def __del__(self):
        """Ensure browser cleanup on garbage collection (defense against stale processes)."""
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == '__main__':
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://bookingexperts.com'
    browser = CompanyBrowser()
    data = browser.research_company(url)
    browser.close()

    print(f"URL: {data['url']}")
    print(f"Reachable: {data['reachable']}")
    print(f"Title: {data['title']}")
    print(f"Tech stack: {', '.join(data['tech_stack'])}")
    print(f"Pricing found: {data['pricing']['found']} ({len(data['pricing']['tiers'])} tiers)")
    print(f"Careers found: {data['careers']['found']} ({len(data['careers']['positions'])} positions)")
    print(f"Pages estimated: {data['page_count_estimate']}")
    print(f"Sources: {len(data['sources_checked'])}")

    # Save JSON
    import os
    from core.utils import atomic_json_dump
    out = os.path.join(os.path.dirname(__file__), '..', 'output', 'HORECA', 'browser-test.json')
    atomic_json_dump(data, out, indent=2)
    print(f"Saved to {out}")
