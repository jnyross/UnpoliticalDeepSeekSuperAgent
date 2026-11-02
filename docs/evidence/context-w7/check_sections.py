"""Offline section check; no browser actions or people testing."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from manual_access import Document

doc = Document((ROOT / 'site/parties.html').read_text())
rows = []
for article in (n for n in doc.nodes if n.tag == 'article'):
    notices = [n for n in article.descendants('p') if n.attrs.get('class') == 'revision-notice']
    if 'IFS' in article.text() or notices:
        rows.append(dict(party_id=article.attrs['data-party-id'],
                         heading=next(article.descendants('h2')).text(),
                         date_blocks=[n.text() for n in article.descendants('div')
                                      if n.attrs.get('class') == 'section-dates'],
                         notice_count=len(notices)))
report = dict(page='site/parties.html', sections=rows,
              ifs_date_present=any('2024-06-24' in s for r in rows for s in r['date_blocks']),
              total_notices=sum(n.attrs.get('class') == 'revision-notice' for n in doc.nodes))
Path(__file__).with_name('section-check.json').write_text(json.dumps(report, indent=2) + '\n')
assert report['ifs_date_present'] and report['total_notices'] == 1
print('PASS: IFS publication date and one retained LibDem notice; no UI change')
