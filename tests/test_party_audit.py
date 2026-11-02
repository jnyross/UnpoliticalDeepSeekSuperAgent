"""The trace must report genuine source gaps and reject fabricated native rows."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import parties
import party_audit

ROOT = Path(__file__).resolve().parents[1]


class PartyAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = parties.validate(ROOT)
        cls.report = party_audit.audit(ROOT, cls.data)

    def test_manifest_covers_every_consumed_source(self):
        self.assertEqual({s['id'] for s in self.report['source_manifest']},
                         {s['id'] for s in self.data['sources'] + self.data['evidence_sources']})

    def test_every_financial_quote_occurrence_is_traced(self):
        expected = []
        for p in self.data['parties']:
            for field in parties.LIMITS:
                ref = p.get('evidence', {}).get(field)
                quote = ref['quote'] if ref else p[field]
                expected.extend((p['id'], field, m.group().strip()) for m in party_audit.FIGURE.finditer(quote))
        self.assertEqual(expected, [(f['party_id'], f['field'], f['figure']) for f in self.report['figures']])
        self.assertGreater(len(expected), 15)

    def test_unreferenced_new_cash_claim_fails(self):
        data = copy.deepcopy(self.data)
        data['parties'][0]['offer'] += ' Cost £99 billion.'
        with self.assertRaisesRegex(AssertionError, 'Unreferenced financial claim'):
            party_audit.audit(ROOT, data)

    def test_new_cash_in_displayed_costing_prefix_fails(self):
        data = copy.deepcopy(self.data)
        data['parties'][0]['costing'] += ' Cost £99 billion.'
        with self.assertRaisesRegex(AssertionError, 'Unreferenced financial claim'):
            party_audit.audit(ROOT, data)

    def test_prose_estimates_are_not_invented_tables(self):
        estimates = [f for f in self.report['figures'] if f['source_id'] == 'rf-two-child-2024']
        self.assertEqual(len(estimates), 5)
        self.assertTrue(all(not f['table_row_available'] and f['limitation'] for f in estimates))
        self.assertFalse(self.report['accuracy_l2_claimed'])

    def test_reform_supplement_has_real_row_but_no_invented_year(self):
        figures = [f for f in self.report['figures'] if f['source_id'] == 'reform']
        self.assertTrue(figures)
        for f in figures:
            self.assertTrue(f['table_row_available'])
            self.assertIsNone(f['supplemental_source_tables'][0]['year'])

    def test_uppercase_nhs_cost_preserves_billions_and_its_actual_row(self):
        figures = [f for f in self.report['figures'] if f['source_id'] == 'reform']
        self.assertEqual(len(figures), 1)
        figure = figures[0]
        self.assertEqual(figure['figure'], '£17 BILLION')
        self.assertEqual(figure['unit'], 'GBP billion')
        self.assertEqual(figure['supplemental_source_tables'][0]['row_label'], 'NHS Pledges')
        self.assertEqual(figure['supplemental_source_tables'][0]['pdf_page'], 26)
        self.assertEqual([m.group() for m in party_audit.financial_matches('20 PER CENT', 'tuv')], ['20 PER CENT'])

    def test_mutated_source_hash_and_table_row_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / 'sources', root / 'sources')
            path = root / 'sources/party-figure-locators.json'
            native = json.loads(path.read_text())
            native['reform'][0]['row_label'] = 'Fabricated publisher row'
            path.write_text(json.dumps(native))
            with self.assertRaisesRegex(AssertionError, 'Table row_label not on PDF page'):
                party_audit.audit(root, self.data)
            shutil.copyfile(ROOT / 'sources/party-figure-locators.json', path)
            raw = root / 'sources/rf-two-child-2024.raw.html.txt'
            raw.write_bytes(raw.read_bytes() + b'changed')
            with self.assertRaisesRegex(AssertionError, 'Audit source hash changed'):
                party_audit.audit(root, self.data)

    def test_financial_formats_are_not_service_counts(self):
        text = '£35m, £2 trillion, 20 per cent, 4%, 7,350 nurses'
        self.assertEqual([m.group() for m in party_audit.financial_matches(text, 'reform')],
                         ['£35m', '£2 trillion', '20 per cent', '4%'])
        self.assertEqual(self.report['occurrences'], 22)
        self.assertEqual(self.report['occurrences_without_source_table'], 17)

    def test_wrong_scale_is_not_matched_to_supplement(self):
        data = copy.deepcopy(self.data)
        p = next(p for p in data['parties'] if p['source_id'] == 'reform')
        p['evidence']['costing']['quote'] = 'This will save £50 million per year,'
        report = party_audit.audit(ROOT, data)
        f = next(f for f in report['figures'] if f['party_id'] == p['id'] and f['field'] == 'costing')
        self.assertFalse(f['table_row_available'])

    def test_swapped_labour_totals_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / 'sources', root / 'sources')
            path = root / 'sources/party-figure-locators.json'
            native = json.loads(path.read_text())
            native['labour'][0]['value'] = '4,835'
            path.write_text(json.dumps(native))
            with self.assertRaisesRegex(AssertionError, 'Amount not in native row span'):
                party_audit.audit(root, self.data)

    def test_invalid_download_date_fails(self):
        data = copy.deepcopy(self.data)
        data['evidence_sources'][0]['downloaded'] = 'not a date'
        with self.assertRaises(ValueError):
            party_audit.audit(ROOT, data)


if __name__ == '__main__':
    unittest.main()
