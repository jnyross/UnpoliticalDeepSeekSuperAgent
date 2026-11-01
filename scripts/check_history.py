#!/usr/bin/env python3
"""Independent PESA history checks; never import the extraction/build code.

Reopen retained official workbook and check every exported observation and locator.
Run --self-test for offline, isolated mutation regression tests.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
from html.parser import HTMLParser
import shutil
import tempfile
import io
import json
import math
from pathlib import Path
import re
import sys
import unittest
from datetime import date, datetime

import openpyxl


class ValidationError(ValueError):
    """A history source/publication invariant failed."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


WORKBOOK_URL = ('https://assets.publishing.service.gov.uk/media/'
                '6a5772e09e63154454413700/PESA_2026_CP_Chapter_4_tables.xlsx')
WORKBOOK_SHA = '50ae80d95c4e542c34a17dfa8bc302858ca6508b6753e27bb31920cec9bb75c4'
RELEASE_URL = 'https://www.gov.uk/government/statistics/public-expenditure-statistical-analyses-2026'
SHEETS = {'cash': '4_2', 'real': '4_3', 'gdp': '4_4'}
YEARS = [f'{y}-{(y + 1) % 100:02d}' for y in range(2003, 2026)]
COMPARISONS = [f'{y}-{(y + 1) % 100:02d}' for y in range(2025, 1944, -10)]
AREA_ROWS = (6, 10, 11, 12, 18, 19, 20, 21, 22, 23, 24)
# Eleven independently rounded £0.1bn parts plus their rounded total.
CASH_ROUNDING_TOLERANCE = 0.6
RAW_LABELS = {
    6: '1. General public services', 7: 'of which: public and common services',
    8: 'of which: international services', 9: 'of which: public sector debt interest',
    10: '2. Defence', 11: '3. Public order and safety', 12: '4. Economic affairs',
    13: 'of which: enterprise and economic development', 14: 'of which: science and technology',
    15: 'of which: employment policies', 16: 'of which: agriculture, fisheries and forestry',
    17: 'of which: transport', 18: '5. Environment protection',
    19: '6. Housing and community amenities', 20: '7. Health',
    21: '8. Recreation, culture and religion', 22: '9. Education',
    23: '10. Social protection', 24: 'EU transactions',
    25: 'Public sector expenditure on services', 26: 'Accounting adjustments',
    27: 'Total Managed Expenditure',
}


def normalized_label(raw):
    return re.sub(r'\s*\(\d+\)(?:,\s*\(\d+\))*', '', str(raw)).strip()


def number(value, context):
    require(type(value) in (int, float) and math.isfinite(value),
            f'{context}: expected finite number, got {value!r}')
    return value


def validate_hash(raw, digest, context):
    require(hashlib.sha256(raw).hexdigest() == digest, f'{context}: SHA-256 mismatch')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def validate_manifest(manifest, release, raw):
    for key, expected in {
        'file': 'history.xlsx', 'url': WORKBOOK_URL, 'sha256': WORKBOOK_SHA,
        'publication': 'Public Expenditure Statistical Analyses 2026, Chapter 4',
        'release_url': RELEASE_URL, 'metadata_url': RELEASE_URL.replace('/government/', '/api/content/government/'),
        'metadata_file': 'history-release.json', 'sheets': SHEETS,
        'geography': 'United Kingdom', 'scope': 'Public sector expenditure on services',
        'status': 'outturn', 'years': '2003-04 to 2025-26', 'real_base_year': '2025-26',
        'deflator': 'ONS GDP deflators released 30 June 2026',
        'gdp_source': 'ONS GDP published 30 June 2026',
        'workbook_vintage': '2026-07-16',
    }.items():
        require(manifest.get(key) == expected, f'History manifest {key}: expected {expected!r}')
    validate_hash(raw, WORKBOOK_SHA, 'Official history workbook')
    require(manifest.get('published') == release['first_published_at'][:10], 'History publication date differs from metadata')
    require(manifest.get('date') == release['public_updated_at'][:10], 'History update date differs from metadata')
    for key in ('published', 'date', 'downloaded', 'workbook_vintage'):
        date.fromisoformat(manifest[key])
    require(date.fromisoformat(manifest['downloaded']) >= date.fromisoformat(manifest['date']),
            'History download predates release update')
    require(any(a.get('url') == WORKBOOK_URL and a.get('title') == 'PESA 2026 Chapter 4 Tables'
                and a.get('file_size') == len(raw) for a in release['details']['attachments']),
            'Retained release does not identify the history workbook')


