"""Version the documentation-only comprehension kit; never collect participant data."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
KIT = Path('docs/comprehension-kit')
INPUTS = ('site/index.html', 'site/data/spending.json', 'site/data/comparisons.json',
          'sources/manifest.json', 'sources/trends-manifest.json',
          'sources/spending.xlsx', 'sources/trends.xlsx')


def questions(root):
    text = (root/'docs/rubric.md').read_text().split('## 3. Plain-language comprehension')[1].split('| Level')[0]
    result = re.findall(r'^\d\. (.+)$', text, re.M)
    if len(result) != 8:
        raise ValueError('Expected eight fixed rubric questions')
    return result


def answers(root):
    d = json.loads((root/'site/data/spending.json').read_text())
    c = json.loads((root/'site/data/comparisons.json').read_text())
    if d['year'] != '2025-26' or d['status'] != 'outturn':
        raise ValueError('Review fixed debt-interest question for a new year/status')
    old, new = c['points']
    top = max(d['rows'], key=lambda r: r['value'])
    health = next(r for r in d['rows'] if r['label'] == 'Total health')
    defence = next(r for r in d['rows'] if r['label'] == 'Total defence')
    pension = next(r for r in d['extras'] if r['label'] == 'of which: pensions')
    interest = next(r for r in d['extras'] if r['label'] == 'of which: central government debt interest')
    money = lambda r: f"£{r['value']/1000:,.1f} billion"
    loc = lambda r: f"5_2!{r['cell']}"
    return [
        (top['label'].removeprefix('Total '), f"{loc(top)}; largest of the eleven functional areas, not TME"),
        (f"£{health['value']/d['total']['value']*100:.2f} per £100", f"{loc(health)} / {loc(d['total'])} × 100; spending on services, not TME"),
        (f"{money(interest)}; {d['year']} outturn (not forecast)", f"{loc(interest)}; gross central government debt interest, not public debt transactions"),
        (f"{'Up' if c['health_change'] > 0 else 'Down' if c['health_change'] < 0 else 'Unchanged'} after inflation", f"{old['year']} to {new['year']}; 4_3!{old['health_real']['cell']} to 4_3!{new['health_real']['cell']}: £{old['health_real']['value']:.1f}bn to £{new['health_real']['value']:.1f}bn in 2025-26 prices"),
        (f"{'Bigger' if c['gdp_change'] > 0 else 'Smaller' if c['gdp_change'] < 0 else 'Unchanged'} share of GDP", f"{old['year']} to {new['year']}; 4_4!{old['tme_gdp']['cell']} to 4_4!{new['tme_gdp']['cell']}: {old['tme_gdp']['value']:.1f}% to {new['tme_gdp']['value']:.1f}%; TME, not services alone"),
        (f"Old-age pensions {money(pension)}; defence {money(defence)}", f"{loc(pension)} and {loc(defence)}; UN functional definition, not NATO; pensions are part of social protection"),
        ('None on the home page; its figures are outturn, not forecasts', f"Spending status: {d['status']}; comparison statuses: {old['status']}, {new['status']}; this question is restricted to the home page, not income-page forecasts"),
        ('Follow a money link to its source row, or Check the source to the official workbook and table/cell', f"For Q3: index.html#{interest['cell']}, Table 5.2, {loc(interest)}; source URL and SHA-256 in sources/manifest.json"),
    ]


def participant(root):
    intro = '''# Participant sheet — eight questions\n\nUse only this sheet and the supplied home page. This is a test of the page,\nnot of you. You may use the page, scroll and follow its source links.\nDo not use a search engine, another person or other notes.\nFor question 7, “the page” means the home page, not linked pages.\nFor question 8, use the debt-interest number in question 3.\nWrite your answers in your own words in the spaces below.\nYou can skip a question or stop at any time.\nWait for the facilitator to say start. Stop writing when asked.\n\n'''
    return intro + '\n'.join(f'{i}. {q}\n\n   Answer: __________________________________________________________\n' for i, q in enumerate(questions(root), 1))


def key_text(root, manifest):
    header = f'''# Facilitator only — answer key\n\nKit prepared: {manifest['prepared_date']} (not a test date).\nTested page revision: `{manifest['page_revision']}`.\nThese are source-derived expected answers, not participant responses or results.\nHome page only; Q8 uses the Q3 debt-interest figure.\n\nSource publications, dates, URLs and hashes:\n\n'''
    for name in ('manifest.json', 'trends-manifest.json'):
        s = json.loads((root/'sources'/name).read_text())
        header += f"- {s['publication']}; published {s['published']}, updated {s['date']}; {s['url']}; SHA-256 `{s['sha256']}`.\n"
    for i, (answer, evidence) in enumerate(answers(root), 1):
        header += f'\n## {i}. {questions(root)[i-1]}\n\nExpected: **{answer}**.\n\nEvidence / scope: {evidence}.\n'
    d = json.loads((root/'site/data/spending.json').read_text())
    share = next(r for r in d['rows'] if r['label'] == 'Total health')['value'] / d['total']['value'] * 100
    debt = next(r for r in d['extras'] if r['label'] == 'of which: central government debt interest')['value'] / 1000
    return header + f'''\n## Marking rules (one point per question; no partial credit)\n\nAccept equivalent plain-English wording. Q1 requires the named area.\nQ2 accepts £{share:.2f}, £{share:.1f} or £{share:.0f} per £100 (rounding to the nearest pound);\nreject a percentage of a different spending total. Q3 requires £{debt:.1f}bn\n(or the exact source amount). Stating status is not required for Q3, but an\nexplicitly wrong status is contradictory and scores zero.\nQ4 and Q5 need the correct direction; numerical changes are not required.\nQ6 requires both amounts with correct labels, each rounded to £0.1bn\n(or exact source amounts); “pensions are bigger” alone is insufficient.\nQ7 must identify that no home-page values are forecasts; naming linked income\nforecasts without distinguishing the home page is insufficient.\nQ8 accepts a demonstrated source link and the matching row/cell, or a written\nroute that identifies Table 5.2 and the Q3 cell. “Government” alone is insufficient.\nMissing, ambiguous or contradictory answers score zero. Freeze responses at\nthe stop time; resolve marking uncertainty against these rules, not with hints.\n'''


def validate(root=ROOT):
    m = json.loads((root/KIT/'version.json').read_text())
    date.fromisoformat(m['prepared_date'])
    if not re.fullmatch('[0-9a-f]{40}', m['page_revision']):
        raise ValueError('Expected full immutable page revision')
    expected = {p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in INPUTS}
    if m['input_sha256'] != expected:
        raise ValueError('Kit inputs changed: review and explicitly re-version the kit')
    # Verify that the pinned revision really contains these bytes (full-history CI).
    for p, digest in expected.items():
        raw = subprocess.check_output(['git', 'show', f"{m['page_revision']}:{p}"], cwd=root)
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(f'Pinned revision differs: {p}')
    for name, expected_text in [('participant.md', participant(root)), ('answer-key.md', key_text(root, m))]:
        if (root/KIT/name).read_text() != expected_text:
            raise ValueError(f'{name} differs from fixed questions / generated data')
    print('PASS: eight questions; source-derived key; input hashes and pinned revision')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write', action='store_true')
    p.add_argument('--revision')
    p.add_argument('--date')
    args = p.parse_args()
    if args.write:
        if not args.revision or not args.date:
            p.error('--write requires explicit --revision and --date')
        m = dict(prepared_date=args.date, page_revision=args.revision,
                 input_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in INPUTS})
        (ROOT/KIT/'version.json').write_text(json.dumps(m, indent=2)+'\n')
        (ROOT/KIT/'participant.md').write_text(participant(ROOT))
        (ROOT/KIT/'answer-key.md').write_text(key_text(ROOT, m))
    validate()


if __name__ == '__main__':
    main()
