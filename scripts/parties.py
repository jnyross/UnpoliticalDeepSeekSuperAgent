"""Equal-format historical party offers, checked against retained party PDFs and Commons API."""
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.request
from datetime import datetime, timezone

LIMITS = {'offer': 45, 'excerpt': 85, 'scope': 30, 'baseline': 30, 'year': 25,
          'status': 25, 'costing': 30, 'assessment': 30}
FIELDS = [('offer', 'Selected official offer'), ('excerpt', 'Party source excerpt'),
          ('scope', 'Scope'), ('baseline', 'Baseline'), ('year', 'Year'),
          ('status', 'Status'), ('costing', 'Costing'), ('assessment', 'Independent assessment')]

def normal(text):
    return ' '.join(text.replace('\u00ad', '').split())

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
    for s in sources.values():
        assert len(s['publication'].split()) <= 35 and len(s['hosting'].split()) <= 30, 'Source label too long'
        assert len(s['url']) <= 2000, 'Source URL too long'
        for name, h in [('file','sha256'), ('text_file','text_sha256')]:
            assert Path(s[name]).name == s[name], 'Source must be flat'
            assert digest(base / s[name]) == s[h], 'Source hash changed: ' + s[name]
        # Reopen the PDF, rather than trusting a separately edited text transcript.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'text.txt'
            subprocess.run(['pdftotext', *(['-raw'] if s.get('text_mode') == 'raw' else []), str(base / s['file']), str(out)], check=True, capture_output=True)
            assert out.read_bytes() == (base / s['text_file']).read_bytes(), 'PDF text differs'
    expected_keys = {'id','name','seats','source_id','locator','pdf_page', *LIMITS}
    for p in d['parties']:
        assert len(p['name'].split()) <= 15 and len(p['locator'].split()) <= 15, 'Party/source label too long'
        assert set(p) == expected_keys, 'Party fields differ'
        for key, limit in LIMITS.items():
            assert isinstance(p[key],str) and 0 < len(p[key].split()) <= limit, 'Length limit: ' + key
        source = sources[p['source_id']]
        pages = (base / source['text_file']).read_text().split('\f')
        assert normal(p['excerpt']) in normal(pages[p['pdf_page']-1]), 'Excerpt not on cited PDF page: ' + p['name']
        assert p['status'] == d['status'], 'Status differs'
        assert p['costing'] == d['costing'] and p['assessment'] == d['assessment'], 'Missing-data treatment differs'
    assert all(s['url'].startswith('https://') for s in d['sources'])
    return d

def refresh(root):
    """Refresh byte snapshots in the caller's staging tree; changed evidence needs review.

    Never silently update hashes or curated claims. A changed document stops the build,
    leaving the published last-good site intact. Same-byte checks retain original dates.
    """
    root = Path(root); d = load(root)
    for s in [d['roster']] + d['sources']:
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
    sources = {s['id']: s for s in d['sources']}
    cards = []
    for p in d['parties']:
        s = sources[p['source_id']]
        fields = ''.join('<dt>'+esc(label)+'</dt><dd>' + ('<q>'+esc(p[key])+'</q>' if key=='excerpt' else esc(p[key])) + '</dd>' for key,label in FIELDS)
        cards.append(f'''<article class="party-offer" data-party-id="{p['id']}" aria-labelledby="party-{p['id']}"><h2 id="party-{p['id']}">{esc(p['name'])}</h2><dl>{fields}
<dt>Source and dates</dt><dd><a href="{esc(s['url'])}#page={p['pdf_page']}">Party manifesto: {esc(p['locator'])}</a>. Published {s['published']}; retained {s['downloaded']}. {esc(s['hosting'])}. <a href="sources/{s['file']}#page={p['pdf_page']}">Retained PDF</a> · <a href="sources/{s['text_file']}">Plain text</a>.</dd></dl></article>''')
    r = d['roster']
    css = '''*{box-sizing:border-box}body{margin:0;background:#fafaf8;color:#20262b;font:17px/1.6 system-ui,sans-serif}header,main,footer{max-width:980px;margin:auto;padding:24px}a{color:#253f50;text-underline-offset:3px}a:focus-visible{outline:3px solid #252525;outline-offset:4px}h1{font-size:clamp(2rem,6vw,3.5rem);line-height:1.15}h2{line-height:1.3}article,section,footer{border-top:1px solid #b5b9bc;margin-top:30px;padding-top:18px}dt{font-weight:700;margin-top:14px}dd{margin:4px 0 12px;overflow-wrap:anywhere}.skip{position:absolute;top:-100px}.skip:focus{top:0;background:white;padding:10px}nav{display:flex;flex-wrap:wrap;gap:10px}footer{font-size:.85rem}@media(max-width:600px){header,main,footer{padding:20px}}'''
    return f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Party offers: 2024 snapshot | UnpoliticalAF</title><meta name="description" content="One sourced fiscal offer from each Commons party at a dated 2024 snapshot, using the same fields and limits."><style>{css}</style></head><body><a class="skip" href="#main">Skip to content</a><header><a href="/">UnpoliticalAF</a> · UK public money<nav aria-label="Main"><a href="/">Spending</a><a href="parties.html" aria-current="page">Party offers</a></nav></header><main id="main"><h1>Party offers: a 2024 snapshot</h1>
