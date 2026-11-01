"""Section-local data vintages, official calendars and retained revision notices."""
import hashlib
import html
import json
import re


def annotate(files, root, spending, comparison):
    calendar = json.loads((root / 'sources/release-calendar.json').read_text())
    for entry in calendar['entries'].values():
        for evidence in [entry, *entry.get('evidence', [])]:
            snapshot = (root / 'sources' / evidence['file']).resolve()
            if snapshot.parent != (root / 'sources').resolve():
                raise ValueError('Invalid calendar evidence path')
            if hashlib.sha256(snapshot.read_bytes()).hexdigest() != evidence['sha256']:
                raise ValueError('Release calendar evidence hash changed')
    state_path = root / 'sources/revision-status.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {'notices': []}
    esc = html.escape

    def note(source_ids, period, manifests, family=None):
        dates = '; '.join(f"{s.get('publication', 'Source')}: published {s.get('published', s.get('date', 'not supplied'))}, source updated {s.get('date', 'not supplied')}" for s in manifests)
        if family:
            e = calendar['entries'][family]
            next_date = e['next_release']
            text = (f'Next announced release: {esc(next_date)}.' if next_date else
                    'No next release date is announced in the checked official calendar.')
            schedule = f'{text} <a href="{esc(e["url"].replace('/api/content/', '/'), quote=True)}">Official release evidence</a> (checked {esc(calendar["checked_at"])}).'
            if family == 'spending' and e.get('status') == 'cadence_only':
                schedule += ' Treasury lists November, February and April updates, not an exact next date.'
            elif family == 'history':
                schedule += ' PESA is an annual release.'
        else:
            schedule = 'No next release date is announced for this fixed historical snapshot.'
        notices = []
        for n in state['notices']:
            if n['source'] in source_ids:
                e = n['evidence']
                kind = ('Source revised' if e['release_url'] == n['baseline_url'] else 'New source release found')
                notices.append(f'<p class="revision-notice"><strong>{kind}.</strong> The figures here still use the retained data, not the changed source. Detected {esc(n["first_detected_at"][:10])}. <a href="{esc(e["release_url"], quote=True)}">Check the changed source</a>.</p>')
        return (f'<div class="section-dates"><p>Data period: {esc(period)}. {esc(dates)}.</p>'
                f'<p>{schedule}</p>{"".join(notices)}</div>')

    main_source = spending['source']
    history = json.loads((root / 'sources/history-manifest.json').read_text())
    party = json.loads((root / 'sources/party-offers.json').read_text())
    for name, raw in list(files.items()):
        if not name.endswith('.html'):
            continue
        page = raw.decode()
        if name == 'index.html':
            normal = note(['hmt-public-spending'], spending['year'], [main_source], 'spending')
            trends = note(['hmt-spending-trends'], ' to '.join(p['year'] for p in comparison['points']), [comparison['source']], 'spending')
            def insert(match):
                return match[0] + (trends if 'ten-years' in match[0] else normal)
            page = re.sub(r'<section\b[^>]*>\s*<h2\b[^>]*>.*?</h2>', insert, page, flags=re.S)
        elif name.startswith('history'):
            period = '2003-04 to 2025-26'
            if name == 'history.html':
                period += '; fixed TME snapshots also 1985-86 and 1995-96'
            stamp = note(['hmt-pesa-functional-history'], period, [history], 'history')
            page = re.sub(r'(<section\b[^>]*>\s*<h2\b[^>]*>.*?</h2>|<details\b[^>]*>\s*<summary>.*?</summary>)', lambda m: m[0]+stamp, page, flags=re.S)
        elif name == 'parties.html':
            roster = note(['party-roster'], party['roster']['as_of'], [party['roster']])
            page = re.sub(r'(<section\b[^>]*>\s*<h2\b[^>]*>.*?</h2>)', lambda m: m[0]+roster, page, flags=re.S)
            for p in party['parties']:
                source = next(s for s in party['sources'] if s['id'] == p['source_id'])
                stamp = note(['party-offers-' + source['id']], '2024 election manifesto', [source])
                pattern = r'(<article\b[^>]*data-party-id="' + re.escape(str(p['id'])) + r'"[^>]*>\s*<h2\b[^>]*>.*?</h2>)'
                page = re.sub(pattern, lambda m: m[0]+stamp, page, flags=re.S)
        files[name] = page.encode()
