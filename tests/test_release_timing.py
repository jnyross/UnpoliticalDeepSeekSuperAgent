"""Offline timing regressions using invented fixtures, never historical/live evidence.

All publisher responses, timestamps, source bytes and deployment responses below are
synthetic. No ledger is written into the repository and no external request is allowed.
"""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('release_timing_tests', ROOT / 'scripts/release_timing.py')
timing = importlib.util.module_from_spec(SPEC)
with mock.patch.object(sys, 'path', [str(ROOT / 'scripts'), *sys.path]):
    SPEC.loader.exec_module(timing)


class ReleaseTimingFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ledger = self.root / 'measurements/timing.jsonl'
        self.source = dict(id='invented-source', manifest='sources/fixture.json')
        self.baseline = dict(release_url='https://publisher.invalid/release',
                             attachment_url='https://publisher.invalid/fixture.xlsx',
                             published='2026-01-01', updated='2026-01-02T08:00:00Z',
                             sha256=timing.sha(b'invented source bytes'))
        self.write_json('config/release-sources.json', [self.source])
        self.write_json(self.source['manifest'], self.baseline)
        self.write_json('site/' + self.source['manifest'], self.baseline)
        self.write_bytes('site/index.html', b'<h1>Invented test deployment</h1>')
        self.write_bytes('site/assets/space name.bin', b'\x00\xfffixture')
        self.at = '2026-01-03T10:00:00Z'
        self.evidence = 'https://ci.invalid/actions/runs/fixture'
        self.live = 'https://deployment.invalid'
        self.revision = 'a' * 40
        self.calls = []
        patch = mock.patch.object(timing.urllib.request.OpenerDirector, 'open',
                                  side_effect=AssertionError('Unexpected network request'))
        patch.start()
        self.addCleanup(patch.stop)

    def test_publication_candidates_measure_listing_not_unfetched_document(self):
        for scope in ('official-policy-listing-review', 'official-publication-listing-review'):
            with self.subTest(scope=scope):
                candidate = dict(self.baseline, discovery_scope=scope,
                                 listing_url='https://publisher.invalid/publications/',
                                 listing_sha256=timing.sha(b'canonical listing fixture'))
                version = timing.version('invented-source', candidate)
                self.assertEqual(version['release_url'], candidate['listing_url'])
                self.assertEqual(version['attachment_url'], candidate['listing_url'])
                self.assertEqual(version['sha256'], candidate['listing_sha256'])
                self.assertIsNone(version['vintage'])
                self.assertIsNone(version['publication_at'])
                self.assertIsNone(version['original_publication'])

    def write_bytes(self, relative, raw):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def write_json(self, relative, value):
        self.write_bytes(relative, json.dumps(value).encode())

    def get(self, address):
        self.calls.append(address)
        self.assertEqual(urlsplit(address).netloc, 'deployment.invalid')
        return (self.root / 'site' / unquote(urlsplit(address).path).lstrip('/')).read_bytes()

    def observe(self, **kwargs):
        args = dict(at=self.at, evidence_url=self.evidence, revision=self.revision)
        args.update(kwargs)
        return timing.observe(self.ledger, self.root, **args)

    def events(self):
        return timing.load(self.ledger)

    def discovery(self, baseline=None, errors=None):
        return dict(checked_at=self.at,
                    sources=[dict(id=self.source['id'], updates=[dict(evidence=baseline or self.baseline)])],
                    errors=errors or [])

    def rewrite_chain(self, events):
        """Sign deliberately invalid synthetic records to test semantic checks too."""
        previous = None
        for event in events:
            event.pop('event_sha256', None)
            event['previous_sha256'] = previous
            previous = timing.sha(timing.canonical(event))
            event['event_sha256'] = previous
        self.ledger.write_bytes(b''.join(timing.canonical(e) + b'\n' for e in events))

    def test_initial_observation_has_identity_not_invented_history(self):
        self.assertTrue(self.observe())
        event, = self.events()
        self.assertEqual(event['kind'], 'observed')
        self.assertEqual(event['version'], timing.version(self.source['id'], self.baseline))
        self.assertEqual(event['sequence'], 1)
        self.assertIsNone(event['previous_sha256'])
        self.assertIsNone(event['historical_first_observed_at'])
        self.assertIsNone(event['historical_first_live_at'])

    def test_unchanged_and_duplicate_discovery_are_byte_identical_noops(self):
        self.observe()
        before = self.ledger.read_bytes()
        self.assertTrue(self.observe(at='2026-01-04T10:00:00Z', discovery=self.discovery()))
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_new_release_and_retained_url_revision_are_distinct(self):
        self.observe()
        before = self.ledger.read_bytes()
        revised = dict(self.baseline, sha256=timing.sha(b'invented changed bytes'))
        self.observe(discovery=self.discovery(revised))
        self.assertTrue(self.ledger.read_bytes().startswith(before))
        self.assertEqual(len(self.events()), 2)
        self.assertEqual(self.events()[1]['version']['sha256'], revised['sha256'])
        newer = dict(revised, updated='2026-01-03T09:00:00Z',
                     release_url='https://publisher.invalid/next-release')
        self.observe(discovery=self.discovery(newer))
        self.assertEqual(len(self.events()), 3)
        self.assertIsNone(timing.report(self.events())['versions'][2]['first_verified_live_at'])

    def test_repeated_update_preserves_first_observation(self):
        changed = dict(self.baseline, sha256=timing.sha(b'changed'))
        self.observe(discovery=self.discovery(changed))
        before = self.ledger.read_bytes()
        self.observe(at='2026-01-04T00:00:00Z', discovery=self.discovery(changed))
        self.assertEqual(self.ledger.read_bytes(), before)
        self.assertEqual(timing.report(self.events())['versions'][1]['first_observed_at'], self.at)

    def test_discovery_errors_append_without_fabricating_versions(self):
        error = dict(source='unreachable-fixture', error='invented timeout')
        self.observe(discovery=self.discovery(errors=[error]))
        self.observe(at='2026-01-04T00:00:00Z', discovery=self.discovery(errors=[error]))
        events = self.events()
        self.assertEqual([e['kind'] for e in events], ['unavailable', 'observed', 'unavailable'])
        self.assertEqual(events[0]['reason'], error['error'])
        self.assertEqual(len(timing.report(events)['unavailable']), 2)

    def test_future_discovery_is_rejected_without_ledger(self):
        discovery = self.discovery()
        discovery['checked_at'] = '2026-01-04T00:00:00Z'
        with self.assertRaisesRegex(ValueError, 'future'):
            self.observe(discovery=discovery)
        self.assertFalse(self.ledger.exists())

    def test_future_publication_rejected_atomically(self):
        for published in ['2026-01-04', '2026-01-03T10:00:01Z']:
            with self.subTest(publication=published):
                future = dict(self.baseline, updated=published)
                with self.assertRaisesRegex(ValueError, 'Publication is after'):
                    self.observe(discovery=self.discovery(future))
                self.assertFalse(self.ledger.exists())

    def test_successful_live_binding_covers_every_site_byte(self):
        self.assertTrue(self.observe(live_url=self.live, get=self.get))
        observed, live = self.events()
        expected = {p.relative_to(self.root / 'site').as_posix(): timing.sha(p.read_bytes())
                    for p in (self.root / 'site').rglob('*') if p.is_file()}
        self.assertEqual(live['files'], expected)
        self.assertEqual(live['site_sha256'], timing.sha(timing.canonical(expected)))
        self.assertEqual(live['version'], observed['version'])
        self.assertEqual(live['revision'], self.revision)
        self.assertEqual(live['live_url'], self.live)
        self.assertEqual(len(self.calls), len(expected))
        self.assertIn(self.live + '/assets/space%20name.bin', self.calls)

    def test_same_live_snapshot_is_not_repeated_and_first_delivery_is_preserved(self):
        self.observe(live_url=self.live, get=self.get)
        before = self.ledger.read_bytes()
        self.observe(at='2026-01-04T00:00:00Z', revision='b' * 40,
                     live_url=self.live, get=self.get)
        self.assertEqual(self.ledger.read_bytes(), before)
        row, = timing.report(self.events())['versions']
        self.assertEqual(row['first_verified_live_at'], self.at)
        self.assertEqual(row['deployed_revision'], self.revision)

    def test_changed_site_appends_delivery_but_report_keeps_first(self):
        self.observe(live_url=self.live, get=self.get)
        self.write_bytes('site/index.html', b'new invented presentation')
        self.observe(at='2026-01-04T00:00:00Z', live_url=self.live, get=self.get)
        self.assertEqual([e['kind'] for e in self.events()], ['observed', 'live', 'live'])
        row, = timing.report(self.events())['versions']
        self.assertEqual(row['first_verified_live_at'], self.at)

    def test_discovery_candidate_is_not_claimed_live_until_in_manifest(self):
        changed = dict(self.baseline, sha256=timing.sha(b'next invented source'))
        self.observe(discovery=self.discovery(changed), live_url=self.live, get=self.get)
        rows = timing.report(self.events())['versions']
        self.assertIsNotNone(rows[0]['first_verified_live_at'])
        self.assertIsNone(rows[1]['first_verified_live_at'])
        self.write_json(self.source['manifest'], changed)
        self.write_json('site/' + self.source['manifest'], changed)
        self.observe(at='2026-01-04T00:00:00Z', live_url=self.live, get=self.get)
        self.assertEqual(timing.report(self.events())['versions'][1]['first_verified_live_at'],
                         '2026-01-04T00:00:00Z')

    def test_live_byte_mismatch_records_failure_never_delivery(self):
        self.assertFalse(self.observe(live_url=self.live, get=lambda _: b'not the site'))
        observed, failed = self.events()
        self.assertEqual(failed['kind'], 'unavailable')
        self.assertEqual(failed['source'], 'live-deployment')
        self.assertIn('Live output mismatch', failed['reason'])
        self.assertIsNone(timing.report([observed, failed])['versions'][0]['first_verified_live_at'])

    def test_live_fetch_exception_is_explicit_failure(self):
        def fail(_):
            raise OSError('invented network outage')
        self.assertFalse(self.observe(live_url=self.live, get=fail))
        self.assertEqual(self.events()[-1]['reason'], 'invented network outage')

    def test_manifest_mismatch_or_missing_copy_prevents_live_fetch(self):
        for raw in [b'{}', None]:
            with self.subTest(raw=raw):
                path = self.root / 'site' / self.source['manifest']
                if raw is None:
                    path.unlink()
                else:
                    path.write_bytes(raw)
                self.assertFalse(self.observe(live_url=self.live, get=self.get))
                self.assertFalse(self.calls)
                self.assertFalse(any(e['kind'] == 'live' for e in self.events()))

    def test_incomplete_and_empty_sites_rejected(self):
        empty = self.root / 'empty'
        empty.mkdir()
        with self.assertRaisesRegex(ValueError, 'Empty/incomplete'):
            timing.verify_site(empty, self.live, lambda _: b'')
        (empty / 'other.html').write_bytes(b'other')
        with self.assertRaisesRegex(ValueError, 'Empty/incomplete'):
            timing.verify_site(empty, self.live, lambda _: b'other')

    def test_corrupt_hash_or_chain_cannot_be_extended(self):
        self.observe()
        original = self.ledger.read_bytes()
        for field, value in [('event_sha256', '0' * 64), ('previous_sha256', 'f' * 64)]:
            with self.subTest(field=field):
                event = json.loads(original)
                event[field] = value
                if field == 'previous_sha256':
                    event.pop('event_sha256')
                    event['event_sha256'] = timing.sha(timing.canonical(event))
                corrupt = timing.canonical(event) + b'\n'
                self.ledger.write_bytes(corrupt)
                with self.assertRaisesRegex(ValueError, 'hash chain'):
                    self.observe()
                self.assertEqual(self.ledger.read_bytes(), corrupt)

    def test_validly_hashed_bad_sequence_and_time_order_rejected(self):
        self.observe(live_url=self.live, get=self.get)
        original = self.events()
        for key, value in [('sequence', 10), ('at', '2026-01-03T09:00:00Z')]:
            with self.subTest(key=key):
                events = copy.deepcopy(original)
                events[1][key] = value
                self.rewrite_chain(events)
                with self.assertRaisesRegex(ValueError, 'sequence/time order'):
                    self.events()

    def test_clock_rollback_addition_does_not_modify_ledger(self):
        self.observe()
        before = self.ledger.read_bytes()
        error = dict(source='fixture', error='invented failure')
        discovery = self.discovery(errors=[error])
        discovery['checked_at'] = '2026-01-03T09:00:00Z'
        with self.assertRaisesRegex(ValueError, 'sequence/time order'):
            self.observe(at='2026-01-03T09:00:00Z', discovery=discovery)
        self.assertEqual(self.ledger.read_bytes(), before)
        self.assertFalse(self.ledger.with_suffix('.pending').exists())

    def test_missing_final_newline_is_not_silently_repaired(self):
        self.observe()
        before = self.ledger.read_bytes().rstrip(b'\n')
        self.ledger.write_bytes(before)
        with self.assertRaisesRegex(ValueError, 'final newline'):
            self.observe()
        self.assertEqual(self.ledger.read_bytes(), before)

    def test_live_without_prior_observation_is_rejected(self):
        self.observe(live_url=self.live, get=self.get)
        live = self.events()[1]
        live['sequence'] = 1
        self.rewrite_chain([live])
        with self.assertRaisesRegex(ValueError, 'no prior observation'):
            self.events()

    def test_live_fingerprint_and_unsafe_file_paths_rejected(self):
        self.observe(live_url=self.live, get=self.get)
        original = self.events()
        for path in ['../outside', '/absolute']:
            with self.subTest(path=path):
                events = copy.deepcopy(original)
                live = events[1]
                live['files'] = {path: 'a' * 64}
                live['site_sha256'] = timing.sha(timing.canonical(live['files']))
                self.rewrite_chain(events)
                with self.assertRaisesRegex(ValueError, 'Invalid verified file'):
                    self.events()
        events = copy.deepcopy(original)
        events[1]['site_sha256'] = '0' * 64
        self.rewrite_chain(events)
        with self.assertRaisesRegex(ValueError, 'Invalid site fingerprint'):
            self.events()

    def test_elapsed_delay_uses_timezone_aware_seconds_not_calendar_days(self):
        self.baseline['updated'] = '2026-01-02T10:00:00+02:00'
        self.write_json(self.source['manifest'], self.baseline)
        self.write_json('site/' + self.source['manifest'], self.baseline)
        self.observe(live_url=self.live, get=self.get)
        row, = timing.report(self.events())['versions']
        self.assertEqual(row['publication_to_verified_live'],
                         dict(min_seconds=93600.0, max_seconds=93600.0))
        self.assertEqual(row['observation_evidence'], self.evidence)
        self.assertEqual(row['live_evidence'], self.evidence)

    def test_date_only_delay_bounds_include_uncertainty_and_zero_floor(self):
        for at, expected in [('2026-01-03T10:00:00Z', (36000, 122400)),
                             ('2026-01-02T10:00:00Z', (0, 36000))]:
            with self.subTest(at=at):
                version = timing.version(self.source['id'], dict(self.baseline, updated='2026-01-02'))
                events = [dict(kind='observed', version=version, at=at, evidence_url=self.evidence),
                          dict(kind='live', version=version, at=at, revision=self.revision,
                               evidence_url=self.evidence)]
                row, = timing.report(events)['versions']
                self.assertEqual(row['publication_to_verified_live'],
                                 dict(min_seconds=expected[0], max_seconds=expected[1]))

    def test_unknown_publication_is_not_substituted_with_original_date(self):
        for unknown in [None, 'not supplied by retained URL']:
            with self.subTest(unknown=unknown):
                v = timing.version(self.source['id'], dict(self.baseline, updated=unknown))
                self.assertIsNone(v['publication_at'])
                self.assertEqual(v['original_publication'], self.baseline['published'])
                events = [dict(kind='observed', version=v, at=self.at, evidence_url=self.evidence),
                          dict(kind='live', version=v, at=self.at, revision=self.revision,
                               evidence_url=self.evidence)]
                row, = timing.report(events)['versions']
                self.assertIsNone(row['publication_to_verified_live'])
                self.assertEqual(row['first_verified_live_at'], self.at)

    def test_roster_snapshot_as_of_is_vintage_not_publication(self):
        v = timing.version('invented-roster', dict(self.baseline, updated='2026-01-02',
                                                 as_of='2026-01-02'))
        self.assertEqual(v['vintage'], '2026-01-02')
        self.assertIsNone(v['publication_at'])
        row, = timing.report([
            dict(kind='observed', version=v, at=self.at, evidence_url=self.evidence),
            dict(kind='live', version=v, at=self.at, revision=self.revision,
                 evidence_url=self.evidence)])['versions']
        self.assertIsNone(row['publication_to_verified_live'])

    def test_malformed_publisher_dates_are_rejected_not_replaced_with_unknown(self):
        for value in ['2026-13-01', 'not a date', '2026-01-02T08:00:00']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                timing.version(self.source['id'], dict(self.baseline, updated=value))

    def test_report_does_not_award_history_or_rubric_level(self):
        self.assertEqual(timing.report([]), dict(schema_version=1, rubric_level_4_claimed=False,
                                                 versions=[], unavailable=[]))
        self.observe()
        report = timing.report(self.events())
        self.assertFalse(report['rubric_level_4_claimed'])
        row, = report['versions']
        for field in ['first_verified_live_at', 'deployed_revision',
                      'publication_to_verified_live', 'historical_first_live_at', 'live_evidence']:
            self.assertIsNone(row[field])

    def test_invalid_or_naive_timestamps_are_rejected(self):
        for value in ['2026-01-03', '2026-01-03T10:00:00', '2026-13-03T10:00:00Z', None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                timing.instant(value)
        self.assertEqual(timing.instant('2026-01-03T12:00:00+02:00'), timing.instant(self.at))

    def test_insecure_or_credential_evidence_urls_are_rejected(self):
        for address in ['http://ci.invalid/run', 'https://user:password@ci.invalid/run',
                        'https://ci.invalid/run#fragment', '/relative']:
            with self.subTest(address=address), self.assertRaises(ValueError):
                self.observe(evidence_url=address)
        self.assertFalse(self.ledger.exists())

    def test_default_fetch_refuses_redirect_to_another_host(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.url = 'https://other.invalid/index.html'
        response.read.return_value = b'invented response'
        with mock.patch.object(timing.urllib.request, 'urlopen', return_value=response):
            with self.assertRaisesRegex(ValueError, 'another host'):
                timing.verify_site(self.root / 'site', self.live)

    def test_cli_report_rejects_absent_ledger_without_network_or_false_evidence(self):
        with mock.patch.object(sys, 'argv', ['release_timing.py', 'report', '--ledger', str(self.ledger)]), \
                contextlib.redirect_stdout(io.StringIO()) as stdout, \
                contextlib.redirect_stderr(io.StringIO()) as stderr, \
                self.assertRaises(SystemExit) as raised:
            timing.main()
        self.assertEqual(raised.exception.code, 2)
        self.assertIn('Ledger does not exist', stderr.getvalue())
        self.assertEqual(stdout.getvalue(), '')
        self.assertFalse(self.ledger.exists())

    def test_cli_previous_ledger_accepts_unchanged_or_extended_prefix(self):
        self.observe()
        previous = self.root / 'previous.jsonl'
        previous.write_bytes(self.ledger.read_bytes())
        for extend in [False, True]:
            with self.subTest(extend=extend):
                if extend:
                    self.observe(live_url=self.live, get=self.get)
                with mock.patch.object(sys, 'argv', [
                        'release_timing.py', 'report', '--ledger', str(self.ledger),
                        '--previous-ledger', str(previous)]), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(timing.main(), 0)

    def test_cli_previous_ledger_rejects_truncation_or_rewritten_history(self):
        self.observe(live_url=self.live, get=self.get)
        previous = self.root / 'previous.jsonl'
        previous.write_bytes(self.ledger.read_bytes())
        original = self.events()
        for rewrite in [False, True]:
            with self.subTest(rewrite=rewrite):
                events = copy.deepcopy(original)
                if rewrite:
                    events[0]['evidence_url'] = 'https://ci.invalid/rewritten'
                else:
                    events = events[:1]
                self.rewrite_chain(events)
                with mock.patch.object(sys, 'argv', [
                        'release_timing.py', 'report', '--ledger', str(self.ledger),
                        '--previous-ledger', str(previous)]), \
                        contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                    timing.main()
                self.assertEqual(raised.exception.code, 2)

    def test_cli_refuses_revision_not_checked_out(self):
        with mock.patch.object(sys, 'argv', ['release_timing.py', 'observe', '--revision', 'b' * 40]), \
                mock.patch.object(timing.subprocess, 'check_output', return_value=self.revision), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            timing.main()
        self.assertEqual(raised.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
