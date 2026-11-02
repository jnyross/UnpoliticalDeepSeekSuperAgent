#!/usr/bin/env python3
"""Read-only, timestamped audit using the existing discovery and live-site adapters.

Never refreshes sources, publishes notices, opens issues, or writes timing history.
An error is unknown, not unchanged. Successful hash equality is a point-in-time
comparison, not a guarantee against subsequent publisher revisions.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit

import discover
from release_timing import verify_site

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def audit(root=ROOT, live_url=None):
    inventory = json.loads((root / 'config/release-sources.json').read_text())
    report = dict(started_at=now(), revision=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(), sources=[],
        calendars=[], requests=[], errors=[])
    original_fetch = discover.fetch

    def recording_fetch(url, hosts=discover.DEFAULT_HOSTS):
        entry = dict(url=url, started_at=now())
        report['requests'].append(entry)
        try:
            raw = original_fetch(url, hosts=hosts)
            entry.update(sha256=discover.digest(raw), bytes=len(raw))
            return raw
        except Exception as exc:
            entry['error'] = str(exc)
            raise
        finally:
            entry['finished_at'] = now()

    discover.fetch = recording_fetch
    try:
        for source in inventory:
            row = dict(id=source['id'], adapter=source['adapter'], started_at=now())
            report['sources'].append(row)
            try:
                baseline = discover.source_baseline(source, root)
                row['baseline'] = baseline
                path = Path(baseline['file'])
                if len(path.parts) == 1:
                    path = Path(source['manifest']).parent / path
                retained = discover.digest((root / path).read_bytes())
                row['retained_sha256'] = retained
                if retained != baseline['sha256']:
                    raise ValueError('Retained bytes do not match manifest')
                first = len(report['requests'])
                row['updates'] = discover.discover(source, root=root)
                row['request_indexes'] = list(range(first, len(report['requests'])))
                row['status'] = 'updates' if row['updates'] else 'unchanged'
            except Exception as exc:
                row.update(status='unknown', error=str(exc))
                report['errors'].append(dict(source=source['id'], error=str(exc)))
            row['finished_at'] = now()
        calendar = json.loads((root / 'sources/release-calendar.json').read_text())
        evidence = {e['url']: e for entry in calendar['entries'].values()
                    for e in entry.get('evidence', [])}
        for url, saved in evidence.items():
            row = dict(url=url, retained_sha256=saved['sha256'],
                       retained_retrieved=saved['retrieved'])
            report['calendars'].append(row)
            try:
                raw = recording_fetch(url, hosts=(urlsplit(url).hostname,))
                row['sha256'] = discover.digest(raw)
                row['status'] = 'unchanged' if row['sha256'] == saved['sha256'] else 'changed-needs-review'
                if row['status'] != 'unchanged':
                    report['errors'].append(dict(source=url, error=row['status']))
            except Exception as exc:
                row.update(status='unknown', error=str(exc))
                report['errors'].append(dict(source=url, error=str(exc)))
        state = discover.load_revision_status(root / 'sources/revision-status.json')
        results = [dict(id=r['id'], updates=r['updates']) for r in report['sources'] if 'updates' in r]
        report['retained_revision_status'] = state
        report['reconciled_revision_status'] = discover.reconcile_revision_status(
            state, inventory, results, root=root, checked_at=report['started_at'])
    finally:
        discover.fetch = original_fetch
    if live_url:
        report['deployment'] = dict(url=live_url, started_at=now())
        try:
            report['deployment']['files'] = verify_site(root / 'site', live_url)
            report['deployment']['status'] = 'exact-byte-match'
        except Exception as exc:
            report['deployment'].update(status='unknown-or-mismatch', error=str(exc))
            report['errors'].append(dict(source='deployment', error=str(exc)))
        report['deployment']['finished_at'] = now()
    report['finished_at'] = now()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--live-url')
    args = parser.parse_args()
    report = audit(live_url=args.live_url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(sources=len(report['sources']), errors=report['errors']), indent=2))
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
