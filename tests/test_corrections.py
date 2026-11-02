"""Offline schema mutations and real Git history fixtures; no published records."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import corrections

SCRIPT = Path(corrections.__file__).resolve()


def record(identifier='test-only-1', stamp='2026-01-01'):
    return {'id': identifier, 'date': stamp, 'page': 'index.html',
            'error': 'Fictional error used only in an isolated test fixture.',
            'correction': 'Fictional replacement used only in an isolated test fixture.',
            'source': 'https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/commit/' + 'a' * 40}


class CorrectionsFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'site').mkdir()
        (self.root / 'site/index.html').write_text('<!doctype html><title>Test fixture</title>')
        (self.root / 'sources').mkdir()
        self.path = self.root / corrections.SOURCE

    def save(self, entries):
        self.path.write_text(json.dumps(entries), encoding='utf-8')

    def invalid(self, entries):
        self.save(entries)
        with self.assertRaises(corrections.ValidationError):
            corrections.load(self.path)


class CorrectionsTests(CorrectionsFixture):
    def test_empty_and_valid_records(self):
        for data in ([], [record()], [record(), record('test-only-2')]):
            self.save(data)
            self.assertEqual(corrections.load(self.path), data)

    def test_json_format_and_exact_fields(self):
        for data in ({}, None, '', [None], [[]], [dict(record(), extra='x')]):
            with self.subTest(data=data):
                self.invalid(data)
        for field in corrections.LIMITS:
            item = record()
            del item[field]
            with self.subTest(missing=field):
                self.invalid([item])
        for text in ('', '[', '[NaN]', '[{"id":"a", "id":"b"}]'):
            self.path.write_text(text)
            with self.assertRaises(corrections.ValidationError):
                corrections.load(self.path)

    def test_nonempty_string_and_length_bounds_for_every_field(self):
        for field, limit in corrections.LIMITS.items():
            for value in (None, False, 123, [], {}, '', ' ', '\t', ' x', 'x ', 'a\x00b', 'a\nb', 'x' * (limit + 1)):
                with self.subTest(field=field, value=value):
                    self.invalid([dict(record(), **{field: value})])
        item = record()
        item.update(error='x' * corrections.LIMITS['error'], correction='x' * corrections.LIMITS['correction'])
        self.save([item])
        self.assertEqual(corrections.load(self.path), [item])

    def test_staging_mode_skips_existence_not_safe_path_validation(self):
        self.save([dict(record(), page='not-rendered-yet.html')])
        self.assertEqual(corrections.load(self.path, check_pages=False)[0]['page'], 'not-rendered-yet.html')
        with self.assertRaises(corrections.ValidationError):
            corrections.load(self.path)
        self.save([dict(record(), page='../outside.html')])
        with self.assertRaises(corrections.ValidationError):
            corrections.load(self.path, check_pages=False)

    def test_id_and_duplicate_mutations(self):
        for value in ('Upper', '-abc', 'abc-', 'abc--def', 'has space', '../id', 'é', 'a_b'):
            with self.subTest(value=value):
                self.invalid([dict(record(), id=value)])
        self.invalid([record(), record()])

    def test_dates_and_chronological_order(self):
        for value in ('2026-1-01', '20260101', '2026-01-01T00:00:00Z', '2026-02-29', '2026-13-01', '0000-01-01'):
            with self.subTest(value=value):
                self.invalid([dict(record(), date=value)])
        self.invalid([record(stamp='2026-02-01'), record('test-only-2', '2026-01-01')])
        data = [record(stamp='2024-02-29'), record('test-only-2', '2026-01-01')]
        self.save(data)
        self.assertEqual(corrections.load(self.path), data)

    def test_page_paths_and_symlink_escape(self):
        for value in ('/index.html', '../index.html', 'site/../../index.html', './index.html',
                      'a//index.html', 'https://example.test/index.html', '//example.test/index.html',
                      'index.html#x', 'index.html?x=y', '%2e%2e/index.html', 'a\\index.html',
                      'missing.html', 'index.htm', 'sources/corrections.json'):
            with self.subTest(value=value):
                self.invalid([dict(record(), page=value)])
        (self.root / 'site/directory.html').mkdir()
        self.invalid([dict(record(), page='directory.html')])
        outside = self.root / 'outside.html'
        outside.write_text('<title>Outside site</title>')
        (self.root / 'site/escape.html').symlink_to(outside)
        self.invalid([dict(record(), page='escape.html')])
        (self.root / 'site/nested').mkdir()
        (self.root / 'site/nested/page.html').write_text('<title>Nested</title>')
        self.save([dict(record(), page='nested/page.html')])
        self.assertEqual(corrections.load(self.path)[0]['page'], 'nested/page.html')

    def test_only_specific_repository_commit_or_pull_source(self):
        base = 'https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/'
        for suffix in ('commit/' + 'a' * 40, 'commit/' + 'F' * 40 + '#diff-abcd1234R10', 'pull/123'):
            self.save([dict(record(), source=base + suffix)])
            self.assertEqual(corrections.load(self.path)[0]['source'], base + suffix)
        bad = [base + suffix for suffix in ('commit/main', 'commit/' + 'a' * 39, 'commit/' + 'a' * 41,
               'commit/' + 'g' * 40, 'pull/0', 'pull/-1', 'pull/01', 'pull/1/files', 'pull/1?x=y',
               'commit/' + 'a' * 40 + '#other')]
        bad += [record()['source'].replace('https:', 'http:'),
                record()['source'].replace('jnyross/', 'someone/'),
                record()['source'].replace('github.com/', 'github.com.evil.test/'),
                record()['source'] + '/extra', record()['source'] + '?x=y']
        for value in bad:
            with self.subTest(source=value):
                self.invalid([dict(record(), source=value)])

    def test_append_only_semantic_prefix(self):
        old = [record(), record('test-only-2')]
        corrections.assert_append_only([], [])
        corrections.assert_append_only([], old)
        corrections.assert_append_only(old, copy.deepcopy(old))
        corrections.assert_append_only(old, old + [record('test-only-3', '2026-02-01')])
        # Key order and whitespace of the JSON encoding are not history edits.
        reordered_keys = [{key: item[key] for key in reversed(list(item))} for item in old]
        corrections.assert_append_only(old, reordered_keys)
        bad = [[], old[:1], old[1:], list(reversed(old))]
        for field in corrections.LIMITS:
            mutation = copy.deepcopy(old)
            mutation[0][field] = {'id': 'changed-id', 'date': '2025-01-01',
                                 'page': 'changed.html', 'source': record()['source'].replace('a' * 40, 'b' * 40)
                                 }.get(field, 'Changed text')
            bad.append(mutation)
        for current in bad:
            with self.subTest(current=current):
                with self.assertRaises(corrections.ValidationError):
                    corrections.assert_append_only(old, current)

    def test_direct_append_api_rejects_invalid_data(self):
        for previous, current in (({}, []), ([], None), ([], [dict(record(), extra='x')]),
                                  ([], [record(), record()])):
            with self.assertRaises(corrections.ValidationError):
                corrections.assert_append_only(previous, current)


class GitIntegrationTests(CorrectionsFixture):
    # Keep the same isolated file helpers; actual subprocess CLI and real Git objects.
    def git(self, *args):
        result = subprocess.run(['git', '-C', str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def setUp(self):
        super().setUp()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Corrections Test Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('add', 'site')
        self.git('commit', '-qm', 'Synthetic test fixture without corrections file')
        self.initial = self.git('rev-parse', 'HEAD')

    def commit_source(self, data):
        self.save(data)
        self.git('add', corrections.SOURCE)
        self.git('commit', '-qm', 'Synthetic corrections fixture')
        return self.git('rev-parse', 'HEAD')

    def cli(self, base=None, succeeds=True):
        command = [sys.executable, str(SCRIPT), '--root', str(self.root)]
        if base is not None:
            command += ['--base=' + base]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if succeeds else 1, result.stdout + result.stderr)
        return result

    def test_cli_missing_old_file_allows_first_introduction_not_missing_ref(self):
        self.save([])
        self.cli(self.initial)
        self.save([record()])
        self.cli(self.initial)
        result = self.cli('this-ref-does-not-exist', succeeds=False)
        self.assertIn('cannot verify corrections history', result.stderr)
        self.cli('--invalid-ref', succeeds=False)
        self.cli(succeeds=True)

    def test_cli_actual_git_append_edit_drop_empty_and_reorder(self):
        old = [record(), record('test-only-2')]
        base = self.commit_source(old)
        self.cli(base)
        self.save(old + [record('test-only-3', '2026-02-01')])
        self.cli(base)
        for current in ([], old[:1], list(reversed(old)), [dict(old[0], correction='Changed'), old[1]]):
            self.save(current)
            self.cli(base, succeeds=False)
        self.path.write_text(json.dumps(old, sort_keys=True, separators=(',', ':')))
        self.cli(base)

    def test_cli_empty_old_ledger_allows_append(self):
        base = self.commit_source([])
        self.save([record()])
        self.cli(base)

    def test_cli_malformed_old_source_is_not_first_introduction(self):
        base = self.commit_source({'wrong': 'shape'})
        self.save([])
        self.cli(base, succeeds=False)

    def test_cli_missing_and_malformed_current_fail(self):
        self.cli(self.initial, succeeds=False)
        self.path.write_text('{')
        self.cli(self.initial, succeeds=False)
        self.save([dict(record(), page='missing.html')])
        self.cli(self.initial, succeeds=False)

    def test_git_show_failure_fails_closed(self):
        base = self.commit_source([])
        run = corrections.subprocess.run

        def broken_show(command, **kwargs):
            if 'show' in command:
                return subprocess.CompletedProcess(command, 128, '', 'simulated object read failure')
            return run(command, **kwargs)

        with patch.object(corrections.subprocess, 'run', side_effect=broken_show):
            with self.assertRaisesRegex(corrections.ValidationError, 'simulated object read failure'):
                corrections.check_base(self.root, base, [])


if __name__ == '__main__':
    unittest.main()
