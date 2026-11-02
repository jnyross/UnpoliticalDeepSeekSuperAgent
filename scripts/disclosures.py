"""Project disclosures and a shared, static error-reporting route."""
import html
import re

REPOSITORY = 'https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent'
REPORT_URL = REPOSITORY + '/issues/new'


def annotate(files, manifest):
    # Reuse the overview's existing shell and neutral styles, not a second design.
    overview = files['index.html'].decode()
    style = re.search(r'<style>.*?</style>', overview, re.S).group()
    style = style.replace('</style>', 'a{overflow-wrap:anywhere}</style>')
    publication = html.escape(manifest['publication'])
    date = html.escape(manifest['date'])
    body = f'''<header><a class="brand" href="index.html">UnpoliticalAF</a><a href="index.html">UK public money</a></header>
<main id="main"><h1>About this project</h1>
<p class="intro">How this site is made, what we know about the project, and how to report an error.</p>
<section id="report"><h2>Report an error</h2>
<p><a href="{REPORT_URL}">Report an error on GitHub</a>. You need to sign in to a GitHub account to submit a report. You can <a href="{REPOSITORY}/issues">read public reports</a> without an account.</p>
<p>Give the page link, the figure or text at fault, and a source that helps us check it. For a display fault, add your screen size and browser. Reports are public: do not include private or sensitive details. This route does not promise a reply time.</p></section>
<section id="project"><h2>Who maintains the project?</h2>
<p>The public code project is <a href="{REPOSITORY}">jnyross/UnpoliticalDeepSeekSuperAgent</a>. Its repository owner is the GitHub account <a href="https://github.com/jnyross">jnyross</a>.</p>
<p>The <a href="{REPOSITORY}/blob/main/AGENTS.md">project instructions</a> state: “The work is done by the dsh-superagent agent (jnyross-agent) on behalf of jnyross.” This describes automated code maintenance. It does not identify a human or legal publisher of the site.</p>
<p>A confirmed site operator or legal publisher has not been supplied in the project records used for this page. The repository owner's account is not proof of that role.</p>
<h2>How is it funded?</h2><p>A confirmed funding statement has not been supplied in those records. This does not mean the site has no funding. Who funds the site, and a confirmed site operator or legal publisher, remain gaps in these disclosures.</p></section>
<section id="methods"><h2>Methods and limits</h2>
<p>This is a static site. Its core pages work with JavaScript off. Code reads retained source files and builds the pages and open data. Checks compare figures with source cells and file hashes before new pages replace the last good output.</p>
<p><a href="index.html#check-source">Spending sources and methods</a>, <a href="income.html">tax, borrowing and debt</a>, <a href="history.html">spending history</a> and <a href="parties.html">party offers</a> give their own dates, scope and source links. Party offers are a dated 2024 snapshot, not current plans. Missing values are not zero. Different totals and source dates must not be mixed.</p>
<p>The overview uses HM Treasury's {publication}, source updated {date}. Other pages keep their own source dates. See the <a href="{REPOSITORY}/blob/main/README.md">README for the rebuild command and full methods</a> and the <a href="{REPOSITORY}/tree/main/scripts">checks and code</a>. Open JSON, CSV and retained raw files are linked beside the figures.</p>
<p>Automated checks are not tests with real users. No claim of human review or a full rubric level is made here.</p></section></main>
<footer>Contains public sector information licensed under the <a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">Open Government Licence v3.0</a>. Party documents keep their own copyright.</footer>'''
    files['about.html'] = (f'<!doctype html>\n<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>About this project | UnpoliticalAF</title>{style}</head><body><a class="skip" href="#main">Skip to content</a>{body}</body></html>\n').encode()
    add_project_links(files)


def add_project_links(files):
    links = f'<nav aria-label="Project"><a href="about.html">About this project and methods</a> · <a href="{REPORT_URL}">Report an error on GitHub</a> (sign-in needed to submit)</nav>'
    for name, content in list(files.items()):
        if name.endswith('.html'):
            files[name] = content.decode().replace('<footer>', '<footer>' + links).encode()
