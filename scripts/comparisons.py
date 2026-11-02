"""Ten-year answers from Treasury's published, already adjusted Chapter 4 tables."""
import hashlib
import html
import json
import math
import re
import openpyxl


def extract(root):
    source = json.loads((root/'sources/trends-manifest.json').read_text())
    raw = root/'sources'/source['file']
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == source['sha256'], 'Trends source hash changed'
    w = openpyxl.load_workbook(raw, data_only=True)
    try:
        real, share = w['4_3'], w['4_4']
        assert real['A20'].value == share['A20'].value == '7. Health'
        assert real['A27'].value == share['A27'].value == 'Total Managed Expenditure(8)'
        assert real['B4'].value == share['B4'].value == 'outturn'
        assert '2025-26 price levels' in real['A28'].value and '30 June 2026' in real['A28'].value
        assert '30 June 2026' in share['A28'].value
        years = {int(c.value[:4]): c.column for c in real[5] if isinstance(c.value, str) and re.fullmatch(r'\d{4}-\d{2}', c.value)}
        latest = max(years)
        assert real.cell(3,years[latest]).value == '£ billion' and share.cell(3,years[latest]).value == 'per cent', 'Source units changed'
        assert latest-10 in years, 'Missing exact ten-year baseline; do not substitute another year'
        points = []
        for start in (latest-10, latest):
            col = years[start]
            year = real.cell(5,col).value
            assert share.cell(5,col).value == year
            record = {'year': year, 'status': 'outturn'}
            for key, sheet, row, unit, scope in (
                ('health_real', real, 20, 'GBP billion, 2025-26 prices', 'Public sector expenditure on services: health'),
                ('tme_gdp', share, 27, 'percent of GDP', 'Total Managed Expenditure, excluding temporary effects of public-sector banks')):
                cell = sheet.cell(row,col)
                assert type(cell.value) in (int,float) and math.isfinite(cell.value)
                record[key] = dict(value=cell.value, sheet=sheet.title, cell=cell.coordinate, row=sheet.cell(row,1).value, unit=unit, scope=scope, geography='United Kingdom')
            points.append(record)
        old, new = points
        return dict(source=source, points=points,
                    health_change=new['health_real']['value']-old['health_real']['value'],
                    health_percent=(new['health_real']['value']/old['health_real']['value']-1)*100,
                    gdp_change=new['tme_gdp']['value']-old['tme_gdp']['value'],
                    formulas={'health_change': 'latest health_real - baseline health_real', 'health_percent': '(latest health_real / baseline health_real - 1) * 100', 'gdp_change': 'latest tme_gdp - baseline tme_gdp'},
                    deflator=real['A28'].value, gdp_vintage=share['A28'].value)
    finally:
        w.close()


def render(d):
    old,new = d['points']; src=d['source']; esc=html.escape
    rows=''.join(f'<tr><th scope="row">{p["year"]} (outturn)</th><td>£{p["health_real"]["value"]:.1f}bn<br><code>4_3!{p["health_real"]["cell"]}</code></td><td>{p["tme_gdp"]["value"]:.1f}%<br><code>4_4!{p["tme_gdp"]["cell"]}</code></td></tr>' for p in d['points'])
    return f'''<section id="ten-years"><h2>What changed over ten years?</h2>
<h3 id="health-ten-years">Has health spending gone up or down after inflation?</h3>
<p><strong>Health spending went {'up' if d['health_change'] >= 0 else 'down'} by {abs(d['health_percent']):.1f}%</strong> from {old['year']} to {new['year']}. It went from £{old['health_real']['value']:.1f} billion to £{new['health_real']['value']:.1f} billion, a change of £{d['health_change']:.1f} billion in {new['year']} prices.</p>
<p>This is UK public sector spending on health services, including day-to-day costs and investment. It is not just the NHS England budget. Treasury adjusts for inflation with ONS GDP deflators released 30 June 2026. This is a whole-economy price measure, not a measure of NHS costs.</p>
<h3 id="gdp-ten-years">Is total spending a bigger or smaller share of the economy?</h3>
<p><strong>Total spending was a {'bigger' if d['gdp_change'] >= 0 else 'smaller'} share of the economy</strong>: {new['tme_gdp']['value']:.1f}% of GDP in {new['year']}, compared with {old['tme_gdp']['value']:.1f}% in {old['year']}. That is a change of {d['gdp_change']:.1f} percentage points.</p>
<p>Here total spending means Total Managed Expenditure (TME), not spending on services alone. It includes accounting adjustments and excludes the temporary effects of banks being classed as public sector. GDP measures the size of the economy; this uses the ONS figures published 30 June 2026.</p>
<table class="comparison"><caption>Ten-year comparison: UK outturn. Health in {new['year']} prices; TME as a share of GDP.</caption><thead><tr><th scope="col">Year</th><th scope="col">Real health spending</th><th scope="col">TME / GDP</th></tr></thead><tbody>{rows}</tbody></table>
<p>The end year is the latest in these tables. The start year is exactly ten years earlier, not a hand-picked year. All four inputs are outturn, not forecasts. The source notes no health definition break within this interval. Spending since 2020-21 was affected by Covid-19 and cost-of-living measures. Earlier series have breaks, including the treatment of Network Rail and student loans; this comparison does not extend across those breaks or fill missing years.</p>
<p>Check: <a href="sources/trends.xlsx">official Trends in public spending workbook</a>, Table 4.3 row “7. Health” and Table 4.4 row “Total Managed Expenditure(8)”. Source: <a href="{src['release_url']}">{esc(src['publication'])}</a>; published {src['published']}, updated {src['date']}, downloaded {src['downloaded']}. No next release date is announced in the retained metadata.</p>
<p>Method: health change = end minus start; percent change = (end / start − 1) × 100. GDP-share change = end share minus start share, in percentage points, not percent growth. We use Treasury's published rounded inputs (health to £0.1 billion and GDP shares to 0.1 point), so changes are approximate. No new inflation series is spliced into the release.</p>
<p><a href="data/comparisons.json">Download inputs, formulas and cell locators (JSON)</a> · <a href="data/comparisons.csv">Download inputs (CSV)</a> · <a href="sources/trends-manifest.json">Download URL, dates and SHA-256</a></p></section>'''
