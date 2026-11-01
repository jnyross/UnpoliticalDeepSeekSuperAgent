"""Mutation checks for party coverage and retained quote evidence."""
import copy
import json
from pathlib import Path
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

    def test_changed_transcript_hash_fails(self):
        self.fails(lambda d: d['sources'][0].update(text_sha256='0' * 64))

    def test_invalid_page_fails(self):
        for page in (0, -1, True, '1', 100000):
            with self.subTest(page=page):
                self.fails(lambda d: d['parties'][0].update(pdf_page=page))

    def test_poppler_layout_variance_passes_with_direct_page_checks(self):
        run = parties.subprocess.run
        calls = []

        def reflow(command, **kwargs):
            result = run(command, **kwargs)
            calls.append(command)
            out = Path(command[-1])
            # Deliberately differ from the retained bytes: new wrapping, spacing,
            # page decorations, and unrelated surrounding text are not evidence changes.
            text = out.read_text()
            out.write_text('Different page header\n' + '\n  '.join(text.split()) + '\n\f')
            return result

        with patch.object(parties.subprocess, 'run', side_effect=reflow):
            self.assertEqual(parties.validate(ROOT), self.original)
        self.assertEqual(len(calls), len(self.original['parties']))
        sources = {s['id']: s for s in self.original['sources']}
        for command, party in zip(calls, self.original['parties']):
            self.assertEqual(command[1:5], ['-f', str(party['pdf_page']), '-l', str(party['pdf_page'])])
            source = sources[party['source_id']]
            self.assertEqual(Path(command[-2]).name, source['file'])
            self.assertEqual('-raw' in command, source.get('text_mode') == 'raw')

    def test_regenerated_page_must_independently_support_quote(self):
        run = parties.subprocess.run

        def missing_quote(command, **kwargs):
            result = run(command, **kwargs)
            Path(command[-1]).write_text('No source quote on this PDF page.\n\f')
            return result

        with patch.object(parties.subprocess, 'run', side_effect=missing_quote):
            with self.assertRaisesRegex(AssertionError, 'Excerpt not on cited PDF page'):
                parties.validate(ROOT)

    def test_changed_quote_words_or_punctuation_fail(self):
        run = parties.subprocess.run
        quote = self.original['parties'][0]['excerpt']
        for changed in (quote.replace(' ', ' invented ', 1), quote.replace(' ', ', ', 1)):
            with self.subTest(changed=changed):
                def changed_quote(command, **kwargs):
                    result = run(command, **kwargs)
                    Path(command[-1]).write_text(changed + '\n\f')
                    return result
                with patch.object(parties.subprocess, 'run', side_effect=changed_quote):
                    with self.assertRaisesRegex(AssertionError, 'Excerpt not on cited PDF page'):
                        parties.validate(ROOT)

    def test_rehashed_forged_transcript_is_not_pdf_evidence(self):
        d = copy.deepcopy(self.original)
        party = d['parties'][0]
        source = next(s for s in d['sources'] if s['id'] == party['source_id'])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / 'sources'
            base.mkdir()
            for path in (ROOT / 'sources').iterdir():
                if path.is_file() and path.name != source['text_file']:
                    (base / path.name).symlink_to(path)
            transcript = (ROOT / 'sources' / source['text_file']).read_text().split('\f')
            party['excerpt'] = 'An invented promise unsupported by the retained PDF.'
            transcript[party['pdf_page'] - 1] += '\n' + party['excerpt']
            forged = base / source['text_file']
            forged.write_text('\f'.join(transcript))
            source['text_sha256'] = parties.digest(forged)
            with patch.object(parties, 'load', return_value=d):
                with self.assertRaisesRegex(AssertionError, 'Excerpt not on cited PDF page'):
                    parties.validate(root)

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
