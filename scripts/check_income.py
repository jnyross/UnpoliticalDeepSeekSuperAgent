#!/usr/bin/env python3
"""Independently reopen the retained OBR workbook; never import income extraction."""
from __future__ import annotations

import argparse
import csv
from datetime import date
import hashlib
import io
import json
import math
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import sys

import openpyxl


class ValidationError(ValueError):
    """An income publication/source invariant failed."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


WORKBOOK_SHA = '16a4bf46d8692e18790e87add342c6c44aa909cebb19f68ae857126a36d36459'
YEAR = '2025-26'
FORECAST_YEARS = ['2026-27', '2027-28', '2028-29', '2029-30', '2030-31', '2031-32']
UNIT = 'GBP billion, cash'
GEOGRAPHY = 'United Kingdom'
RECEIPTS = 'Receipts (£bn)'
AGGREGATES = 'Aggregates (£bn)'
# Three independently rounded £0.001bn inputs: spending - receipts - borrowing.
BORROWING_ROUNDING = 0.0015
# 30 receipt components and their total each rounded to £0.001bn.
RECEIPT_ROUNDING = 0.0155
ARITHMETIC_TOLERANCE = 0.000001


def number(value, context):
    require(type(value) in (int, float) and math.isfinite(value),
            f'{context}: expected finite number, not {value!r}')
    return value


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def check_hash(raw, digest, context):
    require(hashlib.sha256(raw).hexdigest() == digest, f'{context}: SHA-256 mismatch')


def close(actual, expected, tolerance, context):
    require(abs(number(actual, context) - number(expected, context)) <= tolerance + 1e-9,
            f'{context}: reconciliation outside source rounding tolerance ({actual} vs {expected})')


def validate_workbook(workbook):
    """Check semantic cells before trusting any exported locator or arithmetic."""
    require({RECEIPTS, AGGREGATES, 'Glossary', 'Aggregates (per cent of GDP)'} <= set(workbook.sheetnames),
            'Missing income source sheets')
    r, a = workbook[RECEIPTS], workbook[AGGREGATES]
    require(r['C1'].value == 'Public sector current receipts', 'Receipt source title changed')
    require(a['C1'].value == '£ billion', 'Aggregate source unit changed')
    for sheet, current, following in ((r, 'B33', 'B34'), (a, 'B87', 'B88')):
        require(sheet[current].value == YEAR and sheet[following].value == '2026-27',
                'Source year/forecast boundary changed')
    for sheet, outturn, forecast in ((r, 'C40', 'C41'), (a, 'C94', 'C95')):
        require(sheet[outturn].value == 'Outturn fiscal data consistent with the ONS/HM Treasury Public Sector Finances Statistical Bulletin released on 22 September 2026.',
                'Source outturn status/vintage changed')
        require(sheet[forecast].value == 'Forecast years from 2026-27 are consistent with the OBR Economic and fiscal outlook forecast published October 2026.',
                'Source forecast boundary changed')
    for cell, label in {'C4': 'Public sector current receipts', 'D4': 'Total managed expenditure',
                        'I4': 'National account taxes', 'O4': 'Public sector net borrowing',
                        'V4': 'Central government debt interest, net of APF',
                        'X4': 'Public sector net debt'}.items():
        require(a[cell].value == label, f'Aggregate {cell}: source label/scope changed')
    require(a['X5'].value == 'HF6W' and a['V5'].value == 'NMFX+MU74',
            'Debt stock confused with debt interest flow')
    require(workbook['Aggregates (per cent of GDP)']['C90'].value ==
            '2 Debt at end March; GDP centred on end-March.', 'Debt stock date definition changed')
    require('stock measure' in workbook['Glossary']['C14'].value,
            'Debt must be a stock measure, not debt interest')
    for col in range(3, 35):
        number(r.cell(33, col).value, f'Receipts row 33 column {col}')
        require(isinstance(r.cell(4, col).value, str) and isinstance(r.cell(5, col).value, str),
                'Receipt label or ONS code missing')
    for cell in ('C87', 'D87', 'I87', 'O87', 'V87', 'X87'):
        number(a[cell].value, f'Aggregates {cell}')
    close(sum(r.cell(33, c).value for c in range(3, 33)), r['AG33'].value,
          RECEIPT_ROUNDING, 'Receipt component total (including VAT refunds)')
    close(r['AG33'].value, a['C87'].value, 0.001, 'Compatible cross-table receipts')
    close(r['AH33'].value, a['I87'].value, 0.001, 'Compatible cross-table taxes')
    close(a['D87'].value - a['C87'].value, a['O87'].value,
          BORROWING_ROUNDING, 'Compatible spending minus receipts equals borrowing')


    # Independently fix this retained vintage's full coverage and semantic boundary.
    for sheet, start in ((r, 34), (a, 88)):
        years = [c.value for c in sheet['B'] if isinstance(c.value, str)
                 and re.fullmatch(r'\d{4}-\d{2}', c.value) and c.value >= FORECAST_YEARS[0]]
        exact(years, FORECAST_YEARS, 'Complete forecast source coverage')
        for offset, period in enumerate(FORECAST_YEARS):
            require(sheet.cell(start + offset, 2).value == period, 'Forecast source row changed')
    for offset, period in enumerate(FORECAST_YEARS):
        rr, ar = 34 + offset, 88 + offset
        for sheet, address in ((r, f'AG{rr}'), (a, f'C{ar}'), (a, f'D{ar}'), (a, f'O{ar}'), (a, f'X{ar}')):
            number(sheet[address].value, f'Forecast {period} {address}')
        close(r[f'AG{rr}'].value, a[f'C{ar}'].value, ARITHMETIC_TOLERANCE, f'Forecast {period} receipts')
        close(a[f'D{ar}'].value - r[f'AG{rr}'].value, a[f'O{ar}'].value,
              ARITHMETIC_TOLERANCE, f'Forecast {period} borrowing')


SCOPE = 'UK public sector, OBR public finances definitions'
CSV_COLUMNS = ['id', 'label', 'kind', 'value_gbp_billion', 'unit', 'geography',
               'scope', 'period', 'status', 'cells', 'ons_code', 'formula', 'operands',
               'source_publication', 'source_published', 'source_url', 'source_sha256',
               'source_status_cell', 'source_status_note']
ROUNDING = 'Raw values are retained to 12 decimal places in GBP billion; HTML rounds to 0.1 billion. Source actuals are recorded to 0.001 billion. Reconciliations use unrounded data with 0.000001 billion numeric tolerance, not independently rounded display amounts.'
SELECTION = 'Latest complete outturn before the first forecast year stated in Receipts (£bn)!C41.'
RECONCILIATION = 'All identities use one OBR workbook vintage and public sector accounting basis. Tax rows C:AC plus the derived other-tax residual equal national accounts taxes. AF is a mixed tax/non-tax line, not a tax type. It is split by residual against the published tax total; the residuals do not identify further individual taxes. The VAT refund row belongs in the published national accounts tax basis: do not subtract it again or treat it as non-tax. Negative tax entries are net receipts or repayments, not missing data. TME less current receipts equals net borrowing on this accrued basis. Debt is not added to annual receipts or borrowing; changes in debt also reflect financial transactions and cash/accrual differences. This workbook is not reconciled to a separate Treasury workbook vintage.'


def expected_records(workbook):
    """Independent specification of exported records, not extraction code imports."""
    records = []
    for col in range(3, 30):
        letter = openpyxl.utils.get_column_letter(col)
        label = re.sub(r'(?<=[a-z)])\d+$', '', workbook[RECEIPTS].cell(4, col).value).strip()
        records.append(dict(id='receipt-' + letter.lower(), label=label, kind='tax-type',
                            cells=[f'{RECEIPTS}!{letter}33']))
    for ident, label, kind, sheet, address in [
        ('interest-dividends', 'Interest and dividend receipts', 'non-tax-type', RECEIPTS, 'AD33'),
        ('operating-surplus', 'Gross operating surplus', 'non-tax-type', RECEIPTS, 'AE33'),
        ('mixed-other-receipts', 'Other public sector taxes and receipts (mixed source line)', 'mixed', RECEIPTS, 'AF33'),
        ('receipts', 'Public sector current receipts', 'total', RECEIPTS, 'AG33'),
        ('taxes', 'National accounts taxes', 'total', RECEIPTS, 'AH33'),
        ('tme', 'Total Managed Expenditure', 'spending', AGGREGATES, 'D87'),
        ('borrowing', 'Public sector net borrowing', 'borrowing', AGGREGATES, 'O87'),
        ('debt', 'Public sector net debt', 'stock', AGGREGATES, 'X87')]:
        records.append(dict(id=ident, label=label, kind=kind, cells=[f'{sheet}!{address}']))
    for record in records:
        sheet, address = record['cells'][0].split('!')
        record.update(value_gbp_billion=round(number(workbook[sheet][address].value, address), 12),
                      formula=None, operands=[], scope=SCOPE, status='outturn', unit=UNIT,
                      geography=GEOGRAPHY, period='end-March 2026' if record['id'] == 'debt' else YEAR,
                      ons_code=workbook[sheet][re.sub(r'\d+', '5', address)].value)
    lookup = {r['id']: r for r in records}
    taxes = ['receipt-' + openpyxl.utils.get_column_letter(c).lower() for c in range(3, 30)]
    specifications = [
        ('other-taxes', 'Other taxes (residual, not separately named here)', 'tax-type',
         ['taxes'] + taxes, 'taxes - sum(receipt-c through receipt-ac)'),
        ('non-tax', 'Non-tax receipts', 'total', ['receipts', 'taxes'], 'receipts - taxes'),
        ('other-non-tax', 'Other non-tax receipts (residual)', 'non-tax-type',
         ['non-tax', 'interest-dividends', 'operating-surplus'],
         'non-tax - interest-dividends - operating-surplus')]
    for ident, label, kind, operands, formula in specifications:
        wanted = lookup[operands[0]]['value_gbp_billion'] - sum(lookup[i]['value_gbp_billion'] for i in operands[1:])
        cells = list(dict.fromkeys(c for i in operands for c in lookup[i]['cells']))
        record = dict(id=ident, label=label, kind=kind, value_gbp_billion=round(wanted, 12),
                      cells=cells, formula=formula, operands=operands, scope=SCOPE, period=YEAR,
                      status='outturn', unit=UNIT, geography=GEOGRAPHY, ons_code=None)
        records.append(record)
        lookup[ident] = record
    for offset, period in enumerate(FORECAST_YEARS):
        for ident, label, kind, sheet, address in [
            ('receipts', 'Public sector current receipts', 'total', RECEIPTS, f'AG{34+offset}'),
            ('borrowing', 'Public sector net borrowing', 'borrowing', AGGREGATES, f'O{88+offset}'),
            ('debt', 'Public sector net debt', 'stock', AGGREGATES, f'X{88+offset}')]:
            records.append(dict(id=f'forecast-{ident}-{period}', label=label, kind=kind,
                cells=[f'{sheet}!{address}'], value_gbp_billion=round(number(workbook[sheet][address].value, address), 12),
                formula=None, operands=[], scope=SCOPE, status='forecast', unit=UNIT,
                geography=GEOGRAPHY, period='end-March ' + str(int(period[:4])+1) if ident == 'debt' else period,
                ons_code=workbook[sheet][re.sub(r'\d+', '5', address)].value))
    return records


def exact(actual, expected, context):
    """Strict recursive comparison, rejecting bool-as-number and NaN loopholes."""
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and set(actual) == set(expected), f'{context}: record fields differ')
        for key in expected:
            exact(actual[key], expected[key], f'{context}.{key}')
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), f'{context}: list count differs')
        for index, (left, right) in enumerate(zip(actual, expected)):
            exact(left, right, f'{context}[{index}]')
    else:
        if type(expected) in (int, float):
            number(actual, context)
        require(actual == expected and (expected is not None or actual is None),
                f'{context}: differs from independent source expectation {expected!r}')


def validate_data(data, manifest, workbook):
    validate_workbook(workbook)
    expected = expected_records(workbook)
    exact(data.get('records'), expected, 'Income records')
    by_id = {r['id']: r['value_gbp_billion'] for r in expected}
    checks = []
    specs = [
        ('Tax breakdown', 'sum(tax-type records) - taxes',
         sum(r['value_gbp_billion'] for r in expected if r['kind'] == 'tax-type') - by_id['taxes']),
        ('Non-tax breakdown', 'sum(non-tax-type records) - non-tax',
         sum(r['value_gbp_billion'] for r in expected if r['kind'] == 'non-tax-type') - by_id['non-tax']),
        ('Mixed other line split', 'other-taxes + other-non-tax - mixed-other-receipts',
         by_id['other-taxes'] + by_id['other-non-tax'] - by_id['mixed-other-receipts']),
        ('Spending and receipts', 'tme - receipts - borrowing',
         by_id['tme'] - by_id['receipts'] - by_id['borrowing']),
        ('Receipts across sheets', 'Receipts AG - Aggregates C',
         by_id['receipts'] - workbook[AGGREGATES]['C87'].value),
        ('Taxes across sheets', 'Receipts AH - Aggregates I',
         by_id['taxes'] - workbook[AGGREGATES]['I87'].value)]
    for name, formula, residual in specs:
        tolerance = BORROWING_ROUNDING if name == 'Spending and receipts' else ARITHMETIC_TOLERANCE
        close(residual, 0, tolerance, name)
        checks.append(dict(name=name, formula=formula, residual_gbp_billion=round(residual, 12),
                           tolerance_gbp_billion=ARITHMETIC_TOLERANCE))
    notes = [{'cell': f'{sheet}!{cell}', 'text': workbook[sheet][cell].value}
             for sheet, cells in [(RECEIPTS, ['C40', 'C41', 'C42']),
                                  ('Glossary', ['C5', 'C6', 'C11', 'C14', 'C15'])]
             for cell in cells]
    wanted = dict(source=manifest, geography=GEOGRAPHY, year=YEAR, status='outturn', unit=UNIT,
                  scope=SCOPE, records=expected, checks=checks, notes=notes, rounding=ROUNDING,
                  selection=SELECTION, reconciliation=RECONCILIATION,
                  forecast_years=FORECAST_YEARS, forecast_source_note=dict(cell=f'{RECEIPTS}!C41', text=workbook[RECEIPTS]['C41'].value))
    exact(data, wanted, 'Income JSON')


def validate_csv(raw, data):
    rows = list(csv.reader(io.StringIO(raw)))
    require(bool(rows) and rows[0] == CSV_COLUMNS, 'Income CSV columns differ')
    require(len(rows) == len(data['records']) + 1, 'Income CSV missing/extra records')
    for index, (row, record) in enumerate(zip(rows[1:], data['records']), 2):
        require(len(row) == len(CSV_COLUMNS), f'Income CSV row {index}: column count differs')
        expected = dict(record, cells='; '.join(record['cells']), operands='; '.join(record['operands']))
        expected.update({'source_' + field: data['source'][field]
                         for field in ('publication', 'published', 'url', 'sha256')})
        for field, value in zip(CSV_COLUMNS, row):
            wanted = expected[field]
            # A CSV is lossless text, including the 12-decimal stored numeric representation.
            require(value == ('' if wanted is None else str(wanted)),
                    f'Income CSV row {index} {field}: differs from source-checked JSON')


def validate_manifest(manifest, raw, metadata):
    check_hash(raw, manifest.get('sha256'), 'Income workbook')
    check_hash(metadata, manifest.get('metadata_sha256'), 'Income release metadata')
    for field, value in {'file': 'income.xlsx', 'metadata_file': 'income-release.txt',
                         'geography': GEOGRAPHY, 'scope': SCOPE,
                         'release_url': 'https://obr.uk/data/'}.items():
        require(manifest.get(field) == value, f'Income manifest {field} differs')
    for field in ('url', 'download_url'):
        require(isinstance(manifest.get(field), str) and manifest[field].startswith('https://obr.uk/'),
                f'Income manifest {field}: not official OBR URL')
    text = unescape(metadata.decode('utf-8'))
    plain = ' '.join(re.sub(r'<[^>]*>', ' ', text).split())
    require(manifest['download_url'] in text, 'Income official download not in retained release')
    require(manifest.get('publication') in plain, 'Income publication not in retained release')
    published = date.fromisoformat(manifest['published'])
    require(published.strftime('%-d %B %Y') in plain, 'Income publication date not in retained release')
    require(manifest.get('date') == manifest['published'], 'Income source date differs from release date')
    require(date.fromisoformat(manifest['downloaded']) >= published, 'Income downloaded before publication')
    require(manifest.get('next_release') == 'No next release date is announced on the retained OBR data page; databanks are normally updated around two working days after the monthly public finance release.',
            'Income release schedule metadata differs')


class IncomeHTML(HTMLParser):
    """Read visible text and table cells; hidden content cannot supply evidence."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = []
        self.text = []
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None
        self.caption = None
        self.summary_row_classes = []
        self.semantic_errors = []
        self.in_summary = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        suppressed = (tag in ('head', 'script', 'style', 'template') or 'hidden' in attrs
                      or attrs.get('aria-hidden') == 'true' or 'display:none' in attrs.get('style', '').replace(' ', ''))
        if tag not in ('br', 'meta', 'link', 'img', 'input', 'hr', 'wbr'):
            self.hidden.append((tag, suppressed or (self.hidden[-1][1] if self.hidden else False)))
        if (self.hidden and self.hidden[-1][1]) or suppressed:
            return
        self.text.append(' ')
        if tag == 'table':
            self.in_summary = attrs.get('class') == 'forecast-summary'
            self.table = {'caption': '', 'rows': []}
        elif tag == 'caption':
            self.caption = []
        elif tag == 'tr':
            if self.in_summary and attrs.get('class'):
                self.summary_row_classes.append(attrs['class'])
            self.row = []
        elif tag in ('td', 'th'):
            if tag == 'th' and attrs.get('scope') not in ('row', 'col'):
                self.semantic_errors.append('Table header lacks scope')
            self.cell = []
        elif tag == 'br' and self.cell is not None:
            self.cell.append(' ')

    def handle_data(self, text):
        if self.hidden and self.hidden[-1][1]:
            return
        self.text.append(text)
        if self.cell is not None:
            self.cell.append(text)
        if self.caption is not None:
            self.caption.append(text)

    def handle_endtag(self, tag):
        suppressed = self.hidden[-1][1] if self.hidden else False
        if self.hidden and self.hidden[-1][0] == tag:
            self.hidden.pop()
        if suppressed:
            return
        self.text.append(' ')
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        elif tag == 'caption' and self.caption is not None:
            self.table['caption'] = ' '.join(''.join(self.caption).split())
            self.caption = None
        elif tag == 'tr' and self.row is not None:
            self.table['rows'].append(self.row)
            self.row = None
        elif tag == 'table' and self.table is not None:
            self.tables.append(self.table)
            self.table = None


