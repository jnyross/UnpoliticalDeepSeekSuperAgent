"""Review-only discovery of links in a precisely bounded official publication listing.

This does not fetch plan content, identify costings, revise a historical manifesto,
advance a roster, or decide whether a paper belongs in the site's data. The baseline
is an explicit retained JSON listing, not the site's historical source manifest.
"""
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit, urlunsplit


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _allowed(url, hosts):
    parts = urlsplit(url)
    return (parts.scheme == 'https' and parts.hostname in hosts and
            parts.port in (None, 443) and not parts.username and not parts.password)


def _settings(source):
    hosts = source.get('listing_allowed_hosts', source['allowed_hosts'])
    if (not isinstance(hosts, list) or not hosts or
            any(not isinstance(h, str) or not re.fullmatch(r'[a-z0-9.-]+', h) for h in hosts)):
        raise ValueError('Expected explicit official allowed_hosts')
    if not _allowed(source['listing_url'], hosts):
        raise ValueError('Not an allowed official listing URL')
    if 'container_tag' in source:
        if source['container_tag'] not in ('main', 'section', 'div', 'article', 'ul'):
            raise ValueError('Invalid publication container tag')
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', source.get('container_class', '')):
            raise ValueError('Expected explicit publication container class')
        if 'section_id' in source or 'section_end_id' in source:
            raise ValueError('Choose one publication boundary strategy')
    else:
        for field in ('section_id', 'section_end_id'):
            if not isinstance(source[field], str) or not source[field]:
                raise ValueError('Missing listing selector: ' + field)
        if source['section_id'] == source['section_end_id']:
            raise ValueError('Listing section boundaries must differ')
    if 'link_parent_tag' in source:
        if source['link_parent_tag'] not in ('h2', 'h3', 'h4', 'h5') or not re.fullmatch(
                r'[a-zA-Z0-9_-]+', source.get('link_parent_class', '')):
            raise ValueError('Invalid publication title selector')
    if 'link_title_label' in source and (not isinstance(source['link_title_label'], str)
                                           or not source['link_title_label'].strip()):
        raise ValueError('Invalid explicit untitled-link label')
    if not isinstance(source['link_path_pattern'], str) or not source['link_path_pattern']:
        raise ValueError('Missing link path pattern')
    if source.get('listing_scope', 'official-policy-listing-review') not in (
            'official-policy-listing-review', 'official-publication-listing-review'):
        raise ValueError('Unknown publication listing scope')
    re.compile(source['link_path_pattern'])


def _link(source, href, title):
    url = urljoin(source['listing_url'], href)
    parts = urlsplit(url)
    if not re.fullmatch(source['link_path_pattern'], parts.path):
        return None
    if not _allowed(url, source.get('listing_allowed_hosts', source['allowed_hosts'])):
        raise ValueError('Policy link outside allowed official hosts: ' + url)
    # These explicitly path-selected publication links have no query identity.
    # Ignore fragments/tracking queries and whitespace-only presentation changes.
    url = urlunsplit((parts.scheme, parts.netloc, parts.path, '', ''))
    title = source.get('link_title_label', ' '.join(title.split()))
    if not title:
        raise ValueError('Policy link has no readable title')
    return dict(url=url, title=title)


class PolicyListing(HTMLParser):
    """Read links between two publisher-provided ID markers (not a guessed CSS region)."""
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.started = self.ended = False
        self.links = []
        self.href = None
        self.title = []
        self.ignored = 0
        self.container_depth = 0
        self.in_title_region = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        marker = attrs.get('id')
        if 'container_tag' in self.source:
            if tag == self.source['container_tag']:
                selected = self.source['container_class'] in attrs.get('class', '').split()
                if selected:
                    if self.started:
                        raise ValueError('Duplicate publication listing container')
                    self.started = True
                    self.container_depth = 1
                elif self.started and not self.ended:
                    self.container_depth += 1
        else:
            if marker == self.source['section_id']:
                if self.started:
                    raise ValueError('Duplicate policy listing start marker')
                self.started = True
            if marker == self.source['section_end_id']:
                if self.ended or not self.started:
                    raise ValueError('Invalid policy listing end marker')
                if self.href is not None:
                    raise ValueError('Unclosed policy listing link')
                self.ended = True
        if not self.started or self.ended:
            return
        if tag in ('script', 'style'):
            self.ignored += 1
        if tag == self.source.get('link_parent_tag'):
            self.in_title_region = self.source['link_parent_class'] in attrs.get('class', '').split()
        if tag == 'a' and not self.ignored and (not self.source.get('link_parent_tag') or self.in_title_region):
            if self.href is not None:
                raise ValueError('Nested policy listing links')
            self.href = attrs.get('href')
            self.title = []
        elif self.href is not None:
            self.title.append(' ')

    def handle_endtag(self, tag):
        if not self.started or self.ended:
            return
        if tag == self.source.get('container_tag'):
            self.container_depth -= 1
            if self.container_depth == 0:
                if self.href is not None:
                    raise ValueError('Unclosed publication listing link')
                self.ended = True
                return
        if tag == self.source.get('link_parent_tag'):
            self.in_title_region = False
        if tag in ('script', 'style'):
            self.ignored = max(0, self.ignored - 1)
        if tag == 'a' and self.href is not None:
            link = _link(self.source, self.href, ''.join(self.title))
            if link:
                self.links.append(link)
            self.href = None
        elif self.href is not None:
            self.title.append(' ')

    def handle_data(self, data):
        if self.href is not None and not self.ignored:
            self.title.append(data)


