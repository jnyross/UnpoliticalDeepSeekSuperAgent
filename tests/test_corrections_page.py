"""Synthetic rendering fixtures; not real correction events."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from corrections_page import render

METADATA = dict(publication='Test log', date='2026-11-02', date_basis='Test snapshot date.',
                evidence_url='https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/pull/1')


class CorrectionsPageTests(unittest.TestCase):
    def test_empty_is_honest_and_static(self):
        page = render([], '<style>body{color:#20262b}</style>', METADATA)
        self.assertIn('No corrections have been recorded', page)
        self.assertIn('does not mean the site has no errors', page)
        self.assertIn('sources/corrections.json', page)
        self.assertIn('Open Government Licence', page)
        self.assertNotIn('<script', page)

    def test_all_fields_and_html_escaping(self):
        entry = dict(id='test-only', date='2026-11-02', page='index.html',
                     error='<script>test fixture</script>', correction='A & B',
                     source='https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/pull/1')
        page = render([entry], '<style>body{color:#20262b}</style>', METADATA)
        self.assertIn('id="test-only"', page)
        self.assertIn('<time datetime="2026-11-02">', page)
        self.assertIn('href="index.html"', page)
        self.assertIn(entry['source'], page)
        self.assertIn('&lt;script&gt;', page)
        self.assertIn('A &amp; B', page)
        self.assertNotIn('<script>', page)
        self.assertNotIn('No corrections have been recorded', page)
