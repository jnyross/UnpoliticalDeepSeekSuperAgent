"""Bounded wave-seven evidence capture; no refresh, issue writing or state mutation.

Run from repository root: python3 docs/evidence/context-w7/reconcile.py
Writes only incremental-reconciliation.json beside this script. Network observations
are point-in-time evidence; this does not re-audit previously checked source bytes.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import discover
from release_timing import verify_site


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    report = dict(started_at=now(), revision=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), errors=[])
    previous = json.loads((ROOT / 'docs/evidence/context-w6/live-audit.json').read_text())
    inventory = json.loads((ROOT / 'config/release-sources.json').read_text())
    previous_ids = {s['id'] for s in previous['sources']}
    current_ids = {s['id'] for s in inventory}
    report['inventory'] = dict(previous_count=len(previous_ids), current_count=len(current_ids),
                               added=sorted(current_ids - previous_ids),
                               removed=sorted(previous_ids - current_ids))
    expected = ['party-evidence-ifs-june2024-opening-remarks']
    if report['inventory']['added'] != expected or report['inventory']['removed']:
        raise ValueError('Unexpected inventory delta; review audit scope before fetching')
    source = next(s for s in inventory if s['id'] == expected[0])
    baseline = discover.source_baseline(source, ROOT)
    report['source'] = dict(id=source['id'], baseline=baseline, started_at=now())
    report['requests'] = []

    def get(url):
        row = dict(url=url, started_at=now())
        report['requests'].append(row)
        try:
            raw = discover.fetch(url, hosts=source['allowed_hosts'])
            row.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            return raw
        except Exception as exc:
            row['error'] = str(exc)
            raise
        finally:
            row['finished_at'] = now()

    try:
        path = Path(baseline['file'])
        if len(path.parts) == 1:
            path = Path(source['manifest']).parent / path
        sha = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        report['source']['retained_sha256'] = sha
        if sha != baseline['sha256']:
            raise ValueError('Retained IFS PDF hash differs from manifest')
        updates = discover.discover(source, root=ROOT, get=get)
        report['source'].update(updates=updates, status='updates' if updates else 'unchanged')
    except Exception as exc:
        report['source'].update(status='unknown', error=str(exc))
        report['errors'].append(dict(source=source['id'], error=str(exc)))
        updates = []
    report['source']['finished_at'] = now()
    state = discover.load_revision_status(ROOT / 'sources/revision-status.json')
    report['retained_notices'] = state
    report['reconciled_notices'] = discover.reconcile_revision_status(
        state, inventory, [dict(id=source['id'], updates=updates)], root=ROOT, checked_at=now())
    report['notice_state_unchanged'] = state == report['reconciled_notices']
    report['deployment'] = dict(url='https://unpoliticaldeepseeksuperagent.vercel.app', started_at=now())
    try:
        report['deployment']['files'] = verify_site(ROOT / 'site', report['deployment']['url'])
        report['deployment']['status'] = 'exact-byte-match'
    except Exception as exc:
        report['deployment'].update(status='unknown-or-mismatch', error=str(exc))
        report['errors'].append(dict(source='deployment', error=str(exc)))
    report['deployment']['finished_at'] = now()
    report['finished_at'] = now()
    Path(__file__).with_name('incremental-reconciliation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(inventory=report['inventory'], source=report['source']['status'],
                          notice_state_unchanged=report['notice_state_unchanged'], errors=report['errors']), indent=2))
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
