"""Static, source-backed history views. No client script or denominator joins."""
import html
import math

VIEWS = {
    'cash': ('cash_gbp_billion', 'Cash spending', '£ billion, cash'),
    'real': ('real_gbp_billion', 'Inflation-adjusted spending', '£ billion, 2025-26 prices'),
    'gdp': ('gdp_percent', 'Share of the economy', '% of UK GDP'),
}


def warning(ident):
    if ident == 'education':
        return 'The scope changes in 2011-12. The way student loans are counted changes. Do not compare values across this break as if their scope were the same.'
    if ident in ('transport', 'economic-affairs', 'services-total'):
        return 'The scope changes twice. From 2011-12, transport includes TfL subsidiaries. From 2015-16, spending on services includes Network Rail. TME includes Network Rail in all years shown.'
    if ident == 'defence':
        return 'This is UN COFOG defence. It is not NATO qualifying spending. Pensions are in social protection.'
    if ident == 'eu-transactions':
        return 'The scope changes in 2010-11. VAT-based payments are no longer taken off the total. Negative values mean net receipts.'
    return ''


def plot(points, field):
    """Zero-inclusive linear axes. Missing points break lines, never become zero."""
    values = [p[field] for p in points if p[field] is not None]
    assert all(math.isfinite(v) for v in values)
    low, high = min([0, *values]), max([0, *values])
    if high == low:
        high = low + 1
    x = lambda i: 54 + 258 * i / max(1, len(points)-1)
    y = lambda v: 210 - (v-low) / (high-low) * 170
    pieces = []
    ticks = sorted({low, high, 0} if low < 0 < high else {low, (low+high)/2, high})
    for v in ticks:
        colour = '#394b55' if v == 0 else '#b5b9bc'
        pieces.append(f'<path d="M54 {y(v):.2f}H312" stroke="{colour}"/><text x="48" y="{y(v)+4:.2f}" text-anchor="end">{v:,.1f}</text>')
    segment = []
    def flush():
        if segment:
            pieces.append('<polyline fill="none" stroke="#394b55" stroke-width="2.5" points="'+' '.join(segment)+'"/>')
            segment.clear()
    for i, point in enumerate(points):
        value = point[field]
        if value is None:
            flush()
        else:
            segment.append(f'{x(i):.2f},{y(value):.2f}')
            pieces.append(f'<circle cx="{x(i):.2f}" cy="{y(value):.2f}" r="2.5" fill="#394b55"/>')
    flush()
    for i in sorted({0, len(points)//2, len(points)-1}):
        pieces.append(f'<text x="{x(i):.2f}" y="238" text-anchor="middle">{html.escape(points[i]["year"])}</text>')
    return '<svg viewBox="0 0 360 255" aria-hidden="true" focusable="false">'+''.join(pieces)+'</svg>'


def chart_outputs(d):
    esc = html.escape
    css = '''*{box-sizing:border-box}body{margin:0;background:#fafaf8;color:#20262b;font:17px/1.6 system-ui,sans-serif;overflow-wrap:anywhere}header,main,footer{max-width:980px;margin:auto;padding:24px}h1,h2{line-height:1.2}a{color:#253f50;text-underline-offset:3px}a:focus-visible{outline:3px solid #252525;outline-offset:3px}nav{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}nav a,nav strong{padding:5px 10px;border:1px solid #858e91}section{border-top:1px solid #b5b9bc;margin-top:32px;padding-top:16px}svg{display:block;width:100%;max-width:540px;height:auto}svg text{font:14px system-ui,sans-serif;fill:#20262b}figure{margin:20px 0}figcaption{font-weight:650}table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:.9rem}caption{text-align:left;font-weight:650;margin:12px 0}th,td{text-align:left;padding:8px 4px;border-bottom:1px solid #c5c8c9;overflow-wrap:anywhere}thead{background:#e7e9e8}td{font-variant-numeric:tabular-nums}details{margin:16px 0}summary{cursor:pointer;font-weight:650}.skip{position:absolute;top:-100px}.skip:focus{top:0;background:white;padding:10px}footer{border-top:1px solid #b5b9bc;font-size:.85rem}@media(max-width:600px){header,main,footer{padding:16px}table{font-size:.8rem}nav{gap:8px}nav a,nav strong{padding:5px}}'''
    def navigation(view, ident=''):
        return '<nav aria-label="Choose spending view">'+''.join(
            f'<strong aria-current="page">{esc(title)}</strong>' if key == view else
            f'<a href="history-{key}.html{("#"+ident) if ident else ""}">{esc(title)}</a>'
            for key, (_, title, _) in VIEWS.items())+'</nav>'
    files = {}
    for view, (field, title, unit) in VIEWS.items():
        sections = []
        for s in d['series']:
            ident = s['id']
            rows = ''.join(f'<tr><th scope="row">{esc(p["year"])}</th><td>{p[field]:,.1f}</td><td>{esc(p["status"])}</td><td>{esc(p["cells"][view])}</td></tr>' if p[field] is not None else f'<tr><th scope="row">{esc(p["year"])}</th><td>Not available</td><td>{esc(p["missing_reason"] or "Source cell is blank; not zero.")}</td><td>{esc(p["cells"].get(view,""))}</td></tr>' for p in s['values'])
            sections.append(f'''<section id="{ident}"><h2>{esc(s['label'])}</h2>
<p>United Kingdom. Scope: {esc(s['scope'])}. Status: outturn. Source: July 2026.</p>
<p>{esc(warning(ident))} <a href="history.html#source-notes">All source notes and definition breaks</a>.</p>
{navigation(view, ident)}<figure><figcaption>{esc(title)} · {esc(unit)} · {esc(s['label'])}</figcaption>{plot(s['values'],field)}</figure>
<p>Each dot is one fiscal year. All axes include zero. Scales differ by area and view. Missing values break the line. All years show outturn: recorded spending, not forecasts.</p>
<details><summary>Data table: {esc(s['label'])} — {esc(title)}</summary><table><caption>{esc(s['label'])} · {esc(unit)} · {esc(s['scope'])}</caption><thead><tr><th scope="col">Fiscal year</th><th scope="col">{esc(unit)}</th><th scope="col">Status</th><th scope="col">Source cell</th></tr></thead><tbody>{rows}</tbody></table></details></section>''')
        source = d['source']
        page = f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)} over time | UnpoliticalAF</title><style>{css}</style></head><body><a class="skip" href="#main">Skip to content</a><header><a href="index.html">UnpoliticalAF · latest spending</a> · <a href="history.html">History tables and methods</a></header><main id="main"><h1>UK spending over time</h1><p>View shown: <strong>{esc(title)}</strong> ({esc(unit)}). This covers 2003-04 to 2025-26. Fiscal years run from April to March. All figures are recorded spending (outturn). They may still change.</p>{navigation(view)}
