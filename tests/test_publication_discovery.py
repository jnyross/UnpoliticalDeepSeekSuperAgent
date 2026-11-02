"""Network-free publication-listing coverage; no production issue writes."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from scripts import plan_discovery as plans

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('publication_discover', ROOT / 'scripts/discover.py')
discover = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discover)


class PublicationFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = dict(id='fixture-publication', allowed_hosts=['archive.example'],
            listing_allowed_hosts=['publisher.example'], listing_url='https://publisher.example/publications/',
            container_tag='div', container_class='publications',
            link_parent_tag='h2', link_parent_class='entry-title',
            link_path_pattern=r'/publications/[a-z-]+/', listing_scope='official-publication-listing-review')
        self.old = dict(url='https://publisher.example/publications/old/', title='Old paper')
        raw = plans.listing_bytes([self.old])
        (self.root / 'baseline.json').write_bytes(raw)
        self.source['listing_baseline'] = dict(file='baseline.json', sha256=plans._digest(raw))

    def page(self, slug='old', title='Old paper'):
        return (f'<div class="publications"><div><article><h2 class="entry-title">'
                f'<a href="/publications/{slug}/">{title}</a></h2>'
                f'<a href="/publications/{slug}/">READ MORE</a></article></div></div>').encode()

    def test_nested_class_container_and_heading_only_links(self):
        raw = b'<a href="/publications/outside/">Outside</a>' + self.page()
        self.assertEqual(plans.parse_listing(self.source, raw), [self.old])
        self.assertEqual(plans.discover_listing(self.source, self.root, lambda u: raw), [])

    def test_new_publication_repeated_stale_issue_list_writes_once(self):
        updates = plans.discover_listing(self.source, self.root, lambda u: self.page('new', 'New paper'))
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0]['evidence']['discovery_scope'], 'official-publication-listing-review')
        self.assertEqual(updates[0]['evidence']['updated'], 'not supplied by retained URL')
        writes = []
        def transport(*args):
            if args[0] == 'api': return '[[]]'
            writes.append(args)
            self.assertIn('NOT a revision of the retained historical source', args[-1])
            return 'https://github.com/fixture/repo/issues/1'
        path = self.root / 'receipts.json'
        self.assertEqual(discover.open_updates(updates, 'fixture/repo', transport, path)[0]['status'], 'opened')
        self.assertEqual(discover.open_updates(updates, 'fixture/repo', transport, path)[0]['status'], 'already reported')
        self.assertEqual(len(writes), 1)
        state = discover.reconcile_revision_status(dict(schema_version=1, notices=[]), [],
                    [dict(id=self.source['id'], updates=updates)], root=self.root)
        self.assertEqual(state['notices'], [])

    def test_missing_unclosed_duplicate_and_wrong_container_fail_closed(self):
        for raw in (b'<p>No collection</p>', self.page()[:-6], self.page() + self.page(),
                    self.page().replace(b'class="publications"', b'class="other"')):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                plans.parse_listing(self.source, raw)

    def test_host_rules_do_not_expand_historical_snapshot_hosts(self):
        self.assertEqual(self.source['allowed_hosts'], ['archive.example'])
        self.assertEqual(plans.parse_listing(self.source, self.page()), [self.old])
        for url in ('https://evil.example/publications/old/', 'http://publisher.example/publications/old/',
                    'https://publisher.example:8443/publications/old/'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                plans.parse_listing(self.source, self.page().replace(b'/publications/old/', url.encode()))

    def test_explicit_unavailable_title_label_for_image_document_links(self):
        source = copy.deepcopy(self.source)
        source.pop('link_parent_tag'); source.pop('link_parent_class')
        source['link_title_label'] = 'Policy document (publisher title not extracted)'
        raw = (b'<div class="publications"><a href="/publications/old/"><img src="x"></a>'
               b'<a href="/publications/old/">here</a></div>')
        self.assertEqual(plans.parse_listing(source, raw), [dict(self.old, title=source['link_title_label'])])
        source.pop('link_title_label')
        with self.assertRaisesRegex(ValueError, 'readable title'):
            plans.parse_listing(source, raw)

    def test_composite_checks_preserve_updates_when_other_lookup_fails(self):
        source = dict(self.source, adapter='retained-url-and-publication-listing')
        update = plans.discover_listing(self.source, self.root, lambda u: self.page('new', 'New paper'))[0]
        with mock.patch.object(discover, 'discover_snapshot', side_effect=OSError('archive unavailable')), \
             mock.patch.object(plans, 'discover_listing', return_value=[update]) as listing:
            with self.assertRaises(discover.PartialDiscoveryError) as caught:
                discover.discover(source, self.root)
            self.assertEqual(caught.exception.updates, [update])
            self.assertIn('retained-url: archive unavailable', str(caught.exception))
            listing.assert_called_once()
        with mock.patch.object(discover, 'discover_snapshot', return_value=[update]), \
             mock.patch.object(plans, 'discover_listing', side_effect=OSError('listing unavailable')):
            with self.assertRaises(discover.PartialDiscoveryError) as caught:
                discover.discover(source, self.root)
            self.assertEqual(caught.exception.updates, [update])

    def test_main_reports_partial_error_but_can_deliver_verified_candidate(self):
        source = dict(self.source, adapter='retained-url-and-publication-listing', manifest='missing.json')
        config = self.root / 'config/release-sources.json'
        config.parent.mkdir(); config.write_text(json.dumps([source]))
        report = self.root / 'report.json'
        updates = plans.discover_listing(self.source, self.root, lambda u: self.page('new', 'New paper'))
        partial = discover.PartialDiscoveryError(updates, [('retained-url', 'archive unavailable')])
        with mock.patch.object(discover, 'ROOT', self.root), \
             mock.patch.object(discover, 'discover', side_effect=partial), \
             mock.patch.object(discover, 'open_updates', return_value=[{'status': 'opened'}]) as deliver, \
             mock.patch('sys.argv', ['discover.py', '--open-issues', '--repo', 'fixture/repo', '--report', str(report)]), \
             mock.patch('sys.stdout'):
            self.assertEqual(discover.main(), 1)
        result = json.loads(report.read_text())
        self.assertEqual(result['sources'][0]['updates'], updates)
        self.assertIn('archive unavailable', result['errors'][0]['error'])
        self.assertEqual(result['sources'][0]['failed_checks'], [
            {'check': 'retained-url', 'error': 'archive unavailable'}])
        self.assertEqual(result['revision_status']['notices'], [])
        deliver.assert_called_once_with(updates, 'fixture/repo')

    def test_bad_settings_and_lookup_errors_fail_closed(self):
        for change in (dict(container_tag='img'), dict(container_class=''), dict(link_parent_tag='script'),
                       dict(listing_scope='unknown'), dict(section_id='also-an-id')):
            with self.subTest(change=change), self.assertRaises(ValueError):
                plans.parse_listing(dict(self.source, **change), self.page())
        with self.assertRaisesRegex(OSError, 'offline'):
            plans.discover_listing(self.source, self.root, mock.Mock(side_effect=OSError('offline')))


class RegisteredPublicationTests(unittest.TestCase):
    def test_retained_live_fragments_and_dispatch_match_baselines(self):
        paths = {
            'party-offers-dup': ('ni/dup-papers-fragment.html', 14),
            'party-offers-snp': ('gb/snp-manifesto-fragment.html.txt', 11),
            'party-evidence-rf-two-child-2024': ('evidence-listings/rf-social-security.fragment.html', 25)}
        inventory = json.loads((ROOT / 'config/release-sources.json').read_text())
        for source in inventory:
            if source['id'] not in paths: continue
            path, count = paths[source['id']]
            raw = (ROOT / 'docs/evidence/freshness-w8' / path).read_bytes()
            with self.subTest(source=source['id']):
                self.assertEqual(len(plans.parse_listing(source, raw)), count)
                self.assertEqual(plans.discover_listing(source, ROOT, lambda u: raw), [])
                with mock.patch.object(discover, 'discover_snapshot', return_value=[]) as historical:
                    self.assertEqual(discover.discover(source, ROOT, lambda u: raw), [])
                    historical.assert_called_once()
                self.assertEqual(source['allowed_hosts'], [discover.urlsplit(
                    discover.source_baseline(source, ROOT)['url']).hostname])
