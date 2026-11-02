"""One bounded independent DE fetch; preserve baselines, retain provenance and comparisons."""
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import parties

out = Path(__file__).resolve().parent
manifest = json.loads((ROOT / 'sources/party-offers.json').read_text())
source = next(s for s in manifest['evidence_sources'] if s['id'] == 'de-childcare-2024')
card = next(p for p in manifest['parties'] if p['id'] == 7)
request = urllib.request.Request(source['url'], headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'})
started = datetime.now(timezone.utc).isoformat()
with urllib.request.urlopen(request, timeout=60) as response:
    raw = response.read()
    metadata = {'requested_url': source['url'], 'final_url': response.url, 'http_status': response.status, 'headers': dict(response.headers)}
metadata.update(started_at=started, completed_at=datetime.now(timezone.utc).isoformat())
(out / 'independent-de.raw.html.txt').write_bytes(raw)
visible = parties.extract_html(raw.decode('utf-8'))
(out / 'independent-de.visible.txt').write_text(visible)
baseline_raw = (ROOT / 'sources' / source['file']).read_bytes()
baseline_visible = parties.extract_html(baseline_raw.decode('utf-8'))
sha = lambda value: hashlib.sha256(value).hexdigest()
checks = []
reference = card['evidence']['programme']
for label, quote in [('programme', reference['quote']), ('approval', reference['approval_quote']), ('publication_date', 'Date published: 23 May 2024')]:
    checks.append({'field': label, 'quote': quote, 'in_baseline': parties.normal(quote) in parties.normal(baseline_visible), 'in_observed': parties.normal(quote) in parties.normal(visible)})
metadata.update(baseline_sha256=source['sha256'], observed_sha256=sha(raw), raw_equal=raw == baseline_raw, baseline_visible_sha256=sha(baseline_visible.encode()), observed_visible_sha256=sha(visible.encode()), normalized_visible_equal=parties.normal(visible) == parties.normal(baseline_visible), consumed_reference_checks=checks, scope='One fresh DE fetch; no source refresh, archive requests, or baseline edits. Visible extraction uses repository html-blocks-v1; not a browser/human check.')
(out / 'independent-de.visible.diff.txt').write_text(''.join(difflib.unified_diff(baseline_visible.splitlines(True), visible.splitlines(True), fromfile='retained baseline visible text', tofile='independent observed visible text')))
(out / 'independent-de-check.json').write_text(json.dumps(metadata, indent=2) + '\n')
print(json.dumps(metadata, indent=2))
