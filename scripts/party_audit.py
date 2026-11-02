"""Reproducible financial-figure trace, not a substitute for publisher tables.

Native prose locators remain valid evidence but do not pass the table/row rubric.
The audit includes repeated occurrences so a changed displayed claim cannot hide.
"""
import json
from pathlib import Path
import re
import subprocess
import tempfile
from datetime import date

import parties

# Dates and seat counts are not financial claims. Labour's table uses bare £m values.
FIGURE = re.compile(r'£\d[\d,]*(?:\.\d+)?(?:\s*(?:trillion|billion|million|bn|m)\b)?|\b\d+(?:\.\d+)?(?:%|\s+per cent\b)|\b\d{1,3}(?:,\d{3})+\b', re.IGNORECASE)


def financial_matches(text, source_id):
    # Only the selected Labour £m table prints unprefixed cash values.
    return [m for m in FIGURE.finditer(text) if m.group().startswith('£') or '%' in m.group() or 'per cent' in m.group().casefold() or source_id == 'labour']


def audit(root, data):
    root = Path(root)
    sources = {s['id']: s for s in data['sources'] + data.get('evidence_sources', [])}
    native = json.loads((root / 'sources/party-figure-locators.json').read_text())
    assert set(native) <= set(sources), 'Unknown table source'
    manifest = []
    for source in sources.values():
        date.fromisoformat(source['downloaded'])
        assert re.fullmatch(r'\d{4}(?:-\d{2}-\d{2})?', source['published']), 'Invalid publication date'
        if len(source['published']) == 10:
            date.fromisoformat(source['published'])
        for file, hash_key in [('file', 'sha256'), ('text_file', 'text_sha256')]:
            assert parties.digest(root / 'sources' / source[file]) == source[hash_key], 'Audit source hash changed'
        manifest.append(dict(source))
    # A table citation is additional evidence, not a replacement quote. Check its
    # headings, row, column and amount on the actual retained PDF, independently.
    for source_id, tables in native.items():
        source = sources[source_id]
        for table in tables:
            assert set(table) == {'pdf_page', 'table', 'row_label', 'column', 'value', 'year', 'period', 'unit', 'unit_locator', 'row_value_text'}
            assert type(table['pdf_page']) is int and table['pdf_page'] > 0
            assert table['year'] is None or re.fullmatch(r'\d{4}-\d{2}', table['year'])
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / 'table.txt'
                subprocess.run(['pdftotext', '-layout', '-f', str(table['pdf_page']), '-l', str(table['pdf_page']), str(root / 'sources' / source['file']), str(out)], check=True, capture_output=True)
                text = parties.normal(out.read_text())
            assert table['unit'] in ('GBP million', 'GBP billion', 'percent')
            for key in ('table', 'row_label', 'column', 'value', 'period', 'unit_locator'):
                assert table[key] and parties.normal(table[key]) in text, f'Table {key} not on PDF page: {source_id}'
            # Keep a literal row/value span: Labour's two totals share one
            # layout line, so mere page presence or proximity is insufficient.
            span = parties.normal(table['row_value_text'])
            assert span in text, 'Native row/value span not on PDF page'
            assert parties.normal(table['row_label']) in span, 'Row label not in native span'
            assert parties.normal(table['value']) in span, 'Amount not in native row span'
            if table['year']:
                assert table['year'] in text, 'Table year not on PDF page'
    figures = []
    for party in data['parties']:
        for field in parties.LIMITS:
            ref = party.get('evidence', {}).get(field)
            if ref and field == 'costing':
                assert not FIGURE.search(party[field]), 'Unreferenced financial claim in costing prefix'
            quote = ref['quote'] if ref else party[field]
            source_id = ref['source_id'] if ref else party['source_id']
            matches = financial_matches(quote, source_id)
            if not matches:
                continue
            # All displayed financial amounts must come from a checked direct quote.
            assert ref or field == 'excerpt', f'Unreferenced financial claim: {party["name"]}/{field}'
            source_id = ref['source_id'] if ref else party['source_id']
            source = sources[source_id]
            locator = {key: (ref or party)[key] for key in ('locator', 'pdf_page', 'text_line') if key in (ref or party)}
            for match in matches:
                amount = match.group().strip()
                lower_amount = amount.casefold()
                unit = ('percent' if '%' in amount or 'per cent' in lower_amount else 'GBP trillion' if 'trillion' in lower_amount
                        else 'GBP billion' if re.search(r'billion|bn', lower_amount)
                        else 'GBP million' if re.search(r'million|m$', lower_amount) or source_id == 'labour' else 'GBP')
                def same_value(table):
                    # Currency scale is stated in the native column/period. Do not
                    # attach a cash-total row to a rate or a different amount.
                    digits = lambda value: re.sub(r'[^0-9.]', '', value)
                    return digits(amount) == digits(table['value']) and unit == table['unit']
                tables = [table for table in native.get(source_id, []) if same_value(table)]
                figures.append({'party_id': party['id'], 'party': party['name'], 'field': field, 'unit': unit,
                                'figure': match.group().strip(), 'quote_offset': match.start(),
                                'quote': quote, 'source_id': source_id, 'file': source['file'],
                                'native_locator': locator, 'period_and_year': party['year'],
                                'scope': party['scope'], 'baseline': party['baseline'], 'status': party['status'],
                                'supplemental_source_tables': tables,
                                'table_row_available': bool(tables),
                                'limitation': None if tables else 'The cited native evidence is prose, not a publisher table/row. No matching table is verified here.'})
    return {'schema_version': 1, 'scope': 'Displayed financial amounts and tax rates in the historical party template; repeated quotes are separate occurrences. Not an audit of all site figures.',
            'accuracy_l2_claimed': False,
            'limitation': 'Supplemental tables do not replace the quoted evidence or establish an unstated fiscal year. Prose-only and annual-without-fiscal-year evidence remains explicit. See docs/accuracy-source-research.md in the repository.',
            'roster_source': data['roster'], 'source_manifest': manifest, 'figures': figures,
            'occurrences': len(figures), 'occurrences_without_source_table': sum(not f['table_row_available'] for f in figures)}


def output(root, data):
    return (json.dumps(audit(root, data), indent=2, ensure_ascii=False) + '\n').encode()
