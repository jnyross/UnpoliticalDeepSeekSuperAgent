"""Self-contained synthetic comparisons; no downloads or generator imports.

Run: .venv/bin/python -m unittest discover -s tests -p 'test_comparisons.py' -v
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check_comparisons as checker


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ('sources', 'site/sources', 'site/data'):
            (self.root / directory).mkdir(parents=True)
        self.workbook = openpyxl.Workbook()
        self.workbook.remove(self.workbook.active)
        for name in ('4_2', '4_3', '4_4'):
            sheet = self.workbook.create_sheet(name)
            sheet['B4'] = 'outturn'
            sheet['B5'], sheet['C5'], sheet['D5'] = '2014-15', '2015-16', '2025-26'
            sheet['D3'] = 'per cent' if name == '4_4' else '£ billion'
            for row in range(6, 28):
                sheet.cell(row, 1, f'Category {row}')
                sheet.cell(row, 4, 100)
            sheet['A20'] = '7. Health'
            sheet['A27'] = 'Total Managed Expenditure(7)' if name == '4_2' else 'Total Managed Expenditure(8)'
        self.workbook['4_3']['C20'], self.workbook['4_3']['D20'] = 100, 150
        self.workbook['4_2']['D20'] = 150
        self.workbook['4_4']['C27'], self.workbook['4_4']['D27'] = 40, 45
        self.workbook['4_3']['A28'] = '2025-26 price levels; GDP deflators released 30 June 2026'
        self.workbook['4_4']['A28'] = 'GDP figures published 30 June 2026'
        self.manifest = {'file': 'trends.xlsx', 'publication': 'Synthetic retained source',
                         'release_url': 'https://www.gov.uk/example', 'date': '2026-07-29',
                         'published': '2026-07-16', 'downloaded': '2026-11-01'}
        self.save_source()
        # Expected publication is deliberately hand-authored, not extracted by checker.
        self.data = {'source': self.manifest.copy(), 'points': [],
                     'health_change': 50, 'health_percent': 50, 'gdp_change': 5,
                     'formulas': {'health_change': 'latest health_real - baseline health_real',
                                  'health_percent': '(latest health_real / baseline health_real - 1) * 100',
                                  'gdp_change': 'latest tme_gdp - baseline tme_gdp'},
                     'deflator': '2025-26 price levels; GDP deflators released 30 June 2026',
                     'gdp_vintage': 'GDP figures published 30 June 2026'}
        for year, col, health, gdp in [('2015-16', 'C', 100, 40), ('2025-26', 'D', 150, 45)]:
            self.data['points'].append({'year': year, 'status': 'outturn',
                'health_real': {'value': health, 'sheet': '4_3', 'cell': f'{col}20', 'row': '7. Health',
                                'unit': 'GBP billion, 2025-26 prices',
                                'scope': 'Public sector expenditure on services: health', 'geography': 'United Kingdom'},
                'tme_gdp': {'value': gdp, 'sheet': '4_4', 'cell': f'{col}27', 'row': 'Total Managed Expenditure(8)',
                            'unit': 'percent of GDP', 'geography': 'United Kingdom',
                            'scope': 'Total Managed Expenditure, excluding temporary effects of public-sector banks'}})
        self.save_data()
        self.html = '''<h1>Where public money goes</h1><h2>Spending by area</h2>
<h2>What is in these totals?</h2><p>£10 goes on health</p>
<h3>Has health spending gone up or down after inflation?</h3>
<p><strong>Health spending went up by 50.0%</strong> from 2015-16 to 2025-26.
It went from £100.0 billion to £150.0 billion, a change of £50.0 billion in 2025-26 prices.</p>
<h3>Is total spending a bigger or smaller share of the economy?</h3>
<p><strong>Total spending was a bigger share of the economy</strong>: 45.0% of GDP in 2025-26, compared with 40.0% in 2015-16.
That is a change of 5.0 percentage points.</p>
<p>All four inputs are outturn, not forecasts.</p>
<table><tr><th>2015-16 (outturn)</th><td>£100.0bn<br><code>4_3!C20</code></td><td>40.0%<br><code>4_4!C27</code></td></tr>
<tr><th>2025-26 (outturn)</th><td>£150.0bn<br><code>4_3!D20</code></td><td>45.0%<br><code>4_4!D27</code></td></tr></table>
<a href="sources/trends.xlsx">Workbook</a><a href="data/comparisons.json">Data</a><a href="sources/trends-manifest.json">Manifest</a>'''
        self.save_html()

    def save_source(self):
        path = self.root / 'sources/trends.xlsx'
        self.workbook.save(path)
        self.manifest['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        (self.root / 'site/sources/trends.xlsx').write_bytes(path.read_bytes())
        for name in ('sources/trends-manifest.json', 'site/sources/trends-manifest.json'):
            (self.root / name).write_text(json.dumps(self.manifest))

    def save_data(self):
        (self.root / 'site/data/comparisons.json').write_text(json.dumps(self.data))

    def save_html(self):
        (self.root / 'site/index.html').write_text(self.html)

    def test_valid(self):
        checker.validate(self.root)

    def test_missing_exact_baseline_despite_nearby_year(self):
        self.workbook['4_3']['C5'] = None
        self.save_source()
        with self.assertRaisesRegex(checker.ValidationError, 'exact ten-year baseline'):
            checker.validate(self.root)

    def test_source_hash(self):
        with (self.root / 'sources/trends.xlsx').open('ab') as stream:
            stream.write(b'altered retained bytes')
        with self.assertRaisesRegex(checker.ValidationError, 'SHA-256'):
            checker.validate(self.root)

    def test_data_mutations(self):
        mutations = {
            'delta': lambda d: d.update(health_change=51),
            'percentage': lambda d: d.update(health_percent=49),
            'GDP delta': lambda d: d.update(gdp_change=4),
            'source': lambda d: d['source'].update(sha256='0' * 64),
            'locator': lambda d: d['points'][0]['health_real'].update(cell='B20'),
            'sheet': lambda d: d['points'][1]['tme_gdp'].update(sheet='4_3'),
            'status': lambda d: d['points'][0].update(status='forecast'),
            'value': lambda d: d['points'][1]['health_real'].update(value=151),
            'bool value': lambda d: d['points'][1]['health_real'].update(value=True),
            'units': lambda d: d['points'][0]['health_real'].update(unit='GBP million'),
            'year': lambda d: d['points'][0].update(year='2014-15'),
            'formula': lambda d: d['formulas'].update(gdp_change='latest / baseline'),
            'missing baseline': lambda d: d['points'].pop(0),
        }
        original = copy.deepcopy(self.data)
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                self.data = copy.deepcopy(original)
                mutate(self.data)
                self.save_data()
                with self.assertRaises(checker.ValidationError):
                    checker.validate(self.root)

    def test_latest_base_year_cross_check(self):
        for row in (20, 6):
            with self.subTest(row=row):
                original = self.workbook['4_2'].cell(row, 4).value
                self.workbook['4_2'].cell(row, 4, original + 1)
                self.save_source()
                with self.assertRaisesRegex(checker.ValidationError, 'real does not equal nominal'):
                    checker.validate(self.root)
                self.workbook['4_2'].cell(row, 4, original)

    def test_workbook_status_and_units(self):
        for cell, value in [('B4', 'forecast'), ('D3', '£ million')]:
            with self.subTest(cell=cell):
                original = self.workbook['4_3'][cell].value
                self.workbook['4_3'][cell] = value
                self.save_source()
                with self.assertRaises(checker.ValidationError):
                    checker.validate(self.root)
                self.workbook['4_3'][cell] = original

    def test_page_mutations(self):
        original = self.html
        for before, after in [('up by 50.0%', 'up by 51.0%'), ('£50.0 billion', '£49.0 billion'),
                              ('5.0 percentage points', '5.0 percent'), ('4_3!C20', '4_3!B20'),
                              ('2015-16 (outturn)', '2015-16 (forecast)'),
                              ('Has health spending gone up or down after inflation?', ''),
                              ('Is total spending a bigger or smaller share of the economy?', ''),
                              ('Spending by area', ''), ('goes on health', '')]:
            with self.subTest(before=before):
                self.html = original.replace(before, after)
                self.save_html()
                with self.assertRaises(checker.ValidationError):
                    checker.validate(self.root)

    def test_download_mutations(self):
        (self.root / 'site/sources/trends.xlsx').write_bytes(b'wrong download')
        with self.assertRaisesRegex(checker.ValidationError, 'Downloadable trends workbook'):
            checker.validate(self.root)


if __name__ == '__main__':
    unittest.main()
