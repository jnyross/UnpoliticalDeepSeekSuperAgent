"""Retained PESA functional history, kept separate from the current-year vintage."""
import csv
import hashlib
import html
import io
import json
import math
import re
from datetime import datetime, timezone
import urllib.request
import openpyxl
from history_charts import TME_NOTE


def refresh_history(root):
    """Refresh the pinned official vintage; retain download date when bytes match."""
    api = 'https://www.gov.uk/api/content/government/statistics/public-expenditure-statistical-analyses-2026'
    def fetch(url):
        assert url.startswith(('https://www.gov.uk/', 'https://assets.publishing.service.gov.uk/'))
        with urllib.request.urlopen(url, timeout=90) as response:
            return response.read()
    meta = fetch(api)
    j = json.loads(meta)
    attachment = next(a for a in j['details']['attachments'] if a['title'] == 'PESA 2026 Chapter 4 Tables')
    raw = fetch(attachment['url'])
    digest = hashlib.sha256(raw).hexdigest()
    path = root/'sources/history-manifest.json'
    old = json.loads(path.read_text()) if path.exists() else {}
    w = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
    assert w['4_2']['B5'].value == '2003-04' and w['4_2']['X5'].value == '2025-26'
    manifest = dict(file='history.xlsx', url=attachment['url'], sha256=digest,
        publication='Public Expenditure Statistical Analyses 2026, Chapter 4',
        published=j['first_published_at'][:10], date=j['public_updated_at'][:10],
        workbook_vintage='2026-07-16',
        downloaded=old.get('downloaded') if old.get('sha256') == digest else datetime.now(timezone.utc).date().isoformat(),
        release_url='https://www.gov.uk'+j['base_path'], metadata_url=api,
        metadata_file='history-release.json', metadata_sha256=hashlib.sha256(meta).hexdigest(),
        workbook_modified=w.properties.modified.isoformat()+'Z',
        sheets={'cash': '4_2', 'real': '4_3', 'gdp': '4_4'}, geography='United Kingdom',
        scope='Public sector expenditure on services', status='outturn',
        years='2003-04 to 2025-26', real_base_year='2025-26',
        deflator='ONS GDP deflators released 30 June 2026',
        gdp_source='ONS GDP published 30 June 2026',
        next_release='No next release date is announced in the retained release metadata.')
    (root/'sources/history.xlsx').write_bytes(raw)
    (root/'sources/history-release.json').write_bytes(meta)
    path.write_text(json.dumps(manifest, indent=2)+'\n')


ROWS = (
    (6, 'general-public-services'), (7, 'public-and-common-services'),
    (8, 'international-services'), (9, 'public-sector-debt-interest'),
    (10, 'defence'), (11, 'public-order-and-safety'), (12, 'economic-affairs'),
    (13, 'enterprise-and-economic-development'), (14, 'science-and-technology'),
    (15, 'employment-policies'), (16, 'agriculture-fisheries-and-forestry'),
    (17, 'transport'), (18, 'environment-protection'),
    (19, 'housing-and-community-amenities'), (20, 'health'),
    (21, 'recreation-culture-and-religion'), (22, 'education'),
    (23, 'social-protection'), (24, 'eu-transactions'),
    (25, 'services-total'), (26, 'accounting-adjustments'), (27, 'tme'),
)
MAIN_IDS = ('general-public-services', 'defence', 'public-order-and-safety',
            'economic-affairs', 'environment-protection',
            'housing-and-community-amenities', 'health',
            'recreation-culture-and-religion', 'education', 'social-protection',
            'eu-transactions', 'services-total', 'tme')
VIEWS = {'cash': ('4_2', 'cash_gbp_billion'),
         'real': ('4_3', 'real_gbp_billion'),
         'gdp': ('4_4', 'gdp_percent')}
GAP = 'Not available in this retained July 2026 functional history; not zero.'


