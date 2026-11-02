#!/usr/bin/env python3
"""Release/revision checks; opt in to issue creation or persistent revision notices.

Collection and latest-page adapters discover new release links. Retained-URL snapshots only detect
revisions at inventory URLs, including explicitly identified archive-hosted copies;
they cannot discover new manifesto URLs or advance a historical roster's date.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
from urllib.parse import urlsplit, urljoin, urlunsplit, parse_qsl, urlencode

ROOT = Path(__file__).resolve().parents[1]
NOTICE = 'This is by an automated agent, not a human.'
DEFAULT_RECEIPTS = ROOT / '.discovery-issue-receipts.json'


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
    request = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.9'})
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
        collection = source.get('source_collection', 'sources')
        if collection not in ('sources', 'evidence_sources'):
            raise ValueError('Unknown source collection: ' + collection)
        matches = [s for s in manifest[collection] if s['id'] == source['source_id']]
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


class DatabankPage(HTMLParser):
    """Extract download links and readable text without depending on WP CSS classes."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.text = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href')
            if href:
                self.links.append((href, len(self.text)))
        self.text += ' '

    def handle_data(self, data):
        self.text += data


def canonical_download(url):
    # OBR adds a per-request cache-busting timestamp, not a release identifier.
    parts = urlsplit(url)
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if k != 'tmstv'])
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ''))


def discover_obr(source, root, get=None):
    """Follow the latest databank link, and also check the retained workbook for edits."""
    baseline = source_baseline(source, root)
    hosts = ('obr.uk', 'www.obr.uk')

    def checked_get(url):
        if not allowed_url(url, hosts):
            raise ValueError('Not an allowed official URL: ' + url)
        return fetch(url, hosts=hosts) if get is None else get(url)

    page_url = source['page_url']
    page = DatabankPage()
    page.feed(checked_get(page_url).decode('utf-8'))
    matches = {}
    for href, offset in page.links:
        url = canonical_download(urljoin(page_url, href))
        if re.fullmatch(source['download_path_pattern'], urlsplit(url).path):
            if not allowed_url(url, hosts):
                raise ValueError('Not an allowed official URL: ' + url)
            matches.setdefault(url, []).append(offset)
    if len(matches) != 1:
        raise ValueError('Expected exactly one latest OBR databank download')
    latest, offsets = next(iter(matches.items()))
    # The publisher displays the release date after the duplicated icon/title links.
    start = max(offsets)
    end = min((offset for _, offset in page.links if offset > start), default=len(page.text))
    text = ' '.join(page.text[start:end].split())
    date_match = re.search(r'\b([0-9]{1,2} [A-Za-z]+ [0-9]{4})\b', text[:600])
    if not date_match:
        raise ValueError('Missing OBR databank publication date')
    published = datetime.strptime(date_match[1], '%d %B %Y').date().isoformat()
    retained_download = canonical_download(baseline['download_url'])
    candidates = [(latest, latest, published)]
    if latest != retained_download:
        # The latest-page pointer can move while an earlier retained release is revised.
        candidates.append((retained_download, baseline['url'], baseline['date']))
    updates = []
    for download, attachment, updated in candidates:
        sha = digest(checked_get(attachment))
        if (download, updated, sha) == (retained_download, baseline['date'], baseline['sha256']):
            continue
        evidence = dict(source=source['id'], release_url=page_url,
                        published=published if download == latest else baseline['published'],
                        updated=updated, attachment_url=attachment, download_url=download,
                        sha256=sha, metadata_url=page_url,
                        discovery_scope='latest-page-releases-and-revisions',
                        refresh_command='python3 scripts/build.py --refresh')
        key = digest(json.dumps(evidence, sort_keys=True).encode())
        updates.append(dict(key=key, evidence=evidence, baseline=baseline))
    return updates


def discover_current_roster(source, root, get=None, as_of=None):
    """Compare today's official Commons composition with the dated retained roster.

    This is a newer snapshot candidate, NOT a revision of the historical snapshot.
    The semantic identity deliberately excludes polling dates and API timestamps.
    """
    baseline = source_baseline(source, root)
    snapshot = root / baseline['file']
    if len(Path(baseline['file']).parts) == 1:
        snapshot = (root / source['manifest']).parent / baseline['file']
    retained = snapshot.read_bytes()
    if digest(retained) != baseline['sha256']:
        raise ValueError('Retained snapshot does not match manifest hash')
    as_of = as_of or datetime.now(timezone.utc).date().isoformat()
    # Validate before interpolating into the fixed official API endpoint.
    datetime.strptime(as_of, '%Y-%m-%d')
    url = 'https://members-api.parliament.uk/api/Parties/StateOfTheParties/1/' + as_of
    raw = (fetch(url, hosts=['members-api.parliament.uk']) if get is None else get(url))
    semantic_sha = digest(roster_semantics(raw))
    if semantic_sha == digest(roster_semantics(retained)):
        return []
    evidence = dict(source=source['id'], release_url=url, attachment_url=url,
                    sha256=digest(raw), semantic_sha256=semantic_sha,
                    discovery_scope='current-roster-comparison', as_of=as_of,
                    updated=as_of,
                    refresh_command='python3 scripts/build.py --refresh')
    key = digest(json.dumps(dict(source=source['id'], semantic_sha256=semantic_sha),
                            sort_keys=True).encode())
    return [dict(key=key, evidence=evidence, baseline=baseline)]


