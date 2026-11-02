"""Exercise the real issue write path against a deliberately stale fake transport."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('delivery_discover', ROOT / 'scripts/discover.py')
discover = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discover)


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'receipts.json'
        self.update = json.loads((ROOT / 'docs/evidence/freshness-w6/roster-issue-report.json').read_text())['updates'][0]
        self.creates = []
        self.listing = '[[]]'  # Intentionally NEVER shows the successful issue write.

    def transport(self, *args):
        if args[0] == 'api':
            return self.listing
        self.assertEqual(args[:4], ('issue', 'create', '--repo', 'fixture/repo'))
        self.creates.append(args)
        return 'https://github.com/fixture/repo/issues/1'

    def deliver(self, run=None, repo='fixture/repo'):
        return discover.open_updates([self.update], repo, run or self.transport, receipt_path=self.path)

    def test_immediate_repeat_stale_list_creates_once(self):
        self.assertEqual(self.deliver()[0]['status'], 'opened')
        self.assertEqual(self.deliver()[0]['status'], 'already reported')
        self.assertEqual(self.deliver()[0]['status'], 'already reported')
        self.assertEqual(len(self.creates), 1)
        self.assertIn('source-release:' + self.update['key'], self.creates[0][-1])

    def test_timeout_after_remote_create_refuses_blind_repeat_then_reconciles(self):
        def timeout(*args):
            value = self.transport(*args)
            if args[0] == 'issue':
                raise OSError('Response lost after remote accepted create')
            return value
        with self.assertRaises(OSError):
            self.deliver(timeout)
        with self.assertRaisesRegex(RuntimeError, 'delivery uncertain'):
            self.deliver()
        self.assertEqual(len(self.creates), 1)
        self.listing = json.dumps([[{'body': '<!-- source-release:' + self.update['key'] + ' -->'}]])
        self.assertEqual(self.deliver()[0]['status'], 'already reported')
        self.listing = '[[]]'  # A later stale response still cannot duplicate it.
        self.assertEqual(self.deliver()[0]['status'], 'already reported')
        self.assertEqual(len(self.creates), 1)

    def test_receipt_save_failure_before_write_cannot_create(self):
        from scripts.issue_delivery import IssueReceipts
        with mock.patch.object(IssueReceipts, 'save', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'disk full'):
                self.deliver()
        self.assertEqual(self.creates, [])

    def test_failed_success_receipt_retains_pending_and_prevents_second_write(self):
        from scripts.issue_delivery import IssueReceipts
        with mock.patch.object(IssueReceipts, 'created', side_effect=OSError('disk lost after create')):
            with self.assertRaises(OSError):
                self.deliver()
        with self.assertRaisesRegex(RuntimeError, 'delivery uncertain'):
            self.deliver()
        self.assertEqual(len(self.creates), 1)

    def test_invalid_create_response_retains_uncertain_receipt(self):
        run = mock.Mock(side_effect=['[[]]', 'unexpected output'])
        with self.assertRaisesRegex(ValueError, 'Unexpected issue creation response'):
            self.deliver(run)
        with self.assertRaisesRegex(RuntimeError, 'delivery uncertain'):
            self.deliver()
        self.assertEqual(self.creates, [])

    def test_malformed_receipt_fails_closed_without_github_call(self):
        self.path.write_text('{bad json')
        run = mock.Mock(side_effect=AssertionError('Must not call GitHub'))
        with self.assertRaises(ValueError):
            self.deliver(run)
        run.assert_not_called()

    def test_list_failure_does_not_reserve_and_next_attempt_can_create(self):
        with self.assertRaises(OSError):
            self.deliver(mock.Mock(side_effect=OSError('list unavailable')))
        self.assertFalse(self.path.exists())
        self.assertEqual(self.deliver()[0]['status'], 'opened')

    def test_repository_case_preserves_successful_and_uncertain_receipts(self):
        self.deliver()
        self.assertEqual(self.deliver(repo='Fixture/Repo')[0]['status'], 'already reported')
        self.assertEqual(len(self.creates), 1)
        # Older case aliases are reconciled without permitting another write.
        self.path.write_text(json.dumps({'schema_version': 1, 'repositories': {
            'Fixture/Repo': {self.update['key']: {'status': 'pending'}}}}))
        with self.assertRaisesRegex(RuntimeError, 'delivery uncertain'):
            self.deliver()
        self.assertEqual(len(self.creates), 1)

    def test_create_url_accepts_canonical_repository_casing(self):
        run = mock.Mock(side_effect=['[[]]', 'https://github.com/Fixture/Repo/issues/1'])
        self.assertEqual(self.deliver(run)[0]['status'], 'opened')
        self.assertEqual(self.deliver(repo='FIXTURE/REPO')[0]['status'], 'already reported')

    def test_different_repository_does_not_share_receipt(self):
        self.deliver()
        run = mock.Mock(side_effect=['[[]]', 'https://github.com/other/repo/issues/1'])
        self.assertEqual(self.deliver(run, repo='other/repo')[0]['status'], 'opened')
        self.assertEqual(run.call_count, 2)

    def test_receipt_serializes_concurrent_processes_and_survives_restart(self):
        code = '''
import importlib.util,json,sys
from pathlib import Path
root=Path(sys.argv[1])
spec=importlib.util.spec_from_file_location('discover',root/'scripts/discover.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
u=json.loads((root/'docs/evidence/freshness-w6/roster-issue-report.json').read_text())['updates'][0]
def run(*args):
    if args[0]=='api': return '[[]]'
    with open(sys.argv[3],'a') as out: out.write('create\\n')
    return 'https://github.com/fixture/repo/issues/1'
print(m.open_updates([u],'fixture/repo',run,receipt_path=Path(sys.argv[2]))[0]['status'])
'''
        writes = self.path.parent / 'writes.txt'
        args = [sys.executable, '-c', code, str(ROOT), str(self.path), str(writes)]
        processes = [subprocess.Popen(args, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE) for _ in range(2)]
        outcomes = []
        for process in processes:
            out, err = process.communicate(timeout=15)
            self.assertEqual(process.returncode, 0, err)
            outcomes.append(out.strip())
        self.assertEqual(sorted(outcomes), ['already reported', 'opened'])
        self.assertEqual(subprocess.check_output(args, cwd=ROOT, text=True).strip(), 'already reported')
        self.assertEqual(writes.read_text(), 'create\n')
