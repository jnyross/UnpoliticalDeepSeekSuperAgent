"""Offline source and publication mutation tests, independent of income extraction."""
import copy
import csv
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check_income as checker

ROOT = Path(__file__).resolve().parents[1]


class WorkbookTests(unittest.TestCase):
    def setUp(self):
        self.workbook = openpyxl.load_workbook(ROOT / 'sources/income.xlsx', data_only=True)
        self.addCleanup(self.workbook.close)

    def test_valid_source(self):
        checker.validate_workbook(self.workbook)

    def test_semantic_source_mutations(self):
        mutations = [(checker.RECEIPTS, 'B33', '2024-25'),
                     (checker.RECEIPTS, 'C41', 'Forecast years from 2025-26'),
                     (checker.AGGREGATES, 'C1', '£ million'),
                     (checker.AGGREGATES, 'X4', 'Central government debt interest'),
                     (checker.AGGREGATES, 'X5', 'NMFX+MU74'),
                     (checker.AGGREGATES, 'B88', '2025-26'),
                     (checker.AGGREGATES, 'C94', 'Estimated fiscal data'),
                     ('Aggregates (per cent of GDP)', 'C90', 'Debt during the year'),
                     ('Glossary', 'C14', 'Annual interest payments')]
        for sheet, cell, value in mutations:
            with self.subTest(sheet=sheet, cell=cell):
                target = self.workbook[sheet][cell]
                original = target.value
                target.value = value
                with self.assertRaises(checker.ValidationError):
                    checker.validate_workbook(self.workbook)
                target.value = original

    def test_source_arithmetic_mutations(self):
        for sheet, cell in [(checker.RECEIPTS, 'C33'), (checker.RECEIPTS, 'AH33'),
                            (checker.AGGREGATES, 'C87'), (checker.AGGREGATES, 'D87'),
                            (checker.AGGREGATES, 'O87')]:
            with self.subTest(sheet=sheet, cell=cell):
                target = self.workbook[sheet][cell]
                original = target.value
                target.value = original + 1
                with self.assertRaisesRegex(checker.ValidationError, 'rounding'):
                    checker.validate_workbook(self.workbook)
                target.value = original

    def test_forecast_source_mutations(self):
        mutations = [(checker.RECEIPTS, 'B39', '2032-33'),
                     (checker.AGGREGATES, 'B93', '2030-31'),
                     (checker.AGGREGATES, 'C95', 'Forecast years from 2026-27; November 2026'),
                     (checker.RECEIPTS, 'AG34', None),
                     (checker.AGGREGATES, 'O93', float('nan')),
                     (checker.AGGREGATES, 'X88', True)]
        for sheet, cell, value in mutations:
            with self.subTest(sheet=sheet, cell=cell):
                target = self.workbook[sheet][cell]
                original = target.value
                target.value = value
                with self.assertRaises(checker.ValidationError):
                    checker.validate_workbook(self.workbook)
                target.value = original
        for sheet, cell in [(checker.RECEIPTS, 'AG34'), (checker.AGGREGATES, 'O93')]:
            target = self.workbook[sheet][cell]
            original = target.value
            target.value += 1
            with self.assertRaises(checker.ValidationError):
                checker.validate_workbook(self.workbook)
            target.value = original

    def test_borrowing_source_rounding_boundary(self):
        s = self.workbook[checker.AGGREGATES]
        s['O87'] = s['D87'].value - s['C87'].value + checker.BORROWING_ROUNDING
        checker.validate_workbook(self.workbook)
        s['O87'] = s['O87'].value + 0.00001
        with self.assertRaisesRegex(checker.ValidationError, 'borrowing'):
            checker.validate_workbook(self.workbook)

    def test_receipt_source_rounding_boundary(self):
        s = self.workbook[checker.RECEIPTS]
        s['C33'] = s['AG33'].value - sum(s.cell(33, c).value for c in range(4, 33)) + checker.RECEIPT_ROUNDING
        checker.validate_workbook(self.workbook)
        s['C33'] = s['C33'].value + 0.00001
        with self.assertRaisesRegex(checker.ValidationError, 'component total'):
            checker.validate_workbook(self.workbook)

    def test_numbers_are_finite_not_boolean(self):
        for value in (True, float('nan'), float('inf'), '180.326', None):
            with self.subTest(value=value):
                self.workbook[checker.RECEIPTS]['C33'] = value
                with self.assertRaises(checker.ValidationError):
                    checker.validate_workbook(self.workbook)


class PublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workbook = openpyxl.load_workbook(ROOT / 'sources/income.xlsx', data_only=True)
        cls.addClassCleanup(cls.workbook.close)
        cls.manifest = checker.read_json(ROOT / 'sources/income-manifest.json')
        cls.original = checker.read_json(ROOT / 'site/data/income.json')

    def setUp(self):
        self.data = copy.deepcopy(self.original)

    def assert_invalid(self, mutate):
        mutate(self.data)
        with self.assertRaises(checker.ValidationError):
            checker.validate_data(self.data, self.manifest, self.workbook)

    def test_every_record_value(self):
        for index in range(len(self.data['records'])):
            with self.subTest(record=index):
                self.data = copy.deepcopy(self.original)
                self.assert_invalid(lambda d: d['records'][index].update(value_gbp_billion=99999))

    def test_metadata_and_locator_mutations(self):
        mutations = [('period', '2024-25'), ('status', 'forecast'), ('unit', 'GBP million'),
                     ('geography', 'England'), ('scope', 'Central government only'),
                     ('cells', ['Aggregates (£bn)!V87']), ('ons_code', 'WRONG'),
                     ('label', 'Wrong label'), ('kind', 'interest'), ('id', 'wrong'),
                     ('operands', ['debt']), ('formula', 'debt minus interest')]
        for key, value in mutations:
            with self.subTest(field=key):
                self.data = copy.deepcopy(self.original)
                self.assert_invalid(lambda d: d['records'][0].update({key: value}))

    def test_non_numeric_or_nonfinite_exports(self):
        for value in (True, float('nan'), float('inf'), '180.326', None):
            with self.subTest(value=value):
                self.data = copy.deepcopy(self.original)
                self.assert_invalid(lambda d: d['records'][0].update(value_gbp_billion=value))

    def test_record_cardinality_and_order(self):
        for mutate in (lambda d: d['records'].pop(),
                       lambda d: d['records'].append(copy.deepcopy(d['records'][0])),
                       lambda d: d['records'].reverse()):
            self.data = copy.deepcopy(self.original)
            self.assert_invalid(mutate)

    def test_debt_is_stock_not_interest(self):
        debt = next(r for r in self.data['records'] if r['id'] == 'debt')
        debt.update(value_gbp_billion=self.workbook[checker.AGGREGATES]['V87'].value,
                    cells=['Aggregates (£bn)!V87'], period='2025-26')
        with self.assertRaises(checker.ValidationError):
            checker.validate_data(self.data, self.manifest, self.workbook)

    def test_forecast_transition_and_export_provenance(self):
        forecasts = [r for r in self.data['records'] if r['status'] == 'forecast']
        self.assertEqual(len(forecasts), 18)
        self.assertEqual(self.data['forecast_years'], checker.FORECAST_YEARS)
        self.assertEqual(self.data['records'][-1]['period'], 'end-March 2032')
        for record in forecasts:
            for field, value in [('status', 'outturn'), ('period', '2025-26'),
                                 ('cells', ['Aggregates (£bn)!V88']), ('ons_code', 'wrong')]:
                changed = copy.deepcopy(self.original)
                target = next(r for r in changed['records'] if r['id'] == record['id'])
                target[field] = value
                with self.subTest(record=record['id'], field=field):
                    with self.assertRaises(checker.ValidationError):
                        checker.validate_data(changed, self.manifest, self.workbook)
        for mutate in (lambda d: d['forecast_years'].pop(),
                       lambda d: d['forecast_source_note'].update(text='November 2026'),
                       lambda d: d['forecast_source_note'].update(cell='Receipts (£bn)!C40')):
            self.data = copy.deepcopy(self.original)
            self.assert_invalid(mutate)

    def test_forecast_html_style_status_semantics(self):
        raw = (ROOT / 'site/income.html').read_text(encoding='utf-8')
        for before, after in [('class="forecast"', 'class="outturn"'),
                              ('border-top:2px dashed', 'border-top:2px solid'),
                              ('2031-32<br><strong>Forecast', '2031-32<br><strong>Outturn'),
                              ('scope="row"', ''),
                              ('forecast-summary', 'no-summary')]:
            with self.subTest(before=before):
                self.assertIn(before, raw)
                with self.assertRaises(checker.ValidationError):
                    checker.validate_html(raw.replace(before, after), self.data)

    def test_top_level_metadata(self):
        for field, value in [('year', '2026-27'), ('status', 'forecast'),
                             ('geography', 'England'), ('unit', 'GBP million'),
                             ('scope', 'Central government')]:
            with self.subTest(field=field):
                self.data = copy.deepcopy(self.original)
                self.assert_invalid(lambda d: d.update({field: value}))

    def test_notes_checks_and_explanations(self):
        changes = [lambda d: d['notes'][0].update(text='Changed source status'),
                   lambda d: d['notes'][0].update(cell='Receipts (£bn)!C41'),
                   lambda d: d['checks'][0].update(residual_gbp_billion=1),
                   lambda d: d['checks'][0].update(tolerance_gbp_billion=100),
                   lambda d: d.update(rounding='Rounded to millions'),
                   lambda d: d.update(selection='Latest forecast'),
                   lambda d: d.update(reconciliation='Use another release')]
        for change in changes:
            self.data = copy.deepcopy(self.original)
            self.assert_invalid(change)

    def test_html_mutations(self):
        raw = (ROOT / 'site/income.html').read_text(encoding='utf-8')
        checker.validate_html(raw, self.data)
        changes = [('1,231.3', '1,232.3'), ('329.3', '330.3'),
                   ('Receipts (£bn)!C33', 'Receipts (£bn)!C34'),
                   ('end-March 2026', 'end-March 2025'),
                   ('<td>180.3</td>', '<td>180.4</td>'),
                   ('They are not forecasts.', 'These are forecasts.'),
                   ('Borrowing is not tax. Debt is a stock.', 'Debt is annual interest.'),
                   ('<strong>£1,231.3 billion</strong>', '<strong hidden>£1,231.3 billion</strong>')]
        for before, after in changes:
            with self.subTest(before=before):
                self.assertIn(before, raw)
                with self.assertRaises(checker.ValidationError):
                    checker.validate_html(raw.replace(before, after, 1), self.data)

    def test_csv_every_column(self):
        raw = (ROOT / 'site/data/income.csv').read_text(encoding='utf-8')
        checker.validate_csv(raw, self.data)
        rows = list(csv.reader(io.StringIO(raw)))
        for col in range(len(rows[0])):
            with self.subTest(column=rows[0][col]):
                changed = copy.deepcopy(rows)
                changed[1][col] = '99999'
                stream = io.StringIO()
                csv.writer(stream).writerows(changed)
                with self.assertRaises(checker.ValidationError):
                    checker.validate_csv(stream.getvalue(), self.data)
        with self.assertRaises(checker.ValidationError):
            checker.validate_csv(raw + raw.splitlines()[1] + '\n', self.data)


class FilesystemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='income-check-')
        self.addCleanup(self.temp.cleanup)
        self.stage = Path(self.temp.name)
        for relative in ('sources/income.xlsx', 'sources/income-manifest.json',
                         'sources/income-release.txt', 'site/sources/income.xlsx',
                         'site/sources/income-manifest.json', 'site/sources/income-release.txt',
                         'site/data/income.json', 'site/data/income.csv', 'site/income.html'):
            target = self.stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def test_valid_snapshot(self):
        checker.validate(self.stage)

    def test_retained_hashes(self):
        for filename in ('income.xlsx', 'income-release.txt'):
            with self.subTest(filename=filename):
                path = self.stage / 'sources' / filename
                original = path.read_bytes()
                path.write_bytes(original + b'changed')
                with self.assertRaisesRegex(checker.ValidationError, 'SHA-256'):
                    checker.validate(self.stage)
                path.write_bytes(original)

    def test_download_copies(self):
        for filename in ('income.xlsx', 'income-manifest.json', 'income-release.txt'):
            with self.subTest(filename=filename):
                path = self.stage / 'site/sources' / filename
                original = path.read_bytes()
                path.write_bytes(original + b'changed')
                with self.assertRaisesRegex(checker.ValidationError, 'Downloadable'):
                    checker.validate(self.stage)
                path.write_bytes(original)

    def test_embedded_manifest_mutation(self):
        path = self.stage / 'site/data/income.json'
        data = checker.read_json(path)
        data['source']['sha256'] = '0' * 64
        path.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaises(checker.ValidationError):
            checker.validate(self.stage)


if __name__ == '__main__':
    unittest.main()
