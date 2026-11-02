"""Every static page must expose a full data date in readable page copy."""
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from check import Page

DATE = re.compile(r'\b(?:\d{4}-\d{2}-\d{2}|\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4})\b')


def visible_dates(html):
    page = Page()
    page.feed(html)
    return DATE.findall(page.text)


class EveryPageDateTests(unittest.TestCase):
    def test_every_generated_page_has_readable_full_data_date(self):
        pages = sorted((ROOT / 'site').rglob('*.html'))
        self.assertTrue(pages)
        for path in pages:
            with self.subTest(page=path.relative_to(ROOT / 'site')):
                self.assertTrue(visible_dates(path.read_text()),
                                'Missing readable data date (including an empty local log)')

    def test_links_attributes_and_fiscal_years_are_not_data_dates(self):
        for html in ('<p>2025-26 outturn</p>',
                     '<a href="/2026-11-02">Source</a>',
                     '<time datetime="2026-11-02">Unknown</time>'):
            with self.subTest(html=html):
                self.assertFalse(visible_dates(html))
        self.assertTrue(visible_dates('<time datetime="2026-11-02">2026-11-02</time>'))
        self.assertTrue(visible_dates('<p>Data as of 2 November 2026</p>'))
