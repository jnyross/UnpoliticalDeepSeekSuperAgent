"""Equal-format historical party offers, checked against retained party PDFs and Commons API."""
import hashlib
from html.parser import HTMLParser
import html
import json
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.request
from datetime import datetime, timezone


def extract_html(raw):
    """Visible text blocks; rerun on retained HTML, never trust its transcript alone."""
    class Blocks(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.hidden = 0; self.parts = []; self.lines = []
        def flush(self):
            text = ' '.join(' '.join(self.parts).split())
            if text: self.lines.append(text)
            self.parts = []
        def handle_starttag(self, tag, attrs):
            if tag in ('script', 'style'): self.hidden += 1
            if tag in ('p', 'h1', 'h2', 'h3', 'li', 'div', 'br'): self.flush()
        def handle_endtag(self, tag):
            if tag in ('script', 'style'): self.hidden -= 1
            if tag in ('p', 'h1', 'h2', 'h3', 'li', 'div'): self.flush()
        def handle_data(self, data):
            if not self.hidden: self.parts.append(data)
    parser = Blocks(); parser.feed(raw); parser.flush()
    return '\n'.join(parser.lines) + '\n'

LIMITS = {'offer': 45, 'excerpt': 85, 'scope': 30, 'baseline': 30, 'year': 25,
          'status': 25, 'costing': 30, 'assessment': 30}
FIELDS = [('offer', 'Selected official offer'), ('excerpt', 'Party source excerpt'),
          ('scope', 'Scope'), ('baseline', 'Baseline'), ('year', 'Year'),
          ('status', 'Status'), ('costing', 'Costing'), ('assessment', 'Independent assessment')]

def normal(text):
    # Only typographic equivalents: never discard punctuation, digits or word boundaries.
    ligatures = str.maketrans({'ﬀ': 'ff', 'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬃ': 'ffi',
                              'ﬄ': 'ffl', 'ﬅ': 'st', 'ﬆ': 'st'})
    return ' '.join(text.translate(ligatures).replace('\u00ad', '').split())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(root):
    return json.loads((Path(root) / 'sources/party-offers.json').read_text())

def validate(root):
    """Fail closed on changed files, omitted parties, unequal fields or unsupported quotes."""
    root = Path(root); d = load(root); base = root / 'sources'
    assert d['schema_version'] == 1
    roster = d['roster']
    assert roster == json.loads((base / 'commons-roster-metadata.json').read_text()), 'Roster metadata differs'
    assert digest(base / roster['file']) == roster['sha256'], 'Roster hash changed'
    raw = json.loads((base / roster['file']).read_text())
    entries = {i['value']['party']['id']: i['value'] for i in raw['items'] if i['value']['total'] > 0}
    excluded = {d['independents']['id'], d['speaker']['id']}
    assert len(entries) == len(raw['items']), 'Duplicate roster ID'
    assert {p['id'] for p in d['parties']} == set(entries) - excluded, 'Party coverage differs from roster'
    assert len(d['parties']) == len({p['id'] for p in d['parties']}), 'Duplicate party'
    assert [p['name'] for p in d['parties']] == sorted((p['name'] for p in d['parties']), key=str.casefold), 'Party order'
    for p in d['parties'] + [d['independents'], d['speaker']]:
        assert p['name'] == entries[p['id']]['party']['name'], 'Roster name mismatch'
        assert p['seats'] == entries[p['id']]['total'], 'Roster count mismatch'
    sources = {s['id']: s for s in d['sources']}
    assert len(sources) == len(d['sources']) == len(d['parties'])
    extra = d.get('evidence_sources', [])
    all_sources = {s['id']: s for s in d['sources'] + extra}
    assert len(all_sources) == len(d['sources']) + len(extra), 'Duplicate source ID'
    for s in extra:
        assert s['kind'] in ('official', 'independent')
        if s['kind'] == 'independent':
            assert s['publisher'] in ('IFS', 'OBR', 'Resolution Foundation', 'Full Fact', 'NAO')
        assert s['text_mode'] == 'html-blocks-v1'
    for s in all_sources.values():
        assert len(s['publication'].split()) <= 35 and len(s['hosting'].split()) <= 30, 'Source label too long'
        assert len(s['url']) <= 2000, 'Source URL too long'
        for name, h in [('file','sha256'), ('text_file','text_sha256')]:
            assert Path(s[name]).name == s[name], 'Source must be flat'
            assert digest(base / s[name]) == s[h], 'Source hash changed: ' + s[name]
    expected_keys = {'id','name','seats','source_id','locator','pdf_page', *LIMITS}
    for p in d['parties']:
        assert len(p['name'].split()) <= 15 and len(p['locator'].split()) <= 15, 'Party/source label too long'
        assert set(p) - {'evidence'} == expected_keys, 'Party fields differ'
        evidence = p.get('evidence', {})
        assert set(evidence) <= {'costing', 'assessment'}, 'Unknown evidence field'
        for field, ref in evidence.items():
            s = all_sources[ref['source_id']]
            independent = s.get('kind') == 'independent'
            assert set(ref) == {'source_id', 'quote', 'locator', ('pdf_page' if 'pdf_page' in ref else 'text_line')} | ({'attribution'} if field == 'assessment' or independent else set()), 'Evidence fields differ'
            assert 0 < len(ref['quote'].split()) <= LIMITS[field], 'Evidence quote too long'
            assert 0 < len(ref['locator'].split()) <= 15, 'Evidence locator too long'
            if field == 'assessment':
                assert s.get('kind') == 'independent', 'Assessment must be independent'
                assert p[field] == ref['quote'], 'Assessment must be an exact quote'
                assert 0 < len(ref['attribution'].split()) <= 10
                assert len((p[field] + ' ' + ref['attribution']).split()) <= LIMITS[field], 'Assessment and attribution too long'
            else:
                if independent:
                    assert p[field].startswith('Independent estimate, not a party costing.'), 'Independent cost must be labelled'
                    assert ref['attribution'] == s['publisher'], 'Independent cost attribution differs'
                else:
                    assert ref['source_id'] == p['source_id'] or s['publisher'] == 'Liberal Democrats' and p['source_id'] == 'libdem', 'Cost belongs to another party'
                assert len((p[field] + ' ' + ref['quote'] + ' ' + ref.get('attribution', '')).split()) <= LIMITS[field], 'Cost and quote too long'
            if 'pdf_page' in ref:
                page = ref['pdf_page']
                pages = (base / s['text_file']).read_text().split('\f')
                assert type(page) is int and 1 <= page <= len(pages), 'Invalid evidence PDF page'
                assert normal(ref['quote']) in normal(pages[page-1]), 'Cost quote not on transcript page'
                with tempfile.TemporaryDirectory() as tmp:
                    out = Path(tmp) / 'page.txt'
                    subprocess.run(['pdftotext', '-f', str(page), '-l', str(page), *(['-raw'] if s.get('text_mode') == 'raw' else []), str(base / s['file']), str(out)], check=True, capture_output=True)
                    assert normal(ref['quote']) in normal(out.read_text().split('\f')[0]), 'Cost quote not on PDF page'
            else:
                line = ref['text_line']
                retained = (base / s['text_file']).read_text().splitlines()
                actual = extract_html((base / s['file']).read_text()).splitlines()
                assert type(line) is int and 1 <= line <= min(len(retained), len(actual)), 'Invalid HTML text line'
                assert normal(ref['quote']) in normal(retained[line-1]), 'Quote not at retained HTML locator'
                assert normal(ref['quote']) in normal(actual[line-1]), 'Quote not at raw HTML locator'
        for field in ('costing', 'assessment'):
            if field not in evidence:
                assert p[field].startswith('Unavailable here:'), 'Missing evidence must state unavailable'
        for key, limit in LIMITS.items():
            assert isinstance(p[key],str) and 0 < len(p[key].split()) <= limit, 'Length limit: ' + key
        source = sources[p['source_id']]
        pages = (base / source['text_file']).read_text(encoding='utf-8').split('\f')
        page = p['pdf_page']
        assert type(page) is int and 1 <= page <= len(pages), 'Invalid PDF page: ' + p['name']
        assert normal(p['excerpt']) in normal(pages[page-1]), 'Excerpt not on cited transcript page: ' + p['name']
        # Retained transcripts remain hash-checked evidence, not a substitute for the
        # PDF. Poppler versions can change layout elsewhere in the document; check
        # the actual cited page independently, preserving quote words and punctuation.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'page.txt'
            subprocess.run(['pdftotext', '-f', str(page), '-l', str(page),
                            *(['-raw'] if source.get('text_mode') == 'raw' else []),
                            str(base / source['file']), str(out)], check=True, capture_output=True)
            assert normal(p['excerpt']) in normal(out.read_text(encoding='utf-8').split('\f')[0]), 'Excerpt not on cited PDF page: ' + p['name']
        assert p['status'] == d['status'], 'Status differs'
    assert all(s['url'].startswith('https://') for s in all_sources.values())
    return d

def refresh(root):
    """Refresh byte snapshots in the caller's staging tree; changed evidence needs review.

    Never silently update hashes or curated claims. A changed document stops the build,
    leaving the published last-good site intact. Same-byte checks retain original dates.
    """
    root = Path(root); d = load(root)
    for s in [d['roster']] + d['sources'] + d.get('evidence_sources', []):
        request = urllib.request.Request(s['url'], headers={'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'})
        with urllib.request.urlopen(request, timeout=90) as response:
            raw = response.read()
        if s is d['roster']:
            def composition(payload):
                return sorted((i['value']['party']['id'], i['value']['party']['name'], i['value']['total'])
                              for i in json.loads(payload)['items'] if i['value']['total'] > 0)
            retained = (root / 'sources' / s['file']).read_bytes()
            assert composition(raw) == composition(retained), 'Historical roster changed; review before publishing'
            # Cosmetic metadata is not evidence of a new composition; retain original bytes/hash/date.
            continue
        assert hashlib.sha256(raw).hexdigest() == s['sha256'], 'Party source changed; review before publishing: ' + s['url']
        (root / 'sources' / s['file']).write_bytes(raw)
    validate(root)

def render(d):
    esc = html.escape
    sources = {s['id']: s for s in d['sources'] + d.get('evidence_sources', [])}
    def field_html(p, key):
        ref = p.get('evidence', {}).get(key)
        if not ref:
            return '<q>'+esc(p[key])+'</q>' if key == 'excerpt' else esc(p[key])
        source = sources[ref['source_id']]
        fragment = '#page=' + str(ref['pdf_page']) if 'pdf_page' in ref else ''
        label = ref.get('attribution', 'Party source')
        quote = '<q>' + esc(ref['quote']) + '</q>'
        claim = esc(p[key]) + ' ' if key == 'costing' else ''
        return claim + '<a href="' + esc(source['url'] + fragment) + '">' + esc(label) + '</a>: ' + quote
    cards = []
    for p in d['parties']:
        s = sources[p['source_id']]
        fields = ''.join('<dt>'+esc(label)+'</dt><dd>' + field_html(p, key) + '</dd>' for key,label in FIELDS)
        evidence_dates = ''
        for field, ref in p.get('evidence', {}).items():
            source = sources[ref['source_id']]
            suffix = '#page=' + str(ref['pdf_page']) if 'pdf_page' in ref else ''
            evidence_dates += f' {esc(field.title())}: {esc(ref["locator"])}. Published {source["published"]}. Copy saved {source["downloaded"]}. <a href="sources/{source["file"]}{suffix}">Saved source</a> · <a href="sources/{source["text_file"]}">Plain text</a>.'
        cards.append(f'''<article class="party-offer" data-party-id="{p['id']}" aria-labelledby="party-{p['id']}"><h2 id="party-{p['id']}">{esc(p['name'])}</h2><dl>{fields}
<dt>Source and dates</dt><dd><a href="{esc(s['url'])}#page={p['pdf_page']}">Party source: {esc(p['locator'])}</a>. Published {s['published']}. Copy saved {s['downloaded']}. {esc(s['hosting'])}. <a href="sources/{s['file']}#page={p['pdf_page']}">Saved PDF</a> · <a href="sources/{s['text_file']}">Plain text</a>.{evidence_dates}</dd></dl></article>''')
    r = d['roster']
    css = '''*{box-sizing:border-box}body{margin:0;background:#fafaf8;color:#20262b;font:17px/1.6 system-ui,sans-serif}header,main,footer{max-width:980px;margin:auto;padding:24px}a{color:#253f50;text-underline-offset:3px}a:focus-visible{outline:3px solid #252525;outline-offset:4px}h1{font-size:clamp(2rem,6vw,3.5rem);line-height:1.15}h2{line-height:1.3}article,section,footer{border-top:1px solid #b5b9bc;margin-top:30px;padding-top:18px}dt{font-weight:700;margin-top:14px}dd{margin:4px 0 12px;overflow-wrap:anywhere}.skip{position:absolute;top:-100px}.skip:focus{top:0;background:white;padding:10px}nav{display:flex;flex-wrap:wrap;gap:10px}footer{font-size:.85rem}@media(max-width:600px){header,main,footer{padding:20px}}'''
    return f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Party offers: 2024 snapshot | UnpoliticalAF</title><meta name="description" content="One tax, benefit or funding offer from each Commons party on a set date in 2024. Each has a source and the same fields and limits."><style>{css}</style></head><body><a class="skip" href="#main">Skip to content</a><header><a href="/">UnpoliticalAF</a> · UK public money<nav aria-label="Main"><a href="/">Spending</a><a href="parties.html" aria-current="page">Party offers</a></nav></header><main id="main"><h1>Party offers: a 2024 snapshot</h1>
<p>These are past plans, not today's plans. The list of Commons parties is from <strong>{r['as_of']}</strong>. Each offer comes from a party's 2024 general election manifesto: its book of plans. A linked party release may add the cash claim. We do not say these plans are now law. We do not say they have funds or are still party policy.</p>
<p>We show one tax, benefit or public funding offer per party. Each has the same fields and word limits. Parties are in name order. These are examples, not the full plans. We do not rank them. We use no party colours or scores.</p>
<nav aria-label="Party list">{''.join(f'<a href="#party-{p["id"]}">{esc(p["name"])}</a>' for p in d['parties'])}</nav>
<section aria-labelledby="method"><h2 id="method">How to read this page</h2><p>The offer sums up a party claim. The quote is the party's own text, not our view. Costs are party claims or an outside estimate. We label which. They are not our own estimates. An outside quote gives the named source’s view, not ours. It may cover a wider plan; we say so in Scope. We do not rate plans. A missing cost is not zero. “Unavailable here” means this set of data does not give it for this offer. It may exist elsewhere.</p><p>The rule is the same for all parties. We pick one direct tax, benefit or public funding pledge. We add a short quote from the source. We add a cash claim where we have checked the party source. We may use a named body's cost for a matching policy. That is not a party costing or a full plan review. Its place, year and limits are shown. We add a short outside quote where it fits. We use only IFS, OBR, Resolution Foundation, Full Fact or NAO. Our choice does not show which policy matters most to a party. Each source is a manifesto from that party. Some saved PDFs come from the British Manifesto Archive, not the party's own site. We label these copies. Where we have not checked a full date, we give just the year. PDF page counts start at the first page, with the cover. We keep the quote's words. We remove line breaks.</p><p>Each field has a word limit. The offer can use up to 45 words. The quote can use up to 85. Scope and baseline can each use 30. Year and status can each use 25. Costing and its quote can use 30 in all. Assessment and its named source can use 30 in all. Party names and source page labels can each use 15 words. Source titles can use 35 words. Host labels can use 30. Source web links can use 2,000 characters. The checks use these limits for each party.</p></section>
{''.join(cards)}
<section><h2>Independent MPs and the Speaker</h2><p>The same Commons list has {d['independents']['seats']} independent MPs. They are not one party. They have no shared party manifesto. We do not give them a joint offer, cost or assessment. We list the Speaker on their own ({d['speaker']['seats']} seat). This is not a party offer. We include Sinn Féin by the same rule as all other parties on the Commons list. Our rule is to use that list, not whether MPs take their seats.</p></section>
<section><h2>Party list, data and checks</h2><p>Source: UK Parliament, <a href="{esc(r['url'])}">{esc(r['publication'])}</a>. List date: {r['date']}. Copy saved: {r['downloaded']}. This is a fixed view of the past, not today's list. No date for a next release has been announced for this fixed view.</p><p><a href="sources/{r['file']}">Raw Parliament API data</a> · <a href="sources/commons-roster-metadata.json">List dates, web link and hash</a> · <a href="data/party-offers.json">Get all party offers and source hashes (JSON)</a></p><p>Checks open the saved Commons list and each PDF. They check that we cover all parties on the list. They check each quote is on the page we cite. They check that file hashes match. A hash is a code used to check a file has not changed. They also check the same fields, order and length limits for all parties. If a source changes, we stop the update for review. We also check new cash quotes on the saved PDF page or web text block. We read saved web pages again to check outside quotes. Some rows still lack a cost or a matched outside view. We name those gaps; they are not proof that no such source exists. <a href="data/party-offers.json">Get the checked claims, source details and gaps as data</a>. The same evidence rule applies to all.</p></section></main><footer>Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>. The Commons list comes from UK Parliament. We quote party texts so you can check the source. We do not claim that this licence covers party texts.</footer></body></html>\n'''

def outputs(root):
    d = validate(root)
    return {'parties.html':render(d).encode(), 'data/party-offers.json':(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode()}
