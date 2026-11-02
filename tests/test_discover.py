"""Network-free release discovery regression tests.

Run with: python3 -m unittest discover -s tests -p 'test_*.py' -v
All official responses, attachment bytes, and GitHub calls are fixtures.
"""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('release_discover', ROOT / 'scripts/discover.py')
discover = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discover)


class DiscoveryFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = {
            'id': 'fixture-spending',
            'adapter': 'govuk-collection-attachment',
            'manifest': 'sources/manifest.json',
            'collection_api': 'https://www.gov.uk/api/content/government/collections/fixture',
            'release_path_pattern': r'/government/statistics/public-spending-statistics-release-[a-z]+-[0-9]{4}',
            'attachment_title': 'Public sector spending',
        }
        self.path = '/government/statistics/public-spending-statistics-release-july-2026'
        self.meta_url = 'https://www.gov.uk/api/content' + self.path
        self.attachment = 'https://assets.publishing.service.gov.uk/media/fixture/spending.xlsx'
        self.raw = b'fixed workbook fixture bytes'
        self.baseline = {
            'release_url': 'https://www.gov.uk' + self.path,
            'published': '2026-07-16', 'date': '2026-07-29',
            'sha256': hashlib.sha256(self.raw).hexdigest(),
        }
        manifest = self.root / self.source['manifest']
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps(self.baseline))
        self.collection = {'links': {'documents': [self.document(self.path)]}}
        self.metadata = self.release_metadata()
        self.responses = {
            self.source['collection_api']: self.collection,
            self.meta_url: self.metadata,
            self.attachment: self.raw,
        }
        self.calls = []
        # Tripwire: even an accidental use of the real fetch cannot reach the network.
        self.network = mock.patch.object(discover.urllib.request.OpenerDirector, 'open',
                                         side_effect=AssertionError('Unexpected network request'))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.github = mock.patch.object(discover.subprocess, 'check_output',
                                        side_effect=AssertionError('Unexpected GitHub subprocess'))
        self.github.start()
        self.addCleanup(self.github.stop)

    def document(self, path, updated='2026-07-29T10:00:00Z'):
        return {'base_path': path, 'public_updated_at': updated}

    def release_metadata(self, published='2026-07-16', updated='2026-07-29'):
        return {'first_published_at': published + 'T09:00:00Z',
                'public_updated_at': updated + 'T10:00:00Z',
                'details': {'attachments': [
                    {'title': self.source['attachment_title'], 'url': self.attachment}]}}

    def get(self, url):
        self.calls.append(url)
        response = self.responses[url]  # Unexpected URLs fail rather than using the network.
        if isinstance(response, Exception):
            raise response
        return response if isinstance(response, bytes) else json.dumps(response).encode()

    def check(self):
        return discover.discover(self.source, root=self.root, get=self.get)

    def changed(self):
        self.responses[self.attachment] = b'revised workbook'
        return self.check()[0]

    def status(self, updates, state=None):
        return discover.reconcile_revision_status(
            state or {'schema_version': 1, 'notices': []}, [self.source],
            [dict(id=self.source['id'], updates=updates)], root=self.root,
            checked_at='2026-11-01T00:00:00+00:00')

    def test_revision_state_unchanged_has_no_notices(self):
        self.assertEqual(self.status(self.check()), dict(schema_version=1, notices=[]))

    def test_revision_state_persists_revised_hash_and_first_detection(self):
        update = self.changed()
        state = self.status([update])
        notice, = state['notices']
        self.assertEqual(notice['baseline_sha256'], self.baseline['sha256'])
        self.assertEqual(notice['baseline_url'], self.baseline['release_url'])
        self.assertEqual(notice['evidence'], update['evidence'])
        again = discover.reconcile_revision_status(state, [self.source],
                    [dict(id=self.source['id'], updates=[update])], root=self.root,
                    checked_at='2026-11-02T00:00:00+00:00')
        self.assertEqual(again, state)
        self.assertEqual(self.status([], state), state)  # Even a successful unchanged check.

    def test_revision_state_failed_lookup_preserves_notices_and_reports_failure(self):
        state = self.status([self.changed()])
        status = self.root / 'sources/revision-status.json'
        status.write_text(json.dumps(state))
        config = self.root / 'config/release-sources.json'
        config.parent.mkdir()
        config.write_text(json.dumps([self.source]))
        report = self.root / 'report.json'
        with mock.patch.object(discover, 'ROOT', self.root), \
             mock.patch.object(discover, 'discover', side_effect=OSError('offline')), \
             mock.patch('sys.argv', ['discover.py', '--write-revision-status', '--report', str(report)]), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(discover.main(), 1)
        self.assertEqual(json.loads(status.read_text()), state)
        result = json.loads(report.read_text())
        self.assertEqual(result['revision_status'], state)
        self.assertEqual(result['errors'], [dict(source=self.source['id'], error='offline')])

    def test_revision_state_only_matching_updated_hash_clears(self):
        update = self.changed()
        state = self.status([update])
        manifest = self.root / self.source['manifest']
        # Advancing to some other workbook must not dismiss the recorded revision.
        manifest.write_text(json.dumps(dict(self.baseline, sha256=discover.digest(b'other revision'))))
        self.assertEqual(self.status([], state), state)
        # Nor does an identical hash in a different publication establish incorporation.
        manifest.write_text(json.dumps(dict(self.baseline, sha256=update['evidence']['sha256'],
                                           release_url='https://www.gov.uk/other')))
        self.assertEqual(self.status([], state), state)
        manifest.write_text(json.dumps(dict(self.baseline, sha256=update['evidence']['sha256'])))
        self.assertEqual(self.status([], state)['notices'], [])
        self.assertEqual(len(state['notices']), 1)  # Pure reconciliation, no mutation.

    def test_revision_state_clears_only_matching_notice_not_other_revised_hashes(self):
        first = self.changed()
        self.responses[self.attachment] = b'further revision'
        second, = self.check()
        state = self.status([first, second])
        (self.root / self.source['manifest']).write_text(json.dumps(
            dict(self.baseline, sha256=first['evidence']['sha256'])))
        remaining = self.status([], state)['notices']
        self.assertEqual([n['key'] for n in remaining], [second['key']])

    def test_date_only_revision_requires_correct_updated_baseline(self):
        self.metadata['public_updated_at'] = '2026-08-02T08:00:00Z'
        state = self.status(self.check())
        self.assertEqual(len(state['notices']), 1)
        self.assertEqual(self.status([], state), state)
        (self.root / self.source['manifest']).write_text(json.dumps(
            dict(self.baseline, date='2026-08-02')))
        self.assertEqual(self.status([], state)['notices'], [])

    def test_main_persists_revised_notice_even_when_issue_creation_fails(self):
        config = self.root / 'config/release-sources.json'
        config.parent.mkdir()
        config.write_text(json.dumps([self.source]))
        status = self.root / 'sources/revision-status.json'
        report = self.root / 'report.json'
        update = self.changed()
        before = (self.root / self.source['manifest']).read_bytes()
        for failure in (False, True):
            with self.subTest(github_failure=failure), \
                 mock.patch.object(discover, 'ROOT', self.root), \
                 mock.patch.object(discover, 'discover', return_value=[update]), \
                 mock.patch.object(discover, 'open_updates', side_effect=OSError('GitHub offline') if failure else None,
                                   return_value=[]), \
                 mock.patch('sys.argv', ['discover.py', '--write-revision-status', '--open-issues',
                                         '--repo', 'owner/repo', '--report', str(report)]), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(discover.main(), int(failure))
            result = json.loads(report.read_text())
            self.assertEqual(json.loads(status.read_text()), result['revision_status'])
            self.assertEqual(result['revision_status']['notices'][0]['evidence'], update['evidence'])
            self.assertEqual((self.root / self.source['manifest']).read_bytes(), before)

    def test_revision_state_opt_in_and_malformed_state_preservation(self):
        config = self.root / 'config/release-sources.json'
        config.parent.mkdir()
        config.write_text(json.dumps([self.source]))
        status = self.root / 'sources/revision-status.json'
        report = self.root / 'report.json'
        update = self.changed()
        with mock.patch.object(discover, 'ROOT', self.root), \
             mock.patch.object(discover, 'discover', return_value=[update]), \
             mock.patch('sys.argv', ['discover.py', '--report', str(report)]), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(discover.main(), 0)
        self.assertFalse(status.exists())
        self.assertEqual(len(json.loads(report.read_text())['revision_status']['notices']), 1)
        status.write_text('{corrupt state')
        with mock.patch.object(discover, 'ROOT', self.root), \
             mock.patch.object(discover, 'discover', return_value=[update]), \
             mock.patch('sys.argv', ['discover.py', '--write-revision-status', '--report', str(report)]), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(discover.main(), 1)
        self.assertEqual(status.read_text(), '{corrupt state')
        self.assertEqual(json.loads(report.read_text())['errors'][0]['source'], 'revision-status')

    def test_versioned_attachment_title_pattern(self):
        self.source['attachment_title_pattern'] = r'PESA [0-9]{4} Chapter 4 Tables'
        self.metadata['details']['attachments'][0]['title'] = 'PESA 2027 Chapter 4 Tables'
        self.assertEqual(self.check(), [])
        self.metadata['details']['attachments'][0]['title'] = 'PESA 2027 Chapter 5 Tables'
        with self.assertRaises(ValueError):
            self.check()
        self.metadata['details']['attachments'] = [
            {'title': 'PESA 2027 Chapter 4 Tables', 'url': self.attachment},
            {'title': 'PESA 2028 Chapter 4 Tables', 'url': self.attachment}]
        with self.assertRaises(ValueError):
            self.check()

    def test_redirect_handler_rejects_external_hosts_before_following(self):
        handler = discover.OfficialRedirect()
        request = discover.urllib.request.Request(self.meta_url)
        for url in ('https://example.org/data', 'https://www.gov.uk.evil.example/data',
                    'http://www.gov.uk/data'):
            with self.subTest(url=url), \
                 mock.patch.object(discover.urllib.request.HTTPRedirectHandler, 'redirect_request') as follow:
                with self.assertRaisesRegex(ValueError, 'Redirected outside official hosts'):
                    handler.redirect_request(request, None, 302, 'Found', {}, url)
                follow.assert_not_called()

    def test_redirect_handler_permits_official_hosts(self):
        handler = discover.OfficialRedirect()
        request = discover.urllib.request.Request(self.meta_url)
        for url in ('https://www.gov.uk/government/statistics/fixture', self.attachment):
            with self.subTest(url=url):
                redirected = handler.redirect_request(request, None, 302, 'Found', {}, url)
                self.assertEqual(redirected.full_url, url)

    def test_unchanged_release_has_no_updates_and_does_not_write_baseline(self):
        before = (self.root / self.source['manifest']).read_bytes()
        self.assertEqual(self.check(), [])
        self.assertEqual(self.calls, [self.source['collection_api'], self.meta_url, self.attachment])
        self.assertEqual((self.root / self.source['manifest']).read_bytes(), before)

    def test_new_release_is_discovered_with_complete_stable_evidence(self):
        path = '/government/statistics/public-spending-statistics-release-november-2026'
        meta_url = 'https://www.gov.uk/api/content' + path
        attachment = 'https://assets.publishing.service.gov.uk/media/fixture/new.xlsx'
        metadata = self.release_metadata('2026-11-01', '2026-11-02')
        metadata['details']['attachments'][0]['url'] = attachment
        self.collection['links']['documents'].extend([
            self.document(path, '2026-11-02T12:00:00Z'),
            self.document(path, '2026-11-02T12:00:00Z'),  # Duplicate collection link.
            self.document('/government/statistics/unrelated', '2026-11-02T12:00:00Z'),
        ])
        self.responses.update({meta_url: metadata, attachment: b'new workbook'})
        updates = self.check()
        self.assertEqual(len(updates), 1)
        update = updates[0]
        evidence = {'source': self.source['id'], 'release_url': 'https://www.gov.uk' + path,
                    'published': '2026-11-01', 'updated': '2026-11-02',
                    'attachment_url': attachment, 'sha256': hashlib.sha256(b'new workbook').hexdigest(),
                    'metadata_url': meta_url, 'collection_url': self.source['collection_api']}
        self.assertEqual(update['evidence'], evidence)
        self.assertEqual(update['baseline'], self.baseline)
        self.assertEqual(update['key'], hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest())
        self.assertEqual(self.calls.count(meta_url), 1)
        self.assertEqual(self.check(), updates)

    def test_hash_only_revision(self):
        update = self.changed()
        self.assertEqual(update['evidence']['updated'], self.baseline['date'])
        self.assertNotEqual(update['evidence']['sha256'], self.baseline['sha256'])

    def test_date_only_revision(self):
        self.metadata['public_updated_at'] = '2026-08-02T08:00:00Z'
        update, = self.check()
        self.assertEqual(update['evidence']['sha256'], self.baseline['sha256'])
        self.assertEqual(update['evidence']['updated'], '2026-08-02')

    def test_retained_release_checked_even_when_not_linked_in_collection(self):
        newer = '/government/statistics/public-spending-statistics-release-november-2026'
        self.collection['links']['documents'] = [self.document(newer, '2026-11-01T00:00:00Z')]
        # A release with a recent edit but older original publication is not a new release.
        self.responses['https://www.gov.uk/api/content' + newer] = self.release_metadata('2025-11-01')
        update = self.changed()
        self.assertEqual(update['evidence']['release_url'], self.baseline['release_url'])

    def test_older_and_unrelated_collection_documents_are_not_fetched(self):
        self.collection['links']['documents'].extend([
            self.document('/government/statistics/public-spending-statistics-release-june-2026', '2026-06-01'),
            self.document('/government/statistics/unrelated', '2026-12-01'),
        ])
        self.assertEqual(self.check(), [])
        self.assertEqual(len(self.calls), 3)

    def test_failed_fetch_at_every_stage_is_not_an_unchanged_result(self):
        for url in (self.source['collection_api'], self.meta_url, self.attachment):
            with self.subTest(url=url):
                original = self.responses[url]
                self.responses[url] = OSError('fixture fetch failed')
                with self.assertRaisesRegex(OSError, 'fixture fetch failed'):
                    self.check()
                self.responses[url] = original

    def test_invalid_json_and_changed_schema_fail_closed(self):
        cases = [
            (self.source['collection_api'], b'not json', ValueError),
            (self.source['collection_api'], {}, KeyError),
            (self.source['collection_api'], {'links': {'documents': []}}, ValueError),
            (self.source['collection_api'], {'links': {'documents': [self.document('/unrelated')]}}, ValueError),
            (self.meta_url, {}, KeyError),
            (self.meta_url, b'not json', ValueError),
        ]
        for url, value, error in cases:
            with self.subTest(url=url, value=value):
                original = self.responses[url]
                self.responses[url] = value
                with self.assertRaises(error):
                    self.check()
                self.responses[url] = original

    def test_missing_wrong_title_and_ambiguous_attachment_fail_closed(self):
        attachment = copy.deepcopy(self.metadata['details']['attachments'][0])
        for attachments in ([], [dict(attachment, title='Other table')], [attachment, attachment]):
            with self.subTest(attachments=attachments):
                self.metadata['details']['attachments'] = attachments
                with self.assertRaisesRegex(ValueError, 'Expected exactly one data attachment'):
                    self.check()
                self.assertNotIn(self.attachment, self.calls)

    def test_open_and_closed_issue_markers_on_later_pages_deduplicate(self):
        update = self.changed()
        marker = '<!-- source-release:' + update['key'] + ' -->'
        for state in ('open', 'closed'):
            with self.subTest(state=state):
                run = mock.Mock(return_value=json.dumps([
                    [{'body': 'unrelated issue', 'state': 'open'}],
                    [{'body': marker, 'state': state}],
                ]))
                self.assertEqual(discover.open_updates([update], 'owner/repo', run=run),
                                 [{'key': update['key'], 'status': 'already reported'}])
                run.assert_called_once_with('api', '--paginate', '--slurp',
                                            'repos/owner/repo/issues?state=all&per_page=100')

    def test_repeated_discovery_creates_once_and_retains_machine_marker(self):
        update = self.changed()
        issues = []
        calls = []

        def run(*args):
            calls.append(args)
            if args[0] == 'api':
                return json.dumps([copy.deepcopy(issues)])
            self.assertEqual(args[:4], ('issue', 'create', '--repo', 'owner/repo'))
            body = args[args.index('--body') + 1]
            self.assertIn(discover.NOTICE, body)
            self.assertIn('Deployed data have NOT changed', body)
            self.assertIn('<!-- source-release:' + update['key'] + ' -->', body)
            self.assertIn(update['evidence']['sha256'], body)
            issues.append({'body': body, 'state': 'open'})
            return 'https://github.com/owner/repo/issues/1'

        first = discover.open_updates([update, update], 'owner/repo', run=run)
        self.assertEqual([r['status'] for r in first], ['opened', 'already reported'])
        self.assertEqual(first[0]['url'], 'https://github.com/owner/repo/issues/1')
        second = discover.open_updates(self.check(), 'owner/repo', run=run)
        self.assertEqual([r['status'] for r in second], ['already reported'])
        self.assertEqual(sum(c[0] == 'issue' for c in calls), 1)

    def test_pull_request_marker_does_not_suppress_issue(self):
        update = self.changed()
        run = mock.Mock(side_effect=[json.dumps([[{'body': '<!-- source-release:' + update['key'] + ' -->',
                                                   'pull_request': {}}]]), 'https://github.com/owner/repo/issues/2'])
        self.assertEqual(discover.open_updates([update], 'owner/repo', run=run)[0]['status'], 'opened')
        self.assertEqual(run.call_count, 2)

    def test_main_issue_list_or_creation_failure_returns_nonzero_without_changing_baseline(self):
        config = self.root / 'config/release-sources.json'
        config.parent.mkdir()
        config.write_text(json.dumps([self.source]))
        report = self.root / 'report.json'
        before = (self.root / self.source['manifest']).read_bytes()
        update = self.changed()
        for operation in ('issue listing', 'issue creation'):
            with self.subTest(operation=operation), \
                 mock.patch.object(discover, 'ROOT', self.root), \
                 mock.patch.object(discover, 'discover', return_value=[update]), \
                 mock.patch.object(discover, 'open_updates', side_effect=RuntimeError(operation + ' failed')) as open_updates, \
                 mock.patch('sys.argv', ['discover.py', '--open-issues', '--repo', 'owner/repo', '--report', str(report)]), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(discover.main(), 1)
                open_updates.assert_called_once_with([update], 'owner/repo')
                result = json.loads(report.read_text())
                self.assertEqual(result['errors'], [{'source': self.source['id'], 'error': operation + ' failed'}])
                self.assertEqual(result['sources'][0]['id'], self.source['id'])
                self.assertEqual(result['sources'][0]['updates'], [update])
                self.assertEqual((self.root / self.source['manifest']).read_bytes(), before)

    def test_main_missing_malformed_or_empty_inventory_writes_error_report(self):
        cases = {'missing': None, 'malformed': '{', 'empty': '[]'}
        for name, content in cases.items():
            with self.subTest(inventory=name):
                root = self.root / name
                root.mkdir()
                if content is not None:
                    config = root / 'config/release-sources.json'
                    config.parent.mkdir()
                    config.write_text(content)
                report = root / 'report.json'
                with mock.patch.object(discover, 'ROOT', root), \
                     mock.patch.object(discover, 'discover', side_effect=AssertionError('Invalid inventory must not discover')) as check, \
                     mock.patch('sys.argv', ['discover.py', '--report', str(report)]), \
                     contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(discover.main(), 1)
                    check.assert_not_called()
                result = json.loads(report.read_text())
                self.assertEqual(result['sources'], [])
                self.assertTrue(result['errors'])
                self.assertTrue(result['errors'][0]['error'])

    def test_main_reports_fetch_and_schema_errors_and_returns_nonzero(self):
        config = self.root / 'config/release-sources.json'
        config.parent.mkdir()
        config.write_text(json.dumps([self.source]))
        report = self.root / 'report.json'
        real_discover = discover.discover
        for failure in (OSError('fixture offline'), b'{', {}):
            with self.subTest(failure=failure):
                self.responses[self.source['collection_api']] = failure
                with mock.patch.object(discover, 'ROOT', self.root), \
                     mock.patch.object(discover, 'discover', side_effect=lambda s: real_discover(s, self.root, self.get)), \
                     mock.patch.object(discover, 'gh', side_effect=AssertionError('Unexpected GitHub call')), \
                     mock.patch('sys.argv', ['discover.py', '--report', str(report)]), \
                     contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(discover.main(), 1)
                result = json.loads(report.read_text())
                self.assertEqual(result['sources'], [])
                self.assertEqual(len(result['errors']), 1)
                self.assertEqual(result['errors'][0]['source'], self.source['id'])
                self.assertTrue(result['errors'][0]['error'])


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = dict(id='party-roster', adapter='retained-url-snapshot',
                           manifest='party-offers.json', selector='roster',
                           allowed_hosts=['members-api.parliament.uk'],
                           normalization='parliament-party-roster')
        self.url = 'https://members-api.parliament.uk/api/Parties/StateOfTheParties/1/2024-07-09'
        self.roster = {'items': [self.row(15, 'Labour', 411), self.row(4, 'Conservative', 121)],
                       'timestamp': '2026-01-01', 'links': []}
        self.raw = json.dumps(self.roster).encode()
        self.baseline = dict(url=self.url, file='roster.json', sha256=discover.digest(self.raw),
                             downloaded='2026-01-01')
        (self.root / 'roster.json').write_bytes(self.raw)
        self.save_manifest()
        self.network = mock.patch.object(discover.urllib.request.OpenerDirector, 'open',
                                         side_effect=AssertionError('Unexpected network request'))
        self.network.start()
        self.addCleanup(self.network.stop)

    def row(self, identifier, name, total):
        return {'value': {'party': {'id': identifier, 'name': name,
                                    'isIndependentParty': False, 'backgroundColour': 'ff0000'},
                          'total': total}, 'links': []}

    def save_manifest(self):
        (self.root / 'party-offers.json').write_text(json.dumps({'roster': self.baseline}))

    def check(self, raw=None):
        get = mock.Mock(return_value=self.raw if raw is None else raw)
        result = discover.discover(self.source, root=self.root, get=get)
        get.assert_called_once_with(self.url)
        return result

    def test_semantically_unchanged_roster_ignores_time_order_links_and_presentation(self):
        before = (self.root / 'party-offers.json').read_bytes()
        changed = copy.deepcopy(self.roster)
        changed['timestamp'] = '2026-02-01'
        changed['items'].reverse()
        changed['items'][0]['value']['party']['backgroundColour'] = '000000'
        changed['links'] = [{'rel': 'self', 'href': 'changed metadata'}]
        self.assertEqual(self.check(json.dumps(changed).encode()), [])
        self.assertEqual((self.root / 'party-offers.json').read_bytes(), before)

    def test_roster_identity_membership_and_seat_changes_are_detected(self):
        for mutate in (lambda r: r['items'].append(self.row(44, 'Green Party', 4)),
                       lambda r: r['items'].pop(),
                       lambda r: r['items'][0]['value'].update(total=412),
                       lambda r: r['items'][0]['value']['party'].update(name='Renamed'),
                       lambda r: r['items'][0]['value']['party'].update(isIndependentParty=True)):
            changed = copy.deepcopy(self.roster)
            mutate(changed)
            update, = self.check(json.dumps(changed).encode())
            self.assertEqual(update['evidence']['discovery_scope'], 'retained-url-revision')
            self.assertIn('semantic_sha256', update['evidence'])
            # API timestamp changes do not generate a different deduplication key.
            changed['timestamp'] = '2027-01-01'
            again, = self.check(json.dumps(changed).encode())
            self.assertEqual(update['key'], again['key'])

    def test_invalid_roster_and_changed_schema_fail_closed(self):
        for value in ({}, {'items': []}, {'items': [self.row(1, 'A', 2)] * 2},
                      {'items': [self.row(1, 'A', -1)]}, {'items': [{'value': {}}]}):
            with self.subTest(value=value), self.assertRaises((ValueError, KeyError)):
                self.check(json.dumps(value).encode())
        with self.assertRaises(ValueError):
            self.check(b'not json')
        (self.root / 'roster.json').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'manifest hash'):
            self.check()

    def test_generic_plan_hash_revisions_and_source_selector(self):
        self.source.pop('selector')
        self.source.pop('normalization')
        self.source['source_id'] = 'plan'
        (self.root / 'party-offers.json').write_text(json.dumps({'sources': [dict(self.baseline, id='plan')]}))
        self.assertEqual(self.check(), [])
        update, = self.check(b'revised PDF bytes')
        self.assertEqual(update['evidence']['sha256'], discover.digest(b'revised PDF bytes'))
        self.assertNotIn('semantic_sha256', update['evidence'])
        self.assertEqual(self.check(b'revised PDF bytes'), [update])
        run = mock.Mock(side_effect=['[[]]', 'https://github.com/owner/repo/issues/1'])
        discover.open_updates([update], 'owner/repo', run=run)
        body = run.call_args.args[run.call_args.args.index('--body') + 1]
        self.assertIn('does not discover new', body)
        self.assertNotIn('--release', body)
        for sources in ([], [dict(self.baseline, id='plan')] * 2):
            (self.root / 'party-offers.json').write_text(json.dumps({'sources': sources}))
            with self.assertRaisesRegex(ValueError, 'exactly one source'):
                self.check()

    def test_independent_evidence_collection_reuses_snapshot_safety(self):
        self.source.pop('selector')
        self.source.pop('normalization')
        self.source.update(source_id='analysis', source_collection='evidence_sources')
        (self.root / 'party-offers.json').write_text(json.dumps({
            'sources': [], 'evidence_sources': [dict(self.baseline, id='analysis')]}))
        self.assertEqual(self.check(), [])
        update, = self.check(b'revised independent HTML')
        self.assertEqual(update['evidence']['sha256'], discover.digest(b'revised independent HTML'))
        self.assertEqual(self.check(b'revised independent HTML'), [update])
        self.source['source_collection'] = 'unknown'
        with self.assertRaisesRegex(ValueError, 'Unknown source collection'):
            self.check()

    def test_snapshot_source_hosts_are_exact_https_and_checked_before_fetch(self):
        for url in ('https://members-api.parliament.uk.evil.example/data',
                    'https://example.org/data', 'http://members-api.parliament.uk/data',
                    'https://user@members-api.parliament.uk/data',
                    'https://members-api.parliament.uk:8080/data'):
            self.baseline['url'] = url
            self.save_manifest()
            get = mock.Mock()
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, 'official URL'):
                discover.discover(self.source, root=self.root, get=get)
            get.assert_not_called()
        handler = discover.OfficialRedirect(self.source['allowed_hosts'])
        request = discover.urllib.request.Request(self.url)
        with self.assertRaisesRegex(ValueError, 'Redirected outside official hosts'):
            handler.redirect_request(request, None, 302, 'Found', {}, 'https://www.gov.uk/data')
        self.assertEqual(handler.redirect_request(request, None, 302, 'Found', {}, self.url).full_url, self.url)

    def test_fetch_checks_inventory_hosts_at_initial_redirect_and_final_response(self):
        hosts = self.source['allowed_hosts']
        with mock.patch.object(discover.urllib.request, 'build_opener') as build:
            with self.assertRaisesRegex(ValueError, 'official URL'):
                discover.fetch('https://example.org/data', hosts=hosts)
            build.assert_not_called()
            response = mock.MagicMock()
            response.__enter__.return_value = response
            response.url = 'https://example.org/redirected'
            build.return_value.open.return_value = response
            with self.assertRaisesRegex(ValueError, 'Redirected outside official hosts'):
                discover.fetch(self.url, hosts=hosts)
            response.read.assert_not_called()
            response.url = self.url
            response.read.return_value = self.raw
            self.assertEqual(discover.fetch(self.url, hosts=hosts), self.raw)

    def test_main_dispatches_snapshot_adapter_and_reports_limited_scope(self):
        config = self.root / 'config/release-sources.json'
        config.parent.mkdir()
        config.write_text(json.dumps([self.source]))
        report = self.root / 'report.json'
        real_discover = discover.discover
        with mock.patch.object(discover, 'ROOT', self.root), \
             mock.patch.object(discover, 'discover', side_effect=lambda s: real_discover(s, self.root, lambda u: self.raw)), \
             mock.patch('sys.argv', ['discover.py', '--report', str(report)]), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(discover.main(), 0)
        result = json.loads(report.read_text())
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['sources'], [dict(id=self.source['id'], updates=[], issues=[],
                                                  discovery_scope='retained-url-revision')])

    def test_snapshot_fetch_failures_propagate(self):
        with self.assertRaisesRegex(OSError, 'offline'):
            discover.discover(self.source, root=self.root, get=mock.Mock(side_effect=OSError('offline')))


class OBRDatabankTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = dict(id='obr-databank', adapter='obr-databank-latest',
                           manifest='income.json', page_url='https://obr.uk/data/',
                           download_path_pattern=r'/download/public-finances-databank-[a-z0-9-]+/')
        self.download = 'https://obr.uk/download/public-finances-databank-october-2026-efo/'
        self.raw = b'workbook fixture'
        self.baseline = dict(url='https://obr.uk/docs/retained.xlsx', download_url=self.download,
                             release_url=self.source['page_url'], published='2026-10-28',
                             date='2026-10-28', sha256=discover.digest(self.raw))
        (self.root / 'income.json').write_text(json.dumps(self.baseline))
        self.responses = {self.source['page_url']: self.page(), self.download: self.raw,
                          self.baseline['url']: self.raw}
        self.calls = []
        patch = mock.patch.object(discover.urllib.request.OpenerDirector, 'open',
                                  side_effect=AssertionError('Unexpected network request'))
        patch.start()
        self.addCleanup(patch.stop)

    def page(self, url=None, date='28 October 2026', stamp='123'):
        url = url or self.download
        # Real OBR layout has duplicate icon/title anchors and a cachebuster.
        return (f'<a href="{url}?tmstv={stamp}">xlsx</a>'
                f'<a href="{url}?tmstv={stamp}">Public finances databank</a>'
                f'<p>{date} &ndash; 385 KB</p>'
                '<a href="/download/unrelated/">Unrelated</a> 30 October 2026').encode()

    def get(self, url):
        self.calls.append(url)
        value = self.responses[url]
        if isinstance(value, Exception):
            raise value
        return value

    def check(self):
        return discover.discover(self.source, self.root, self.get)

    def test_unchanged_and_cachebuster_do_not_change_baseline(self):
        before = (self.root / 'income.json').read_bytes()
        self.assertEqual(self.check(), [])
        self.responses[self.source['page_url']] = self.page(stamp='999999')
        self.assertEqual(self.check(), [])
        self.assertEqual((self.root / 'income.json').read_bytes(), before)

    def test_new_release_follows_latest_page_and_checks_retained_revision(self):
        new = self.download.replace('october', 'november')
        self.responses[self.source['page_url']] = self.page(new, '25 November 2026')
        self.responses[new] = b'new release'
        update, = self.check()
        self.assertEqual(update['evidence']['download_url'], new)
        self.assertEqual(update['evidence']['published'], '2026-11-25')
        self.assertEqual(update['evidence']['sha256'], discover.digest(b'new release'))
        self.assertIn(self.baseline['url'], self.calls)
        self.responses[self.baseline['url']] = b'revised old workbook'
        updates = self.check()
        self.assertEqual(len(updates), 2)
        self.assertEqual(updates[1]['evidence']['published'], self.baseline['published'])
        self.assertEqual(self.check(), updates)

    def test_hash_only_and_date_only_revisions(self):
        self.responses[self.download] = b'revised'
        update, = self.check()
        self.assertEqual(update['evidence']['updated'], self.baseline['date'])
        self.responses[self.download] = self.raw
        self.responses[self.source['page_url']] = self.page(date='29 October 2026')
        update, = self.check()
        self.assertEqual(update['evidence']['updated'], '2026-10-29')
        self.assertEqual(update['evidence']['sha256'], self.baseline['sha256'])

    def test_repeated_discovery_deduplicates_issues_and_uses_refresh_command(self):
        self.responses[self.download] = b'revised'
        update, = self.check()
        run = mock.Mock(side_effect=['[[]]', 'https://github.com/o/r/issues/1'])
        discover.open_updates([update], 'o/r', run=run)
        body = run.call_args.args[run.call_args.args.index('--body') + 1]
        self.assertIn('latest databank page', body)
        self.assertIn('python3 scripts/build.py --refresh', body)
        self.assertNotIn('--release', body)
        run = mock.Mock(return_value=json.dumps([[{'body': body, 'state': 'closed'}]]))
        self.assertEqual(discover.open_updates(self.check(), 'o/r', run=run)[0]['status'],
                         'already reported')
        self.assertEqual(run.call_count, 1)

    def test_missing_ambiguous_invalid_dates_and_external_links_fail_closed(self):
        pages = [b'<p>no databank</p>', self.page() + self.page(self.download.replace('october', 'november')),
                 self.page(date='no date'), self.page(date='32 October 2026'),
                 self.page(url=self.download.replace('obr.uk', 'evil.example'))]
        for page in pages:
            with self.subTest(page=page), self.assertRaises(ValueError):
                self.responses[self.source['page_url']] = page
                self.check()

    def test_page_workbook_and_retained_fetch_errors_propagate(self):
        for url in (self.source['page_url'], self.download):
            original = self.responses[url]
            self.responses[url] = OSError('offline')
            with self.subTest(url=url), self.assertRaisesRegex(OSError, 'offline'):
                self.check()
            self.responses[url] = original
        new = self.download.replace('october', 'november')
        self.responses[self.source['page_url']] = self.page(new, '25 November 2026')
        self.responses[new] = b'new'
        self.responses[self.baseline['url']] = OSError('retained offline')
        with self.assertRaisesRegex(OSError, 'retained offline'):
            self.check()

    def test_main_reports_obr_scope_and_fails_on_page_or_download_errors(self):
        config = self.root / 'config/release-sources.json'
        config.parent.mkdir()
        config.write_text(json.dumps([self.source]))
        report = self.root / 'report.json'
        real_discover = discover.discover
        for failure in (None, OSError('offline'), b'<p>changed schema</p>'):
            self.responses[self.source['page_url']] = self.page() if failure is None else failure
            with mock.patch.object(discover, 'ROOT', self.root), \
                 mock.patch.object(discover, 'discover', side_effect=lambda s: real_discover(s, self.root, self.get)), \
                 mock.patch('sys.argv', ['discover.py', '--report', str(report)]), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(discover.main(), 0 if failure is None else 1)
            result = json.loads(report.read_text())
            if failure is None:
                self.assertEqual(result['sources'], [dict(id=self.source['id'], updates=[], issues=[],
                                      discovery_scope='latest-page-releases-and-revisions')])
                self.assertEqual(result['errors'], [])
            else:
                self.assertEqual(result['sources'], [])
                self.assertEqual(result['errors'][0]['source'], self.source['id'])
                self.assertTrue(result['errors'][0]['error'])

    def test_official_redirects_allow_only_obr_https_hosts(self):
        handler = discover.OfficialRedirect(('obr.uk', 'www.obr.uk'))
        request = discover.urllib.request.Request(self.download)
        for url in ('https://evil.example/a', 'https://obr.uk.evil.example/a', 'http://obr.uk/a'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                handler.redirect_request(request, None, 302, 'Found', {}, url)
        self.assertEqual(handler.redirect_request(request, None, 302, 'Found', {},
                                                 self.baseline['url']).full_url, self.baseline['url'])


class InventoryTests(unittest.TestCase):
    def test_every_retained_party_source_and_roster_is_registered_once(self):
        inventory = json.loads((ROOT / 'config/release-sources.json').read_text())
        manifest_path = 'sources/party-offers.json'
        retained = json.loads((ROOT / manifest_path).read_text())
        entries = [s for s in inventory if s['manifest'] == manifest_path]
        rosters = [s for s in entries if s.get('selector') == 'roster']
        self.assertEqual(len(rosters), 1)
        self.assertEqual(rosters[0]['normalization'], 'parliament-party-roster')
        plans = [s for s in entries if 'source_id' in s]
        expected = [(collection, s['id']) for collection in ('sources', 'evidence_sources')
                    for s in retained.get(collection, [])]
        self.assertCountEqual([(s.get('source_collection', 'sources'), s['source_id']) for s in plans], expected)
        self.assertEqual(len(entries), len(expected) + 1)
        for entry in entries:
            self.assertEqual(entry['adapter'], 'retained-url-snapshot')
            baseline = discover.source_baseline(entry, ROOT)
            # Exact inventory hosts are intentionally not a wildcard or all-party allowlist.
            self.assertEqual(entry['allowed_hosts'], [discover.urlsplit(baseline['url']).hostname])

    def test_inventory_covers_every_source_manifest_consumed_by_site_data(self):
        inventory = json.loads((ROOT / 'config/release-sources.json').read_text())
        self.assertTrue(inventory)
        self.assertEqual(len({s['id'] for s in inventory}), len(inventory))
        manifests = []
        for entry in inventory:
            manifest_path = ROOT / entry['manifest']
            self.assertTrue(manifest_path.is_file(), entry['manifest'])
            manifest = discover.source_baseline(entry, ROOT)
            if entry['adapter'] == 'govuk-collection-attachment':
                self.assertRegex(manifest['release_url'].removeprefix('https://www.gov.uk'),
                                 '^' + entry['release_path_pattern'] + '$')
            elif entry['adapter'] == 'obr-databank-latest':
                self.assertEqual(manifest['release_url'], entry['page_url'])
                self.assertTrue(discover.allowed_url(manifest['url'], ('obr.uk', 'www.obr.uk')))
                self.assertRegex(discover.urlsplit(manifest['download_url']).path,
                                 '^' + entry['download_path_pattern'] + '$')
                self.assertRegex(manifest['sha256'], r'^[0-9a-f]{64}$')
            else:
                self.assertEqual(entry['adapter'], 'retained-url-snapshot')
                self.assertTrue(discover.allowed_url(manifest['url'], entry['allowed_hosts']))
                self.assertRegex(manifest['sha256'], r'^[0-9a-f]{64}$')
            manifests.append(manifest)
        consumed = []

        def sources(value):
            if isinstance(value, dict):
                if 'sha256' in value and ('release_url' in value or 'url' in value):
                    if value not in consumed:
                        consumed.append(value)
                else:
                    for child in value.values():
                        sources(child)
            elif isinstance(value, list):
                for child in value:
                    sources(child)

        data_files = list((ROOT / 'site/data').rglob('*.json'))
        self.assertTrue(data_files)
        for path in data_files:
            sources(json.loads(path.read_text()))
        self.assertTrue(consumed, 'No consumed source manifests found in site/data JSON')
        for manifest in consumed:
            self.assertIn(manifest, manifests, 'A site/data source manifest is missing from the discovery inventory')
        for manifest in manifests:
            self.assertIn(manifest, consumed, 'Inventory manifest is not consumed by site/data')


if __name__ == '__main__':
    unittest.main()
