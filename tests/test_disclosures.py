"""Regression checks for static project links and honest disclosure copy."""
import sys
from pathlib import Path
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from check import Page, ValidationError, validate_project_links


class DisclosureTests(unittest.TestCase):
    def test_all_pages_have_static_project_links(self):
        for path in (ROOT / 'site').glob('*.html'):
            with self.subTest(page=path.name):
                page = Page()
                page.feed(path.read_text())
                validate_project_links(page, path)

    def test_missing_links_and_login_notice_fail(self):
        text = (ROOT / 'site/about.html').read_text()
        for old, new in [('about.html', 'missing.html'),
                         ('/issues/new', '/wrong'),
                         ('sign-in needed to submit', 'no account needed')]:
            with self.subTest(mutation=old), self.assertRaises(ValidationError):
                page = Page()
                page.feed(text.replace(old, new))
                validate_project_links(page, 'mutated')

    def test_about_local_links_resolve_including_fragments(self):
        page = Page()
        page.feed((ROOT / 'site/about.html').read_text())
        for href in page.links:
            url = urlsplit(href)
            if url.scheme or not url.path:
                continue
            target = ROOT / 'site' / url.path
            self.assertTrue(target.is_file(), href)
            if url.fragment:
                self.assertIn(f'id="{url.fragment}"', target.read_text(), href)

    def test_operator_and_funding_not_invented(self):
        text = (ROOT / 'site/about.html').read_text()
        self.assertIn('automated code maintenance', text)
        self.assertIn('not proof of that role', text)
        self.assertIn('does not mean the site has no funding', text)
        self.assertIn('A confirmed funding statement has not been supplied', text)


if __name__ == '__main__':
    unittest.main()
