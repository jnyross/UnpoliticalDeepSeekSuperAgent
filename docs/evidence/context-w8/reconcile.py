"""Bounded wave-eight evidence capture; never refreshes sources or writes notices.

Only the three sources added after the completed wave-seven audit are fetched.
Reuses existing discovery/reconciliation and exact deployment verification.
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
    previous_revision = '278cc11526ea50a612c4644e2dd521c479bfe5db'
    old = json.loads(subprocess.check_output(
        ['git', 'show', previous_revision + ':config/release-sources.json'], cwd=ROOT, text=True))
    inventory = json.loads((ROOT / 'config/release-sources.json').read_text())
    old_ids = {s['id'] for s in old}
    current_ids = {s['id'] for s in inventory}
    added = sorted(current_ids - old_ids)
    expected = ['party-evidence-conservative-costings-2024', 'party-evidence-de-childcare-2024',
                'party-evidence-libdem-costings-2024']
    if added != expected or old_ids - current_ids:
        raise ValueError('Unexpected inventory delta: review scope before fetching')
    report = dict(started_at=now(), revision=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        previous_audit_revision=previous_revision,
        inventory=dict(previous_count=len(old_ids), current_count=len(current_ids), added=added, removed=[]),
        sources=[], errors=[])
    for source in (s for s in inventory if s['id'] in added):
        row = dict(id=source['id'], adapter=source['adapter'], started_at=now(), requests=[])
        report['sources'].append(row)

        def get(url):
            request = dict(url=url, started_at=now())
            row['requests'].append(request)
            try:
                raw = discover.fetch(url, hosts=source['allowed_hosts'])
                request.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
                return raw
            except Exception as exc:
                request['error'] = str(exc)
                raise
            finally:
                request['finished_at'] = now()

        try:
            baseline = discover.source_baseline(source, ROOT)
            row['baseline'] = baseline
            path = Path(baseline['file'])
            if len(path.parts) == 1:
                path = Path(source['manifest']).parent / path
            sha = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            row['retained_sha256'] = sha
            if sha != baseline['sha256']:
                raise ValueError('Retained source hash differs from manifest')
            row['updates'] = discover.discover(source, root=ROOT, get=get)
            row['status'] = 'updates' if row['updates'] else 'unchanged'
        except Exception as exc:
            row.update(status='unknown', error=str(exc))
            report['errors'].append(dict(source=source['id'], error=str(exc)))
        row['finished_at'] = now()
    state = discover.load_revision_status(ROOT / 'sources/revision-status.json')
    results = [dict(id=r['id'], updates=r['updates']) for r in report['sources'] if 'updates' in r]
    report['retained_notices'] = state
    report['reconciled_notices'] = discover.reconcile_revision_status(
        state, inventory, results, root=ROOT, checked_at=now())
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
    print(json.dumps(dict(inventory=report['inventory'], sources=[dict(id=r['id'], status=r['status'])
                      for r in report['sources']], notice_state_unchanged=report['notice_state_unchanged'],
                      errors=report['errors']), indent=2))
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
