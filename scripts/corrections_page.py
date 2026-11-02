"""Static corrections page, sharing the site's neutral base styles."""
import html
import re


def render(entries, home, metadata):
    esc = html.escape
    style = re.search(r'<style>(.*?)</style>', home, re.S)[1]
    records = []
    for entry in entries:
        records.append(
            f'<article id="{esc(entry["id"])}"><h2>Correction: {esc(entry["date"])}</h2>'
            f'<p>Date applied: <time datetime="{esc(entry["date"])}">{esc(entry["date"])}</time>. '
            f'Page: <a href="{esc(entry["page"])}">{esc(entry["page"])}</a>.</p>'
            f'<h3>Error</h3><p>{esc(entry["error"])}</p>'
            f'<h3>Correction</h3><p>{esc(entry["correction"])}</p>'
            f'<p><a href="{esc(entry["source"], quote=True)}">Evidence for this change</a></p></article>')
    log = '\n'.join(records) if records else '<p>No corrections have been recorded in this log yet. This does not mean the site has no errors.</p>'
    return f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Corrections | UnpoliticalAF</title><style>{style}</style></head><body>
<a class="skip" href="#main">Skip to content</a><header><a class="brand" href="/">UnpoliticalAF</a><span>UK public money</span></header>
<main id="main"><h1>Corrections</h1><nav aria-label="Site pages"><a href="index.html">Spending</a> · <a href="income.html">Taxes, borrowing and debt</a> · <a href="history.html">History</a> · <a href="parties.html">Party offers</a></nav>
<p class="intro">When we fix an error, we record what was wrong and what changed.</p>
<p>Source publication: <a href="sources/{esc(metadata['file'], quote=True)}">{esc(metadata['publication'])}</a>. This is this site's own record of fixes, not a government data release. It contains no spending figures.</p>
<p>Log data as of <time datetime="{esc(metadata['date'])}">{esc(metadata['date'])}</time>. {esc(metadata['date_basis'])} <a href="{esc(metadata['evidence_url'], quote=True)}">Snapshot evidence</a> · <a href="sources/corrections-metadata.json">Source and date details (JSON)</a>. There is no set next release date.</p>
<section><h2>The log</h2>{log}</section>
<section><h2>How this log works</h2><p>Each entry gives the date the fix was applied, the page, the error and the fix. It links to the change as evidence. The same source checks apply to all parties.</p>
<p>We add entries at the end. We do not change or remove old entries. If an entry is wrong, we add a new one that names it and explains the fix. Routine data updates and new features are not corrections.</p>
<p><a href="sources/corrections.json">Download the full log (JSON)</a> · <a href="https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/commits/main/sources/corrections.json">View the log history</a></p></section>
<section><h2>Report an error</h2><p><a href="https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/new">Report an error on GitHub</a> (a GitHub account is needed). Please give the page link, what looks wrong and a source we can check.</p>
<p>This log does not claim that people from opposing political views have read the site. That review has not been recorded here.</p></section></main>
<footer>Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>. Data sources are named on each page.</footer></body></html>
'''
