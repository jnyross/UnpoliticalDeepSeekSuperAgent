"""Network-free semantic policy-listing discovery tests; fixture responses only."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import discover
import plan_discovery as plans


class PolicyListingFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = dict(id='fixture-libdem', listing_url='https://www.libdems.org.uk/members/make-policy',
                           allowed_hosts=['www.libdems.org.uk'], section_id='policy-papers',
                           section_end_id='register-for-conference',
                           link_path_pattern=r'/conference/papers/[a-z0-9/-]+')
        self.old = dict(url='https://www.libdems.org.uk/conference/papers/autumn-2026/old',
                        title='166 - Existing policy (2026)')
        self.new = dict(url='https://www.libdems.org.uk/conference/papers/autumn-2026/new',
                        title='167 - New policy (2026)')
        self.raw = plans.listing_bytes([self.old])
        (self.root / 'baseline.json').write_bytes(self.raw)
        self.source['listing_baseline'] = dict(file='baseline.json', sha256=hashlib.sha256(self.raw).hexdigest())
        self.net = mock.patch.object(discover.urllib.request.OpenerDirector, 'open',
                                     side_effect=AssertionError('Unexpected network'))
        self.net.start()
        self.addCleanup(self.net.stop)

    def anchor(self, link):
        return '<p><a href="' + link['url'] + '">' + link['title'] + '</a></p>'

    def page(self, links, before='', after=''):
        return (before + '<div id="policy-papers"></div><h2>Policy Papers</h2>' +
                ''.join(self.anchor(link) for link in links) +
                '<div id="register-for-conference"></div>' + after).encode()

    def run_page(self, raw):
        get = mock.Mock(return_value=raw)
        result = plans.discover_listing(self.source, self.root, get=get)
        get.assert_called_once_with(self.source['listing_url'])
        return result

    def test_unchanged_listing_has_no_candidates(self):
        self.assertEqual(self.run_page(self.page([self.old])), [])

    def test_new_link_is_review_only_not_historical_revision(self):
        result = self.run_page(self.page([self.old, self.new]))
        self.assertEqual(len(result), 1)
        evidence = result[0]['evidence']
        self.assertEqual(evidence['release_url'], self.new['url'])
        self.assertEqual(evidence['change'], 'new-link')
        self.assertEqual(evidence['discovery_scope'], 'official-policy-listing-review')
        self.assertTrue(evidence['review_only'])
        self.assertIn('not a revision', evidence['review_note'])
        self.assertEqual(evidence['updated'], 'not supplied by retained URL')
        self.assertEqual((self.root / 'baseline.json').read_bytes(), self.raw)

    def test_repeated_poll_and_closed_issue_are_deduplicated(self):
        first = self.run_page(self.page([self.old, self.new]))
        repeated = self.run_page(self.page([self.new, self.old, self.new], before='timestamp changed'))
        self.assertEqual(first[0]['key'], repeated[0]['key'])
        self.assertEqual(first[0]['evidence']['listing_sha256'], repeated[0]['evidence']['listing_sha256'])
        github = mock.Mock(return_value=json.dumps([[dict(state='closed', body='<!-- source-release:' + first[0]['key'] + ' -->')]]))
        self.assertEqual(discover.open_updates(repeated, 'owner/repo', run=github, receipt_path=self.root / 'receipts.json')[0]['status'], 'already reported')
        self.assertEqual(github.call_count, 1)

    def test_relative_links_tracking_html_and_whitespace_are_semantically_unchanged(self):
        page = self.page([self.old]).decode().replace(self.old['url'], '/conference/papers/autumn-2026/old?utm_source=x#top')
        page = page.replace(self.old['title'], '166 - <strong>Existing policy</strong>\n (2026)')
        self.assertEqual(self.run_page(page.encode()), [])

    def test_boundary_motions_pdfs_navigation_and_news_are_excluded(self):
        unrelated = dict(url='https://www.libdems.org.uk/conference/papers/autumn-2026/outside', title='Outside')
        nonpapers = [dict(url='https://www.libdems.org.uk/conference/motions/f1', title='Motion'),
                     dict(url='https://www.libdems.org.uk/fileadmin/paper.pdf', title='PDF'),
                     dict(url='https://www.libdems.org.uk/news/policy', title='News')]
        self.assertEqual(self.run_page(self.page([self.old] + nonpapers,
                                                before=self.anchor(unrelated), after=self.anchor(unrelated))), [])

    def test_title_change_is_a_distinct_stable_review_candidate(self):
        changed = dict(self.old, title='166 - Corrected policy title (2026)')
        result = self.run_page(self.page([changed]))
        self.assertEqual(result[0]['evidence']['change'], 'title-changed')
        self.assertEqual(result[0]['key'], self.run_page(self.page([changed]))[0]['key'])

    def test_removal_alone_does_not_claim_a_new_plan(self):
        retained = plans.listing_bytes([self.old, self.new])
        (self.root / 'baseline.json').write_bytes(retained)
        self.source['listing_baseline']['sha256'] = hashlib.sha256(retained).hexdigest()
        self.assertEqual(self.run_page(self.page([self.old])), [])

    def test_missing_empty_duplicate_or_reversed_section_fails_closed(self):
        cases = [b'<a href="/conference/papers/elsewhere">Elsewhere</a>',
                 self.page([]),
                 self.page([self.old]).replace(b'<h2>', b'<div id="policy-papers"></div><h2>'),
                 self.page([self.old]).replace(b'id="register-for-conference"', b'id="different-end"'),
                 b'<div id="register-for-conference"></div>' + self.page([self.old])]
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.run_page(raw)

    def test_official_host_required_in_listing_and_selected_links(self):
        for url in ('https://evil.invalid/conference/papers/new',
                    'http://www.libdems.org.uk/conference/papers/new',
                    'https://user@www.libdems.org.uk/conference/papers/new'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.run_page(self.page([self.old, dict(url=url, title='167 - Bad link')]))
        self.source['listing_url'] = 'https://evil.invalid/listing'
        with self.assertRaises(ValueError):
            self.run_page(self.page([self.old]))

    def test_baseline_hash_and_schema_validated_before_fetch(self):
        get = mock.Mock(side_effect=AssertionError('Should not fetch'))
        (self.root / 'baseline.json').write_bytes(b'changed bytes')
        with self.assertRaisesRegex(ValueError, 'baseline hash'):
            plans.discover_listing(self.source, self.root, get=get)
        invalid = b'{"links": [{"url": "invalid"}]}'
        (self.root / 'baseline.json').write_bytes(invalid)
        self.source['listing_baseline']['sha256'] = hashlib.sha256(invalid).hexdigest()
        with self.assertRaises(ValueError):
            plans.discover_listing(self.source, self.root, get=get)
        get.assert_not_called()

    def test_empty_and_conflicting_titles_fail_closed(self):
        for links in ([dict(self.old, title=' ')], [self.old, dict(self.old, title='Conflicting')]):
            with self.subTest(links=links), self.assertRaises(ValueError):
                self.run_page(self.page(links))

    def test_fetch_failure_is_not_unchanged_success(self):
        with self.assertRaisesRegex(OSError, 'fixture unavailable'):
            plans.discover_listing(self.source, self.root,
                                   get=mock.Mock(side_effect=OSError('fixture unavailable')))

    def test_retained_live_response_reproduces_baseline_without_candidates(self):
        root = Path(__file__).resolve().parents[1]
        folder = root / 'docs/evidence/freshness-w6'
        evidence = json.loads((folder / 'libdem-policy-listing-request.json').read_text())
        raw = (root / evidence['response_file']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence['response_sha256'])
        source = evidence['selector']
        links = plans.parse_listing(source, raw)
        self.assertEqual(len(links), evidence['link_count'])
        self.assertEqual(plans.listing_bytes(links),
                         (root / source['listing_baseline']['file']).read_bytes())
        self.assertEqual(plans.discover_listing(source, root, get=lambda url: raw), [])

    def test_live_path_uses_discover_fetch_and_explicit_allowlist(self):
        with mock.patch.object(discover, 'fetch', return_value=self.page([self.old])) as fetch:
            self.assertEqual(plans.discover_listing(self.source, self.root), [])
        fetch.assert_called_once_with(self.source['listing_url'], hosts=self.source['allowed_hosts'])


if __name__ == '__main__':
    unittest.main()
