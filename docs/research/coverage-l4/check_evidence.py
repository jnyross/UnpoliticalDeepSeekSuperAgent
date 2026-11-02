"""Offline integrity check for research snapshots, not a Coverage L4 acceptance test."""
import hashlib
import json
from pathlib import Path
import sys


def validate(directory):
    directory = Path(directory)
    records = json.loads((directory / 'publisher-evidence-metadata.json').read_text())
    seen = set()
    checked = 0
    for record in records:
        assert record['requested_url'].startswith('https://')
        assert record['retrieved_at']
        if record['status'] != 200:
            assert not record.get('file'), 'Failed response must not be treated as evidence'
            continue
        assert record['text_source_html'] == record['file'], 'Transcript source differs'
        for file_key, hash_key in [('file', 'sha256'), ('text_file', 'text_sha256')]:
            name = record[file_key]
            assert Path(name).name == name and name not in seen, 'Invalid or duplicate evidence file'
            seen.add(name)
            data = (directory / name).read_bytes()
            assert hashlib.sha256(data).hexdigest() == record[hash_key], f'Changed evidence: {name}'
            if file_key == 'file':
                assert len(data) == record['bytes'], f'Changed size: {name}'
            checked += 1
    assert checked > 0, 'No successful evidence snapshots'
    assert {p.name for p in directory.glob('*.html')} <= seen, 'Unregistered HTML snapshot'
    assert {p.name for p in directory.glob('*.txt')} <= seen, 'Unregistered text snapshot'
    return checked


if __name__ == '__main__':
    directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    print(f'PASS: {validate(directory)} research file hashes; no rubric level claimed')
