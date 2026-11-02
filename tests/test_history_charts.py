"""Chart contracts, missing/negative data, and independent raw value checks."""
import json
from pathlib import Path
import sys
import unittest
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from history_charts import VIEWS, chart_outputs, plot


class ChartTests(unittest.TestCase):
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
            page = outputs[f'history-{view}.html'].decode()
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