<p>This is history, not a list of current plans. The Commons roster is as of <strong>{r['as_of']}</strong>. The offers are from the parties' 2024 general election manifestos. We do not say these plans are now law, funded or still party policy.</p>
<p>Each party gets one selected tax, benefit or funding offer, the same fields and the same word limits. Parties are in name order. These are examples, not the full plans or a ranking. We use no party colours or scores.</p>
<nav aria-label="Party list">{''.join(f'<a href="#party-{p["id"]}">{esc(p["name"])}</a>' for p in d['parties'])}</nav>
<section aria-labelledby="method"><h2 id="method">How to read this page</h2><p>The offer is a short summary of a party claim. The quote is the party's own text, not our view. We do not assess its impact. Our selection is qualitative: it does not report a cash cost, yield or impact estimate. A missing cost is not zero. “Unavailable here” means not supplied for this selected offer in this dataset, not that none exists elsewhere.</p><p>We use the same rule for all parties: one direct tax, benefit or public funding pledge with a short source quote. We choose qualitative passages that need no cash cost or impact estimate. This choice does not show which policy matters most to a party. Each source is a party-issued manifesto. Some retained PDFs come from the British Manifesto Archive, not the party's server; these are labelled. Dates are stated to year precision where a full date has not been checked. PDF page numbers count from the first page, including the cover. Text quotes retain the words, with line breaks removed.</p><p>The limits, in words, are: offer 45; quote 85; scope and baseline 30 each; year and status 25 each; costing and assessment 30 each. Party names and source locators have a 15-word limit each. Source titles have a 35-word limit; host labels 30 words; source URLs 2,000 characters. The checks apply these limits to every party.</p></section>
{''.join(cards)}
<section><h2>Independent MPs and the Speaker</h2><p>The same roster lists {d['independents']['seats']} independent MPs. They are not one party and have no shared party manifesto. No joint offer, cost or assessment is attributed to them. The Speaker is listed on their own ({d['speaker']['seats']} seat), not as a party offer. Sinn Féin is included on the same basis as all other parties in the official Commons roster; taking seats is not our coverage rule.</p></section>
<section><h2>Roster, data and checks</h2><p>Source: UK Parliament, <a href="{esc(r['url'])}">{esc(r['publication'])}</a>. Roster date {r['date']}; retained {r['downloaded']}. This is a fixed historical snapshot, not today's roster. No next release date is announced for this fixed snapshot.</p><p><a href="sources/{r['file']}">Raw Parliament API response</a> · <a href="sources/commons-roster-metadata.json">Roster dates, URL and hash</a> · <a href="data/party-offers.json">Download all party offers and source hashes (JSON)</a></p><p>Checks reopen the retained roster and each PDF. They test all represented parties are covered, each quote is on its cited page, hashes match, and the same fields, order and length limits apply. A changed source stops a refresh for review. No independent policy judgement is supplied here. All independent assessment fields are marked unavailable on the same basis.</p></section></main><footer>Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>. Roster source: UK Parliament. Party manifesto text is quoted for source checking; party documents are not claimed to be covered by that licence.</footer></body></html>\n'''

def outputs(root):
    d = validate(root)
    return {'parties.html':render(d).encode(), 'data/party-offers.json':(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode()}