def history_extract(root):
    source = json.loads((root/'sources/history-manifest.json').read_text())
    raw = root/'sources'/source['file']
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == source['sha256'], 'History source hash changed'
    assert hashlib.sha256((root/'sources'/source['metadata_file']).read_bytes()).hexdigest() == source['metadata_sha256'], 'History metadata hash changed'
    workbook = openpyxl.load_workbook(raw, data_only=True)
    sheets = {view: workbook[sheet] for view, (sheet, _) in VIEWS.items()}
    years = [sheets['cash'].cell(5, col).value for col in range(2, 25)]
    assert years == [f'{y}-{str(y+1)[-2:]}' for y in range(2003, 2026)]
    for s in sheets.values():
        assert s['B4'].value == 'outturn'
        assert [s.cell(5, col).value for col in range(2, 25)] == years
    notes = {s.title: [{'cell': f'{s.title}!A{row}', 'text': s.cell(row, 1).value}
                       for row in range(28, 37) if s.cell(row, 1).value]
             for s in sheets.values()}
    aggregate = workbook['4_1']
    assert '2025-26' in aggregate['B3'].value and 'Outturn' in aggregate['B3'].value
    notes['4_1'] = [{'cell': f'4_1!B{r}', 'text': aggregate.cell(r, 2).value} for r in (51, 52, 53)]
    series = []
    for row, ident in ROWS:
        label = sheets['cash'].cell(row, 1).value.strip()
        label = re.sub(r'\s*\(\d+\)(?:,\s*\(\d+\))*', '', label)
        scope = ('Total Managed Expenditure' if ident == 'tme' else
                 'Accounting adjustments between TES and TME' if ident == 'accounting-adjustments' else
                 'Public sector expenditure on services')
        values = []
        for col, year in enumerate(years, 2):
            point = dict(year=year, status='outturn', cells={}, missing_reason=None)
            for view, (sheet, field) in VIEWS.items():
                cell = sheets[view].cell(row, col)
                numeric = isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool)
                assert cell.value is None or (numeric and math.isfinite(cell.value)), f'Unexpected history value at {sheet}!{cell.coordinate}'
                point[field] = round(cell.value, 1) if numeric else None
                point['cells'][view] = f'{sheet}!{cell.coordinate}'
                if not numeric:
                    point['missing_reason'] = 'Source cell is blank; not zero.'
            values.append(point)
        series.append(dict(id=ident, label=label, scope=scope, source_row=row,
                           is_subcategory=label.lower().startswith('of which:'), values=values))
    # Fixed years are selected by rule, not by the size or direction of a change.
    latest = json.loads((root/'sources/manifest.json').read_text())
    current = openpyxl.load_workbook(root/'sources'/latest['file'], data_only=True)['5_2']
    latest_year = max(c.value for c in current[5] if isinstance(c.value, str) and re.fullmatch(r'\d{4}-\d{2}', c.value))
    end = int(latest_year[:4])
    fixed_years = [f'{y}-{str(y+1)[-2:]}' for y in range(end, 1944, -10)]
    fixed = []
    for item in series:
        if item['id'] not in MAIN_IDS:
            continue
        available = {p['year']: p for p in item['values']}
        if item['id'] == 'tme':
            for r in (6, 16):
                year = aggregate.cell(r, 2).value
                assert year in ('1985-86', '1995-96')
                available[year] = dict(year=year, status='outturn', missing_reason=None,
                    cash_gbp_billion=round(aggregate.cell(r, 13).value, 1),
                    real_gbp_billion=round(aggregate.cell(r, 14).value, 1),
                    gdp_percent=round(aggregate.cell(r, 15).value, 1),
                    cells={v: f'4_1!{aggregate.cell(r, col).coordinate}' for v, col in [('cash', 13), ('real', 14), ('gdp', 15)]})
        fixed.append(dict(id=item['id'], label=item['label'], values=[
            available[year] if year in available else dict(year=year, status='unavailable',
                cash_gbp_billion=None, real_gbp_billion=None, gdp_percent=None,
                cells={}, missing_reason=GAP) for year in fixed_years]))
    return dict(source=source, geography='United Kingdom', years=years,
                units=dict(cash_gbp_billion='GBP billion, cash',
                           real_gbp_billion='GBP billion, 2025-26 prices',
                           gdp_percent='percent of GDP'), notes=notes, series=series,
                fixed_comparison_years=fixed_years, fixed_comparisons=fixed,
                latest_overview_year=latest_year, overview_source=latest,
                vintage_note='This history is from PESA Chapter 4, July 2026. The latest overview uses a separate workbook: Chapter 5 of the July 2026 spending statistics. Its source page was updated later. We keep a source record for each workbook. We do not mix their values. The sources round to different units. This history uses £0.1 billion. The overview uses £ million.',
                limitations='This source shows spending by area from 2003-04. Table 4.1 also gives TME for 1985-86 and 1995-96. Those two years cover TME only. The other earlier ten-year entries are not held here. Other official sources may hold older data. Each subcategory is part of its parent area. Do not add it again. The source rounds figures to one decimal place. This may cause small gaps in sums.')


