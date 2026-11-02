"""Automated kit regression checks, not participant evidence."""
import copy
import csv
import io
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import comprehension_kit as kit


class KitTests(unittest.TestCase):
    def test_checked_in_kit_and_pinned_revision(self):
        kit.validate(ROOT)

    def test_all_eight_questions_without_answers_on_sheet(self):
        sheet = kit.participant(ROOT)
        for i, question in enumerate(kit.questions(ROOT), 1):
            self.assertEqual(sheet.count(f'{i}. {question}\n'), 1)
        self.assertEqual(sheet.count('Answer:'), 8)
        self.assertNotIn('Expected:', sheet)
        self.assertNotIn('£96.9', sheet)

    def test_template_is_empty_and_complete(self):
        rows = list(csv.reader(io.StringIO((ROOT/kit.KIT/'results-template.csv').read_text())))
        self.assertEqual(len(rows), 1, 'No invented participant rows')
        fields = rows[0]
        self.assertEqual(len(fields), len(set(fields)))
        for i in range(1, 9):
            self.assertIn(f'q{i}_response', fields)
            self.assertIn(f'q{i}_score', fields)
        for name in ('page_revision', 'kit_revision', 'session_date_utc', 'politics_following',
                     'elapsed_seconds', 'protocol_valid', 'total_correct', 'qualifies'):
            self.assertIn(name, fields)

    def test_each_answer_changes_with_its_data(self):
        spending = json.loads((ROOT/'site/data/spending.json').read_text())
        comparison = json.loads((ROOT/'site/data/comparisons.json').read_text())
        expected = kit.answers(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'site/data').mkdir(parents=True)
            for index in range(8):
                d, c = copy.deepcopy(spending), copy.deepcopy(comparison)
                if index == 0:
                    d['rows'][0]['value'] = 999999999
                elif index == 1:
                    d['total']['value'] *= 2
                elif index == 2:
                    d['extras'][1]['value'] += 10000
                elif index == 3:
                    c['health_change'] *= -1
                elif index == 4:
                    c['gdp_change'] *= -1
                elif index == 5:
                    d['extras'][0]['value'] += 10000
                elif index == 6:
                    c['points'][0]['status'] = 'forecast'
                elif index == 7:
                    d['extras'][1]['cell'] = 'H15'
                (root/'site/data/spending.json').write_text(json.dumps(d))
                (root/'site/data/comparisons.json').write_text(json.dumps(c))
                self.assertNotEqual(kit.answers(root)[index], expected[index])

    def test_stale_key_sheet_and_inputs_are_rejected(self):
        # Read-only symlinks to real inputs; mutate only disposable kit files.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'site').symlink_to(ROOT/'site', target_is_directory=True)
            (root/'sources').symlink_to(ROOT/'sources', target_is_directory=True)
            (root/kit.KIT).mkdir(parents=True)
            (root/'docs/rubric.md').symlink_to(ROOT/'docs/rubric.md')
            for name in ('version.json', 'participant.md', 'answer-key.md'):
                (root/kit.KIT/name).write_bytes((ROOT/kit.KIT/name).read_bytes())
            # git show uses the existing repository while fixtures supply input bytes.
            gitdir = subprocess.check_output(['git', 'rev-parse', '--absolute-git-dir'], cwd=ROOT, text=True).strip()
            (root/'.git').write_text(f'gitdir: {gitdir}\n')
            for name in ('participant.md', 'answer-key.md'):
                path = root/kit.KIT/name
                original = path.read_text()
                path.write_text(original + '\nChanged\n')
                with self.assertRaises(ValueError):
                    kit.validate(root)
                path.write_text(original)
            path = root/kit.KIT/'version.json'
            m = json.loads(path.read_text())
            m['input_sha256']['site/index.html'] = '0'*64
            path.write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError, 'Kit inputs changed'):
                kit.validate(root)


if __name__ == '__main__':
    unittest.main()
