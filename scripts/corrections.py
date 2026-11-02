#!/usr/bin/env python3
"""Validate the public corrections ledger, and optionally its append-only history.

Public API: load(path) -> list[dict], assert_append_only(previous, current) -> None.
Both reject invalid input with ValidationError (a ValueError). Pages are canonical
site-relative HTML paths, e.g. ``index.html``, not filesystem or remote URLs.
An empty ledger is valid: tests use fictional records only in temporary fixtures.
"""
from __future__ import annotations

import argparse
import hashlib
from datetime import date
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'sources/corrections.json'
LIMITS = {'id': 80, 'date': 10, 'page': 240, 'error': 2000,
          'correction': 2000, 'source': 512}
ID_RE = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
SOURCE_RE = re.compile(
    r'https://github\.com/jnyross/UnpoliticalDeepSeekSuperAgent/'
    r'(?:commit/[0-9a-fA-F]{40}(?:#diff-[A-Za-z0-9_-]+)?|pull/[1-9][0-9]*)\Z')


class ValidationError(ValueError):
    """Invalid corrections data or an unverifiable append-only comparison."""


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f'duplicate JSON field: {key}')
        result[key] = value
    return result


def _decode(text):
    try:
        return json.loads(text, object_pairs_hook=_object)
    except json.JSONDecodeError as exc:
        raise ValidationError(f'invalid corrections JSON: {exc}') from exc


def _validate(entries, site=None):
    if not isinstance(entries, list):
        raise ValidationError('corrections must be a JSON list')
    seen = set()
    last_date = None
    for index, entry in enumerate(entries):
        label = f'correction {index + 1}'
        if not isinstance(entry, dict) or set(entry) != set(LIMITS):
            raise ValidationError(f'{label}: expected exactly {", ".join(LIMITS)}')
        for field, limit in LIMITS.items():
            value = entry[field]
            if (not isinstance(value, str) or not value.strip() or
                    value != value.strip() or len(value) > limit or
                    any(ord(c) < 32 or ord(c) == 127 for c in value)):
                raise ValidationError(f'{label}: {field} must be a nonempty string '
                                      f'of at most {limit} characters without controls or edge whitespace')
        if not ID_RE.fullmatch(entry['id']):
            raise ValidationError(f'{label}: id must be lowercase alphanumeric words joined by hyphens')
        if entry['id'] in seen:
            raise ValidationError(f'{label}: duplicate id {entry["id"]}')
        seen.add(entry['id'])
        stamp = entry['date']
        try:
            if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', stamp):
                raise ValueError('expected YYYY-MM-DD')
            parsed_date = date.fromisoformat(stamp)
        except ValueError as exc:
            raise ValidationError(f'{label}: date must be a real ISO YYYY-MM-DD date') from exc
        if last_date is not None and parsed_date < last_date:
            raise ValidationError(f'{label}: dates must be chronological (oldest first)')
        last_date = parsed_date
        page = entry['page']
        parts = page.split('/')
        if (not re.fullmatch(r'[A-Za-z0-9_./-]+', page) or
                any(part in ('', '.', '..') for part in parts) or
                not page.endswith('.html')):
            raise ValidationError(f'{label}: page must be a safe site-relative HTML path')
        if site is not None:
            site = Path(site).resolve()
            target = (site / page).resolve()
            if not target.is_relative_to(site) or not target.is_file():
                raise ValidationError(f'{label}: page must be an existing local HTML file within site/')
        if not SOURCE_RE.fullmatch(entry['source']):
            raise ValidationError(f'{label}: source must be this repository\'s full commit URL '
                                  '(optional #diff- fragment) or pull/N URL')
    return entries


def load(path, *, check_pages=True):
    """Read and validate a source file against its sibling repository's site/ tree.

    ``path`` is normally ROOT/sources/corrections.json. No strings are normalized
    or silently discarded. Equal dates are allowed; IDs remain unique. A build
    staging data before rendering pages may pass ``check_pages=False``; canonical
    safe path syntax is still checked, and the final output must use the default.
    """
    path = Path(path)
    site = path.parent.parent / 'site' if check_pages else None
    return _validate(_decode(path.read_text(encoding='utf-8')), site)


