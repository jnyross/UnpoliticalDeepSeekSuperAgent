"""Material coverage regression tests, not manual accessibility outcomes."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from scripts.manual_access import inventory, validate, blank_records, ROOT, INVENTORY


class ManualInventoryTests(unittest.TestCase):
    def fixture(self, directory, html):
        site = Path(directory)
        (site / 'index.html').write_text(html)
        return site

    def test_committed_inventory_matches_every_generated_page(self):
        manifest = validate(ROOT / 'site', json.loads(INVENTORY.read_text()))
        self.assertEqual(len(manifest['pages']), len(list((ROOT / 'site').rglob('*.html'))))

    def test_details_controls_tables_charts_and_view_links(self):
        with tempfile.TemporaryDirectory() as directory:
            site = self.fixture(directory, '''<main><details><summary>Data</summary>
            <table><caption>Amounts</caption></table></details><details open><summary>Notes</summary></details>
            <button aria-expanded="false" aria-controls="panel">More</button><div id="panel"></div>
            <figure><figcaption>History</figcaption><svg aria-hidden="true"></svg></figure>
            <a href="history-real.html#health">Real</a></main>''')
            page = inventory(site)['pages'][0]
            self.assertEqual(page['states'], ['initial', 'all-details-expanded', 'expanded-button:1'])
            self.assertEqual([t['kind'] for t in page['targets']],
                             ['disclosure', 'table', 'disclosure', 'expanded-control', 'chart', 'view-link'])
            self.assertEqual(page['targets'][0]['label'], 'Data')
            self.assertEqual(page['targets'][2]['initial'], 'expanded')
            self.assertEqual(page['targets'][4]['label'], 'History')

    def test_page_and_control_drift_fail_until_reviewed(self):
        with tempfile.TemporaryDirectory() as directory:
            site = self.fixture(directory, '<main>Content</main>')
            saved = inventory(site)
            for changed in ('<main>New content</main>', '<details><summary>New</summary></details>',
                            '<button aria-expanded="false">New</button>'):
                (site / 'index.html').write_text(changed)
                with self.assertRaisesRegex(ValueError, 'stale'):
                    validate(site, saved)
            (site / 'index.html').write_text('<main>Content</main>')
            (site / 'new.html').write_text('<main>Another page</main>')
            with self.assertRaisesRegex(ValueError, 'stale'):
                validate(site, saved)
            (site / 'index.html').unlink()
            with self.assertRaisesRegex(ValueError, 'stale'):
                validate(site, saved)

    def test_removed_state_or_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            site = self.fixture(directory, '<details><summary>Data</summary></details>')
            saved = inventory(site)
            for field in ('targets', 'states', 'tasks'):
                edited = copy.deepcopy(saved)
                edited['pages'][0][field].pop()
                with self.assertRaises(ValueError):
                    validate(site, edited)

    def test_records_cover_cross_product_and_remain_unperformed(self):
        with tempfile.TemporaryDirectory() as directory:
            site = self.fixture(directory, '<details><summary>Data</summary></details>')
            manifest = inventory(site)
            records = blank_records(manifest)
            rows = records['results']
            self.assertEqual(len(rows), 2 * 2 * 2 * 4)
            self.assertEqual({row['outcome'] for row in rows}, {'unperformed'})
            self.assertTrue(all(value == '' for value in records['environment'].values()))
            self.assertEqual(records['findings'], [])
            self.assertEqual(len({(r['page'], r['mode'], r['viewport'], r['state'], r['target'], r['task']) for r in rows}), len(rows))

    def test_record_cli_never_overwrites_existing_results(self):
        with tempfile.TemporaryDirectory() as directory:
            site = self.fixture(directory, '<main>Content</main>')
            saved = site / 'inventory.json'
            saved.write_text(json.dumps(inventory(site)))
            records = site / 'records.json'
            records.write_text('keep real observations')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/manual_access.py'),
                                     '--site', str(site), '--inventory', str(saved),
                                     '--records', str(records)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('FileExistsError', result.stderr)
            self.assertEqual(records.read_text(), 'keep real observations')

    def test_empty_site_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'No generated HTML'):
                inventory(Path(directory))


if __name__ == '__main__':
    unittest.main()
