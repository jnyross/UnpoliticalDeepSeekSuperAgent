"""Retained local snapshot fixtures, not published correction events."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import corrections
from check import validate_page, ValidationError


class MetadataTests(unittest.TestCase):
    def test_retained_snapshot_is_hash_bound(self):
        entries = corrections.load(ROOT / 'sources/corrections.json')
        metadata = corrections.load_metadata(ROOT / 'sources/corrections-metadata.json', entries)
        self.assertRegex(metadata['date'], r'^\d{4}-\d{2}-\d{2}$')
        self.assertEqual(metadata['publication'], 'UnpoliticalAF corrections log')

    def test_invalid_or_stale_snapshot_fails(self):
        original = json.loads((ROOT / 'sources/corrections-metadata.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'corrections.json').write_bytes(b'[]\n')
            path = root / 'corrections-metadata.json'
            for key, value in [('date', '2026-02-30'), ('date', '20261102'),
                               ('publication', ''), ('sha256', '0' * 64),
                               ('evidence_url', 'https://example.com')]:
                with self.subTest(key=key, value=value):
                    changed = dict(original, **{key: value})
                    path.write_text(json.dumps(changed))
                    with self.assertRaises(ValueError):
                        corrections.load_metadata(path, [])
            path.write_text(json.dumps(original))
            entries = [dict(id='fixture', date='2026-11-03', page='index.html',
                            error='Fixture only', correction='Fixture only',
                            source=original['evidence_url'])]
            (root / 'corrections.json').write_text(json.dumps(entries))
            original['sha256'] = hashlib.sha256((root / 'corrections.json').read_bytes()).hexdigest()
            path.write_text(json.dumps(original))
            with self.assertRaisesRegex(ValueError, 'predates'):
                corrections.load_metadata(path, entries)

    def test_date_and_publication_are_required_in_visible_copy(self):
        metadata = json.loads((ROOT / 'sources/corrections-metadata.json').read_text())
        html = (ROOT / 'site/corrections.html').read_text()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'corrections.html'
            for field in ('date', 'publication'):
                with self.subTest(field=field):
                    path.write_text(html.replace(metadata[field], 'MISSING'))
                    with self.assertRaises(ValidationError):
                        validate_page(path, metadata, [])
