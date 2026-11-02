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
    def render(self, notices=None, mutate_sources=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'sources').mkdir()
            for path in (ROOT/'sources').iterdir():
                if path.is_file():
                    (root/'sources'/path.name).write_bytes(path.read_bytes())
            (root/'sources/revision-status.json').write_text(json.dumps({'notices': notices or []}))
            if mutate_sources:
                mutate_sources(root/'sources')
            files = {p.name: p.read_bytes() for p in (ROOT/'site').glob('*.html')}
            # Remove existing stamps before exercising annotator on renderer-like input.
            import re
            for key, raw in files.items():
                files[key] = re.sub(r'<div class="section-dates">.*?</div>', '', raw.decode(), flags=re.S).encode()
            files['data/income.json'] = (ROOT/'site/data/income.json').read_bytes()
            section_dates.annotate(files, root, json.loads((ROOT/'site/data/spending.json').read_text()), json.loads((ROOT/'site/data/comparisons.json').read_text()))
            return {k: v.decode() for k, v in files.items() if k.endswith('.html')}

    def test_every_section_and_party_offer_has_dates(self):
        import re
        pages = self.render()
        for name, page in pages.items():
            if name == 'corrections.html':
                # Ledger policy is not a fiscal data release: do not invent a vintage.
                self.assertNotIn('class="section-dates"', page)
                continue
            headers = re.findall(r'<(?:section|article)\b[^>]*>\s*<h2\b[^>]*>.*?</h2>', page, re.S)
            for header in headers:
                self.assertIn(header+'<div class="section-dates">', page, name)
        self.assertEqual(pages['parties.html'].count('2024 election manifesto'), 13)
        self.assertNotIn('published 2024-07-09', pages['parties.html'])
        self.assertIn('Snapshot as of 2024-07-09. Publish and update dates not supplied.', pages['parties.html'])
        self.assertIn('Data period: 2015-16 to 2025-26', pages['index.html'])
        for view in ('cash', 'real', 'gdp'):
            self.assertNotIn('Data period: 2003-04 to 2025-26; fixed TME', pages[f'history-{view}.html'])

    def test_income_periods_release_and_as_of_are_local(self):
        import re
        page = self.render()['income.html']
        sections = dict(re.findall(r'<section id="([^"]+)">(.*?)</section>', page, re.S))
        self.assertEqual(set(sections), {'forecasts', 'tax', 'non-tax', 'borrowing-debt', 'sources'})
        for section, body in sections.items():
            stamp = body.split('<div class="section-dates">')[1].split('</div>')[0]
            self.assertIn('Data period: 2025-26', stamp)
            self.assertIn('Published 2026-10-28. Source updated 2026-10-28.', stamp)
            self.assertIn('as of 2026-11-01', stamp)
            self.assertIn('No next release date is announced on the retained OBR data page', stamp)
            self.assertIn('https://obr.uk/data/', stamp)
            self.assertIn('sources/income-release.txt', stamp)
            self.assertEqual('debt at end-March 2026' in stamp,
                             section == 'borrowing-debt')
            self.assertEqual('2026-27 to 2031-32 forecast; debt at each end-March' in stamp,
                             section in ('forecasts', 'sources'))

    def test_independent_party_evidence_dates_and_revision_notices_are_local(self):
        notice = {'source': 'party-evidence-rf-economic-battle-lines',
                  'baseline_url': 'https://www.resolutionfoundation.org/comment/economic-battle-lines/',
                  'first_detected_at': '2026-11-02T00:00:00Z',
                  'evidence': {'release_url': 'https://www.resolutionfoundation.org/comment/economic-battle-lines/'}}
        pages = self.render([notice])
        import re
        cards = dict(re.findall(r'<article[^>]*data-party-id="([^"]+)"[^>]*>(.*?)</article>',
                                pages['parties.html'], re.S))
        for identifier, card in cards.items():
            self.assertEqual('Source revised.' in card, identifier in ('4', '15'))
            if identifier in ('4', '15'):
                self.assertIn('Published 2024-06-14', card)
        for name, page in pages.items():
            if name != 'parties.html':
                self.assertNotIn('Source revised.', page)

    def test_income_release_metadata_hash_and_path_are_checked(self):
        def changed(sources):
            with (sources/'income-release.txt').open('ab') as stream:
                stream.write(b'changed')
        with self.assertRaisesRegex(ValueError, 'Income release evidence hash changed'):
            self.render(mutate_sources=changed)

        def escaped(sources):
            path = sources/'income-manifest.json'
            source = json.loads(path.read_text())
            source['metadata_file'] = '../outside.txt'
            path.write_text(json.dumps(source))
        with self.assertRaisesRegex(ValueError, 'Invalid income release evidence path'):
            self.render(mutate_sources=escaped)

    def test_income_revision_notice_is_scoped_and_escaped(self):
        for url, label in [('https://obr.uk/data/', 'Source revised.'),
                           ('https://obr.uk/new?x=1&y="2"', 'New source release found.')]:
            notice = {'source': 'obr-public-finances-databank',
                      'baseline_url': 'https://obr.uk/data/',
                      'first_detected_at': '2026-11-02T00:00:00Z',
                      'evidence': {'release_url': url}}
            pages = self.render([notice])
            self.assertEqual(pages['income.html'].count(f'<strong>{label}</strong>'), 5)
            self.assertIn('These figures still use the saved data, not the changed source.', pages['income.html'])
            for name, page in pages.items():
                if name != 'income.html':
                    self.assertNotIn('class="revision-notice"', page, name)
            if 'new?' in url:
                self.assertIn('href="https://obr.uk/new?x=1&amp;y=&quot;2&quot;"', pages['income.html'])

    def test_annotations_keep_grade_gate(self):
        import reading_grade
        for name, page in self.render().items():
            result = reading_grade.measure(page)
            with self.subTest(page=name):
                self.assertLessEqual(max(result.grade, result.verbal_grade, result.prose_grade), 7)

    def test_revision_notice_scoped_visible_and_escaped(self):
        notice = {'source': 'hmt-public-spending', 'baseline_url': 'https://www.gov.uk/old', 'first_detected_at': '2026-11-01T00:00:00Z', 'evidence': {'release_url': 'https://www.gov.uk/old'}}
        pages = self.render([notice])
        self.assertIn('Source revised.', pages['index.html'])
        self.assertNotIn('Source revised.', pages['history.html'])
        self.assertNotIn('Source revised.', pages['parties.html'])
        # Comparison uses another workbook and must not inherit this notice.
        comparison = pages['index.html'].split('<section id="ten-years">')[1].split('</section>')[0]
        self.assertNotIn('Source revised.', comparison)
