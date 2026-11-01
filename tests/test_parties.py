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

    def with_pdf_text(self, transform):
        """Run the real extractor, altering only its output for one source."""
        party = self.original['parties'][0]
        source = next(s for s in self.original['sources'] if s['id'] == party['source_id'])
        run = parties.subprocess.run

        def extract(command, **kwargs):
            result = run(command, **kwargs)
            if Path(command[-2]).name == source['file']:
                out = Path(command[-1])
                out.write_text(transform(out.read_text(encoding='utf-8'), party), encoding='utf-8')
            return result

        return patch.object(parties.subprocess, 'run', side_effect=extract)

    def test_typographic_normalization_preserves_factual_distinctions(self):
        self.assertEqual(parties.normal('ofﬁce\u00a0fund\u00ad ing\n  ﬂow'), 'office fund ing flow')
        for changed in ('£10 million', '£1 billion', 'not £1 million', '£1-million', '£1million'):
            self.assertNotEqual(parties.normal('£1 million'), parties.normal(changed))

    def test_extraction_whitespace_and_ligatures_are_portable(self):
        def typography(text, party):
            # Preserve form feeds: they delimit the independently cited PDF pages.
            return text.replace(' ', '\u00a0  ').replace('\n', '\n\n').replace('fi', 'ﬁ').replace('fl', 'ﬂ')
        with self.with_pdf_text(typography):
            parties.validate(ROOT)

    def test_unrelated_extraction_layout_differences_are_not_quote_evidence(self):
        # Poppler changes dot leaders / overlapping text elsewhere in some PDFs.
        with self.with_pdf_text(lambda text, party: 'Different extracted header layout\n' + text):
            parties.validate(ROOT)

    def test_retained_quote_alone_is_not_pdf_evidence(self):
        def remove_cited_page(text, party):
            pages = text.split('\f')
            pages[party['pdf_page'] - 1] = 'No supporting text on this page.'
            return '\f'.join(pages)
        with self.with_pdf_text(remove_cited_page):
            with self.assertRaisesRegex(AssertionError, 'Excerpt not on cited PDF page'):
                parties.validate(ROOT)

    def test_quote_elsewhere_in_pdf_does_not_support_cited_page(self):
        def move_cited_page(text, party):
            pages = text.split('\f')
            index = party['pdf_page'] - 1
            pages[index], pages[0] = pages[0], pages[index]
            return '\f'.join(pages)
        with self.with_pdf_text(move_cited_page):
            with self.assertRaisesRegex(AssertionError, 'Excerpt not on cited PDF page'):
                parties.validate(ROOT)

    def test_changed_transcript_hash_fails(self):
        self.fails(lambda d: d['sources'][0].update(text_sha256='0' * 64))

    def test_invalid_page_fails(self):
        for page in (0, -1, 10000, '1', True):
            with self.subTest(page=page):
                self.fails(lambda d: d['parties'][0].update(pdf_page=page))

    def test_render_equal_fields_and_no_script(self):
        page = parties.render(self.original)
        self.assertEqual(page.count('class="party-offer"'), 13)
        self.assertNotIn('<script', page)
        for _, label in parties.FIELDS:
            self.assertEqual(page.count('<dt>' + label + '</dt>'), 13)
        self.assertLess(len(page.encode()), 500_000)

if __name__ == '__main__':
    unittest.main()