def validate_workbook(workbook):
    require(set(SHEETS.values()) <= set(workbook.sheetnames), 'Missing history source sheets')
    for name, title in SHEETS.items():
        sheet = workbook[title]
        require(sheet['B4'].value == 'outturn', f'{title}!B4: expected outturn')
        require(sheet['X3'].value == ('per cent' if name == 'gdp' else '£ billion'),
                f'{title}: source unit changed')
        require([sheet.cell(5, c).value for c in range(2, 25)] == YEARS,
                f'{title}: source year headers changed')
        for row, expected in RAW_LABELS.items():
            require(normalized_label(sheet.cell(row, 1).value) == expected,
                    f'{title}!A{row}: source layout/label changed')
            for col in range(2, 25):
                number(sheet.cell(row, col).value, f'{title}!{sheet.cell(row, col).coordinate}')
    cash, real = workbook['4_2'], workbook['4_3']
    for col in range(2, 25):
        gap = abs(sum(cash.cell(r, col).value for r in AREA_ROWS) - cash.cell(25, col).value)
        require(gap <= CASH_ROUNDING_TOLERANCE + 1e-9,
                f'History cash {YEARS[col-2]}: area total exceeds £0.6bn rounding tolerance ({gap})')
        gap = abs(cash.cell(25, col).value + cash.cell(26, col).value - cash.cell(27, col).value)
        require(gap <= 0.15 + 1e-9, f'History cash {YEARS[col-2]}: TES + adjustments differs from TME')
    for row in RAW_LABELS:
        require(cash.cell(row, 24).value == real.cell(row, 24).value,
                f'History real base-year amount differs from cash at X{row}')
    require('2025-26 price levels' in real['A28'].value and '30 June 2026' in real['A28'].value,
            'Real price base or deflator vintage changed')
    require('30 June 2026' in workbook['4_4']['A28'].value, 'GDP vintage changed')


IDS = ('general-public-services', 'public-and-common-services', 'international-services',
       'public-sector-debt-interest', 'defence', 'public-order-and-safety', 'economic-affairs',
       'enterprise-and-economic-development', 'science-and-technology', 'employment-policies',
       'agriculture-fisheries-and-forestry', 'transport', 'environment-protection',
       'housing-and-community-amenities', 'health', 'recreation-culture-and-religion',
       'education', 'social-protection', 'eu-transactions', 'services-total',
       'accounting-adjustments', 'tme')
FIELDS = {'cash': 'cash_gbp_billion', 'real': 'real_gbp_billion', 'gdp': 'gdp_percent'}
UNITS = {'cash_gbp_billion': 'GBP billion, cash',
         'real_gbp_billion': 'GBP billion, 2025-26 prices', 'gdp_percent': 'percent of GDP'}
GAP = 'Not available in this retained July 2026 functional history; not zero.'


def expected_point(workbook, row, col):
    return dict(year=YEARS[col-2], status='outturn', missing_reason=None,
                cells={v: f'{s}!{openpyxl.utils.get_column_letter(col)}{row}' for v, s in SHEETS.items()},
                **{FIELDS[v]: workbook[s].cell(row, col).value for v, s in SHEETS.items()})


def same_point(actual, expected, context):
    require(isinstance(actual, dict), f'{context}: expected record')
    require(set(actual) == set(expected), f'{context}: unexpected/missing record fields')
    for field, value in expected.items():
        if field in FIELDS.values() and value is not None:
            number(actual.get(field), f'{context}.{field}')
        require(actual.get(field) == value, f'{context}.{field}: differs from raw source: expected {value!r}')


