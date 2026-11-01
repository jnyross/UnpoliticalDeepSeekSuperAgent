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


class InventoryTests(unittest.TestCase):
    def test_inventory_covers_every_source_manifest_consumed_by_site_data(self):
        inventory = json.loads((ROOT / 'config/release-sources.json').read_text())
        self.assertTrue(inventory)
        self.assertEqual(len({s['id'] for s in inventory}), len(inventory))
        manifests = []
        for entry in inventory:
            self.assertEqual(entry['adapter'], 'govuk-collection-attachment')
            manifest_path = ROOT / entry['manifest']
            self.assertTrue(manifest_path.is_file(), entry['manifest'])
            manifest = json.loads(manifest_path.read_text())
            self.assertRegex(manifest['release_url'].removeprefix('https://www.gov.uk'),
                             '^' + entry['release_path_pattern'] + '$')
            manifests.append(manifest)
        consumed = []

        def sources(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == 'source' and isinstance(child, dict) and 'release_url' in child:
                        consumed.append(child)
                    else:
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
