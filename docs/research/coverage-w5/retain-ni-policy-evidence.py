"""Retain ordinary public publisher HTTP responses; never bypass challenges."""
import datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent
URLS = {
    'rf-catastrophic-caps-january2024': 'https://www.resolutionfoundation.org/publications/catastophic-caps/',
    'rf-two-child-july2024': 'https://www.resolutionfoundation.org/press-releases/almost-two-in-five-large-families-are-now-affected-by-the-two-child-limit-and-the-majority-are-set-to-fall-into-poverty-when-the-policy-is-fully-rolled-out/',
    'snp-manifesto-launch-june2024': 'https://www.snp.org/snp-leader-john-swinneys-2024-manifesto-speech/',
}
class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'): self.skip += 1
    def handle_endtag(self, tag):
        if tag in ('script', 'style'): self.skip = max(0, self.skip - 1)
    def handle_data(self, data):
        if not self.skip and data.strip(): self.parts.append(data.strip())

def digest(data): return hashlib.sha256(data).hexdigest()
rows = []
for key, url in URLS.items():
    row = {'id': key, 'url': url, 'retrieved': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            body = response.read()
            row.update(status=response.status, final_url=response.url, bytes=len(body))
        if row['status'] == 200:
            parser = Text()
            parser.feed(body.decode('utf-8', 'replace'))
            text = ('\n'.join(parser.parts) + '\n').encode()
            (ROOT / (key + '.html')).write_bytes(body)
            (ROOT / (key + '.txt')).write_bytes(text)
            row.update(sha256=digest(body), text_sha256=digest(text))
    except Exception as error:
        row['error'] = str(error)
    rows.append(row)
    print(row, flush=True)
(ROOT / 'ni-two-child-metadata.json').write_text(json.dumps(rows, indent=2) + '\n')