def validate_data(data, manifest, workbook):
    validate_workbook(workbook)
    require(data.get('source') == manifest, 'History source differs from manifest')
    require(data.get('geography') == 'United Kingdom', 'History geography differs')
    require(data.get('years') == YEARS, 'History exported years differ from raw headers')
    require(data.get('units') == UNITS, 'History units differ from source')
    expected_notes = {s: [{'cell': f'{s}!A{r}', 'text': workbook[s].cell(r, 1).value}
                          for r in range(28, 37) if workbook[s].cell(r, 1).value]
                      for s in SHEETS.values()}
    expected_notes['4_1'] = [{'cell': f'4_1!B{r}', 'text': workbook['4_1'].cell(r, 2).value}
                              for r in (51, 52, 53)]
    require(data.get('notes') == expected_notes, 'History source notes/locators differ')
    series = data.get('series')
    require(isinstance(series, list) and len(series) == 22, 'Expected all 22 history series')
    for row, ident, actual in zip(range(6, 28), IDS, series):
        label = RAW_LABELS[row]
        scope = ('Total Managed Expenditure' if row == 27 else
                 'Accounting adjustments between TES and TME' if row == 26 else
                 'Public sector expenditure on services')
        for key, expected in {'id': ident, 'label': label, 'scope': scope, 'source_row': row,
                              'is_subcategory': label.startswith('of which:')}.items():
            require(actual.get(key) == expected, f'History {ident}.{key}: expected {expected!r}')
        values = actual.get('values')
        require(isinstance(values, list) and len(values) == 23, f'{ident}: expected 23 annual observations')
        for col, point in enumerate(values, 2):
            same_point(point, expected_point(workbook, row, col), f'{ident} {YEARS[col-2]}')
    require(data.get('fixed_comparison_years') == COMPARISONS, 'Fixed-decade selection rule changed')
    require(data.get('latest_overview_year') == '2025-26', 'Latest overview year differs')
    main_rows = (*AREA_ROWS, 25, 27)
    fixed = data.get('fixed_comparisons')
    require(isinstance(fixed, list) and len(fixed) == len(main_rows), 'Fixed comparisons omit/add areas')
    for row, actual in zip(main_rows, fixed):
        require(actual.get('id') == IDS[row-6] and actual.get('label') == RAW_LABELS[row],
                'Fixed comparison series/label differs')
        require(len(actual.get('values', [])) == len(COMPARISONS), 'Fixed comparison missing/extra years')
        for year, point in zip(COMPARISONS, actual['values']):
            if year in YEARS:
                expected = expected_point(workbook, row, YEARS.index(year) + 2)
            elif row == 27 and year in ('1985-86', '1995-96'):
                aggregate = workbook['4_1']
                source_row = 6 if year == '1985-86' else 16
                require(aggregate.cell(source_row, 2).value == year, 'Aggregate TME year changed')
                require('2025-26' in aggregate['B3'].value and 'Outturn' in aggregate['B3'].value,
                        'Aggregate TME outturn header changed')
                require(aggregate['M4'].value == 'Total Managed Expenditure (3)' and
                        aggregate['M5'].value == 'Nominal\n£ billion' and
                        aggregate['N5'].value == 'Real terms (1)\n£ billion' and
                        aggregate['O5'].value == 'Per cent\nof GDP (2)', 'Aggregate TME units/scope changed')
                expected = dict(year=year, status='outturn', missing_reason=None,
                                cells={v: f'4_1!{openpyxl.utils.get_column_letter(c)}{source_row}'
                                       for v, c in zip(SHEETS, (13, 14, 15))},
                                **{f: number(aggregate.cell(source_row, c).value, 'Aggregate TME')
                                   for f, c in zip(FIELDS.values(), (13, 14, 15))})
            else:
                expected = dict(year=year, status='unavailable', cells={}, missing_reason=GAP,
                                **{f: None for f in FIELDS.values()})
            same_point(point, expected, f'Fixed {IDS[row-6]} {year}')


CSV_COLUMNS = ['series_id', 'label', 'scope', 'geography', 'year', 'status',
               'cash_gbp_billion', 'real_gbp_billion_2025_26_prices', 'gdp_percent',
               'cash_cell', 'real_cell', 'gdp_cell', 'missing_reason', 'source_vintage',
               'source_sha256', 'selection']


