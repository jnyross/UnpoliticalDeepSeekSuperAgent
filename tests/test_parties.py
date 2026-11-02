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
        evidence_calls = sum('pdf_page' in ref for p in self.original['parties'] for ref in p.get('evidence', {}).values())
        self.assertEqual(len(calls), len(self.original['parties']) + evidence_calls)
        sources = {s['id']: s for s in self.original['sources']}
        main_calls = []
        index = 0
        for party in self.original['parties']:
            index += sum('pdf_page' in ref for ref in party.get('evidence', {}).values())
            main_calls.append(calls[index]); index += 1
        for command, party in zip(main_calls, self.original['parties']):
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
            with self.assertRaisesRegex(AssertionError, '(?i)(excerpt not on cited PDF page|cost quote not on PDF page)'):
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
                    with self.assertRaisesRegex(AssertionError, '(?i)(excerpt not on cited PDF page|cost quote not on PDF page)'):
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
                with self.assertRaisesRegex(AssertionError, '(?i)(excerpt not on cited PDF page|cost quote not on PDF page)'):
                    parties.validate(root)

    def test_unequal_missing_evidence_fails(self):
        self.fails(lambda d: next(p for p in d['parties'] if p['source_id'] == 'dup').update(costing='Zero'))

    def test_independent_sources_have_separate_register(self):
        self.assertEqual(len(self.original['sources']), 13)
        self.assertEqual(len(self.original['evidence_sources']), 4)
        self.assertEqual(sum('assessment' in p.get('evidence', {}) for p in self.original['parties']), 7)
        self.assertEqual(sum(set(p.get('evidence', {})) == {'costing'} for p in self.original['parties']), 3)

    def test_cost_only_claims_keep_independent_assessment_gap(self):
        for source_id in ('reform', 'sdlp', 'uup'):
            party = next(p for p in self.original['parties'] if p['source_id'] == source_id)
            with self.subTest(source_id=source_id):
                self.assertEqual(set(party['evidence']), {'costing'})
                self.assertTrue(party['assessment'].startswith('Unavailable here:'))
                self.assertEqual(party['evidence']['costing']['source_id'], source_id)
                self.assertIn('pdf_page', party['evidence']['costing'])
                self.fails(lambda d: next(p for p in d['parties'] if p['source_id'] == source_id).update(assessment='This plan is affordable.'))

    def test_official_cost_cannot_masquerade_as_independent_assessment(self):
        def fake_assessment(d):
            party = next(p for p in d['parties'] if p['source_id'] == 'uup')
            ref = copy.deepcopy(party['evidence']['costing'])
            ref['attribution'] = 'Ulster Unionist Party'
            party['assessment'] = ref['quote']
            party['evidence']['assessment'] = ref
        self.fails(fake_assessment)

    def test_new_cost_claims_reject_amount_and_page_mutations(self):
        for source_id in ('reform', 'sdlp', 'uup'):
            with self.subTest(source_id=source_id):
                self.fails(lambda d: next(p for p in d['parties'] if p['source_id'] == source_id)['evidence']['costing'].update(quote='£999 billion'))
                self.fails(lambda d: next(p for p in d['parties'] if p['source_id'] == source_id)['evidence']['costing'].update(pdf_page=1))

    def test_independent_cost_estimates_are_labelled_and_scoped(self):
        for identifier in ('alliance', 'green', 'plaid', 'snp'):
            row = next(p for p in self.original['parties'] if p['source_id'] == identifier)
            with self.subTest(party=identifier):
                self.assertEqual(row['evidence']['costing']['source_id'], 'rf-two-child-2024')
                self.assertIn('not a party costing', row['costing'])
                self.assertIn('Great Britain', row['scope'])
                self.assertIn('Northern Ireland', row['scope'])
                self.assertIn('take-up', row['baseline'])
                self.fails(lambda d: next(p for p in d['parties'] if p['source_id'] == identifier).update(costing='Party claim:'))
                self.fails(lambda d: next(p for p in d['parties'] if p['source_id'] == identifier)['evidence']['costing'].update(attribution='Party source'))
                self.fails(lambda d: next(p for p in d['parties'] if p['source_id'] == identifier)['evidence']['costing'].update(quote='£999 billion'))
                self.fails(lambda d: next(p for p in d['parties'] if p['source_id'] == identifier)['evidence']['assessment'].update(text_line=1))

    def test_evidence_hash_quote_locator_and_attribution_fail_closed(self):
        def party(d):
            return next(p for p in d['parties'] if p['source_id'] == 'libdem')
        self.fails(lambda d: d['evidence_sources'][0].update(sha256='0' * 64))
        self.fails(lambda d: d['evidence_sources'][0].update(text_sha256='0' * 64))
        self.fails(lambda d: party(d)['evidence']['costing'].update(quote='£9 billion a year'))
        self.fails(lambda d: party(d)['evidence']['assessment'].update(text_line=1))
        self.fails(lambda d: party(d)['evidence']['assessment'].update(text_line=True))
        self.fails(lambda d: party(d)['evidence']['assessment'].update(attribution='word ' * 31))
        self.fails(lambda d: party(d).update(assessment='An unsupported judgement.'))
        self.fails(lambda d: party(d)['evidence']['costing'].update(source_id='fullfact-buybacks'))

    def test_evidence_cost_pdf_is_reopened(self):
        self.fails(lambda d: next(p for p in d['parties'] if p['source_id'] == 'labour')['evidence']['costing'].update(pdf_page=1))

    def test_forged_html_transcript_is_not_raw_evidence(self):
        # Hash-consistent extracted text cannot replace the retained raw response.
        d = copy.deepcopy(self.original)
        p = next(p for p in d['parties'] if p['source_id'] == 'libdem')
        ref = p['evidence']['assessment']
        source = next(s for s in d['evidence_sources'] if s['id'] == ref['source_id'])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); base = root / 'sources'; base.mkdir()
            for path in (ROOT / 'sources').iterdir():
                if path.is_file() and path.name != source['text_file']:
                    (base / path.name).symlink_to(path)
            lines = (ROOT / 'sources' / source['text_file']).read_text().splitlines()
            ref['quote'] = p['assessment'] = 'This new tax would raise no money.'
            lines[ref['text_line'] - 1] = ref['quote']
            forged = base / source['text_file']; forged.write_text('\n'.join(lines))
            source['text_sha256'] = parties.digest(forged)
            with patch.object(parties, 'load', return_value=d):
                with self.assertRaisesRegex(AssertionError, 'raw HTML locator'):
                    parties.validate(root)

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
            # Preserve the cited-page boundary returned by pdftotext -f/-l.
            return text.replace(' ', '\u00a0  ').replace('\n', '\n\n').replace('fi', 'ﬁ').replace('fl', 'ﬂ')
        with self.with_pdf_text(typography):
            parties.validate(ROOT)

    def test_unrelated_extraction_layout_differences_are_not_quote_evidence(self):
        # Poppler changes dot leaders / overlapping text elsewhere in some PDFs.
        with self.with_pdf_text(lambda text, party: 'Different extracted header layout\n' + text):
            parties.validate(ROOT)

    def test_retained_quote_alone_is_not_pdf_evidence(self):
        def remove_cited_page(text, party):
            # The extractor now returns only the requested cited page.
            return 'No supporting text on this page.\n\f'
        with self.with_pdf_text(remove_cited_page):
            with self.assertRaisesRegex(AssertionError, '(?i)(excerpt not on cited PDF page|cost quote not on PDF page)'):
                parties.validate(ROOT)

    def test_quote_elsewhere_in_pdf_does_not_support_cited_page(self):
        def move_cited_page(text, party):
            # Even if extraction unexpectedly yields another page, its quote must
            # not stand in for the requested page's missing evidence.
            return 'No supporting text on the cited page.\n\f' + text
        with self.with_pdf_text(move_cited_page):
            with self.assertRaisesRegex(AssertionError, '(?i)(excerpt not on cited PDF page|cost quote not on PDF page)'):
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
