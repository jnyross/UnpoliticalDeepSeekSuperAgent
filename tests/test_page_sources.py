"""Every generated page, including an empty corrections log, needs a named source."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from check import Page, ValidationError, validate, validate_page


class PageSourceTests(unittest.TestCase):
    def test_removing_source_from_each_generated_page_fails(self):
        # Exercise the actual project dispatch, not only a chart/figure fixture.
        publications = {
            json.loads(path.read_text())['publication']
            for path in (ROOT / 'sources').glob('*manifest.json')
        }
        publications.add(json.loads((ROOT / 'sources/party-offers.json').read_text())['roster']['publication'])
        publications.add(json.loads((ROOT / 'sources/corrections-metadata.json').read_text())['publication'])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'sources').symlink_to(ROOT / 'sources', target_is_directory=True)
            shutil.copytree(ROOT / 'site', root / 'site')
            for path in sorted((root / 'site').rglob('*.html')):
                with self.subTest(page=path.name):
                    original = path.read_text()
                    mutated = original
                    for publication in publications:
                        mutated = mutated.replace(publication, 'Source name removed')
                    self.assertNotEqual(mutated, original)
                    path.write_text(mutated)
                    try:
                        with self.assertRaisesRegex(ValidationError, 'missing source publication'):
                            validate(root)
                    finally:
                        path.write_text(original)

    def test_generic_footer_or_hidden_name_is_not_a_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'page.html'
            path.write_text('<html lang="en"><head><meta name="viewport" content="width=device-width">'
                            '<title>Named source</title></head><body><main><h1>Page</h1></main>'
                            '<footer>Data sources are named on each page. '
                            '<a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">'
                            'Open Government Licence</a></footer></body></html>')
            with self.assertRaisesRegex(ValidationError, 'missing source publication'):
                validate_page(path, {'publication': 'Named source'}, [])
            with self.assertRaisesRegex(ValidationError, 'missing source publication metadata'):
                validate_page(path, None, [])