def validate_csv(raw, data):
    rows = list(csv.reader(io.StringIO(raw)))
    require(bool(rows) and rows[0] == CSV_COLUMNS, 'History CSV columns/units changed')
    expected = []
    scopes = {s['id']: s['scope'] for s in data['series']}
    for selection, series in [('annual', data['series']), ('fixed_decade', data['fixed_comparisons'])]:
        for s in series:
            for p in s['values']:
                expected.append([s['id'], s['label'], scopes[s['id']], 'United Kingdom', p['year'],
                    p['status'], *[p[f] for f in FIELDS.values()],
                    *[p['cells'].get(v, '') for v in SHEETS], p['missing_reason'] or '',
                    data['source']['workbook_vintage'], data['source']['sha256'], selection])
    require(len(rows) == len(expected) + 1, 'History CSV missing/extra observations')
    for i, (actual, wanted) in enumerate(zip(rows[1:], expected), 2):
        require(len(actual) == len(CSV_COLUMNS), f'History CSV row {i}: column count')
        for col, (left, right) in enumerate(zip(actual, wanted)):
            if 6 <= col <= 8 and right is not None:
                try:
                    left = float(left)
                except ValueError as exc:
                    raise ValidationError(f'History CSV row {i}: invalid number') from exc
                number(left, f'CSV row {i}')
            elif right is None:
                right = ''
            require(left == right, f'History CSV row {i} {CSV_COLUMNS[col]} differs')


def compact(text):
    return ' '.join(text.split())


