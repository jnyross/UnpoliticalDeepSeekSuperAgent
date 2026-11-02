"""Offline regressions for the independent reading-grade gate."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from reading_grade import (GradeError, copy_blocks, measure, scan, sentence_count,
                           syllables, tokens, validate)

HARD = ('The institutionalisation of intergovernmental fiscal responsibilities '
        'necessitates comprehensive methodological reconciliation, notwithstanding '
        'heterogeneous jurisdictional classifications and consequential '
        'macroeconomic redistribution. ')
EASY = 'We pay for care. We pay for schools. This is our tax. '


class ReadingGradeTests(unittest.TestCase):
    def test_known_formula(self):
        result = measure('<p>The cat sat on the mat.</p>')
        self.assertEqual((result.words, result.sentences, result.syllables), (6, 1, 6))
        self.assertAlmostEqual(result.grade, 0.39 * 6 + 11.8 - 15.59)

    def test_dictionary_difficult_words(self):
        for word, expected in [('education', 4), ('reconciliation', 6),
                               ('fire', 1), ('queue', 1), ('people', 2)]:
            with self.subTest(word=word):
                self.assertEqual(syllables(word), (expected, False))

    def test_unknown_is_reported_not_silently_omitted(self):
        result = measure('<p>Florbulation is hard.</p>')
        self.assertIn('florbulation', result.unknown)
        self.assertGreater(result.syllables, 3)
        self.assertEqual(syllables('XYZ'), (3, False))

    def test_tokens_contractions_accents_hyphens_and_numbers(self):
        self.assertEqual(tokens('Féin can’t re-use £1,234.50 in 2025–26.'),
                         ['Fein', "can't", 're', 'use', '1,234.50', 'in', '2025', '26'])

    def test_inline_markup_does_not_create_words_or_sentences(self):
        self.assertEqual(measure('<p>We fund edu<em>ca</em>tion and <a>health</a>.</p>'),
                         measure('<p>We fund education and health.</p>'))
        self.assertEqual(copy_blocks('<p>One <span>long</span><br>line.</p>'), ['One long line.'])
        self.assertEqual(copy_blocks('<nav><a>Health</a><a>Care</a></nav>'), ['Health Care'])

    def test_sentence_punctuation_and_fragments(self):
        self.assertEqual(sentence_count('What?! Yes... A final fragment'), 3)
        self.assertEqual(sentence_count('Dr. Smith paid 3.14 in the U.K. today.'), 1)
        self.assertEqual(sentence_count('See https://example.gov.uk/a?x=2 and 5_2!G79.'), 1)
        self.assertEqual(sentence_count('123 45.67'), 0)
        self.assertEqual(measure('<h1>Tax</h1><p>We pay.<br>We fund care.</p>').sentences, 3)

    def test_table_row_not_each_cell_is_fragment(self):
        result = measure('<table><tr><th>Health</th><td>123</td><td>5_2!G79</td></tr>'
                         '<tr><td>456</td><td>789</td></tr></table>')
        self.assertEqual(result.sentences, 1)
        self.assertIsNone(result.prose_grade)

    def test_nested_closed_details_table_labels_and_quotes_included(self):
        html = ('<details><summary>More</summary><details><summary>Source</summary>'
                '<table><tr><th>Official source label</th><td><q>' + HARD +
                '</q></td></tr></table><p>' + HARD + '</p></details></details>')
        joined = ' '.join(copy_blocks(html))
        self.assertIn('Official source label', joined)
        self.assertEqual(joined.count('institutionalisation'), 2)
        result = measure(html)
        self.assertGreater(result.grade, 7)
        self.assertGreater(result.prose_grade, 7)

    def test_only_nonreadable_script_style_excluded_from_full_copy(self):
        html = ('<head><title>Title</title><style>' + HARD + '</style></head>'
                '<script>' + HARD + '</script><p hidden>Hidden text</p>'
                '<template>Template text</template><noscript>No script text</noscript>'
                '<svg><text>Chart label</text></svg><p aria-hidden="true">Still text</p>')
        text = ' '.join(copy_blocks(html))
        for expected in ['Title', 'Hidden text', 'Template text', 'No script text', 'Chart label', 'Still text']:
            self.assertIn(expected, text)
        self.assertNotIn('institutionalisation', text)
        self.assertEqual(copy_blocks('<p>We <script>code</script>pay tax.</p>'), ['We pay tax.'])

    def test_numeric_padding_cannot_mask_difficult_copy(self):
        result = measure('<p>' + HARD + '</p><table>' +
                         '<tr><td>123 456 789 101 111</td></tr>' * 1000 + '</table>')
        self.assertGreater(result.verbal_grade, 7)
        self.assertGreater(result.prose_grade, 7)

    def test_labels_cannot_mask_difficult_prose(self):
        result = measure('<p>' + HARD + '</p><table>' +
                         '<tr><th>Tax</th><td>Pay</td></tr>' * 1000 + '</table>')
        self.assertLess(result.grade, 7)
        self.assertGreater(result.prose_grade, 7)

    def test_blank_and_numeric_only_page_fail_closed(self):
        for html in ['', '<script>text</script>', '<p>12345</p>']:
            with self.subTest(html=html), self.assertRaises(GradeError):
                measure(html)

    def test_all_pages_recursively_scanned_and_difficult_copy_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'site/nested').mkdir(parents=True)
            (root / 'site/index.html').write_text('<p>' + EASY + '</p>')
            (root / 'site/nested/new.html').write_text('<details><summary>More</summary><p>' + HARD + '</p></details>')
            self.assertEqual(len(scan(root)), 2)
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(GradeError, 'nested/new.html'):
                validate(root)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(len(validate(root, report_only=True)), 2)

    def test_missing_site_does_not_pass(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(GradeError):
            scan(Path(directory))

    def test_threshold_uses_unrounded_grade(self):
        from dataclasses import replace
        result = replace(measure('<p>' + EASY + '</p>'), grade=7.000001,
                         verbal_grade=6, prose_grade=6)
        with patch('reading_grade.scan', return_value={Path('/site/index.html'): result}):
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(GradeError):
                validate(Path('/'))

    def test_check_entrypoint_enforces_readability_first(self):
        import check
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'site').mkdir()
            (root / 'site/index.html').write_text('<p>' + HARD + '</p>')
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(GradeError):
                check.validate(root)


if __name__ == '__main__':
    unittest.main()
