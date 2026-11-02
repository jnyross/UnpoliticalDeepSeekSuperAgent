#!/usr/bin/env python3
"""Append-only, forward-looking source/deployment observations; never a rubric scorer."""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
from urllib.parse import urlsplit, quote

from discover import source_baseline

ROOT = Path(__file__).resolve().parents[1]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def instant(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)', value):
        raise ValueError('Expected timezone-aware timestamp')
    return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)


def publication(value):
    if value is None:
        return None
    if re.fullmatch(r'\d{4}-\d\d-\d\d', value):
        start = datetime.strptime(value, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        return start, start + timedelta(days=1)
    point = instant(value)
    return point, point


def url(value):
    p = urlsplit(value)
    if p.scheme != 'https' or not p.netloc or p.username or p.password or p.fragment:
        raise ValueError('Expected public HTTPS evidence URL')


def version(source, baseline):
    if baseline.get('discovery_scope') in ('official-policy-listing-review',
                                           'official-publication-listing-review'):
        # The candidate document was NOT downloaded. Record the actual listing
        # observation, never attribute its semantic hash/date to document bytes.
        return dict(source=source, release_url=baseline['listing_url'],
                    attachment_url=baseline['listing_url'], sha256=baseline['listing_sha256'],
                    vintage=None, original_publication=None, publication_at=None)
    # updated date is the publication of this vintage, not the original release.
    updated = baseline.get('updated', baseline.get('date'))
    if updated == 'not supplied by retained URL':
        updated = None  # explicitly unavailable, not a guessed publication date
    publication(updated)
    return dict(source=source, release_url=baseline.get('release_url', baseline.get('url')),
                attachment_url=baseline.get('attachment_url', baseline.get('url')),
                sha256=baseline['sha256'], vintage=updated,
                original_publication=baseline.get('published'),
                publication_at=None if 'as_of' in baseline else updated)


def version_id(v):
    return sha(canonical(v))


def validate_event(e):
    if e.get('schema_version') != 1 or e.get('kind') not in ('observed', 'live', 'unavailable'):
        raise ValueError('Invalid event schema/kind')
    instant(e['at']); url(e['evidence_url'])
    if e['kind'] == 'unavailable':
        if not e.get('reason') or not e.get('source'):
            raise ValueError('Unavailable evidence needs source and reason')
        return
    v = e['version']
    if not v.get('source') or not re.fullmatch('[0-9a-f]{64}', v['sha256']):
        raise ValueError('Invalid source identity/hash')
    url(v['release_url']); url(v['attachment_url'])
    bounds = publication(v['publication_at'])
    if bounds and bounds[0] > instant(e['at']):
        raise ValueError('Publication is after observation')
    if e['kind'] == 'live':
        if (not re.fullmatch('[0-9a-f]{40}', e['revision']) or
                not re.fullmatch('[0-9a-f]{64}', e['site_sha256']) or not e['files']):
            raise ValueError('Invalid deployment evidence')
        url(e['live_url'])
        for path, digest in e['files'].items():
            if path.startswith('/') or '..' in Path(path).parts or not re.fullmatch('[0-9a-f]{64}', digest):
                raise ValueError('Invalid verified file')
        if sha(canonical(e['files'])) != e['site_sha256']:
            raise ValueError('Invalid site fingerprint')


def load(path):
    events = []
    if not path.exists():
        return events
    for line in path.read_text().splitlines():
        e = json.loads(line)
        digest = e.pop('event_sha256')
        if sha(canonical(e)) != digest or e['previous_sha256'] != (events[-1]['event_sha256'] if events else None):
            raise ValueError('Broken ledger hash chain')
        validate_event(e)
        if e['sequence'] != len(events) + 1 or (events and instant(e['at']) < instant(events[-1]['at'])):
            raise ValueError('Invalid ledger sequence/time order')
        if e['kind'] == 'live' and not any(p['kind'] == 'observed' and p['version'] == e['version'] for p in events):
            raise ValueError('Live version has no prior observation')
        e['event_sha256'] = digest
        events.append(e)
    return events


def append(path, events, additions):
    # Validate the complete candidate before replacing; never rewrite prior bytes.
    old = path.read_bytes() if path.exists() else b''
    if old and not old.endswith(b'\n'):
        raise ValueError('Ledger missing final newline')
    pending = bytearray(old)
    for item in additions:
        e = dict(item, sequence=len(events) + 1,
                 previous_sha256=events[-1]['event_sha256'] if events else None)
        validate_event(e)
        e['event_sha256'] = sha(canonical(e))
        pending.extend(canonical(e) + b'\n')
        events.append(e)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.pending')
    temp.write_bytes(pending)
    try:
        load(temp)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def verify_site(site, live_url, get=None):
    url(live_url)
    def fetch(address):
        request = urllib.request.Request(address, headers={'Cache-Control': 'no-cache'})
        with urllib.request.urlopen(request, timeout=30) as response:
            if urlsplit(response.url).netloc != urlsplit(live_url).netloc:
                raise ValueError('Live fetch redirected to another host')
            return response.read()
    get = get or fetch
    files = {}
    for file in sorted(site.rglob('*')):
        if file.is_file():
            path = file.relative_to(site).as_posix()
            expected = file.read_bytes()
            if get(live_url.rstrip('/') + '/' + quote(path)) != expected:
                raise ValueError('Live output mismatch: ' + path)
            files[path] = sha(expected)
    if not files or 'index.html' not in files:
        raise ValueError('Empty/incomplete site')
    return files


def observe(path, root, at, evidence_url, revision, discovery=None, live_url=None, get=None):
    events = load(path)
    additions = []
    def add(kind, **fields):
        additions.append(dict(schema_version=1, kind=kind, at=at, evidence_url=evidence_url, **fields))
    inventory = json.loads((root / 'config/release-sources.json').read_text())
    baselines = [version(s['id'], source_baseline(s, root)) for s in inventory]
    candidates = list(baselines)
    if discovery:
        if instant(discovery['checked_at']) > instant(at):
            raise ValueError('Discovery report is from the future')
        for result in discovery['sources']:
            candidates.extend(version(result['id'], u['evidence']) for u in result['updates'])
        for error in discovery['errors']:
            add('unavailable', source=error['source'], reason=error['error'])
    known = {version_id(e['version']) for e in events if e['kind'] == 'observed'}
    for v in candidates:
        if version_id(v) not in known:
            add('observed', version=v, historical_first_observed_at=None,
                historical_first_live_at=None)
            known.add(version_id(v))
    success = True
    if live_url:
        try:
            # Bind source identities to the actual generated snapshot, not just root manifests.
            for s in inventory:
                manifest = Path(s['manifest'])
                if (root / manifest).read_bytes() != (root / 'site' / manifest).read_bytes():
                    raise ValueError('Generated source manifest differs: ' + str(manifest))
            files = verify_site(root / 'site', live_url, get)
            # The production clock is sampled AFTER the last successful byte comparison.
            # Injected fetches in offline fixtures use their explicitly supplied fixture clock.
            if get is None:
                at = datetime.now(timezone.utc).isoformat()
            fingerprint = sha(canonical(files))
            for v in baselines:
                if not any(e['kind'] == 'live' and e['version'] == v and
                           e['site_sha256'] == fingerprint for e in events):
                    add('live', version=v, revision=revision, live_url=live_url,
                        files=files, site_sha256=fingerprint)
        except Exception as exc:
            success = False
            add('unavailable', source='live-deployment', reason=str(exc))
    append(path, events, additions)
    return success


def report(events):
    rows = []
    for e in events:
        if e['kind'] != 'observed':
            continue
        v = e['version']
        live = next((p for p in events if p['kind'] == 'live' and p['version'] == v), None)
        bounds = publication(v['publication_at'])
        delay = None
        if live and bounds:
            at = instant(live['at'])
            delay = dict(min_seconds=max(0, (at - bounds[1]).total_seconds()),
                         max_seconds=(at - bounds[0]).total_seconds())
        rows.append(dict(version=v, first_observed_at=e['at'],
                         first_verified_live_at=live['at'] if live else None,
                         deployed_revision=live['revision'] if live else None,
                         publication_to_verified_live=delay,
                         observation_evidence=e['evidence_url'],
                         live_evidence=live['evidence_url'] if live else None,
                         historical_first_live_at=None))
    return dict(schema_version=1, rubric_level_4_claimed=False, versions=rows,
                unavailable=[e for e in events if e['kind'] == 'unavailable'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['observe', 'report'])
    parser.add_argument('--ledger', type=Path, default=Path('measurements/release-timing.jsonl'))
    parser.add_argument('--previous-ledger', type=Path,
                        help='Reject deletion or modification of any previously committed ledger bytes')
    parser.add_argument('--discovery', type=Path)
    parser.add_argument('--revision')
    parser.add_argument('--evidence-url')
    parser.add_argument('--live-url')
    args = parser.parse_args()
    if args.previous_ledger:
        load(args.previous_ledger)
        if not args.ledger.read_bytes().startswith(args.previous_ledger.read_bytes()):
            parser.error('Previously committed ledger bytes were modified or removed')
    if args.command == 'report':
        if not args.ledger.is_file():
            parser.error('Ledger does not exist; no observations available')
        print(json.dumps(report(load(args.ledger)), indent=2))
        return 0
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if args.revision != head:
        parser.error('--revision must be the checked-out commit')
    # A successful deterministic build is required before claiming delivery.
    if args.live_url:
        subprocess.run([sys.executable, 'scripts/build.py', '--check'], cwd=ROOT, check=True,
                       stdout=sys.stderr)
    success = observe(args.ledger, ROOT, datetime.now(timezone.utc).isoformat(),
                      args.evidence_url, args.revision,
                      json.loads(args.discovery.read_text()) if args.discovery else None,
                      args.live_url)
    print(json.dumps(report(load(args.ledger)), indent=2))
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