class HistoryTables(HTMLParser):
    """Extract visible table content without importing the renderer or checker."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.table = None
        self.row = None
        self.parts = None
        self.caption = None

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            require(self.table is None, 'Nested history table')
            self.table = {'caption': '', 'rows': []}
        elif tag == 'caption' and self.table is not None:
            self.caption = []
        elif tag == 'tr' and self.table is not None:
            self.row = []
        elif tag in ('td', 'th') and self.row is not None:
            self.parts = []
        elif tag == 'br' and self.parts is not None:
            self.parts.append(' ')

    def handle_data(self, text):
        if self.caption is not None:
            self.caption.append(text)
        if self.parts is not None:
            self.parts.append(text)

    def handle_endtag(self, tag):
        if tag == 'caption' and self.caption is not None:
            self.table['caption'] = compact(''.join(self.caption))
            self.caption = None
        elif tag in ('td', 'th') and self.parts is not None:
            self.row.append(compact(''.join(self.parts)))
            self.parts = None
        elif tag == 'tr' and self.row is not None:
            self.table['rows'].append(self.row)
            self.row = None
        elif tag == 'table' and self.table is not None:
            self.tables.append(self.table)
            self.table = None


def validate_html(raw, data):
    parser = HistoryTables()
    parser.feed(raw)
    expected = []
    for fixed, series in [(False, data['series']), (True, data['fixed_comparisons'])]:
        for s in series:
            rows = [['Fiscal year', 'Cash £bn', 'Real £bn, 2025-26 prices',
                     'GDP share %', 'Status and source cells']]
            for p in s['values']:
                status = p['status'] + (': ' + p['missing_reason'] if p['missing_reason'] else '')
                locators = ' · '.join(p['cells'][v] for v in SHEETS if v in p['cells'])
                rows.append([p['year'], *['Not available' if p[f] is None else f'{p[f]:,.1f}'
                                         for f in FIELDS.values()], compact(status + ' ' + locators)])
            expected.append({'caption': s['label'] + (' — fixed ten-year snapshots' if fixed else ' — annual history'),
                             'rows': rows})
    require(len(parser.tables) == len(expected), 'History HTML missing/extra tables')
    for actual, wanted in zip(parser.tables, expected):
        require(actual == wanted, f'History HTML displayed values/units/status/locators differ: {wanted["caption"]}')


def validate(root):
    root = Path(root)
    manifest = read_json(root / 'sources/history-manifest.json')
    raw = (root / 'sources/history.xlsx').read_bytes()
    release_raw = (root / 'sources/history-release.json').read_bytes()
    validate_hash(release_raw, manifest.get('metadata_sha256'), 'History release metadata')
    validate_manifest(manifest, json.loads(release_raw), raw)
    for filename in ('history.xlsx', 'history-manifest.json', 'history-release.json'):
        require((root / 'sources' / filename).read_bytes() == (root / 'site/sources' / filename).read_bytes(),
                f'Downloadable {filename} differs from retained source')
    workbook = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
    try:
        modified = workbook.properties.modified
        require(modified.isoformat() + 'Z' == manifest.get('workbook_modified'), 'Workbook modified date differs')
        data = read_json(root / 'site/data/history.json')
        validate_data(data, manifest, workbook)
        overview = read_json(root / 'sources/manifest.json')
        require(data.get('overview_source') == overview, 'History overview source metadata differs')
        validate_csv((root / 'site/data/history.csv').read_text(encoding='utf-8'), data)
        validate_html((root / 'site/history.html').read_text(encoding='utf-8'), data)
    finally:
        workbook.close()
    print('PASS: independent history SHA/source copies, every annual/fixed JSON/CSV/HTML observation, '
          'year, units, status, locators, notes, base year and cash reconciliation')


class MutationTests(unittest.TestCase):
    """Mutate private copies of the retained release; no extractor or network calls."""
    root = Path(__file__).resolve().parents[1]

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='history-check-')
        self.addCleanup(self.temp.cleanup)
        self.stage = Path(self.temp.name)
        for relative in ('sources/history.xlsx', 'sources/history-manifest.json',
                         'sources/history-release.json', 'sources/manifest.json',
                         'site/sources/history.xlsx', 'site/sources/history-manifest.json',
                         'site/sources/history-release.json', 'site/data/history.json',
                         'site/data/history.csv', 'site/history.html'):
            target = self.stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.root / relative, target)

    def mutate_json(self, change):
        path = self.stage / 'site/data/history.json'
        data = read_json(self.root / 'site/data/history.json')
        change(data)
        path.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaises(ValidationError):
            validate(self.stage)

    def test_valid_snapshot(self):
        validate(self.stage)

    def test_each_numeric_view(self):
        for field in FIELDS.values():
            with self.subTest(field=field):
                self.mutate_json(lambda d: d['series'][0]['values'][0].update({field: 12345}))

    def test_bool_not_a_number(self):
        self.mutate_json(lambda d: d['series'][0]['values'][0].update(cash_gbp_billion=True))

    def test_nonfinite_not_a_number(self):
        self.mutate_json(lambda d: d['series'][0]['values'][0].update(cash_gbp_billion=float('nan')))

    def test_year(self):
        self.mutate_json(lambda d: d['series'][0]['values'][0].update(year='2002-03'))

    def test_status(self):
        self.mutate_json(lambda d: d['series'][0]['values'][0].update(status='forecast'))

    def test_locator(self):
        self.mutate_json(lambda d: d['series'][0]['values'][0]['cells'].update(real='4_2!B6'))

    def test_units(self):
        self.mutate_json(lambda d: d['units'].update(real_gbp_billion='GBP billion, 2024-25 prices'))

    def test_label_scope_and_row(self):
        for field, value in [('label', 'Wrong'), ('scope', 'Total Managed Expenditure'), ('source_row', 7)]:
            with self.subTest(field=field):
                self.mutate_json(lambda d: d['series'][0].update({field: value}))

    def test_omitted_series(self):
        self.mutate_json(lambda d: d['series'].pop())

    def test_duplicate_or_omitted_year(self):
        self.mutate_json(lambda d: d['series'][0]['values'].pop())

    def test_fixed_decade_rule(self):
        self.mutate_json(lambda d: d['fixed_comparison_years'].reverse())

    def test_missing_is_not_zero(self):
        self.mutate_json(lambda d: d['fixed_comparisons'][0]['values'][-1].update(cash_gbp_billion=0))

    def test_aggregate_old_tme(self):
        self.mutate_json(lambda d: d['fixed_comparisons'][-1]['values'][3].update(cash_gbp_billion=0))

    def test_source_note(self):
        self.mutate_json(lambda d: d['notes']['4_3'][0].update(text='Wrong price base'))

    def test_source_metadata(self):
        self.mutate_json(lambda d: d['source'].update(real_base_year='2024-25'))

    def test_raw_sha(self):
        path = self.stage / 'sources/history.xlsx'
        path.write_bytes(path.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValidationError, 'SHA-256'):
            validate(self.stage)

    def test_release_sha(self):
        path = self.stage / 'sources/history-release.json'
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValidationError, 'SHA-256'):
            validate(self.stage)

    def test_download_copies(self):
        for filename in ('history.xlsx', 'history-manifest.json', 'history-release.json'):
            with self.subTest(filename=filename):
                path = self.stage / 'site/sources' / filename
                original = path.read_bytes()
                path.write_bytes(original + b' ')
                with self.assertRaisesRegex(ValidationError, 'Downloadable'):
                    validate(self.stage)
                path.write_bytes(original)

    def test_csv_value_and_locator(self):
        path = self.stage / 'site/data/history.csv'
        original = path.read_text(encoding='utf-8')
        rows = list(csv.reader(io.StringIO(original)))
        for col in (6, 7, 8, 9, 10, 11):
            with self.subTest(col=col):
                changed = copy.deepcopy(rows)
                changed[1][col] = '99999' if col < 9 else '4_2!Z99'
                stream = io.StringIO()
                csv.writer(stream).writerows(changed)
                path.write_text(stream.getvalue(), encoding='utf-8')
                with self.assertRaisesRegex(ValidationError, 'CSV'):
                    validate(self.stage)

    def test_html_amount_and_locator(self):
        path = self.stage / 'site/history.html'
        original = path.read_text(encoding='utf-8')
        for old, new in [('4_2!B6', '4_2!Z99'), ('<td>', '<td>99999')]:
            with self.subTest(old=old):
                require(old in original, 'HTML regression fixture missing target')
                path.write_text(original.replace(old, new, 1), encoding='utf-8')
                with self.assertRaisesRegex(ValidationError, 'HTML'):
                    validate(self.stage)

    def test_raw_layout_and_rounding(self):
        raw = (self.root / 'sources/history.xlsx').read_bytes()
        for cell, value, message in [('A20', 'Wrong', 'layout'), ('X3', '£ million', 'unit'),
                                     ('B4', 'forecast', 'outturn'), ('B5', '2002-03', 'headers'),
                                     ('B6', 9999, 'rounding'), ('X20', 9999, 'rounding')]:
            with self.subTest(cell=cell):
                workbook = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
                workbook['4_2'][cell] = value
                with self.assertRaisesRegex(ValidationError, message):
                    validate_workbook(workbook)
                workbook.close()

    def test_rounding_boundary(self):
        workbook = openpyxl.load_workbook(self.root / 'sources/history.xlsx', data_only=True)
        self.addCleanup(workbook.close)
        cash = workbook['4_2']
        cash['B6'] = cash['B25'].value - sum(cash.cell(r, 2).value for r in AREA_ROWS if r != 6) + 0.6
        validate_workbook(workbook)
        cash['B6'] = cash['B6'].value + 0.1
        with self.assertRaisesRegex(ValidationError, 'rounding'):
            validate_workbook(workbook)

    def test_real_base_year(self):
        workbook = openpyxl.load_workbook(self.root / 'sources/history.xlsx', data_only=True)
        self.addCleanup(workbook.close)
        workbook['4_3']['X20'] = 9999
        with self.assertRaisesRegex(ValidationError, 'base-year'):
            validate_workbook(workbook)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--self-test', action='store_true', help='run isolated offline mutation tests')
    args = parser.parse_args()
    if args.self_test:
        MutationTests.root = args.root.resolve()
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(MutationTests))
        return 0 if result.wasSuccessful() else 1
    try:
        validate(args.root.resolve())
    except (ValueError, OSError, KeyError, TypeError, AssertionError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
