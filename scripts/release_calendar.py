"""Recheck retained official release evidence without inventing publication dates.

The calendar is curated: a changed upstream page can announce a date, withdraw one,
or merely alter navigation. Never carry a 'no announcement' interpretation across
changed bytes automatically. Fetch the whole evidence set first, then require review
on a change. Network failures and changes leave every retained byte untouched.
"""
import hashlib
import json
from pathlib import Path
import urllib.request


class CalendarReviewRequired(ValueError):
    """Official evidence changed; review is needed before a calendar refresh."""


def refresh(root):
    """Verify all unique calendar evidence URLs; return a deterministic summary.

    Unchanged bytes retain their original retrieval/check date: that date describes
    the retained snapshot, not a fictional publication or next-release date. A
    changed response raises CalendarReviewRequired before any write. Reviewers must
    retain the new official bytes and update interpretations/hashes together.
    """
    root = Path(root)
    calendar = json.loads((root / 'sources/release-calendar.json').read_text())
    evidence = {}
    for entry in calendar['entries'].values():
        for item in [entry, *entry.get('evidence', [])]:
            key = item['file']
            record = (item['url'], item['sha256'])
            if key in evidence and evidence[key] != record:
                raise ValueError(f'Conflicting release calendar evidence: {key}')
            evidence[key] = record
    # Validate local evidence before performing network operations.
    for name, (_, expected) in evidence.items():
        path = (root / 'sources' / name).resolve()
        if path.parent != (root / 'sources').resolve():
            raise ValueError(f'Invalid calendar snapshot path: {name}')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Release calendar evidence hash changed: {name}')
    fetched = {}
    for name, (url, _) in sorted(evidence.items()):
        if not url.startswith('https://'):
            raise ValueError(f'Calendar evidence requires HTTPS: {url}')
        request = urllib.request.Request(url, headers={'User-Agent': 'UnpoliticalAF-release-calendar/1.0'})
        with urllib.request.urlopen(request, timeout=90) as response:
            data = response.read()
        # Every retained calendar endpoint is JSON. A successful HTML error page
        # must not be mistaken for valid official release metadata.
        metadata = json.loads(data)
        if not isinstance(metadata, dict):
            raise ValueError(f'Calendar endpoint returned non-object metadata: {name}')
        baseline = json.loads((root / 'sources' / name).read_bytes())
        if 'results' in baseline:
            if (not isinstance(metadata.get('results'), list)
                    or type(metadata.get('total')) is not int
                    or metadata['total'] < len(metadata['results'])):
                raise ValueError(f'Malformed calendar search metadata: {name}')
        elif 'base_path' in baseline:
            if (not isinstance(metadata.get('base_path'), str)
                    or not isinstance(metadata.get('details'), dict)):
                raise ValueError(f'Malformed calendar content metadata: {name}')
        elif 'items' in baseline and not isinstance(metadata.get('items'), list):
            raise ValueError(f'Malformed calendar roster metadata: {name}')
        fetched[name] = hashlib.sha256(data).hexdigest()
    changed = [name for name in sorted(evidence) if fetched[name] != evidence[name][1]]
    if changed:
        raise CalendarReviewRequired(
            'Official release calendar evidence changed; retained calendar left untouched. '
            'Review and retain new snapshots before updating next-release claims: '
            + ', '.join(changed)
        )
    return {'status': 'unchanged', 'checked_at': calendar['checked_at'], 'snapshots': len(evidence)}
