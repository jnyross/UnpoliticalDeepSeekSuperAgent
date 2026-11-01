"""UK receipts, borrowing and debt from the retained official OBR databank.

No network access during outputs(). refresh() validates new official bytes before
replacing its retained files. The caller stages the whole build atomically.
"""
import csv
import hashlib
import html
from html.parser import HTMLParser
import io
import json
import math
import re
from datetime import datetime, timezone
import urllib.request

import openpyxl

PAGE = 'https://obr.uk/data/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
}
RECEIPTS = 'Receipts (£bn)'
AGGREGATES = 'Aggregates (£bn)'
SCOPE = 'UK public sector, OBR public finances definitions'
UNIT = 'GBP billion, cash'
TOLERANCE = 0.000001


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs).get('href', ''))

    def handle_data(self, data):
        self.text.append(data)


def _fetch(url):
    assert url.startswith(('https://obr.uk/', 'https://www.obr.uk/')), 'Only official OBR sources allowed'
    from discover import OfficialRedirect, allowed_url
    hosts = ('obr.uk', 'www.obr.uk')
    assert allowed_url(url, hosts), 'Only official OBR sources allowed'
    opener = urllib.request.build_opener(OfficialRedirect(hosts))
    with opener.open(urllib.request.Request(url, headers=HEADERS), timeout=90) as response:
        assert allowed_url(response.url, hosts)
        return response.read(), response.url


def refresh(root):
    """Discover latest official databank, fetch via urllib and retain with hashes."""
    metadata, _ = _fetch(PAGE)
    parser = Links()
    parser.feed(metadata.decode('utf-8'))
    link = next(u.split('?')[0] for u in parser.links
                if '/download/public-finances-databank-' in u)
    raw, url = _fetch(link)
    workbook = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
    # Validate the complete extraction and its identities before retaining any bytes.
    _extract(workbook, {})
    plain = ' '.join(parser.text)
    match = re.search(r'Public finances databank\s*[–—-]\s*([^\n]+?)\s+(\d{1,2} [A-Z][a-z]+ \d{4})\s*[–—-]', plain)
    assert match, 'Databank publication/date not found in official release page'
    publication = 'Public finances databank – ' + ' '.join(match[1].split())
    published = datetime.strptime(match[2], '%d %B %Y').date().isoformat()
    digest = hashlib.sha256(raw).hexdigest()
    manifest_path = root / 'sources/income-manifest.json'
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest = dict(file='income.xlsx', url=url, download_url=link, sha256=digest,
        publication=publication, published=published, date=published,
        downloaded=previous.get('downloaded') if previous.get('sha256') == digest else datetime.now(timezone.utc).date().isoformat(),
        release_url=PAGE, metadata_file='income-release.txt',
        metadata_sha256=hashlib.sha256(metadata).hexdigest(),
        geography='United Kingdom', scope=SCOPE,
        next_release='No next release date is announced on the retained OBR data page; databanks are normally updated around two working days after the monthly public finance release.')
    (root / 'sources/income.xlsx').write_bytes(raw)
    (root / 'sources/income-release.txt').write_bytes(metadata)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')


