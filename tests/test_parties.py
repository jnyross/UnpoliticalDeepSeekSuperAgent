"""Mutation checks for party coverage and retained quote evidence."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import parties

ROOT = Path(__file__).resolve().parents[1]

class PartyOffersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = parties.validate(ROOT)

    def fails(self, mutate):
        d = copy.deepcopy(self.original)
        mutate(d)
        with patch.object(parties, 'load', return_value=d):
            with self.assertRaises(AssertionError):
                parties.validate(ROOT)

    def test_all_parties_and_separate_non_parties(self):
        self.assertEqual(len(self.original['parties']), 13)
        self.assertEqual(self.original['roster']['as_of'], '2024-07-09')
        self.assertEqual(sum(p['seats'] for p in self.original['parties']) +
                         self.original['independents']['seats'] + self.original['speaker']['seats'], 650)

    def test_omitted_party_fails(self):
        self.fails(lambda d: d['parties'].pop())

    def test_extra_party_fails(self):
        self.fails(lambda d: d['parties'].append(copy.deepcopy(d['parties'][0])))

    def test_order_fails(self):
        self.fails(lambda d: d['parties'].reverse())

    def test_long_offer_fails(self):
        self.fails(lambda d: d['parties'][0].update(offer='word ' * 46))

    def test_unsupported_quote_fails(self):
        self.fails(lambda d: d['parties'][0].update(excerpt='This quote is not in the manifesto.'))

    def test_wrong_page_fails(self):
        self.fails(lambda d: d['parties'][0].update(pdf_page=1))

    def test_changed_source_hash_fails(self):
        self.fails(lambda d: d['sources'][0].update(sha256='0' * 64))

    def test_unequal_missing_evidence_fails(self):
        self.fails(lambda d: d['parties'][0].update(costing='Zero'))

    def test_extra_field_fails(self):
        self.fails(lambda d: d['parties'][0].update(rating='a score'))

    def test_render_equal_fields_and_no_script(self):
        page = parties.render(self.original)
        self.assertEqual(page.count('class="party-offer"'), 13)
        self.assertNotIn('<script', page)
        for _, label in parties.FIELDS:
            self.assertEqual(page.count('<dt>' + label + '</dt>'), 13)
        self.assertLess(len(page.encode()), 500_000)

if __name__ == '__main__':
    unittest.main()
