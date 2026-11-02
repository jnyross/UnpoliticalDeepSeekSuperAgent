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

    def note(source_ids, period, manifests, family=None, schedule=None):
        dates = ' '.join(
            (f"Snapshot as of {s['as_of']}. Publish and update dates not supplied."
             if 'as_of' in s else
             f"Published {s.get('published', 'not supplied')}. Source updated {s.get('date', 'not supplied')}.")
            for s in manifests)
        if schedule is not None:
            pass
        elif family:
            e = calendar['entries'][family]
            next_date = e['next_release']
            text = (f'Next announced release: {esc(next_date)}.' if next_date else
                    'No next release date is announced in the checked source.')
            source_url = e['url'].replace('/api/content/', '/')
            schedule = f'{text} <a href="{esc(source_url, quote=True)}">Official source</a> (checked {esc(e.get("checked_at", calendar["checked_at"]))}).'
            if family == 'spending' and e.get('status') == 'cadence_only':
                schedule += ' Treasury lists November, February and April updates, not an exact next date.'
            elif family == 'history':
                schedule += ' PESA is an annual release.'
        else:
            schedule = 'This is a fixed past snapshot. No next release date is announced.'
        notices = []
        for n in state['notices']:
            if n['source'] in source_ids:
                e = n['evidence']
                kind = ('Source revised' if e['release_url'] == n['baseline_url'] else 'New source release found')
                notices.append(f'<p class="revision-notice"><strong>{kind}.</strong> These figures still use the saved data, not the changed source. Found {esc(n["first_detected_at"][:10])}. <a href="{esc(e["release_url"], quote=True)}">Check the changed source</a>.</p>')
        return (f'<div class="section-dates"><p>Data period: {esc(period)}. {esc(dates)}</p>'
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
        elif name == 'income.html':
            income = json.loads(files['data/income.json'])
            source = json.loads((root / 'sources/income-manifest.json').read_text())
            metadata = (root / 'sources' / source['metadata_file']).resolve()
            if metadata.parent != (root / 'sources').resolve():
                raise ValueError('Invalid income release evidence path')
            if hashlib.sha256(metadata.read_bytes()).hexdigest() != source['metadata_sha256']:
                raise ValueError('Income release evidence hash changed')
            # The inventory id, not the workbook filename, scopes revision alerts.
            source_ids = ['obr-public-finances-databank']
            debt_period = next(r['period'] for r in income['records'] if r['id'] == 'debt')
            release = calendar['entries'].get('income')
            schedule = None if release else (
                f'{esc(source["next_release"].replace("; databanks", ". Databanks"))} '
                f'<a href="{esc(source["release_url"], quote=True)}">Official source</a>. '
                f'<a href="sources/{esc(source["metadata_file"], quote=True)}">Saved source page</a> '
                f'(as of {esc(source["downloaded"])}).')

            def income_stamp(match):
                section = match['section']
                period = income['year']
                if section in ('borrowing-debt', 'sources'):
                    period += '; debt at ' + debt_period
                return match[0] + note(source_ids, period, [source],
                                       'income' if release else None, schedule=schedule)

            page = re.sub(r'<section\b[^>]*id="(?P<section>[^"]+)"[^>]*>\s*<h2\b[^>]*>.*?</h2>',
                          income_stamp, page, flags=re.S)
        elif name == 'parties.html':
            roster = note(['party-roster'], party['roster']['as_of'], [party['roster']])
            page = re.sub(r'(<section\b[^>]*>\s*<h2\b[^>]*>.*?</h2>)', lambda m: m[0]+roster, page, flags=re.S)
            for p in party['parties']:
                source = next(s for s in party['sources'] if s['id'] == p['source_id'])
                stamp = note(['party-offers-' + source['id']], '2024 election manifesto', [source])
                pattern = r'(<article\b[^>]*data-party-id="' + re.escape(str(p['id'])) + r'"[^>]*>\s*<h2\b[^>]*>.*?</h2>)'
                page = re.sub(pattern, lambda m: m[0]+stamp, page, flags=re.S)
        files[name] = page.encode()