def _extract(workbook, source):
    receipts, aggregates = workbook[RECEIPTS], workbook[AGGREGATES]
    assert receipts['AG4'].value == 'Public sector current receipts'
    assert receipts['AH4'].value == 'National accounts taxes'
    assert aggregates['O4'].value == 'Public sector net borrowing'
    assert aggregates['X4'].value == 'Public sector net debt'
    note = receipts['C41'].value
    match = re.search(r'Forecast years from (\d{4})-\d{2}', note)
    assert match, 'Source must explicitly distinguish outturn from forecast'
    first_forecast = int(match[1])
    # Latest complete outturn in this source, never a forecast or partial fiscal year.
    candidates = [(c.row, c.value) for c in receipts['B']
                  if isinstance(c.value, str) and re.fullmatch(r'\d{4}-\d{2}', c.value)
                  and int(c.value[:4]) < first_forecast]
    row, year = max(candidates, key=lambda x: x[1])
    arow = next(c.row for c in aggregates['B'] if c.value == year)
    assert receipts['C40'].value == aggregates['C94'].value
    assert receipts['C41'].value == aggregates['C95'].value
    records = []

    def raw(ident, label, kind, sheet, cell, period=None):
        value = workbook[sheet][cell].value
        assert isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value), f'Missing/non-numeric: {sheet}!{cell}'
        col = re.match(r'[A-Z]+', cell)[0]
        code = workbook[sheet][f'{col}5'].value
        record = dict(id=ident, label=label, kind=kind, value_gbp_billion=round(value, 12),
            cells=[f'{sheet}!{cell}'], formula=None, operands=[], scope=SCOPE,
            period=period or year, status='outturn', unit=UNIT, geography='United Kingdom',
            ons_code=code)
        records.append(record)
        return record

    for col in range(3, 30):
        letter = openpyxl.utils.get_column_letter(col)
        label = receipts.cell(4, col).value
        label = re.sub(r'(?<=[a-z)])\d+$', '', label).strip()
        raw('receipt-' + letter.lower(), label, 'tax-type', RECEIPTS, f'{letter}{row}')
    for ident, label, kind, col in [
            ('interest-dividends', 'Interest and dividend receipts', 'non-tax-type', 'AD'),
            ('operating-surplus', 'Gross operating surplus', 'non-tax-type', 'AE'),
            ('mixed-other-receipts', 'Other public sector taxes and receipts (mixed source line)', 'mixed', 'AF'),
            ('receipts', 'Public sector current receipts', 'total', 'AG'),
            ('taxes', 'National accounts taxes', 'total', 'AH')]:
        raw(ident, label, kind, RECEIPTS, f'{col}{row}')
    for ident, label, kind, col in [
            ('tme', 'Total Managed Expenditure', 'spending', 'D'),
            ('borrowing', 'Public sector net borrowing', 'borrowing', 'O'),
            ('debt', 'Public sector net debt', 'stock', 'X')]:
        raw(ident, label, kind, AGGREGATES, f'{col}{arow}',
            'end-March ' + str(int(year[:4]) + 1) if ident == 'debt' else None)
    by_id = {r['id']: r for r in records}

    def derived(ident, label, kind, operands, formula):
        first, *subtract = operands
        value = by_id[first]['value_gbp_billion'] - sum(by_id[t]['value_gbp_billion'] for t in subtract)
        record = dict(id=ident, label=label, kind=kind, value_gbp_billion=round(value, 12),
            cells=list(dict.fromkeys(c for t in operands for c in by_id[t]['cells'])),
            formula=formula, operands=operands, scope=SCOPE, period=year,
            status='outturn', unit=UNIT, geography='United Kingdom', ons_code=None)
        records.append(record)
        by_id[ident] = record

    tax_ids = [r['id'] for r in records if r['kind'] == 'tax-type']
    derived('other-taxes', 'Other taxes (residual, not separately named here)', 'tax-type',
            ['taxes'] + tax_ids, 'taxes - sum(receipt-c through receipt-ac)')
    derived('non-tax', 'Non-tax receipts', 'total', ['receipts', 'taxes'], 'receipts - taxes')
    derived('other-non-tax', 'Other non-tax receipts (residual)', 'non-tax-type',
            ['non-tax', 'interest-dividends', 'operating-surplus'],
            'non-tax - interest-dividends - operating-surplus')
    value = lambda ident: by_id[ident]['value_gbp_billion']
    checks = [
        dict(name='Tax breakdown', formula='sum(tax-type records) - taxes',
             residual_gbp_billion=sum(r['value_gbp_billion'] for r in records if r['kind'] == 'tax-type') - value('taxes')),
        dict(name='Non-tax breakdown', formula='sum(non-tax-type records) - non-tax',
             residual_gbp_billion=sum(r['value_gbp_billion'] for r in records if r['kind'] == 'non-tax-type') - value('non-tax')),
        dict(name='Mixed other line split', formula='other-taxes + other-non-tax - mixed-other-receipts',
             residual_gbp_billion=value('other-taxes') + value('other-non-tax') - value('mixed-other-receipts')),
        dict(name='Spending and receipts', formula='tme - receipts - borrowing',
             residual_gbp_billion=value('tme') - value('receipts') - value('borrowing')),
        dict(name='Receipts across sheets', formula='Receipts AG - Aggregates C',
             residual_gbp_billion=value('receipts') - aggregates[f'C{arow}'].value),
        dict(name='Taxes across sheets', formula='Receipts AH - Aggregates I',
             residual_gbp_billion=value('taxes') - aggregates[f'I{arow}'].value),
    ]
    for check in checks:
        assert abs(check['residual_gbp_billion']) <= TOLERANCE, check
        check['residual_gbp_billion'] = round(check['residual_gbp_billion'], 12)
        check['tolerance_gbp_billion'] = TOLERANCE
    notes = [dict(cell=f'{sheet}!{cell}', text=workbook[sheet][cell].value)
             for sheet, cells in [(RECEIPTS, ['C40', 'C41', 'C42']),
                 ('Glossary', ['C5', 'C6', 'C11', 'C14', 'C15'])] for cell in cells]
    return dict(source=source, geography='United Kingdom', year=year, status='outturn',
        unit=UNIT, scope=SCOPE, records=records, checks=checks, notes=notes,
        rounding='Raw values are retained to 12 decimal places in GBP billion; HTML rounds to 0.1 billion. Source actuals are recorded to 0.001 billion. Reconciliations use unrounded data with 0.000001 billion numeric tolerance, not independently rounded display amounts.',
        selection='Latest complete outturn before the first forecast year stated in Receipts (£bn)!C41.',
        reconciliation='All identities use one OBR workbook vintage and public sector accounting basis. Tax rows C:AC plus the derived other-tax residual equal national accounts taxes. AF is a mixed tax/non-tax line, not a tax type. It is split by residual against the published tax total; the residuals do not identify further individual taxes. The VAT refund row belongs in the published national accounts tax basis: do not subtract it again or treat it as non-tax. Negative tax entries are net receipts or repayments, not missing data. TME less current receipts equals net borrowing on this accrued basis. Debt is not added to annual receipts or borrowing; changes in debt also reflect financial transactions and cash/accrual differences. This workbook is not reconciled to a separate Treasury workbook vintage.')


