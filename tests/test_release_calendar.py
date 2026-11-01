"""Automated calendar provenance and safe-refresh checks; no live network needed."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import release_calendar

ROOT = Path(__file__).resolve().parents[1]


class ReleaseCalendarTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sources = self.root / 'sources'
        self.sources.mkdir()
        self.calendar = json.loads((ROOT / 'sources/release-calendar.json').read_text())
        self.responses = {}
        for entry in self.calendar['entries'].values():
            for item in [entry, *entry.get('evidence', [])]:
                data = (ROOT / 'sources' / item['file']).read_bytes()
                (self.sources / item['file']).write_bytes(data)
                self.responses[item['url']] = data
        self.save_calendar()

    def save_calendar(self):
        (self.sources / 'release-calendar.json').write_text(json.dumps(self.calendar))

    def state(self):
        return {p.name: p.read_bytes() for p in self.sources.iterdir()}

    def fetch(self, request, timeout):
        self.assertEqual(timeout, 90)
        return io.BytesIO(self.responses[request.full_url])

    def test_unchanged_is_deterministic_and_keeps_snapshot_date(self):
        before = self.state()
        with patch('urllib.request.urlopen', side_effect=self.fetch) as fetch:
            result = release_calendar.refresh(self.root)
        self.assertEqual(result['status'], 'unchanged')
        self.assertEqual(result['checked_at'], self.calendar['checked_at'])
        self.assertEqual(fetch.call_count, result['snapshots'])
        self.assertEqual(before, self.state())

    def test_changed_evidence_requires_review_and_preserves_last_good(self):
        before = self.state()
        # Valid metadata can change while still requiring human/agent review of
        # the interpretation. Do not carry the old null-date claim forward.
        url = self.calendar['entries']['spending']['url']
        data = json.loads(self.responses[url])
        data['description'] = 'Changed official release metadata'
        self.responses[url] = json.dumps(data).encode()
        with patch('urllib.request.urlopen', side_effect=self.fetch):
            with self.assertRaises(release_calendar.CalendarReviewRequired):
                release_calendar.refresh(self.root)
        self.assertEqual(before, self.state())

    def test_failed_lookup_retains_every_snapshot(self):
        before = self.state()
        count = 0

        def fail_later(request, timeout):
            nonlocal count
            count += 1
            if count == 3:
                raise OSError('Network unavailable')
            return self.fetch(request, timeout)

        with patch('urllib.request.urlopen', side_effect=fail_later):
            with self.assertRaises(OSError):
                release_calendar.refresh(self.root)
        self.assertEqual(count, 3)
        self.assertEqual(before, self.state())

    def test_mutated_local_hash_fails_before_network(self):
        path = self.sources / self.calendar['entries']['spending']['file']
        path.write_bytes(path.read_bytes() + b' ')
        with patch('urllib.request.urlopen') as fetch:
            with self.assertRaisesRegex(ValueError, 'hash changed'):
                release_calendar.refresh(self.root)
            fetch.assert_not_called()

    def test_non_json_and_non_object_responses_are_rejected(self):
        for bad in [b'<html>Unavailable</html>', b'[]']:
            with self.subTest(data=bad):
                before = self.state()
                with patch('urllib.request.urlopen', return_value=io.BytesIO(bad)):
                    with self.assertRaises(ValueError):
                        release_calendar.refresh(self.root)
                self.assertEqual(before, self.state())

    def test_malformed_search_metadata_is_rejected(self):
        for bad in [{'results': [], 'total': '0'}, {'results': [], 'total': -1}, {'results': None, 'total': 0}]:
            with self.subTest(metadata=bad):
                before = self.state()
                url = next(u for u in self.responses if '/api/search.json?' in u)
                self.responses[url] = json.dumps(bad).encode()
                with patch('urllib.request.urlopen', side_effect=self.fetch):
                    with self.assertRaisesRegex(ValueError, 'Malformed calendar search'):
                        release_calendar.refresh(self.root)
                self.assertEqual(before, self.state())

    def test_conflicting_metadata_and_path_escape_are_rejected(self):
        entry = self.calendar['entries']['spending']
        entry['evidence'].append({'file': entry['file'], 'url': entry['url'], 'sha256': '0' * 64})
        self.save_calendar()
        with patch('urllib.request.urlopen') as fetch:
            with self.assertRaisesRegex(ValueError, 'Conflicting'):
                release_calendar.refresh(self.root)
            fetch.assert_not_called()
        entry['evidence'].pop()
        entry['file'] = '../escape.json'
        self.save_calendar()
        with patch('urllib.request.urlopen') as fetch:
            with self.assertRaisesRegex(ValueError, 'Invalid calendar snapshot path'):
                release_calendar.refresh(self.root)
            fetch.assert_not_called()

    def test_retained_quotes_hashes_and_date_precision(self):
        import html
        import re
        body = json.loads((self.sources / 'calendar-hmt-spending-guidance.json').read_text())['details']['body']
        normalized = ' '.join(html.unescape(re.sub('<[^>]*>', ' ', body)).split())
        for key in ['spending', 'history']:
            entry = self.calendar['entries'][key]
            self.assertIn(entry['source_text'], normalized)
            self.assertIsNone(entry['next_release'])
        for entry in self.calendar['entries'].values():
            for item in [entry, *entry.get('evidence', [])]:
                data = (self.sources / item['file']).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), item['sha256'])
        self.assertEqual(self.calendar['entries']['parties']['publication_date_precision'], 'year')


if __name__ == '__main__':
    unittest.main()