def history_render(d):
    esc = html.escape
    src = d['source']
    def number(value):
        return 'Not available' if value is None else f'{value:,.1f}'
    def row(point, locator=True):
        cells = point['cells']
        links = ' · '.join(esc(cells[v]) for v in VIEWS if v in cells)
        status = point['status']
        if point['missing_reason']:
            status += ': ' + point['missing_reason']
        return (f'<tr><th scope="row">{esc(point["year"])}</th>'
                f'<td>{number(point["cash_gbp_billion"])}</td>'
                f'<td>{number(point["real_gbp_billion"])}</td>'
                f'<td>{number(point["gdp_percent"])}</td>'
                + (f'<td>{esc(status)}<br><small>{links}</small></td>' if locator else '') + '</tr>')
    def table(item, fixed=False):
        scope_note = (f' {TME_NOTE} Source note: ' + ('4_1!B53' if fixed else '4_2!A35; 4_3!A36; 4_4!A36') + '.') if item['id'] == 'tme' else ''
        return (f'<table><caption>{esc(item["label"])} — '+('fixed ten-year snapshots' if fixed else 'annual history')+esc(scope_note)+'</caption>'
                '<thead><tr><th scope="col">Fiscal year</th><th scope="col">Cash<br>£bn</th>'
                '<th scope="col">Real<br>£bn, 2025-26 prices</th><th scope="col">GDP share<br>%</th>'
                '<th scope="col">Status and source cells</th></tr></thead><tbody>'
                + ''.join(row(p) for p in item['values']) + '</tbody></table>')
    note_items = ''.join(f'<li id="note-{n["cell"].replace("!", "-")}">{esc(n["text"])} <small>({esc(n["cell"])})</small></li>' for n in d['notes']['4_2'])
    contents = ' · '.join(f'<a href="#{s["id"]}">{esc(s["label"])}</a>' for s in d['series'])
    tables = []
    for s in d['series']:
        specific = ''
        if s['id'] in ('education',):
            specific = 'The scope changes in 2011-12. It no longer counts the grant-equivalent part of student loans. Do not compare values across this break as if their scope were the same.'
        elif s['id'] in ('transport', 'economic-affairs', 'services-total'):
            specific = 'The scope changes twice. From 2011-12, transport includes spending by TfL subsidiaries. From 2015-16, spending on services includes Network Rail. TME includes Network Rail in all years shown.'
        elif s['id'] == 'defence':
            specific = 'This is UN COFOG defence. It is not the same as NATO qualifying defence spending. Pensions are in social protection here.'
        elif s['id'] == 'eu-transactions':
            specific = 'From 2010-11, VAT-based payments are no longer taken off the total. Negative values mean net receipts. They are not missing data.'
        tables.append(f'<details id="{s["id"]}"' + (' open' if s['id'] == 'services-total' else '') + f'><summary>{esc(s["label"])}</summary><p>United Kingdom. Scope: {esc(s["scope"])}. Source: July 2026. Status: outturn. {esc(specific)} <a href="#source-notes">All source notes</a>.</p>{table(s)}</details>')
    fixed = ''.join(f'<details><summary>{esc(s["label"])}</summary>{table(s, True)}</details>' for s in d['fixed_comparisons'])
    css = '''*{box-sizing:border-box}body{overflow-wrap:anywhere;margin:0;color:#20262b;background:#fafaf8;font:17px/1.6 system-ui,sans-serif}header,main,footer{max-width:1060px;margin:auto;padding:24px}a{color:#253f50;text-underline-offset:3px}a:focus-visible{outline:3px solid #252525;outline-offset:3px}h1{line-height:1.15;font-size:clamp(2rem,6vw,3.3rem)}h2{line-height:1.3}details{border-top:1px solid #b5b9bc;padding:14px 0}summary{cursor:pointer;font-weight:650}section{border-top:1px solid #b5b9bc;margin-top:32px;padding-top:12px}table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:.85rem;margin:24px 0}caption{text-align:left;font-weight:700;margin-bottom:10px}th,td{text-align:left;vertical-align:top;padding:10px 5px;border-bottom:1px solid #c5c8c9;overflow-wrap:anywhere}thead{background:#e7e9e8}th:first-child{width:16%}th:last-child{width:30%}td{font-variant-numeric:tabular-nums}small{font-size:.8em}code{overflow-wrap:anywhere}.skip{position:absolute;top:-100px}.skip:focus{top:0;background:white;padding:10px}footer{border-top:1px solid #b5b9bc;font-size:.85rem}@media(max-width:600px){header,main,footer{padding:16px}table{font-size:.8rem}th,td{padding:8px 3px}th:last-child{width:29%}}'''
    return f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>UK spending history | UnpoliticalAF</title><meta name="description" content="23 years of UK functional spending with cash, real and GDP-share values and explicit historical gaps."><style>{css}</style></head><body><a class="skip" href="#main">Skip to content</a>