def load_metadata(path, entries):
    """Validate the retained local snapshot, including an explicitly empty ledger.

    Dates are maintained with source evidence, never taken from the build clock.
    The byte hash forces a reviewed metadata update when the ledger changes.
    """
    path = Path(path)
    metadata = _decode(path.read_text(encoding='utf-8'))
    fields = {'publication', 'file', 'date', 'sha256', 'date_basis', 'evidence_url'}
    if not isinstance(metadata, dict) or set(metadata) != fields:
        raise ValidationError('corrections metadata: unexpected fields')
    if metadata['file'] != 'corrections.json':
        raise ValidationError('corrections metadata: invalid source file')
    for key in fields:
        value = metadata[key]
        if (not isinstance(value, str) or not value.strip() or value != value.strip()
                or len(value) > 512 or any(ord(c) < 32 for c in value)):
            raise ValidationError(f'corrections metadata: invalid {key}')
    try:
        stamp = date.fromisoformat(metadata['date'])
        if stamp.isoformat() != metadata['date']:
            raise ValueError('not canonical')
    except ValueError as exc:
        raise ValidationError('corrections metadata: invalid date') from exc
    _validate(entries)
    if any(date.fromisoformat(entry['date']) > stamp for entry in entries):
        raise ValidationError('corrections metadata: snapshot predates an entry')
    raw = (path.parent / 'corrections.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != metadata['sha256']:
        raise ValidationError('corrections metadata: snapshot hash differs')
    if not SOURCE_RE.fullmatch(metadata['evidence_url']):
        raise ValidationError('corrections metadata: invalid snapshot evidence URL')
    return metadata


def assert_append_only(previous, current):
    """Reject deletion, reordering, or edits; permit identical data and new suffixes.

    Compare decoded records, not JSON formatting or object-key order. Validate
    schema even when used directly; file existence is checked separately by load.
    """
    _validate(previous)
    _validate(current)
    if len(current) < len(previous):
        raise ValidationError('append-only corrections: existing entries were dropped')
    for index, entry in enumerate(previous):
        if current[index] != entry:
            raise ValidationError(f'append-only corrections: existing entry {index + 1} was changed or reordered')


def _git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True,
                            text=True, encoding='utf-8')
    if result.returncode:
        raise ValidationError(f'cannot verify corrections history: git {args[0]}: '
                              f'{result.stderr.strip() or "command failed"}')
    return result.stdout


def check_base(root, base, current):
    """Compare against a verified Git commit; only a genuinely absent old file is new."""
    # Resolve first: a nonexistent ref must NEVER be mistaken for a missing file.
    commit = _git(root, 'rev-parse', '--verify', '--end-of-options', base + '^{commit}').strip()
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', commit):
        raise ValidationError('cannot verify corrections history: invalid resolved commit')
    tree = _git(root, 'ls-tree', '-z', commit, '--', SOURCE)
    if not tree:
        assert_append_only([], current)
        return
    if not re.fullmatch(r'100(?:644|755) blob [0-9a-f]+\tsources/corrections\.json\x00', tree):
        raise ValidationError('previous corrections source is not a regular Git file')
    previous = _validate(_decode(_git(root, 'show', f'{commit}:{SOURCE}')), Path(root) / 'site')
    assert_append_only(previous, current)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', metavar='REF', help='require an append-only change from this Git commit/ref')
    parser.add_argument('--root', type=Path, default=ROOT, help='repository root (default: script repository)')
    args = parser.parse_args(argv)
    try:
        current = load(args.root / SOURCE)
        if args.base is not None:
            check_base(args.root, args.base, current)
    except (ValueError, OSError, UnicodeError) as exc:
        print(f'Corrections check failed: {exc}', file=sys.stderr)
        return 1
    print(f'Corrections valid: {len(current)} entries' + ('; append-only history verified' if args.base is not None else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
