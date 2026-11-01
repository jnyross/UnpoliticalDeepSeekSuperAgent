# UnpoliticalAF — UK public spending

A static, source-linked first page showing UK spending by area in 2025-26, the latest
full year in HM Treasury's **Public spending statistics: July 2026**. The table labels
this year **outturn**, not forecast. This foundation is not the full product and does
not claim rubric levels. A separate history page now shows spending overall and by area
from the retained PESA historical tables. Tax, borrowing, debt stocks and party plans remain
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

This downloads the official release metadata and Chapter 5 workbook, and refreshes the
separately versioned PESA Chapter 4 history workbook and metadata. It retains their
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
Historical refresh is separately pinned to PESA 2026 Chapter 4, so changing the
latest-year `--release` never silently substitutes a different historical vintage.
The year is derived from the workbook, not a configured figure. If its layout or
accounting definitions change, validation deliberately stops; update and review the
parser/checks rather than silently interpreting a new schema. This foundation does
not yet discover releases on a schedule.

## Reproduce and check without network access

```sh
.venv/bin/python scripts/build.py --check
.venv/bin/python scripts/check.py --self-test
.venv/bin/python scripts/check_history.py --self-test
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

- [Retained official source](sources/manifest.json) and workbook in `sources/`.
- [Historical source manifest](sources/history-manifest.json) identifies the retained
  PESA 2026 Chapter 4 workbook, with 23 annual outturn years, 2003-04 to 2025-26.
  [History JSON](site/data/history.json) and [CSV](site/data/history.csv) retain all
  cash, real and GDP-share source cells. [History page](site/history.html) shows all
  years by area and the fixed decade grid from the latest overview year back to 1945-46.
  Unavailable years are explicitly missing, not zero. The historical source is
  not spliced with the separate July 2026 latest-year workbook. Important source definition breaks
  are shown beside the tables. Published real values use 2025-26 prices and the ONS
  GDP deflators of 30 June 2026; GDP shares use that date's ONS GDP series.
  The independent history checker reopens all three raw tables, checks every cell,
  reconciles each year and verifies cash equals real in the base year.
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
