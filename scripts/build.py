#!/usr/bin/env python3
"""Rebuild only from retained official files; refresh stages and validates before publishing."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import html
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import openpyxl
from history import history_outputs, refresh_history
import comparisons
import parties
import section_dates
import income
import disclosures
import corrections
import corrections_page

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = 'public-spending-statistics-release-july-2026'

def fetch(url):
    if not url.startswith(('https://www.gov.uk/', 'https://assets.publishing.service.gov.uk/')):
        raise ValueError('Only official GOV.UK sources are accepted')
    with urllib.request.urlopen(url, timeout=90) as response:
        return response.read()

def extract(root):
    source = json.loads((root/'sources/manifest.json').read_text())
    raw = root/'sources'/source['file']
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == source['sha256'], 'Source hash changed'
    s = openpyxl.load_workbook(raw, data_only=True)['5_2']
    col = max(c.column for c in s[5] if isinstance(c.value, str) and c.value[:4].isdigit())
    def item(row):
        c = s.cell(row, col)
        assert isinstance(c.value, (float, int)), f'Missing value at {c.coordinate}'
        return dict(label=s.cell(row,2).value.strip(), value=c.value, cell=c.coordinate)
    assert s.cell(6,col).value == 'outturn', 'This page supports full-year outturn only; review a new status before publishing'
    rows = [item(r) for r in (20,27,37,56,64,74,79,87,99,121,130)]
    total = item(131)
    return dict(year=s.cell(5,col).value, status=s.cell(6,col).value, unit='GBP million',
                geography='United Kingdom', scope='Public sector expenditure on services',
                rows=rows,total=total,adjustment=item(132),tme=item(133),
                extras=[item(107),item(15)],health_share=rows[6]['value']/total['value']*100,source=source)

def render(d, comparison):
    esc=html.escape
    src=d['source']; year=d['year']; total=d['total']['value']
    def money(v): return f'£{v/1000:,.1f} billion'
    def link(r): return f'<a href="#{r["cell"]}">{money(r["value"])}</a>'
    def label(r): return r['label'].removeprefix('Total ')
    sorted_rows=sorted(d['rows'], key=lambda r:r['value'], reverse=True)
    chart=''.join(f'<div class="bar-row"><span>{esc(label(r))}</span><span class="track"><span class="bar" style="width:{max(0,r["value"])/max(x["value"] for x in d["rows"])*100:.4f}%"></span></span><span>{money(r["value"])}</span></div>' for r in sorted_rows)
    table=''.join(f'<tr><th scope="row">{esc(label(r))}</th><td>{link(r)}</td></tr>' for r in sorted_rows)
    locators=''.join(f'<tr id="{r["cell"]}"><th scope="row">{esc(r["label"])}</th><td>{r["value"]:,}</td><td>5_2!{r["cell"]}</td></tr>' for r in d['rows']+[d['total'],d['adjustment'],d['tme']]+d['extras'])
    body=f'''<header><a class="brand" href="/">UnpoliticalAF</a><span>UK public money · The first page</span></header>
<main id="main"><p class="eyebrow">Spending / {year} / {esc(d['status'])}</p>
<h1>Where public money goes</h1>
<nav aria-label="Spending questions"><a href="income.html">Taxes, borrowing and debt</a> · <a href="parties.html">Party offers</a> · <a href="#total">Spending by area</a> · <a href="#ten-years">Ten-year answers</a> · <a href="#check-source">Check a number</a> · <a href="history.html">Spending history: overall and by area</a></nav>
<p class="intro">Social protection is the largest area of spending. It includes pensions, benefits and care.</p>
<p>These are UK-wide figures for {year}, the latest full year in this release. They are <strong>outturn</strong>: recorded spending, not a forecast. They can still be revised.</p>
<section aria-labelledby="total"><h2 id="total">Spending on services: {link(d['total'])}</h2>
<p>The source calls this public sector expenditure on services. It covers daily costs and spending on assets, such as roads. These are cash amounts. They do not take price rises into account.</p>
<p>Of each £100 spent on services, <strong>£{d['health_share']:.2f} goes on health</strong>. This is health spending divided by total spending on services, times 100.</p>
<h3>Spending by area</h3><p>The bars use the same scale. The EU entry is a net receipt, so it has no positive bar. Exact amounts are in the table and source list below.</p>
<div class="chart" aria-hidden="true">{chart}</div>
<table><caption>UK spending on services by area, {year} (outturn). Rounded to £0.1 billion.</caption><thead><tr><th scope="col">Area</th><th scope="col">Cash spending</th></tr></thead><tbody>{table}</tbody></table></section>
<section><h2>What is in these totals?</h2>
<p>Old-age pensions were {link(d['extras'][0])}. These form part of social protection, not the whole of it. Defence was {link(d['rows'][1])}. This uses the UN rules, not NATO's measure. NATO includes some costs, such as pensions, elsewhere in this table.</p>
<p>In {year}, central government debt interest was {link(d['extras'][1])} ({esc(d['status'])}, not a forecast). This is gross interest: the full sum paid to firms, people and bodies outside the UK state. It includes sums paid abroad. It is part of general public services, not an extra amount to add to the chart. The source row called public debt transactions includes other items too. It is not the same measure.</p>
<p>Total Managed Expenditure was {link(d['tme'])}. It equals spending on services plus {link(d['adjustment'])} of changes made to fit the accounts rules. These totals use different rules; we do not treat them as the same figure.</p></section>
{comparisons.render(comparison)}
<section><h2 id="check-source">Check the source</h2><p>Source: <a href="{src['release_url']}">{esc(src['publication'])}</a>, HM Treasury. First published {src['published']}; source page updated {src['date']}. Downloaded {src['downloaded']}. The main spending table covers {year}; the comparison covers {comparison['points'][0]['year']} to {comparison['points'][1]['year']}. None of the numbers on this page are forecasts: all are labelled outturn in this release. The saved release notes give no next release date.</p>
<p><a href="data/spending.csv">Download the data (CSV)</a> · <a href="data/spending.json">Data with source details (JSON)</a> · <a href="sources/spending.xlsx">Retained official workbook</a> · <a href="sources/manifest.json">Source URL, dates and SHA-256</a></p>
<p>All source amounts below are in £ million and cover the UK. The scope is public sector expenditure on services, unless the row says adjustment or Total Managed Expenditure. The cell codes are from sheet 5_2 in the workbook. Click a figure above to find its row.</p>
<table class="source-table"><caption>Exact source values and workbook cells · {year} · outturn</caption><thead><tr><th scope="col">Source row</th><th scope="col">£ million</th><th scope="col">Cell</th></tr></thead><tbody>{locators}</tbody></table>
<p class="hash">SHA-256: <code>{src['sha256']}</code></p></section>
<section><h2>Method and limits</h2><p>Code reads the latest year in the official table. It does not fill missing cells with zero. We check that the areas add up to the total, within rounding, and that totals match the economic table in the same workbook. The source rounds to £ million. Displayed billions are divided by 1,000 and rounded to one decimal place. Health's share uses the unrounded source values.</p>
<p>This page covers the latest year of spending and a ten-year comparison. The linked history page shows past spending, both the total and each area. <a href="income.html">See where money comes from: taxes, other receipts, borrowing and debt stocks.</a> <a href="parties.html">Party offers</a> are a record from a past election, not current spending. The year shown is the latest year we can compare in this release. This does not mean all figures are final. Later releases may change them.</p>
<p><a href="banned-words.txt">Words we do not use to judge policies</a>. The build checks page copy against this list. No party colours are used. No people checks are claimed. See the project page for known facts and gaps about who runs and funds the site.</p></section></main>
<footer>Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>. Source: HM Treasury.</footer>'''
    css='''*{box-sizing:border-box}body{margin:0;color:#20262b;background:#fafaf8;font:17px/1.6 system-ui,sans-serif}header,main,footer{max-width:980px;margin:auto;padding:24px}header{display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between;border-bottom:1px solid #b5b9bc;font-size:14px}.brand{font-weight:750}a{color:#253f50;text-underline-offset:3px}a:hover{text-decoration-thickness:3px}a:focus-visible{outline:3px solid #252525;outline-offset:4px}h1{font-size:clamp(2.3rem,6vw,3.8rem);line-height:1.12;letter-spacing:-.035em;margin:12px 0 24px}h2{line-height:1.3;font-size:1.55rem}h3{font-size:1.2rem}.eyebrow{text-transform:uppercase;font-size:.8rem;letter-spacing:.09em;margin-top:24px}.intro{font-size:1.35rem;max-width:650px}section{border-top:1px solid #b5b9bc;margin-top:36px;padding-top:16px}table{border-collapse:collapse;width:100%;font-size:.9rem;margin:24px 0;table-layout:fixed}caption{text-align:left;font-weight:650;margin-bottom:12px}th,td{text-align:left;padding:12px 6px;vertical-align:top;border-bottom:1px solid #c5c8c9;overflow-wrap:anywhere}th:first-child{width:55%}.source-table th:first-child{width:48%}.comparison th:first-child{width:40%}.source-table td{white-space:nowrap}td{font-variant-numeric:tabular-nums}thead{background:#e7e9e8}.chart{margin:28px 0}.bar-row{display:grid;grid-template-columns:220px 1fr 145px;gap:12px;align-items:center;margin:12px 0;font-size:.85rem}.bar-row>span:last-child{text-align:right}.track{height:18px;background:#e5e7e6}.bar{display:block;height:100%;background:#4c5960}.hash{overflow-wrap:anywhere;font-size:.75rem}footer{border-top:1px solid #b5b9bc;font-size:.85rem}.skip{position:absolute;top:-100px}.skip:focus{top:0;background:white;padding:10px}tr:target{background:#e0e4e2}@media(max-width:600px){header,main,footer{padding:20px}.bar-row{grid-template-columns:1fr 100px;gap:5px}.bar-row>span:first-child{grid-column:1/-1}.bar-row>span:last-child{font-size:.75rem}th,td{padding:10px 4px}table{font-size:.8rem}}'''
    return f'<!doctype html>\n<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Where public money goes | UnpoliticalAF</title><meta name="description" content="UK public spending by area, with official source data and methods."><style>{css}</style></head><body><a class="skip" href="#main">Skip to content</a>{body}</body></html>\n'

def outputs(root):
    d=extract(root)
    comparison=comparisons.extract(root)
    stream=io.StringIO(); writer=csv.writer(stream,lineterminator='\n')
    writer.writerow(['label','value_gbp_million','year','status','geography','sheet','cell'])
    for r in d['rows']+[d['total'],d['adjustment'],d['tme']]+d['extras']:
        writer.writerow([r['label'],r['value'],d['year'],d['status'],d['geography'],'5_2',r['cell']])
    comparison_csv=io.StringIO(); cw=csv.writer(comparison_csv,lineterminator='\n')
    cw.writerow(['year','status','measure','value','unit','scope','geography','sheet','cell'])
    for point in comparison['points']:
        for key in ('health_real','tme_gdp'):
            r=point[key]
            cw.writerow([point['year'],point['status'],key,r['value'],r['unit'],r['scope'],r['geography'],r['sheet'],r['cell']])
    files={'data/comparisons.json':(json.dumps(comparison,indent=2,ensure_ascii=False)+'\n').encode(),'data/comparisons.csv':comparison_csv.getvalue().encode(),'index.html':render(d,comparison).encode(),'data/spending.json':(json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode(),'data/spending.csv':stream.getvalue().encode(),'banned-words.txt':(ROOT/'scripts/banned-words.txt').read_bytes()}
    files.update(parties.outputs(root))
    files.update(income.outputs(root))
    files.update(history_outputs(root))
    section_dates.annotate(files, root, d, comparison)
    entries = corrections.load(root/'sources/corrections.json', check_pages=False)
    files['corrections.html'] = corrections_page.render(entries, files['index.html'].decode()).encode()
    disclosures.annotate(files, d['source'])
    for name, raw in list(files.items()):
        if name.endswith('.html') and name != 'corrections.html':
            files[name] = raw.replace(b'<footer>', b'<footer><p><a href="corrections.html">Corrections and report an error</a></p>')
    for p in (root/'sources').iterdir(): files['sources/'+p.name]=p.read_bytes()
    return files

def main():
    p=argparse.ArgumentParser(); p.add_argument('--refresh',action='store_true'); p.add_argument('--check',action='store_true'); p.add_argument('--release',default=DEFAULT); args=p.parse_args()
    if args.refresh and args.check: p.error('Choose refresh or check')
    with tempfile.TemporaryDirectory() as tmp:
        stage=Path(tmp); shutil.copytree(ROOT/'sources',stage/'sources')
        if args.refresh:
            meta=fetch('https://www.gov.uk/api/content/government/statistics/'+args.release)
            j=json.loads(meta); a=next(a for a in j['details']['attachments'] if a['title']=='Public sector spending')
            raw=fetch(a['url']); digest=hashlib.sha256(raw).hexdigest()
            old=json.loads((ROOT/'sources/manifest.json').read_text()) if (ROOT/'sources/manifest.json').exists() else {}
            manifest=dict(file='spending.xlsx',url=a['url'],sha256=digest,publication=next(a['title'] for a in j['details']['attachments'] if a.get('attachment_type')=='html'),published=j['first_published_at'][:10],date=j['public_updated_at'][:10],downloaded=old.get('downloaded') if old.get('sha256')==digest else datetime.now(timezone.utc).date().isoformat(),release_url='https://www.gov.uk'+j['base_path'])
            (stage/'sources/spending.xlsx').write_bytes(raw); (stage/'sources/release.json').write_bytes(meta)
            (stage/'sources/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
            refresh_history(stage)
            trends_attachment=next(a for a in j['details']['attachments'] if a['title']=='Trends in public spending')
            trends_raw=fetch(trends_attachment['url']); trends_hash=hashlib.sha256(trends_raw).hexdigest()
            trends_old=json.loads((ROOT/'sources/trends-manifest.json').read_text())
            trends_manifest=dict(manifest, file='trends.xlsx', url=trends_attachment['url'], sha256=trends_hash,
                                 downloaded=trends_old['downloaded'] if trends_old['sha256']==trends_hash else datetime.now(timezone.utc).date().isoformat())
            (stage/'sources/trends.xlsx').write_bytes(trends_raw)
            (stage/'sources/trends-manifest.json').write_text(json.dumps(trends_manifest,indent=2)+'\n')
            parties.refresh(stage)
            income.refresh(stage)
            import release_calendar
            release_calendar.refresh(stage)
        status_path = stage/'sources/revision-status.json'
        if status_path.exists():
            from discover import load_revision_status, reconcile_revision_status
            inventory = json.loads((ROOT/'config/release-sources.json').read_text())
            state = reconcile_revision_status(load_revision_status(status_path), inventory, [], stage, None)
            status_path.write_text(json.dumps(state, indent=2)+'\n')
        files=outputs(stage)
        for name,content in files.items():
            dest=stage/'site'/name; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(content)
        subprocess.run([sys.executable,str(ROOT/'scripts/check.py'),'--root',str(stage)],check=True)
        changed=[name for name,content in files.items() if not (ROOT/'site'/name).exists() or (ROOT/'site'/name).read_bytes()!=content]
        print('Changed generated files:', ', '.join(changed) or 'none')
        if args.check:
            assert not changed, 'Generated site differs: rebuild and commit output'
        else:
            # All network, parsing and validation work completes before touching last-good output.
            for name,content in files.items():
                dest=ROOT/'site'/name; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(content)
            if status_path.exists():
                shutil.copyfile(status_path, ROOT/'sources/revision-status.json')
            if args.refresh:
                for f in (stage/'sources').iterdir(): shutil.copyfile(f,ROOT/'sources'/f.name)
if __name__=='__main__': main()