def _unique(links):
    by_url = {}
    for link in links:
        if link['url'] in by_url and by_url[link['url']] != link['title']:
            raise ValueError('Conflicting titles for policy listing URL')
        by_url[link['url']] = link['title']
    if not by_url:
        raise ValueError('No matching policy links in selected listing section')
    return [dict(url=url, title=by_url[url]) for url in sorted(by_url)]


def listing_bytes(links):
    """Canonical semantic listing fingerprint: order/duplicates/HTML do not matter."""
    return (json.dumps(dict(links=_unique(links)), ensure_ascii=False,
                       sort_keys=True, indent=2) + '\n').encode('utf-8')


def parse_listing(source, raw):
    _settings(source)
    page = PolicyListing(source)
    page.feed(raw.decode('utf-8'))
    page.close()
    if not page.started or not page.ended:
        raise ValueError('Missing verified policy listing section boundary')
    return _unique(page.links)


def discover_listing(source, root, get=None):
    """Return new/title-changed link candidates; fail closed on baseline/parser errors.

    Required source fields: id, listing_url, allowed_hosts, section_id,
    section_end_id, link_path_pattern, listing_baseline={file,sha256}.
    Inject get(url) for offline tests; live requests use discover.fetch with the
    explicit host allowlist (including its redirect guard).
    """
    _settings(source)
    baseline = source['listing_baseline']
    retained = (Path(root) / baseline['file']).read_bytes()
    if _digest(retained) != baseline['sha256']:
        raise ValueError('Retained listing does not match baseline hash')
    document = json.loads(retained)
    if not isinstance(document, dict) or set(document) != {'links'} or not isinstance(document['links'], list):
        raise ValueError('Expected retained listing JSON with links array')
    old = []
    for entry in document['links']:
        if (not isinstance(entry, dict) or set(entry) != {'url', 'title'} or
                not all(isinstance(entry[k], str) for k in ('url', 'title'))):
            raise ValueError('Invalid retained policy listing entry')
        link = _link(source, entry['url'], entry['title'])
        if not link or link != entry:
            raise ValueError('Noncanonical retained policy listing entry')
        old.append(link)
    old = _unique(old)
    if get is None:
        # Import lazily to avoid a circular import with discover's adapter dispatcher.
        import discover
        raw = discover.fetch(source['listing_url'], hosts=source.get('listing_allowed_hosts', source['allowed_hosts']))
    else:
        raw = get(source['listing_url'])
    current = parse_listing(source, raw)
    semantic_sha = _digest(listing_bytes(current))
    old_by_url = {row['url']: row['title'] for row in old}
    updates = []
    for link in current:
        if old_by_url.get(link['url']) == link['title']:
            continue
        evidence = dict(source=source['id'], release_url=link['url'],
                        attachment_url=link['url'], title=link['title'],
                        listing_url=source['listing_url'], listing_sha256=semantic_sha,
                        sha256=semantic_sha, response_sha256=_digest(raw),
                        hash_scope='canonical-listing-links-and-labels-not-document-bytes',
                        discovery_scope=source.get('listing_scope', 'official-policy-listing-review'),
                        change='title-changed' if link['url'] in old_by_url else 'new-link',
                        updated='not supplied by retained URL', review_only=True,
                        review_note='Listing evidence only; not a revision of the retained historical source. '
                                    'Review scope, publication date, content and coverage before any data update.',
                        refresh_command='# Review publication and retain approved evidence; do not auto-refresh historical snapshots')
        identity = dict(source=source['id'], url=link['url'], title=link['title'])
        key = _digest(json.dumps(identity, sort_keys=True).encode())
        updates.append(dict(key=key, evidence=evidence,
                            baseline=dict(url=source['listing_url'], sha256=baseline['sha256'],
                                          file=baseline['file'])))
    return updates
