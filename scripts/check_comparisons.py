#!/usr/bin/env python3
"""Independent retained-workbook regression checks; never imports the generator."""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re

import openpyxl


class ValidationError(ValueError):
    """Comparison source, data or static answer failed validation."""


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def numeric(value, context):
    require(type(value) in (int, float) and math.isfinite(value),
            f"{context}: expected finite numeric input")
    return value


def years(sheet):
    result = {}
    for cell in sheet[5]:
        match = re.fullmatch(r"(\d{4})-(\d{2})", str(cell.value))
        if match:
            start = int(match[1])
            require(int(match[2]) == (start + 1) % 100, "Invalid fiscal year")
            require(start not in result, f"Duplicate year in {sheet.title}")
            result[start] = cell.column
    require(bool(result), f"No years in {sheet.title}")
    return result


def expected_data(workbook, manifest):
    """Derive the contract directly from raw worksheets, not published JSON."""
    require({'4_2', '4_3', '4_4'} <= set(workbook.sheetnames), 'Missing comparison source sheets')
    nominal, real, share = (workbook[name] for name in ('4_2', '4_3', '4_4'))
    headers = {s.title: years(s) for s in (nominal, real, share)}
    latest = max(headers['4_3'])
    require(all(max(h) == latest for h in headers.values()), 'Comparison latest years disagree')
    baseline = latest - 10
    require(all(baseline in h for h in headers.values()), 'Missing exact ten-year baseline')
    end_year = real.cell(5, headers['4_3'][latest]).value
    for sheet in (nominal, real, share):
        require(sheet['B4'].value == 'outturn', f'{sheet.title}: status is not outturn')
        require(sheet['A20'].value == '7. Health', f'{sheet.title}: health row changed')
        unit = 'per cent' if sheet is share else '£ billion'
        require(sheet.cell(3, headers[sheet.title][latest]).value == unit,
                f'{sheet.title}: raw units changed')
    for sheet in (real, share):
        require(sheet['A27'].value == 'Total Managed Expenditure(8)', f'{sheet.title}: TME row changed')
    deflator, vintage = real['A28'].value, share['A28'].value
    require(isinstance(deflator, str) and f'{end_year} price levels' in deflator
            and '30 June 2026' in deflator, 'Unexpected price base or deflator vintage')
    require(isinstance(vintage, str) and '30 June 2026' in vintage, 'Unexpected GDP vintage')
    # All published expenditure rows must agree in the deflator base year,
    # not just the health cell used by the generated comparison.
    for row in range(6, 28):
        n = numeric(nominal.cell(row, headers['4_2'][latest]).value, f'4_2 row {row}')
        r = numeric(real.cell(row, headers['4_3'][latest]).value, f'4_3 row {row}')
        require(n == r, f'Latest base-year real does not equal nominal at row {row}')
    points = []
    for start in (baseline, latest):
        year = f'{start}-{(start + 1) % 100:02d}'
        point = {'year': year, 'status': 'outturn'}
        for key, sheet, row, unit, scope in (
                ('health_real', real, 20, f'GBP billion, {end_year} prices',
                 'Public sector expenditure on services: health'),
                ('tme_gdp', share, 27, 'percent of GDP',
                 'Total Managed Expenditure, excluding temporary effects of public-sector banks')):
            col = headers[sheet.title][start]
            require(sheet.cell(5, col).value == year, f'{sheet.title}: year mismatch')
            cell = sheet.cell(row, col)
            point[key] = {'value': numeric(cell.value, f'{sheet.title}!{cell.coordinate}'),
                          'sheet': sheet.title, 'cell': cell.coordinate,
                          'row': sheet.cell(row, 1).value, 'unit': unit, 'scope': scope,
                          'geography': 'United Kingdom'}
        points.append(point)
    old, new = points
    return {'source': manifest, 'points': points,
            'health_change': new['health_real']['value'] - old['health_real']['value'],
            'health_percent': (new['health_real']['value'] / old['health_real']['value'] - 1) * 100,
            'gdp_change': new['tme_gdp']['value'] - old['tme_gdp']['value'],
            'formulas': {'health_change': 'latest health_real - baseline health_real',
                         'health_percent': '(latest health_real / baseline health_real - 1) * 100',
                         'gdp_change': 'latest tme_gdp - baseline tme_gdp'},
            'deflator': deflator, 'gdp_vintage': vintage}


