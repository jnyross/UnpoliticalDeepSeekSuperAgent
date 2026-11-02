"""Inventory preparation only; never executes or certifies a manual accessibility check."""
import argparse
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'docs/evidence/access/manual/inventory.json'
VERSION = 1
VIEWPORTS = ['360x800', '1280x900']


class Node:
    def __init__(self, tag, attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []

    def text(self):
        return ' '.join(''.join(c if isinstance(c, str) else c.text() for c in self.children).split())

    def descendants(self, tag):
        for child in self.children:
            if isinstance(child, Node):
                if child.tag == tag:
                    yield child
                yield from child.descendants(tag)


class Document(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = self.current = Node('document')
        self.nodes = []
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        self.nodes.append(node)
        if tag not in self.VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        node = self.current
        while node.parent:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def inventory(site):
    pages = []
    for path in sorted(site.rglob('*.html')):
        data = path.read_bytes()
        doc = Document(data.decode('utf-8'))
        targets, counts = [], {}
        for node in doc.nodes:
            kind = None
            if node.tag == 'details':
                kind = 'disclosure'
            elif 'aria-expanded' in node.attrs:
                kind = 'expanded-control'
            elif node.tag == 'table':
                kind = 'table'
            elif node.tag == 'svg':
                kind = 'chart'
            elif node.tag == 'a' and re.search(r'(^|/)history-(cash|real|gdp)\.html(?:#|$)', node.attrs.get('href', '')):
                kind = 'view-link'
            if not kind:
                continue
            counts[node.tag] = counts.get(node.tag, 0) + 1
            target_id = f'{node.tag}:{counts[node.tag]}'
            # Ordinal is among inventoried elements of the same tag, not a CSS index.
            label = node.attrs.get('aria-label') or node.text()
            for label_tag in ('summary', 'caption'):
                children = list(node.descendants(label_tag))
                if children:
                    label = children[0].text()
                    break
            if kind == 'chart' and node.parent:
                captions = list(node.parent.descendants('figcaption'))
                label = captions[0].text() if captions else label
            target = {'id': target_id, 'kind': kind, 'label': label[:240],
                      'tasks': ['disclosure' if kind == 'expanded-control' else kind]}
            if 'id' in node.attrs:
                target['anchor'] = node.attrs['id']
            if kind == 'view-link':
                target['href'] = node.attrs['href']
            if kind in ('disclosure', 'expanded-control'):
                target['initial'] = ('expanded' if 'open' in node.attrs else 'collapsed') if kind == 'disclosure' else node.attrs['aria-expanded']
            targets.append(target)
        states = ['initial']
        if any(t['kind'] == 'disclosure' for t in targets):
            states.append('all-details-expanded')
        states += [f"expanded-{t['id']}" for t in targets if t['kind'] == 'expanded-control']
        pages.append({'path': path.relative_to(site).as_posix(), 'sha256': sha256(data).hexdigest(),
                      'states': states, 'tasks': ['navigation', 'structure', 'focus'], 'targets': targets})
    if not pages:
        raise ValueError('No generated HTML pages found')
    return {'protocol_version': VERSION, 'viewports': VIEWPORTS, 'pages': pages}


def validate(site, saved):
    expected = inventory(site)
    if saved != expected:
        raise ValueError('Manual task inventory is stale: review protocols, then run python3 scripts/manual_access.py --write')
    return expected


def blank_records(manifest):
    rows = []
    for page in manifest['pages']:
        for viewport in manifest['viewports']:
            for mode in ('keyboard', 'screen-reader'):
                for state in page['states']:
                    for target in [{'id': 'page', 'tasks': page['tasks']}] + page['targets']:
                        for task in target['tasks']:
                            rows.append({'page': page['path'], 'html_sha256': page['sha256'],
                                         'viewport': viewport, 'mode': mode, 'state': state,
                                         'target': target['id'], 'task': task,
                                         'outcome': 'unperformed', 'observations': '', 'finding_ids': []})
    return {'protocol_version': VERSION, 'status': 'unperformed',
            'environment': {key: '' for key in ('tested_revision', 'base_url', 'date_time_timezone',
                           'tester_reference', 'browser_version', 'os_version', 'assistive_technology_version',
                           'keyboard_settings', 'zoom', 'theme', 'javascript', 'deployment_identity_evidence')},
            'results': rows, 'findings': []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, default=ROOT / 'site')
    parser.add_argument('--inventory', type=Path, default=INVENTORY)
    parser.add_argument('--write', action='store_true', help='Refresh inventory after protocol review (not test results)')
    parser.add_argument('--records', type=Path, help='Create new, unperformed records; never overwrite a record')
    args = parser.parse_args()
    if args.write:
        manifest = inventory(args.site)
        args.inventory.parent.mkdir(parents=True, exist_ok=True)
        args.inventory.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    else:
        manifest = validate(args.site, json.loads(args.inventory.read_text()))
    if args.records:
        with args.records.open('x') as stream:
            json.dump(blank_records(manifest), stream, indent=2, ensure_ascii=False)
            stream.write('\n')
    print(f"Manual materials inventory valid: {len(manifest['pages'])} pages; no manual checks performed.")


if __name__ == '__main__':
    main()