<header><a href="index.html">UnpoliticalAF · latest spending</a></header><main id="main">
<h1>UK spending over time</h1><p>This covers 23 full fiscal years, 2003-04 to 2025-26. These are outturn figures. That means recorded spending, which may still change. A fiscal year runs from April to March.</p>
<p><a href="history-cash.html#services-total">See charts for cash, real spending and GDP share</a>. Switch views beside each chart. No JavaScript is needed.</p>
<p>Each table shows three views. <strong>Cash</strong> is the amount spent at the time. <strong>Real spending</strong> uses <strong>2025-26 prices</strong> to allow for price changes. <strong>Share of GDP</strong> shows spending as a share of the economy. GDP measures the size of the economy. Real figures use ONS GDP deflators released 30 June 2026. GDP shares use ONS GDP published 30 June 2026. We use the views in the Treasury source. We do not work out new values.</p>
<p>{esc(d['vintage_note'])} The <a href="index.html">latest overview</a> covers {d['latest_overview_year']}. We do not add its figures to these tables.</p>
<p>{esc(d['limitations'])}</p><nav aria-label="Spending areas">{contents} · <a href="#fixed-decades">Fixed ten-year snapshots</a></nav>
<section id="source-notes"><h2>Source, dates and definition breaks</h2><p><a href="{src['release_url']}">{esc(src['publication'])}</a>, HM Treasury. First published {src['published']}; July workbook vintage {src['workbook_vintage']}. The source page was updated {src['date']}. Downloaded {src['downloaded']}. {esc(src['next_release'])}</p>
<p><a href="data/history.csv">Download history CSV</a> · <a href="data/history.json">Data, locators and all source notes JSON</a> · <a href="sources/history.xlsx">Retained official workbook</a> · <a href="sources/history-manifest.json">Source manifest</a> · <a href="sources/history-release.json">Release metadata</a></p>
<p>The source cell is shown beside each year. Cash is on sheet 4_2. Real is on 4_3. GDP share is on 4_4. The two earlier TME snapshots use sheet 4_1. They use columns M for cash, N for real and O for GDP share. All amounts have one decimal place in the source. Each subcategory is part of a main area. Do not add it again. TES means spending on services. Add accounting adjustments to TES to get TME (Total Managed Expenditure). Rounding may cause small gaps. These totals cover different things.</p>
<ul>{note_items}</ul><p>Earlier TME snapshots (4_1) use the same price base: 2025-26. They use the same ONS GDP sources, dated 30 June 2026. Table 4.1 also has later OBR forecasts. We do not use those years here. Its TME excludes the short-term effects of banks classed as public sector (4_1!B51:B53).</p><p>Real-price note: {esc(d['notes']['4_3'][0]['text'])} (4_3!A28). GDP note: {esc(d['notes']['4_4'][0]['text'])} (4_4!A28).</p>
<p>SHA-256: <code>{src['sha256']}</code></p></section>
{''.join(tables)}
<section id="fixed-decades"><h2>Fixed ten-year snapshots back to 1945-46</h2><p>We start with {d['latest_overview_year']}, the latest overview year. We then step back ten years at a time to 1945-46. We use the same years for each area. Values come only from the July 2026 history above. Years not held in that source are marked as not available. They are never shown as zero. We do not add values from the July 2026 overview. {esc(d['limitations'])} <a href="#source-notes">Read all source notes and breaks</a> before comparing years.</p>{fixed}</section>
</main><footer>Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>. Source: HM Treasury.</footer></body></html>
'''


def history_outputs(root):
    d = history_extract(root)
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow(['series_id', 'label', 'scope', 'geography', 'year', 'status',
                     'cash_gbp_billion', 'real_gbp_billion_2025_26_prices', 'gdp_percent',
                     'cash_cell', 'real_cell', 'gdp_cell', 'missing_reason', 'source_vintage', 'source_sha256', 'selection'])
    for selection, series in [('annual', d['series']), ('fixed_decade', d['fixed_comparisons'])]:
        for s in series:
            original = next(t for t in d['series'] if t['id'] == s['id'])
            for p in s['values']:
                writer.writerow([s['id'], s['label'], original['scope'], d['geography'],
                    p['year'], p['status'], p['cash_gbp_billion'], p['real_gbp_billion'],
                    p['gdp_percent'], *[p['cells'].get(v, '') for v in VIEWS],
                    p['missing_reason'] or '', d['source']['workbook_vintage'],
                    d['source']['sha256'], selection])
    from history_charts import chart_outputs
    return {**chart_outputs(d), 'history.html': history_render(d).encode(),
            'data/history.json': (json.dumps(d, indent=2, ensure_ascii=False)+'\n').encode(),
            'data/history.csv': stream.getvalue().encode()}
