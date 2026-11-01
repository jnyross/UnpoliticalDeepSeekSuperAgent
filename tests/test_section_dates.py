import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import section_dates

ROOT = Path(__file__).resolve().parents[1]


class SectionDatesTests(unittest.TestCase):
    def render(self, notices=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'sources').mkdir()
            for path in (ROOT/'sources').iterdir():
                if path.is_file():
                    (root/'sources'/path.name).write_bytes(path.read_bytes())
            (root/'sources/revision-status.json').write_text(json.dumps({'notices': notices or []}))
            files = {p.name: p.read_bytes() for p in (ROOT/'site').glob('*.html')}
            # Remove existing stamps before exercising annotator on renderer-like input.
            import re
            for key, raw in files.items():
                files[key] = re.sub(r'<div class="section-dates">.*?</div>', '', raw.decode(), flags=re.S).encode()
            section_dates.annotate(files, root, json.loads((ROOT/'site/data/spending.json').read_text()), json.loads((ROOT/'site/data/comparisons.json').read_text()))
            return {k: v.decode() for k, v in files.items()}

    def test_every_section_and_party_offer_has_dates(self):
        import re
        pages = self.render()
        for name, page in pages.items():
            headers = re.findall(r'<(?:section|article)\b[^>]*>\s*<h2\b[^>]*>.*?</h2>', page, re.S)
            for header in headers:
                self.assertIn(header+'<div class="section-dates">', page, name)
        self.assertEqual(pages['parties.html'].count('2024 election manifesto'), 13)
        self.assertNotIn('published 2024-07-09', pages['parties.html'])
        self.assertIn('snapshot as of 2024-07-09; publication/update dates not supplied', pages['parties.html'])
        self.assertIn('Data period: 2015-16 to 2025-26', pages['index.html'])
        for view in ('cash', 'real', 'gdp'):
            self.assertNotIn('Data period: 2003-04 to 2025-26; fixed TME', pages[f'history-{view}.html'])

    def test_revision_notice_scoped_visible_and_escaped(self):
        notice = {'source': 'hmt-public-spending', 'baseline_url': 'https://www.gov.uk/old', 'first_detected_at': '2026-11-01T00:00:00Z', 'evidence': {'release_url': 'https://www.gov.uk/old'}}
        pages = self.render([notice])
        self.assertIn('Source revised.', pages['index.html'])
        self.assertNotIn('Source revised.', pages['history.html'])
        self.assertNotIn('Source revised.', pages['parties.html'])
        # Comparison uses another workbook and must not inherit this notice.
        comparison = pages['index.html'].split('<section id="ten-years">')[1].split('</section>')[0]
        self.assertNotIn('Source revised.', comparison)
