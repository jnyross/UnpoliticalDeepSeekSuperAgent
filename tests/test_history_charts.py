"""Chart contracts, missing/negative data, and independent raw value checks."""
import json
import re
from pathlib import Path
import sys
import unittest
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from history_charts import VIEWS, chart_outputs, plot


class ChartTests(unittest.TestCase):
    def test_definition_notes_stay_with_each_affected_chart_and_table(self):
        # Independent expectations: a page-wide source footnote cannot satisfy these.
        expected = {
            'tme': ('excludes the temporary effects of banks being classed as public sector',),
            'defence': ('UN COFOG defence', 'not NATO', 'Pensions'),
            'education': ('2011-12', 'student loans', 'Do not compare'),
            'transport': ('2011-12', 'TfL', '2015-16', 'Network Rail'),
            'economic-affairs': ('2011-12', 'TfL', '2015-16', 'Network Rail'),
            'services-total': ('2011-12', 'TfL', '2015-16', 'Network Rail'),
            'eu-transactions': ('2010-11', 'VAT', 'Negative values'),
        }
        cells = {'cash': '4_2!A35', 'real': '4_3!A36', 'gdp': '4_4!A36'}
        import openpyxl
        book = openpyxl.load_workbook(ROOT/'sources/history.xlsx', data_only=True)
        official = 'This excludes the temporary effects of banks being classified to the public sector.'
        for view in VIEWS:
            page = (ROOT/'site'/f'history-{view}.html').read_text()
            for ident, phrases in expected.items():
                section = re.search(fr'<section id="{ident}">.*?</section>', page, re.S)[0]
                before_chart = section.split('<figure>')[0]
                for phrase in phrases:
                    self.assertIn(phrase, before_chart, (view, ident))
                self.assertIn('<table>', section)
                if ident == 'tme':
                    caption = re.search(r'<caption>(.*?)</caption>', section)[1]
                    self.assertIn(expected['tme'][0], caption)
                    self.assertIn(cells[view], caption)
            sheet, cell = cells[view].split('!')
            self.assertIn(official, book[sheet][cell].value)
            self.assertRegex(book[sheet]['A27'].value, r'Total Managed Expenditure')
        # The non-chart annual and fixed-decade tables carry the same scope, too.
        history = (ROOT/'site/history.html').read_text()
        captions = re.findall(r'<caption>(.*?)</caption>', history)
        tme_captions = [c for c in captions if c.startswith('Total Managed Expenditure')]
        self.assertEqual(len(tme_captions), 2)
        for caption in tme_captions:
            self.assertIn(expected['tme'][0], caption)
        self.assertIn('4_1!B53', tme_captions[1])
        self.assertIn(official, book['4_1']['B53'].value)

    def test_missing_splits_lines_and_negative_is_not_zero(self):
        svg = plot([{'year':str(i), 'v':v} for i,v in enumerate([-2, 3, None, 5, 0])], 'v')
        self.assertEqual(svg.count('<polyline'), 2)
        self.assertEqual(svg.count('<circle'), 4)
        self.assertIn('-2.0</text>', svg)
        self.assertIn('5.0</text>', svg)
        self.assertIn('>0.0</text>', svg)
        self.assertIn('M54 161.43H312', svg)

    def test_zero_series_and_single_point(self):
        self.assertIn('cy="210.00"', plot([{'year':'2025-26', 'v':0}], 'v'))
        self.assertNotIn('nan', plot([{'year':'2025-26', 'v':None}], 'v').lower())

    def test_all_series_have_three_views_with_exact_source_values(self):
        d = json.loads((ROOT/'site/data/history.json').read_text())
        import openpyxl
        book = openpyxl.load_workbook(ROOT/'sources/history.xlsx', data_only=True)
        outputs = chart_outputs(d)
        # The pipeline adds section-local vintage/calendar/revision context after rendering.
        from section_dates import annotate
        annotate(outputs, ROOT, json.loads((ROOT/'site/data/spending.json').read_text()),
                 json.loads((ROOT/'site/data/comparisons.json').read_text()))
        from disclosures import add_project_links
        add_project_links(outputs)
        for view, (field, title, unit) in VIEWS.items():
            # Global footer navigation is added after the chart renderer/annotations.
            page = outputs[f'history-{view}.html'].decode().replace(
                '<footer>', '<footer><p><a href="corrections.html">Corrections and report an error</a></p>')
            self.assertLess(len(page.encode()), 500000)
            self.assertNotIn('<script', page)
            for s in d['series']:
                self.assertIn(f'id="{s["id"]}"', page)
                self.assertIn(f'{title} · {unit} · {s["label"]}'.replace('&','&amp;'), page)
                for other in VIEWS:
                    if other != view:
                        self.assertIn(f'history-{other}.html#{s["id"]}', page)
                for p in s['values']:
                    sheet, cell = p['cells'][view].split('!')
                    raw = book[sheet][cell].value
                    value = round(raw,1) if raw is not None else None
                    self.assertEqual(p[field], value)
                    if value is not None:
                        self.assertIn(f'<td>{value:,.1f}</td><td>{p["status"]}</td><td>{sheet}!{cell}</td>', page)
            self.assertEqual(page.count('<svg '), len(d['series']))
            self.assertEqual(page.count('<table>'), len(d['series']))
            self.assertEqual(page.encode(), (ROOT/'site'/f'history-{view}.html').read_bytes())


if __name__ == '__main__':
    unittest.main()