def discover(source, root=ROOT, get=None):
    """Dispatch explicit discovery scopes, including dynamic official latest-page links."""
    if source['adapter'] == 'retained-url-and-policy-listing':
        try:
            from scripts.plan_discovery import discover_listing
        except ModuleNotFoundError:  # Direct `python scripts/discover.py` execution.
            from plan_discovery import discover_listing
        return discover_snapshot(source, root, get) + discover_listing(
            source, root, get or (lambda url: fetch(url, hosts=source['allowed_hosts'])))
    if source['adapter'] == 'parliament-current-roster':
        # Retain the old snapshot revision check as well as checking today's composition.
        return discover_snapshot(source, root, get) + discover_current_roster(source, root, get)
    if source['adapter'] == 'retained-url-snapshot':
        return discover_snapshot(source, root, get)
    if source['adapter'] == 'obr-databank-latest':
        return discover_obr(source, root, get)
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


def open_updates(updates, repo, run=gh, receipt_path=None):
    try:
        from scripts.issue_delivery import IssueReceipts
    except ModuleNotFoundError:
        from issue_delivery import IssueReceipts
    with IssueReceipts(receipt_path or DEFAULT_RECEIPTS, repo) as receipts:
        return _open_updates(updates, repo, run, receipts)


def _open_updates(updates, repo, run, receipts):
    # All states, all pages: closing an issue is also a recorded review decision.
    # Request revalidation after writes; this cannot make the remote list/create atomic.
    pages = json.loads(run('api', '--paginate', '--slurp', '-H', 'Cache-Control: no-cache',
                           f'repos/{repo}/issues?state=all&per_page=100'))
    bodies = '\n'.join(issue.get('body') or '' for page in pages for issue in page if 'pull_request' not in issue)
    results = []
    for update in updates:
        marker = '<!-- source-release:' + update['key'] + ' -->'
        if marker in bodies:
            receipts.reported(update['key'])
            results.append(dict(key=update['key'], status='already reported'))
            continue
        receipt = receipts.entries.get(update['key'])
        if receipt:
            if receipt['status'] in ('created', 'reported'):
                results.append(dict(key=update['key'], status='already reported'))
                continue
            raise RuntimeError('Issue delivery uncertain for ' + update['key'] +
                               '; refusing another create until its remote marker is visible or '
                               'the failed attempt is verified not to have created an issue')
        e = update['evidence']; b = update['baseline']
        slug = e.get('download_url', e['release_url']).rstrip('/').rsplit('/', 1)[-1]
        retained = e.get('discovery_scope') == 'retained-url-revision'
        scope = ('Only the retained URL was checked for a revision. This does not discover new '
                 'publication URLs, newly published plans, or a later roster date.' if retained else
                 'Collection links and the retained release were checked for releases and revisions.')
        if e.get('discovery_scope') == 'latest-page-releases-and-revisions':
            scope = 'The official latest databank page and retained workbook were checked for releases and revisions.'
        if e.get('discovery_scope') == 'official-policy-listing-review':
            scope = ('The official adopted-policy listing contains a new or retitled link. '
                     'This is listing evidence only, NOT a revision of the historical manifesto. '
                     'Review adoption, dates, content, costings and site coverage before any update.')
        if e.get('discovery_scope') == 'current-roster-comparison':
            scope = ("Today's official Commons party/seat snapshot differs from the retained historical "
                     "roster. This is NOT a revision of that historical snapshot. Review party coverage "
                     "and retain a new dated roster plus matching plan evidence before changing the site. "
                     "The refresh command alone does not advance the pinned historical roster.")
        command = (e['refresh_command'] if 'refresh_command' in e else
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
        receipts.reserve(update['key'])
        url = run('issue', 'create', '--repo', repo, '--title',
                  f"[Source update] {e['source']}: {slug} ({e['updated']}, {e['sha256'][:12]})",
                  '--body', body)
        if not re.fullmatch(r'https://github\.com/' + re.escape(repo) + r'/issues/[1-9][0-9]*', url, flags=re.IGNORECASE):
            raise ValueError('Unexpected issue creation response; pending delivery receipt retained')
        receipts.created(update['key'], url)
        bodies += '\n' + marker
        results.append(dict(key=update['key'], status='opened', url=url))
    return results


def load_revision_status(path):
    """Missing state starts empty; malformed state must never erase known notices."""
    if not path.exists():
        return dict(schema_version=1, notices=[])
    state = json.loads(path.read_text())
    if (not isinstance(state, dict) or state.get('schema_version') != 1 or
            not isinstance(state.get('notices'), list)):
        raise ValueError('Invalid revision status schema')
    for notice in state['notices']:
        if (not isinstance(notice, dict) or
                not all(k in notice for k in ('source', 'baseline_sha256', 'baseline_url',
                                               'key', 'first_detected_at', 'evidence')) or
                not isinstance(notice['evidence'], dict) or
                not all(k in notice['evidence'] for k in ('sha256', 'release_url'))):
            raise ValueError('Invalid revision notice')
    return state


def reconcile_revision_status(state, inventory, results, root=ROOT, checked_at=None):
    """Return durable notices, without modifying state, manifests or source bytes.

    A failed/unchanged lookup is not evidence that a known revision was incorporated.
    Only the exact observed revision hash at its release URL resolves a notice.
    Date-only revisions additionally require the recorded publisher update date.
    Build integration can pass results=[] after refreshing its staged manifests.
    """
    checked_at = checked_at or datetime.now(timezone.utc).isoformat()
    baselines = {}
    for source in inventory:
        try:
            baselines[source['id']] = source_baseline(source, root)
        except (OSError, ValueError, KeyError, TypeError):
            # A broken/unavailable manifest cannot prove resolution either.
            continue

    def incorporated(notice):
        baseline = baselines.get(notice['source'], {})
        evidence = notice['evidence']
        if (baseline.get('sha256') != evidence['sha256'] or
                baseline.get('release_url', baseline.get('url')) != evidence['release_url']):
            return False
        if evidence['sha256'] == notice['baseline_sha256']:
            return baseline.get('date') == evidence.get('updated')
        return True

    notices = { (n['source'], n['baseline_sha256'], n['key']): dict(n)
                for n in state['notices'] if not incorporated(n) }
    for result in results or []:
        for update in result['updates']:
            # A later roster does not mean the explicitly historical roster was revised.
            # Keep the review issue, but never publish a false historical-revision warning.
            if update['evidence'].get('discovery_scope') in (
                    'current-roster-comparison', 'official-policy-listing-review'):
                continue
            baseline = update['baseline']
            notice = dict(source=result['id'], baseline_sha256=baseline['sha256'],
                          baseline_url=baseline.get('release_url', baseline.get('url')),
                          key=update['key'], first_detected_at=checked_at,
                          evidence=dict(update['evidence']))
            identity = (notice['source'], notice['baseline_sha256'], notice['key'])
            if not incorporated(notice):
                notices.setdefault(identity, notice)
    return dict(schema_version=1, notices=[notices[k] for k in sorted(notices)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--open-issues', action='store_true')
    parser.add_argument('--repo', default=os.environ.get('GITHUB_REPOSITORY'))
    parser.add_argument('--report', type=Path, default=Path('discovery-report.json'))
    parser.add_argument('--write-revision-status', action='store_true',
                        help='Persist unresolved notices in sources/revision-status.json')
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
            scope = {'retained-url-and-policy-listing': 'official-policy-listing-and-retained-revisions',
                     'parliament-current-roster': 'current-roster-and-retained-revisions',
                     'retained-url-snapshot': 'retained-url-revision',
                     'obr-databank-latest': 'latest-page-releases-and-revisions'}.get(
                         source['adapter'], 'collection-releases-and-revisions')
            result = dict(id=source_id, discovery_scope=scope, updates=updates, issues=[])
            report['sources'].append(result)
            if args.open_issues and updates:
                result['issues'] = open_updates(updates, args.repo)
        except Exception as exc:
            report['errors'].append(dict(source=source_id, error=str(exc)))
    try:
        status_path = ROOT / 'sources/revision-status.json'
        state = load_revision_status(status_path)
        report['revision_status'] = reconcile_revision_status(
            state, inventory, report['sources'], root=ROOT, checked_at=report['checked_at'])
        if args.write_revision_status:
            status_path.parent.mkdir(parents=True, exist_ok=True)
            # Replace only after complete serialization; interrupted writes keep last good state.
            # Keep temporary bytes outside sources/, which the static build copies verbatim.
            pending = ROOT / '.revision-status.json.tmp'
            pending.write_text(json.dumps(report['revision_status'], indent=2) + '\n')
            pending.replace(status_path)
    except Exception as exc:
        report['errors'].append(dict(source='revision-status', error=str(exc)))
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
