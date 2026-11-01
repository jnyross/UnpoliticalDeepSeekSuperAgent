#!/usr/bin/env python3
"""Read-only official release discovery; only --open-issues writes (GitHub issues)."""
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

ROOT = Path(__file__).resolve().parents[1]
NOTICE = 'This is by an automated agent, not a human.'


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.startswith(('https://www.gov.uk/', 'https://assets.publishing.service.gov.uk/')):
            raise ValueError('Redirected outside official hosts')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url):
    if not url.startswith(('https://www.gov.uk/', 'https://assets.publishing.service.gov.uk/')):
        raise ValueError('Not an allowed official URL: ' + url)
    with urllib.request.build_opener(OfficialRedirect()).open(url, timeout=60) as response:
        if not response.url.startswith(('https://www.gov.uk/', 'https://assets.publishing.service.gov.uk/')):
            raise ValueError('Redirected outside official hosts')
        return response.read()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def discover(source, root=ROOT, get=fetch):
    """Collection links discover new slugs; the retained release is also checked for revisions."""
    baseline = json.loads((root / source['manifest']).read_text())
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
        title_pattern = source.get('attachment_title_pattern')
        matches = [a for a in meta['details']['attachments']
                   if (re.fullmatch(title_pattern, a['title']) if title_pattern
                       else a['title'] == source['attachment_title'])]
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
        body = f'''{NOTICE}

A source release or revision needs a data update review. Deployed data have NOT changed.

## Discovered official evidence
```json
{json.dumps(e, indent=2)}
```

## Retained baseline
Release: {b['release_url']}
Source updated: {b['date']}
SHA-256: `{b['sha256']}`

Review the official publication and accounting scope, then refresh with:
```sh
.venv/bin/python scripts/build.py --refresh --release {slug}
```
Inspect the changed-file report and source/data diff, run all documented checks,
and submit the validated update in a PR. A changed format must not bypass validation.
The command above is the spending adapter; future families must document their own refresh command.

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
            if source['adapter'] != 'govuk-collection-attachment':
                raise ValueError('Unknown adapter: ' + source['adapter'])
            updates = discover(source)
            result = dict(id=source_id, updates=updates, issues=[])
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