def extract(root):
    source = json.loads((root / 'sources/income-manifest.json').read_text())
    raw = (root / 'sources' / source['file']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source['sha256'], 'Income workbook hash changed'
    metadata = (root / 'sources' / source['metadata_file']).read_bytes()
    assert hashlib.sha256(metadata).hexdigest() == source['metadata_sha256'], 'Income metadata hash changed'
    return _extract(openpyxl.load_workbook(io.BytesIO(raw), data_only=True), source)


def render(data):
    esc = html.escape
    source = data['source']
    records = {r['id']: r for r in data['records']}
    def amount(ident):
        return f'£{records[ident]["value_gbp_billion"]:,.1f} billion'
    def table(title, rows):
        body = ''.join(f'<tr><th scope="row">{esc(r["label"])}</th><td>{r["value_gbp_billion"]:,.1f}</td><td>{esc(r["status"])}<br>{esc(r["period"])}</td><td><small>{esc("; ".join(r["cells"]))}{"<br>Derived: " + esc(r["formula"]) if r["formula"] else ""}</small></td></tr>' for r in rows)
        return f'<table><caption>{esc(title)} · United Kingdom · cash £ billion</caption><thead><tr><th scope="col">Type</th><th scope="col">£bn</th><th scope="col">Status / period</th><th scope="col">Source cell / formula</th></tr></thead><tbody>{body}</tbody></table>'
    css = '''*{box-sizing:border-box}body{margin:0;color:#20262b;background:#fafaf8;font:17px/1.6 system-ui,sans-serif;overflow-wrap:anywhere}header,main,footer{max-width:1060px;margin:auto;padding:24px}a{color:#253f50;text-underline-offset:3px}a:focus-visible{outline:3px solid #252525;outline-offset:3px}h1{line-height:1.15;font-size:clamp(2rem,6vw,3.3rem)}h2{line-height:1.3}section{border-top:1px solid #b5b9bc;margin-top:32px;padding-top:12px}table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:.85rem;margin:24px 0}caption{text-align:left;font-weight:700;margin-bottom:10px}th,td{text-align:left;vertical-align:top;padding:10px 5px;border-bottom:1px solid #c5c8c9;overflow-wrap:anywhere}thead{background:#e7e9e8}th:first-child{width:32%}th:nth-child(2){width:13%}th:nth-child(3){width:20%}td{font-variant-numeric:tabular-nums}small{font-size:.85em}.skip{position:absolute;top:-100px}.skip:focus{top:0;background:white;padding:10px}footer{border-top:1px solid #b5b9bc;font-size:.85rem}@media(max-width:600px){header,main,footer{padding:16px}table{font-size:.8rem}th,td{padding:8px 3px}}'''
    taxes = [r for r in data['records'] if r['kind'] == 'tax-type']
    non_tax = [r for r in data['records'] if r['kind'] == 'non-tax-type']
    note_html = ''.join(f'<li>{esc(n["text"])} <small>({esc(n["cell"])})</small></li>' for n in data['notes'])
    checks = ''.join(f'<li>{esc(c["name"])}: {esc(c["formula"])} = {c["residual_gbp_billion"]:g} £bn (tolerance {c["tolerance_gbp_billion"]:g} £bn).</li>' for c in data['checks'])
    income_tax = sum(records[i]['value_gbp_billion'] for i in ['receipt-q', 'receipt-r', 'receipt-s'])
    return f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>UK tax, receipts, borrowing and debt | UnpoliticalAF</title><meta name="description" content="Actual UK tax types, non-tax receipts, annual borrowing and debt stock with official OBR source cells."><style>{css}</style></head><body><a class="skip" href="#main">Skip to content</a><header><a href="index.html">UnpoliticalAF · latest spending</a> · <a href="history.html">Spending history</a></header><main id="main"><h1>UK tax, receipts, borrowing and debt</h1>
<p>In {data['year']}, the UK public sector took in <strong>{amount('receipts')}</strong>. Of this, {amount('taxes')} was tax and {amount('non-tax')} was non-tax income. These are <strong>outturn</strong> figures: recorded results that can still change. They are not forecasts.</p>
<p>Spending was {amount('tme')}. The gap was <strong>{amount('borrowing')} of net borrowing</strong>. Debt stood at <strong>{amount('debt')}</strong> at end-March {int(data['year'][:4])+1}.</p>
<nav aria-label="Income sections"><a href="#tax">Tax types</a> · <a href="#non-tax">Non-tax income</a> · <a href="#borrowing-debt">Borrowing and debt</a> · <a href="#sources">Check the source</a></nav>
<p>All figures cover the United Kingdom public sector, not just central government. Cash means pounds at the time, not adjusted for price rises. A fiscal year runs from April to March. We use one OBR source vintage for all sums on this page, not the separate Treasury spending page.</p>
<section id="tax"><h2>Which taxes bring in income?</h2><p>Income tax brought in £{income_tax:,.1f} billion. This is the sum of PAYE, self assessed and other income tax (rows Q, R and S below). National Insurance brought in {amount('receipt-ab')}; VAT net of refunds brought in {amount('receipt-c')}. The full list below keeps the source tax types. NICs are part of the tax total here.</p>
{table('Tax types in ' + data['year'], taxes + [records['taxes']])}
<p>VAT has two rows in this source. Its national accounts tax total includes the VAT refund row. Do not take refunds off a second time. A minus sign means net repayments or a tax adjustment, not a missing figure.</p>
<p>The source groups some taxes with other receipts. “Other taxes” is the tax total less all the named tax rows. It is not a claim to know each tax in that group. This avoids calling a mixed tax and non-tax line all tax.</p></section>
<section id="non-tax"><h2>Receipts are not all tax</h2><p>Non-tax income was {amount('non-tax')}. It includes interest, dividends and income from public sector trading. Gross operating surplus is a national accounts measure of trading income before the cost of worn-out assets. It is not all cash paid in by households.</p>
{table('Non-tax receipts in ' + data['year'], non_tax + [records['non-tax']])}
<p>We find non-tax receipts by taking tax off total receipts. Other non-tax receipts are what is left after interest, dividends and gross operating surplus. This is a residual, not a new named source of income.</p></section>
<section id="borrowing-debt"><h2>Borrowing is not tax. Debt is a stock.</h2><p>Borrowing is the gap between spending and receipts in a year. It is not a tax or a receipt. Net borrowing uses the accrued basis: income and costs count when they arise, not just when cash moves.</p>
{table('Annual flows and the year-end debt stock', [records[i] for i in ['receipts','taxes','non-tax','tme','borrowing','debt']])}
<p>Debt is a stock at a point in time. Net debt is debt liabilities less liquid assets, such as cash. It is not the same as all assets less all debts. Do not add debt to annual income. A change in debt need not equal that year’s borrowing: loans, asset sales and the timing of cash can also change debt.</p>
<p>On this source basis, receipts plus net borrowing equal Total Managed Expenditure (TME). TME is not the same as spending on services. We do not combine these OBR sums with a separate Treasury release. <a href="index.html">See the spending page and its own scope</a>.</p></section>
<section id="sources"><h2>Check these numbers</h2><p><a href="{esc(source['release_url'])}">{esc(source['publication'])}</a>, Office for Budget Responsibility. Published {source['published']}; source date {source['date']}; downloaded {source['downloaded']}. {esc(source['next_release'])}</p>
<p><a href="data/income.csv">Download CSV</a> · <a href="data/income.json">Download JSON with cell references and formulas</a> · <a href="sources/income.xlsx">Retained official OBR workbook</a> · <a href="{esc(source['download_url'])}">Official download</a> · <a href="sources/income-manifest.json">Source manifest</a> · <a href="sources/income-release.txt">Retained release page</a></p>
<p>The tables give exact sheet and cell references. All rows are {data['year']} outturn, except debt which is the stock at year end. The workbook has forecasts too; none are used on this page. We select the latest complete year before the first forecast year in the source note.</p>
<p>{esc(data['rounding'])}</p><p>{esc(data['reconciliation'])}</p><h3>Checks on the source basis</h3><ul>{checks}</ul><h3>Source notes and definitions</h3><ul>{note_html}</ul><p>Workbook SHA-256: <code>{source['sha256']}</code></p><p>Release page SHA-256: <code>{source['metadata_sha256']}</code></p></section>
</main><footer>Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>. Source: Office for Budget Responsibility, using ONS/HM Treasury public finances data.</footer></body></html>'''


def outputs(root):
    """Return deterministic generated page and open datasets; do not write site files."""
    data = extract(root)
    stream = io.StringIO()
    columns = ['id', 'label', 'kind', 'value_gbp_billion', 'unit', 'geography',
               'scope', 'period', 'status', 'cells', 'ons_code', 'formula', 'operands',
               'source_publication', 'source_published', 'source_url', 'source_sha256']
    writer = csv.DictWriter(stream, columns, lineterminator='\n')
    writer.writeheader()
    for record in data['records']:
        writer.writerow({**record, 'cells': '; '.join(record['cells']),
            'operands': '; '.join(record['operands']),
            **{'source_' + field: data['source'][field] for field in ['publication', 'published', 'url', 'sha256']}})
    return {'income.html': render(data).encode(),
            'data/income.json': (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode(),
            'data/income.csv': stream.getvalue().encode()}