<p>Cash is the amount spent at the time. Real spending allows for price changes. It uses 2025-26 prices and ONS GDP deflators released 30 June 2026. Share of the economy means spending as a share of UK GDP. This uses ONS GDP published 30 June 2026. All three views come from the Treasury source. They use the same workbook and years. They cover the same UK area and the same types of spending. We do not work out new values.</p>
<p>Source: <a href="{source['release_url']}">{esc(source['publication'])}</a>, HM Treasury. Published {source['published']}; source page updated {source['date']}. {esc(source['next_release'])} Cash: table 4.2; real: 4.3; GDP share: 4.4. <a href="sources/history-manifest.json">Source URL, dates and SHA-256</a> · <a href="sources/history.xlsx">Official workbook</a> · <a href="data/history.csv">Download data CSV</a>.</p>
<p>{esc(d['vintage_note'])} Each subcategory is part of its parent area. Do not add it twice. Spending on services and Total Managed Expenditure (TME) are different totals. The source rounds all values to one decimal place.</p><p>Jump to an area: {' · '.join(f'<a href="#{s["id"]}">{esc(s["label"])}</a>' for s in d['series'])}</p>{''.join(sections)}</main><footer>Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>. Source: HM Treasury.</footer></body></html>\n'''
        files[f'history-{view}.html'] = page.encode()
    return files
