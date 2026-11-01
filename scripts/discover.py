#!/usr/bin/env python3
"""Read-only release/revision checks; only --open-issues writes (GitHub issues).

Collection adapters discover new release links. Retained-URL snapshots only detect
revisions at inventory URLs, including explicitly identified archive-hosted copies;
they cannot discover new manifesto URLs or advance a historical roster's date.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
NOTICE = 'This is by an automated agent, not a human.'


DEFAULT_HOSTS = ('www.gov.uk', 'assets.publishing.service.gov.uk')


def allowed_url(url, hosts):
    parsed = urlsplit(url)
    return (parsed.scheme == 'https' and parsed.hostname in hosts and
            parsed.port in (None, 443) and not parsed.username and not parsed.password)


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts=DEFAULT_HOSTS):
        super().__init__()
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not allowed_url(newurl, self.hosts):
            raise ValueError('Redirected outside official hosts')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, hosts=DEFAULT_HOSTS):
    if not allowed_url(url, hosts):
        raise ValueError('Not an allowed official URL: ' + url)
    # Publisher/archive CDNs reject urllib's default user agent, even for public PDFs.
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'})
    with urllib.request.build_opener(OfficialRedirect(hosts)).open(request, timeout=60) as response:
        if not allowed_url(response.url, hosts):
            raise ValueError('Redirected outside official hosts')
        return response.read()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def source_baseline(source, root):
    manifest = json.loads((root / source['manifest']).read_text())
    if source.get('selector') == 'roster':
        return manifest['roster']
    if 'source_id' in source:
        matches = [s for s in manifest['sources'] if s['id'] == source['source_id']]
        if len(matches) != 1:
            raise ValueError('Expected exactly one source matching ' + source['source_id'])
        return matches[0]
    return manifest


def roster_semantics(raw):
    """Only consumed party identity and seat totals; ignore API timestamps/presentation."""
    items = json.loads(raw)['items']
    if not isinstance(items, list) or not items:
        raise ValueError('Empty or invalid party roster')
    rows = []
    for item in items:
        value = item['value']
        party = value['party']
        row = dict(id=party['id'], name=party['name'], total=value['total'],
                   independent=party['isIndependentParty'])
        if (type(row['id']) is not int or not isinstance(row['name'], str) or
                not row['name'] or type(row['total']) is not int or row['total'] < 0 or
                type(row['independent']) is not bool):
            raise ValueError('Invalid party identity or seat total')
        rows.append(row)
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate party in roster')
    return json.dumps(sorted(rows, key=lambda row: row['id']), sort_keys=True).encode()


def discover_snapshot(source, root, get=None):
    """Detect revisions at retained URLs only, not newly published plans or rosters."""
    baseline = source_baseline(source, root)
    hosts = source['allowed_hosts']
    if (not isinstance(hosts, list) or not hosts or
            any(not isinstance(h, str) or not re.fullmatch(r'[a-z0-9.-]+', h) for h in hosts)):
        raise ValueError('Expected explicit official allowed_hosts')
    url = baseline['url']
    if not allowed_url(url, hosts):
        raise ValueError('Not an allowed official URL: ' + url)
    raw = fetch(url, hosts=hosts) if get is None else get(url)
    sha = digest(raw)
    normalization = source.get('normalization')
    semantic_sha = None
    if normalization:
        if normalization != 'parliament-party-roster':
            raise ValueError('Unknown snapshot normalization: ' + normalization)
        snapshot = Path(baseline['file'])
        snapshot = ((root / source['manifest']).parent / snapshot if len(snapshot.parts) == 1
                    else root / snapshot)
        retained = snapshot.read_bytes()
        if digest(retained) != baseline['sha256']:
            raise ValueError('Retained snapshot does not match manifest hash')
        semantic_sha = digest(roster_semantics(raw))
        if semantic_sha == digest(roster_semantics(retained)):
            return []
    elif sha == baseline['sha256']:
        return []
    evidence = dict(source=source['id'], release_url=url, attachment_url=url,
                    sha256=sha, discovery_scope='retained-url-revision',
                    updated='not supplied by retained URL',
                    refresh_command='python3 scripts/build.py --refresh')
    if baseline.get('hosting'):
        evidence['hosting'] = baseline['hosting']
    if semantic_sha:
        evidence['semantic_sha256'] = semantic_sha
    # A roster's incidental timestamps must not make repeated identical semantic changes
    # open different issues. Keep the byte hash as evidence, not as its identity.
    identity = dict(source=source['id'], url=url, sha256=semantic_sha or sha)
    key = digest(json.dumps(identity, sort_keys=True).encode())
    return [dict(key=key, evidence=evidence, baseline=baseline)]


def discover(source, root=ROOT, get=None):
    """Dispatch explicit discovery scopes; only collection adapters find new releases."""
    if source['adapter'] == 'retained-url-snapshot':
        return discover_snapshot(source, root, get)
    if source['adapter'] != 'govuk-collection-attachment':
        raise ValueError('Unknown adapter: ' + source['adapter'])
    get = get or fetch
    baseline = source_baseline(source, root)
    collection = json.loads(get(source['collection_api']))
    documents = collection['links']['documents']
    if not documents:
        raise ValueError('Empty release collection')
    paths = {baseline['release_url'].removeprefix('https://www.gov.uk')}
    for doc in documents:
        if re.fullmatch(source['release_path_pattern'], doc['base_path']):
            # Include new releases and revisions since the retained publication.
            if doc['public_updated_at'][:10] >= baseline['published']:
                paths.add(doc['base_path'])
    if not any(re.fullmatch(source['release_path_pattern'], d['base_path']) for d in documents):
        raise ValueError('Collection no longer contains this release family')
    updates = []
    for path in sorted(paths):
        meta_url = 'https://www.gov.uk/api/content' + path
        meta = json.loads(get(meta_url))
        published = meta['first_published_at'][:10]
        updated = meta['public_updated_at'][:10]
        if path != baseline['release_url'].removeprefix('https://www.gov.uk') and published < baseline['published']:
            continue
        matches = [a for a in meta['details']['attachments'] if a['title'] == source['attachment_title']]
        if len(matches) != 1:
            raise ValueError('Expected exactly one data attachment at ' + meta_url)
        attachment = matches[0]['url']
        sha = digest(get(attachment))
        release = 'https://www.gov.uk' + path
        if (release, updated, sha) == (baseline['release_url'], baseline['date'], baseline['sha256']):
            continue
        evidence = dict(source=source['id'], release_url=release, published=published,
                        updated=updated, attachment_url=attachment, sha256=sha,
                        metadata_url=meta_url, collection_url=source['collection_api'])
        key = digest(json.dumps(evidence, sort_keys=True).encode())
        updates.append(dict(key=key, evidence=evidence, baseline=baseline))
    return updates


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True).strip()


def open_updates(updates, repo, run=gh):
    # All states, all pages: closing an issue is also a recorded review decision.
    pages = json.loads(run('api', '--paginate', '--slurp', f'repos/{repo}/issues?state=all&per_page=100'))
    bodies = '\n'.join(issue.get('body') or '' for page in pages for issue in page if 'pull_request' not in issue)
    results = []
    for update in updates:
        marker = '<!-- source-release:' + update['key'] + ' -->'
        if marker in bodies:
            results.append(dict(key=update['key'], status='already reported'))
            continue
        e = update['evidence']; b = update['baseline']
        slug = e['release_url'].rsplit('/', 1)[-1]
        retained = e.get('discovery_scope') == 'retained-url-revision'
        scope = ('Only the retained URL was checked for a revision. This does not discover new '
                 'publication URLs, newly published plans, or a later roster date.' if retained else
                 'Collection links and the retained release were checked for releases and revisions.')
        command = (e['refresh_command'] if retained else
                   f'.venv/bin/python scripts/build.py --refresh --release {slug}')
        body = f'''{NOTICE}

A source release or revision needs a data update review. Deployed data have NOT changed.
{scope}

## Discovered source evidence
```json
{json.dumps(e, indent=2)}
```

## Retained baseline
Release: {b.get('release_url', b.get('url'))}
Source updated/downloaded: {b.get('date', b.get('downloaded', 'not supplied'))}
SHA-256: `{b['sha256']}`

Review the official publication and accounting scope, then refresh with:
```sh
{command}
```
Inspect the changed-file report and source/data diff, run all documented checks,
and submit the validated update in a PR. A changed format must not bypass validation.
Retained-URL checks cannot establish whether a newer publication exists elsewhere.

{marker}
'''
        url = run('issue', 'create', '--repo', repo, '--title',
                  f"[Source update] {e['source']}: {slug} ({e['updated']}, {e['sha256'][:12]})",
                  '--body', body)
        bodies += '\n' + marker
        results.append(dict(key=update['key'], status='opened', url=url))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--open-issues', action='store_true')
    parser.add_argument('--repo', default=os.environ.get('GITHUB_REPOSITORY'))
    parser.add_argument('--report', type=Path, default=Path('discovery-report.json'))
    args = parser.parse_args()
    if args.open_issues and not args.repo:
        parser.error('--repo or GITHUB_REPOSITORY is required')
    report = dict(checked_at=datetime.now(timezone.utc).isoformat(), sources=[], errors=[])
    try:
        inventory = json.loads((ROOT / 'config/release-sources.json').read_text())
        if not isinstance(inventory, list) or not inventory:
            raise ValueError('Source inventory must be a nonempty list')
    except Exception as exc:
        inventory = []
        report['errors'].append(dict(source='inventory', error=str(exc)))
    for source in inventory:
        source_id = source.get('id', 'unknown') if isinstance(source, dict) else 'unknown'
        try:
            updates = discover(source)
            scope = ('retained-url-revision' if source['adapter'] == 'retained-url-snapshot'
                     else 'collection-releases-and-revisions')
            result = dict(id=source_id, discovery_scope=scope, updates=updates, issues=[])
            report['sources'].append(result)
            if args.open_issues and updates:
                result['issues'] = open_updates(updates, args.repo)
        except Exception as exc:
            report['errors'].append(dict(source=source_id, error=str(exc)))
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