def validate_html(raw, data):
    parser = IncomeHTML()
    parser.feed(raw)
    records = {r['id']: r for r in data['records']}
    summary_rows = [['Fiscal year / status', 'Receipts £bn', 'Borrowing £bn', 'Net debt £bn', 'Debt date / source cells']]
    for period in [YEAR] + FORECAST_YEARS:
        forecast = period != YEAR
        selected = [records[f'forecast-{i}-{period}' if forecast else i] for i in ('receipts', 'borrowing', 'debt')]
        summary_rows.append([period + (' Forecast' if forecast else ' Outturn (recorded)')]
            + [f'{r["value_gbp_billion"]:,.1f}' for r in selected]
            + [f'end-March {int(period[:4])+1} ' + '; '.join(r['cells'][0] for r in selected)])
    tables = [dict(caption='Latest outturn and OBR forecasts · United Kingdom · cash £ billion', rows=summary_rows)]
    exact(parser.summary_row_classes, ['outturn'] + ['forecast'] * len(FORECAST_YEARS), 'Forecast row style/status')
    require(not parser.semantic_errors, 'Semantic table headers require scope')
    require('.forecast-summary .forecast>*{border-top:2px dashed #555;border-bottom:2px dashed #555;' in raw,
            'Forecast dashed row styling missing')
    require('.forecast-summary .outturn>*{border-top:2px solid #555;border-bottom:2px solid #555}' in raw,
            'Outturn solid row styling missing')
    groups = [('Tax types in ' + YEAR, [r for r in data['records'] if r['kind'] == 'tax-type'] + [records['taxes']]),
              ('Non-tax receipts in ' + YEAR, [r for r in data['records'] if r['kind'] == 'non-tax-type'] + [records['non-tax']]),
              ('Annual flows and the year-end debt stock', [records[i] for i in ('receipts', 'taxes', 'non-tax', 'tme', 'borrowing', 'debt')])]
    for title, rows in groups:
        expected = [['Type', '£bn', 'Status / period', 'Source cell / formula']]
        for record in rows:
            locator = '; '.join(record['cells']) + (' Derived: ' + record['formula'] if record['formula'] else '')
            expected.append([record['label'], f'{record["value_gbp_billion"]:,.1f}',
                             record['status'] + ' ' + record['period'], locator])
        tables.append(dict(caption=title + ' · United Kingdom · cash £ billion', rows=expected))
    exact(parser.tables, tables, 'Income HTML tables')
    text = ' '.join(''.join(parser.text).split())
    amount = lambda i: f'£{records[i]["value_gbp_billion"]:,.1f} billion'
    income_tax = sum(records[i]['value_gbp_billion'] for i in ('receipt-q', 'receipt-r', 'receipt-s'))
    phrases = [f'In {YEAR}, the UK public sector took in {amount("receipts")}',
               f'Of this, {amount("taxes")} was tax and {amount("non-tax")} was non-tax income',
               f'Spending was {amount("tme")}', f'{amount("borrowing")} of net borrowing',
               f'Debt stood at {amount("debt")} at end-March 2026',
               f'Income tax brought in £{income_tax:,.1f} billion',
               f'National Insurance brought in {amount("receipt-ab")}',
               f'VAT net of refunds brought in {amount("receipt-c")}',
               f'Non-tax income was {amount("non-tax")}',
               'Borrowing is not tax. Debt is a stock.', 'They are not forecasts.',
               'Net borrowing uses the accrued basis', 'Debt is a stock at a point in time.',
               'VAT refund row', 'Do not take refunds off a second time.',
                'Which numbers are forecasts?', 'forecasts, not recorded results',
                'Forecast source and date:', data['forecast_source_note']['text'],
                data['forecast_source_note']['cell'], data['source']['published'],
                'The tax breakdown below stays on the latest outturn.',
               data['source']['publication'], data['source']['sha256'], data['source']['metadata_sha256'],
               ROUNDING, RECONCILIATION]
    for phrase in phrases:
        require(phrase in text, f'Income HTML missing/changed visible answer: {phrase}')
    for note in data['notes']:
        require(note['text'] in text and note['cell'] in text, 'Income HTML source note/locator differs')
    for check in data['checks']:
        phrase = f'{check["name"]}: {check["formula"]} = {check["residual_gbp_billion"]:g} £bn (tolerance {check["tolerance_gbp_billion"]:g} £bn).'
        require(phrase in text, 'Income HTML reconciliation differs')


def validate(root):
    root = Path(root)
    manifest = read_json(root / 'sources/income-manifest.json')
    raw = (root / 'sources/income.xlsx').read_bytes()
    metadata = (root / 'sources/income-release.txt').read_bytes()
    validate_manifest(manifest, raw, metadata)
    for filename in ('income.xlsx', 'income-manifest.json', 'income-release.txt'):
        require((root / 'sources' / filename).read_bytes() == (root / 'site/sources' / filename).read_bytes(),
                f'Downloadable {filename} differs from retained source')
    workbook = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
    try:
        data = read_json(root / 'site/data/income.json')
        validate_data(data, manifest, workbook)
        validate_csv((root / 'site/data/income.csv').read_text(encoding='utf-8'), data)
        validate_html((root / 'site/income.html').read_text(encoding='utf-8'), data)
    finally:
        workbook.close()
    print('PASS: independent income hashes/copies, every JSON/CSV value and metadata, HTML tables/headlines, source cells, '
          'period/status, tax/non-tax/receipt reconciliation, compatible borrowing, debt stock not interest')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        validate(args.root.resolve())
    except (ValueError, OSError, KeyError, TypeError, AssertionError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
