"""Synthetic adapter fixtures, not evidence about publisher availability."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit_context
import discover


class ContextAuditTests(unittest.TestCase):
    def run_audit(self, raw=b'retained', fail=False, calendar=b'calendar', live_fail=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'config').mkdir()
            (root / 'sources').mkdir()
            sha = lambda data: hashlib.sha256(data).hexdigest()
            source = dict(id='fixture', adapter='retained-url-snapshot',
                          manifest='sources/manifest.json', allowed_hosts=['example.org'])
            baseline = dict(file='data.bin', url='https://example.org/data', sha256=sha(b'retained'))
            (root / 'config/release-sources.json').write_text(json.dumps([source]))
            (root / 'sources/manifest.json').write_text(json.dumps(baseline))
            (root / 'sources/data.bin').write_bytes(b'retained')
            (root / 'sources/release-calendar.json').write_text(json.dumps(dict(entries=dict(
                fixture=dict(evidence=[dict(url='https://example.org/calendar',
                                           sha256=sha(b'calendar'), retrieved='2026-11-01')])))))
            before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
            def fetch(url, hosts):
                if url.endswith('/calendar'):
                    return calendar
                if fail:
                    raise OSError('unavailable fixture')
                return raw
            with patch.object(discover, 'fetch', side_effect=fetch) as mocked, patch.object(
                    audit_context.subprocess, 'check_output', return_value='revision\n'), patch.object(
                    audit_context, 'verify_site', side_effect=ValueError('live mismatch') if live_fail else None,
                    return_value={'index.html': sha(b'html')}):
                report = audit_context.audit(root, 'https://example.org')
                self.assertIs(discover.fetch, mocked)
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob('*') if p.is_file()})
            return report

    def test_unchanged_retains_positive_hash_evidence(self):
        report = self.run_audit()
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['sources'][0]['status'], 'unchanged')
        self.assertEqual(report['requests'][0]['sha256'], report['sources'][0]['retained_sha256'])
        self.assertIn('finished_at', report['requests'][0])
        self.assertEqual(report['deployment']['status'], 'exact-byte-match')

    def test_failed_source_is_unknown_and_other_checks_continue(self):
        report = self.run_audit(fail=True)
        self.assertEqual(report['sources'][0]['status'], 'unknown')
        self.assertNotIn('updates', report['sources'][0])
        self.assertEqual(report['calendars'][0]['status'], 'unchanged')
        self.assertTrue(report['errors'])

    def test_changed_snapshot_yields_notice_without_writing_it(self):
        report = self.run_audit(raw=b'revised')
        self.assertEqual(report['sources'][0]['status'], 'updates')
        self.assertEqual(report['retained_revision_status']['notices'], [])
        self.assertEqual(len(report['reconciled_revision_status']['notices']), 1)

    def test_changed_calendar_requires_review(self):
        report = self.run_audit(calendar=b'changed')
        self.assertEqual(report['calendars'][0]['status'], 'changed-needs-review')
        self.assertTrue(report['errors'])

    def test_deployment_failure_does_not_claim_success(self):
        report = self.run_audit(live_fail=True)
        self.assertEqual(report['deployment']['status'], 'unknown-or-mismatch')
        self.assertNotIn('files', report['deployment'])
        self.assertTrue(report['errors'])


if __name__ == '__main__':
    unittest.main()