def compare(actual, expected, context='comparisons'):
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and set(actual) == set(expected), f'{context}: fields differ')
        for key in expected:
            compare(actual[key], expected[key], f'{context}.{key}')
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), f'{context}: points differ')
        for i, item in enumerate(expected):
            compare(actual[i], item, f'{context}[{i}]')
    else:
        if type(expected) in (int, float):
            numeric(actual, context)
        require(actual == expected, f'{context}: published {actual!r}, expected {expected!r}')


class Content(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = False
        self.stack = []
        self.parts = []
        self.rows = []
        self.row = None
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        void = tag in ('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                       'link', 'meta', 'param', 'source', 'track', 'wbr')
        if not void:
            self.stack.append((tag, self.hidden))
            self.hidden = (self.hidden or tag in ('head', 'script', 'style')
                           or 'hidden' in attrs or attrs.get('aria-hidden') == 'true')
        if tag == 'tr' and not self.hidden:
            self.row = []
        if tag == 'a' and not self.hidden:
            self.links.append(attrs.get('href'))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                self.hidden = self.stack[index][1]
                del self.stack[index:]
                break
        if tag == 'tr' and self.row is not None:
            self.rows.append(' '.join(' '.join(self.row).split()))
            self.row = None

    def handle_data(self, value):
        if not self.hidden:
            self.parts.append(value)
            if self.row is not None:
                self.row.append(value)

    @property
    def text(self):
        return ' '.join(' '.join(self.parts).split())


def validate_page(path, expected):
    page = Content()
    page.feed(path.read_text(encoding='utf-8'))
    old, new = expected['points']
    change, percent, gdp = (expected[k] for k in ('health_change', 'health_percent', 'gdp_change'))
    answers = [
        'Has health spending gone up or down after inflation?',
        'Is total spending a bigger or smaller share of the economy?',
        f"Health spending went {'up' if change >= 0 else 'down'} by {abs(percent):.1f}%",
        f"from {old['year']} to {new['year']}",
        f"It went from £{old['health_real']['value']:.1f} billion to £{new['health_real']['value']:.1f} billion, a change of £{change:.1f} billion in {new['year']} prices.",
        f"Total spending was a {'bigger' if gdp >= 0 else 'smaller'} share of the economy",
        f"{new['tme_gdp']['value']:.1f}% of GDP in {new['year']}, compared with {old['tme_gdp']['value']:.1f}% in {old['year']}.",
        f'That is a change of {gdp:.1f} percentage points.',
        'All four inputs are outturn, not forecasts.',
    ]
    for answer in answers:
        require(answer in page.text, f'Comparison HTML missing or changed answer: {answer}')
    for point in expected['points']:
        row = (f"{point['year']} (outturn) £{point['health_real']['value']:.1f}bn "
               f"4_3!{point['health_real']['cell']} {point['tme_gdp']['value']:.1f}% "
               f"4_4!{point['tme_gdp']['cell']}")
        require(row in page.rows, f'Comparison HTML source row missing or changed: {row}')
    for link in ('sources/trends.xlsx', 'data/comparisons.json', 'sources/trends-manifest.json'):
        require(link in page.links, f'Missing comparison source download: {link}')
    # Existing implied questions: headline total, biggest area, and health per £100.
    for question in ('Where public money goes', 'Spending by area', 'What is in these totals?'):
        require(question in page.text, f'Missing existing question/topic: {question}')
    require('goes on health' in page.text, 'Missing existing health-share answer')


def validate(root):
    root = Path(root)
    manifest = json.loads((root / 'sources/trends-manifest.json').read_text(encoding='utf-8'))
    require(manifest.get('file') == 'trends.xlsx', 'Unexpected trends source filename')
    raw = (root / 'sources/trends.xlsx').read_bytes()
    require(hashlib.sha256(raw).hexdigest() == manifest.get('sha256'), 'Trends source SHA-256 differs from manifest')
    require((root / 'site/sources/trends.xlsx').read_bytes() == raw, 'Downloadable trends workbook differs')
    require(json.loads((root / 'site/sources/trends-manifest.json').read_text(encoding='utf-8')) == manifest,
            'Downloadable trends manifest differs')
    workbook = openpyxl.load_workbook(root / 'sources/trends.xlsx', data_only=True)
    try:
        expected = expected_data(workbook, manifest)
    finally:
        workbook.close()
    actual = json.loads((root / 'site/data/comparisons.json').read_text(encoding='utf-8'))
    compare(actual, expected)
    validate_page(root / 'site/index.html', expected)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    validate(parser.parse_args().root)
    print('PASS: independent ten-year comparisons, source hash, base-year cross-check and static answers')
