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

    def extracted_text(self, mutate=lambda text, source: text):
        """Simulate another Poppler version without changing retained evidence."""
        sources = {s['file']: s for s in self.original['sources']}
        def run(command, **kwargs):
            source = sources[Path(command[-2]).name]
            self.assertEqual('-raw' in command, source.get('text_mode') == 'raw')
            text = (ROOT / 'sources' / source['text_file']).read_text(encoding='utf-8')
            Path(command[-1]).write_text(mutate(text, source), encoding='utf-8')
        return patch.object(parties.subprocess, 'run', side_effect=run)

    def test_extraction_layout_can_differ_without_rewriting_provenance(self):
        # Observed Poppler 24 vs 26 differences include dot-leader spacing,
        # line breaks and merged words elsewhere in the document. Only quoted
        # evidence must match, on the same page, in both independent readings.
        def layout(text, source):
            pages = text.split('\f')
            pages[0] += '\nDifferent extraction layout on the cover\n'
            return '\f'.join(pages).replace(' ', '  ').replace('\n', '\n\n')
        before = {s[key]: (ROOT / 'sources' / s[key]).read_bytes()
                  for s in self.original['sources'] for key in ('file', 'text_file')}
        with self.extracted_text(layout):
            self.assertEqual(parties.validate(ROOT), self.original)
        for name, raw in before.items():
            self.assertEqual((ROOT / 'sources' / name).read_bytes(), raw)

    def test_quote_must_be_in_fresh_pdf_extraction(self):
        p = self.original['parties'][0]
        def remove_quote(text, source):
            pages = text.split('\f')
            if source['id'] == p['source_id']:
                pages[p['pdf_page']-1] = 'No supporting words on this page.'
            return '\f'.join(pages)
        with self.extracted_text(remove_quote):
            with self.assertRaisesRegex(AssertionError, 'cited PDF page'):
                parties.validate(ROOT)

    def test_fresh_pdf_quote_on_another_page_is_not_evidence(self):
        p = self.original['parties'][0]
        def move_page(text, source):
            if source['id'] != p['source_id']:
                return text
            pages = text.split('\f')
            pages[0], pages[p['pdf_page']-1] = pages[p['pdf_page']-1], pages[0]
            return '\f'.join(pages)
        with self.extracted_text(move_page):
            with self.assertRaisesRegex(AssertionError, 'cited PDF page'):
                parties.validate(ROOT)

    def test_quote_must_still_be_in_retained_transcript(self):
        d = copy.deepcopy(self.original)
        d['parties'][0]['excerpt'] = 'A fabricated manifesto promise.'
        p = d['parties'][0]
        def insert_quote(text, source):
            pages = text.split('\f')
            if source['id'] == p['source_id']:
                pages[p['pdf_page']-1] += p['excerpt']
            return '\f'.join(pages)
        with self.extracted_text(insert_quote), patch.object(parties, 'load', return_value=d):
            with self.assertRaisesRegex(AssertionError, 'cited retained text page'):
                parties.validate(ROOT)

    def test_invalid_page_numbers_fail_closed(self):
        with self.extracted_text():
            for page in (0, -1, 10000, True, '17'):
                with self.subTest(page=page):
                    self.fails(lambda d: d['parties'][0].update(pdf_page=page))

    def test_raw_pdf_and_transcript_byte_changes_fail_hash_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / 'sources', root / 'sources')
            for key in ('file', 'text_file'):
                path = root / 'sources' / self.original['sources'][0][key]
                raw = path.read_bytes()
                path.write_bytes(raw + b'\n')  # Even cosmetic retained-byte drift fails.
                with self.subTest(key=key), self.assertRaisesRegex(AssertionError, 'Source hash changed'):
                    parties.validate(root)
                path.write_bytes(raw)

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
