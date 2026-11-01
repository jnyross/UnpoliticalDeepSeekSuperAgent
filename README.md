# UnpoliticalAF — UK public spending

A static, source-linked page showing UK spending by area and ten-year answers on
real health spending and Total Managed Expenditure as a share of GDP. It uses 2025-26, the latest
full year in HM Treasury's **Public spending statistics: July 2026**. The table labels
this year **outturn**, not forecast. This foundation is not the full product and does
not claim rubric levels: tax, borrowing, debt stocks, history and party plans remain
future work. See [product specification](docs/product-spec.md),
[rubric](docs/rubric.md) and [repository instructions](AGENTS.md).

## Setup

Python 3.11+ and Node.js 22+ are required for the complete checks:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
npm ci
npx playwright install --with-deps chromium
```

## One-command refresh

```sh
.venv/bin/python scripts/build.py --refresh
```

This downloads the official release metadata and Chapter 4 and 5 workbooks, retains their
URLs, publication/update/download dates and SHA-256, parses the latest fiscal column,
validates it independently, then replaces the committed generated files. Failed
network requests, missing cells, changed formats or failed validation leave the last
good output untouched. Review the printed changed-file list and `git diff --stat`
plus the source/data diff before committing. A new download date is recorded only
when the workbook hash changes. No figures are entered by hand.

For a new release, use the **same command** with its GOV.UK publication slug:

```sh
.venv/bin/python scripts/build.py --refresh --release public-spending-statistics-release-july-2026
```

Use a release which contains the **Public sector spending** workbook attachment.
The year is derived from the workbook, not a configured figure. If its layout or
accounting definitions change, validation deliberately stops; update and review the
parser/checks rather than silently interpreting a new schema.

## Scheduled release discovery

[Discover official releases](.github/workflows/discover.yml) runs daily at 07:23 UTC
(GitHub may delay scheduled runs), or on demand with `workflow_dispatch`:

```sh
python3 scripts/discover.py                         # read-only, no GitHub token needed
GH_TOKEN=… python3 scripts/discover.py --open-issues --repo owner/repo
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Do not paste a token into shell history; Actions supplies `github.token`. The job needs
only `contents: read` for checkout and `issues: write` to list/create update issues.
It needs no repository write, pull-request, deployment or external secret permissions.
The checked-in [inventory](config/release-sources.json) currently covers the site's only
source family, HMT Public Spending Statistics. The official GOV.UK collection discovers
new publication slugs, not just changes to the retained URL. The retained release is
also checked for date revisions and changed workbook bytes (SHA-256), even at an
unchanged attachment URL. Only releases published on or after the retained publication
are candidates; superseded older releases are not update tasks for this latest-year page.

Each new release/revision opens an issue containing official links, dates, attachment
hash, retained baseline and the refresh/review command. Stable evidence markers are
checked against **all pages of open and closed issues**; closing an issue records a
review decision and does not cause it to reopen. A serialized workflow prevents
concurrent runs from creating duplicates. Run local issue-writing discovery only when
no workflow is active. The inventory baseline advances only with an explicitly reviewed
refresh commit, never when discovery notices a release.

Discovery never writes `sources/` or `site/`. Network, schema or GitHub failures fail
the job and are recorded in `discovery-report.json`, retained as an Actions artifact;
other source families can still be checked. The last good deployed data stay intact.
A successful unchanged run records zero updates. Re-run failed jobs after inspecting
the error; do not replace a missing source with guessed data. The report is operational
evidence, not generated site content; it is not committed.

When adding history, deflators, GDP, party rosters or plans, register **every consumed
source family** with its retained manifest, official discovery endpoint, adapter and
refresh instructions. Families sharing a publication can share one entry; distinct
publishers need their own adapter plus unchanged/new/repeated/error fixtures. The
current adapter supports GOV.UK collections with one named workbook attachment; do
not pretend ONS, OBR, Parliament or party sites use that schema. Extend the inventory
coverage test along with the source pipeline. This schedule notices releases and opens
review tasks; it does not claim a year of timely updates or people-review evidence.

## Reproduce and check without network access

```sh
.venv/bin/python scripts/build.py --check
.venv/bin/python scripts/check.py --self-test
npm run test:browser
```

To rebuild from the retained files (without fetching), omit `--check`. The check mode
regenerates all bytes in a temporary directory and fails if the committed site differs.
The independent checker reopens the workbook, verifies its hash, checks every exported
value and its cell, reconciles functional totals within source rounding, and compares
compatible totals with Table 5.3. It checks status, year, derived health share, attribution,
page size, prohibited words and static HTML. Browser checks use JavaScript disabled
for content and layout, plus axe WCAG 2.2 AA at phone and desktop sizes; these are not
manual keyboard, screen-reader or user-test evidence. CI runs these checks on every PR.

Serve `site/` with any static HTTP server (for example `python3 -m http.server 8000
--directory site`). There is no client-side JavaScript. Vercel serves the committed
`site/` directory unchanged, with no build step; see [configuration](vercel.json).

## Data and methods

- Chapter 4 Tables 4.3 and 4.4 supply the latest year and exactly ten years earlier.
  We use Treasury's published real health figures in 2025-26 prices (ONS GDP deflators,
  30 June 2026) and TME shares of GDP from the same vintage, not a spliced series.
  Missing exact baselines, changed units/status or definitions fail the build.
  Derived changes use rounded official inputs, so are approximate. Inputs, cell
  locators and formulas are downloadable as `data/comparisons.json` and CSV.
  TME includes accounting adjustments and is distinct from expenditure on services.

- [Retained official source](sources/manifest.json) and workbook in `sources/`.
- [Generated open JSON](site/data/spending.json) includes fiscal year, status, unit,
  geography, scope, raw cell locators and complete source provenance.
- [Generated CSV](site/data/spending.csv) provides each displayed input value.
- Public sector expenditure on services is the chart denominator. Accounting
  adjustments bridge it to Total Managed Expenditure; the two are never equated.
- Functional areas include EU net transactions (negative), not just positive spending.
  Debt interest and old-age pensions are nested within the areas, not added again.
- Shares use source £ million values; billions are divided by 1,000 and rounded to one
  decimal place. Source rounding allows up to £6 million discrepancy for the eleven
  components and their rounded total. Definitions and defence/NATO differences appear
  beside the content, not only here.
- [Evaluative-word exclusions](scripts/banned-words.txt) are published on the site and
  enforced against page text. Charts use a neutral grey palette.

Contains public sector information licensed under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
No owner/funding/contact facts or people evidence are invented. The owner made the
code repository public on 1 November 2026; downloadable source and data are also
served as part of the site.
