# UnpoliticalAF — UK public spending

A static, source-linked page showing UK spending by area and ten-year answers on
real health spending and Total Managed Expenditure as a share of GDP. It uses 2025-26, the latest
full year in HM Treasury's **Public spending statistics: July 2026**. The table labels
this year **outturn**, not forecast. This foundation is not the full product and does
not claim rubric levels. A separate history page shows spending overall and by area
from the retained PESA historical tables. The income page shows tax types, other receipts,
borrowing and the debt stock from the OBR public finances databank, with the source's
own period and forecast labels. The income page pairs the latest outturn with all
forecast years from that same workbook for receipts, borrowing and year-end debt.
Forecast rows have dashed borders and explicit status text, with the OBR forecast
vintage note and databank date beside the table. These are cash amounts, not a
price-adjusted time-series chart. The existing history charts retain cash, real and
GDP-share views. Debt is not debt interest; borrowing is not tax.
The party page adds a historical 2024 election-offer snapshot, using the Commons roster
dated 9 July 2024; it is not a current roster or a record of implemented policy.
The [Coverage L4 evidence audit](docs/research/coverage-l4/ni-devolved-feasibility.md)
records the initial costing/assessment gaps; [wave-five follow-up](docs/research/coverage-w5/ni-devolved-followup.md)
records additional checked policy evidence. Conservative, Labour and Liberal Democrat
claims retain their independent quotations. Alliance, Green, Plaid Cymru, SNP and UUP pair a
selected two-child-limit pledge with Resolution Foundation's 2024-25 Great Britain
estimate and assessment, explicitly not a party costing or complete UK total.
[Wave-six research](docs/research/coverage-w6/ni-selected-policy-followup.md) adds UUP's exact
UK-government repeal commitment and a checked TUV employer-tax projection. Reform's NHS
package claim is paired with Paul Johnson's direct IFS assessment from an obtainable
[official PDF](docs/research/coverage-w6/reform/README.md), not an unrelated NHS fact-check.
[Wave-seven research](docs/research/coverage-w7/ni/selected-policy-research.md) verifies the
DUP manifesto's already-approved £25m childcare package for 2024-25 against the official
23 May announcement. It is not new Westminster funding, does not price the separate
nursery/grant election promises, and is not an independent assessment. Sinn Féin's selected
offer still lacks a checked cost. DUP, Sinn Féin, SDLP and TUV retain unmatched independent
assessment gaps, and the new DUP nursery/grant commitments remain unpriced. This is
partial coverage, not a claim to Coverage L4; unlike plans are not ranked or added together.
The deterministic build also publishes a [financial-figure trace](site/data/party-figure-audit.json)
for every displayed party cash/rate quote occurrence, including duplicates. It joins
native page/text-block locators to a complete consumed-source URL/date/SHA-256 manifest,
with scope, baseline, year and status retained. Verified supplemental publisher tables
are checked against the raw PDF, not treated as replacements for the quotes. The
[curated native table locators](sources/party-figure-locators.json) and
[source research](docs/accuracy-source-research.md) distinguish genuine table rows
from prose-only evidence. This trace does **not** claim Accuracy L2: several sources
lack a verified matching table/row, and annual claims do not establish a fiscal year.
[Wave-seven archive research](docs/research/accuracy-w7/conservative/README.md)
now supplies the native Conservative welfare row: £12,000m in 2029-30, exactly £12bn.
The original prose year qualification and independent assessment stay unchanged.
[Other alternatives](docs/research/accuracy-w7/alternatives/README.md) include the
retained Lib Dem £1,420m 2028-29 row: it remains an explicitly **unmatched** related
supplement to the £1.4bn release, never rounded into an exact match. The trace now
has 22 financial occurrences, 15 still without matching table evidence. Cross-source
supplements name the actual retained evidence source; currency conversions use exact
decimal equality and fiscal columns are checked in order. No displayed claims or
party-page layout were changed to evade those gaps.

See [product specification](docs/product-spec.md),
[rubric](docs/rubric.md) and [repository instructions](AGENTS.md).

Manual accessibility testing prerequisites (not performed results):
[protocols, page/state inventory and blank records](docs/evidence/access/manual/README.md).
Completing these materials does not award Accessibility L4.

## Setup

Python 3.11+, Node.js 22+ and Poppler's `pdftotext` are required for the complete checks
(`sudo apt-get install poppler-utils` on Debian/Ubuntu). PDF text is re-extracted to
verify each retained party quote against its source document:

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

This downloads the official release metadata and spending-statistics Chapter 4 and 5
workbooks, and refreshes the separately versioned PESA Chapter 4 history workbook
and metadata. It also downloads the latest public finances databank linked on the
OBR data page. Income data keep their own vintage: they are not forced to match
the PESA spending tables. It retains their
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
`contents: write`, `issues: write` and `pull-requests: write`: it opens update issues,
then publishes changed revision notices through a validated PR without refreshing figures.
The default Actions token is used; branch protection is not bypassed.
The checked-in [inventory](config/release-sources.json) covers HMT Public Spending
Statistics, PESA functional history, the OBR public finances databank, the historical Commons roster and all retained
party manifestos and the consumed historical costing/assessment pages. The roster also
checks today's dated Commons API snapshot, deduplicating composition changes by party/seat
semantics rather than the daily URL or API timestamp. A current snapshot is a review
candidate, not a revision of the explicitly historical 2024 roster; it never silently
updates the site. The Liberal Democrat adapter also watches new/retitled conference-paper
links within the official adopted-policy listing, against a retained 14-link baseline.
It does not fetch paper contents, infer publication dates or claim reviewed costings.
Both adapters retain their original historical-URL revision checks. Other party sources
remain retained-URL monitors, NOT new-plan discovery. See the
[wave-six coverage and operational limits](docs/evidence/freshness-w6/README.md). HTML evidence is watched for raw-byte changes at its saved
URL; this can also flag presentation-only changes, and does not discover new analyses. PESA's year-dependent
attachment title uses an anchored `attachment_title_pattern`; exact-title sources
retain `attachment_title` matching. The official GOV.UK collection discovers
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

Default discovery is read-only. `--write-revision-status` retains notices in
`sources/revision-status.json`; an offline rebuild places them beside the affected
sections. Notices survive failed lookups and unchanged checks. Only publication of
the observed revised hash (and release URL/date where relevant) clears them: dismissing
an update issue does not. A different, unrelated baseline does not erase a warning.
The scheduled workflow validates and publishes notice changes through a PR, including
Before/After browser evidence. It never refreshes the data automatically. Network,
schema or GitHub errors are retained in `discovery-report.json` and fail the job after
known notices have been preserved; other families can still be checked. Daily polling
can only show revisions after detection and deployment, not at the instant a publisher
changes bytes. Never claim continuous real-time revision coverage.

### Prospective release and deployment timing

The append-only [measurement ledger](measurements/release-timing.jsonl) records
retained source baselines, newly discovered versions, discovery errors and verified
live snapshots. Discovery includes it in its existing validated PR and evidence
artifact, even when another source reports an error. A separate
[deployment-only workflow](.github/workflows/deployment-timing.yml) runs on main
pushes, manual dispatch or completion of trusted main-branch release discovery
(including token-driven notice merges), fetches **every local site file** from production and
requires exact byte equality before recording live success. It performs no source
refresh or discovery. Bounded retries allow deployment propagation; failure is not
silently treated as success. Validated changes go through a measurement-only PR
by `jnyross-agent`, without bypassing failed checks or branch protection.
Source-version/site-fingerprint deduplication makes ledger-only merges a no-op
rather than an endless series of measurement PRs. Both scheduled workflows check out
`main` with full Git history (`fetch-depth: 0`): the validation suite reads the
comprehension kit's pinned application revision, which need not be the current
commit or its parent. A shallow checkout cannot run those checks and must not
skip them or persist unvalidated measurements.

```sh
python scripts/release_timing.py report --ledger measurements/release-timing.jsonl
# Observe a completed discovery run (use its real public Actions run URL):
python scripts/release_timing.py observe --ledger measurements/release-timing.jsonl \
  --discovery discovery-report.json --revision "$(git rev-parse HEAD)" \
  --evidence-url https://github.com/OWNER/REPO/actions/runs/RUN_ID
```

This is forward-looking evidence, **not a Freshness L4 claim**. Historical first-live
times remain unknown; date-only publications yield uncertainty bounds, not invented
midnight publication times or exact delays. CI validates the ledger's hash chain
and unchanged historical prefix against the base revision. See
[release timing methods and commands](docs/release-timing.md) for live verification,
append-only validation, error handling and interpretation limits.

### Reproduce a bounded source/date audit

```sh
python3 scripts/audit_context.py --output /tmp/context-audit.json \
  --live-url https://unpoliticaldeepseeksuperagent.vercel.app
```

This read-only audit reuses discovery and deployment verification, checks every current
inventory entry, verifies retained source hashes, and compares the retained calendar
endpoints. It retains request timestamps, byte counts/hashes, per-source errors,
revision-notice reconciliation and exact deployed-file hashes. It does not refresh
sources, publish notices, open issues or write timing measurements. Exit 1 means an
unknown/error or changed calendar needs investigation; source updates are recorded
separately as findings, not errors. A successful lookup is only point-in-time evidence.
The [wave-six audit](docs/evidence/context-w6/README.md) records the 22-source result,
actual revision warning, section coverage and remaining Context L4 limitations.
The [wave-seven incremental follow-up](docs/evidence/context-w7/README.md) checks the
added IFS source and current deployed notices, with verified official calendar
alternatives; it does not rerun the historical 22-source audit or claim L4.

### Section dates and official release evidence

Every spending/income section, history chart/table and party offer carries its data period
and source publication/update dates. `sources/release-calendar.json` links retained,
hash-checked official GOV.UK publication, guidance, collection and upcoming-statistics
responses. As checked on 1 November 2026, no exact next HMT spending/PESA release date
was announced there. Treasury gives November/February/April cadence for spending
updates and annual PESA publication, not an exact next date. Fixed 2024 party/roster
snapshots have no scheduled next release. The UI says so rather than inventing dates.
The owner decision on issue #24 (2 November 2026) accepts this explicit fallback
under product-spec requirement 4; the independent scorer judges the rubric level.
Release dates, data years, source updates and monitoring times are distinct.
A source refresh verifies calendar evidence too; changed evidence stops for a new
reviewed interpretation instead of silently carrying forward a stale schedule.

When adding history, deflators, GDP, party rosters or plans, register **every consumed
source family** with its retained manifest, official discovery endpoint, adapter and
refresh instructions. Families sharing a publication can share one entry; distinct
publishers need their own adapter plus unchanged/new/repeated/error fixtures. The
current adapter supports GOV.UK collections with one named workbook attachment; do
not pretend ONS, Parliament or party sites use that schema. The OBR adapter reads
the latest databank link and publication date on its data page, then checks the
workbook hash. It also checks the retained workbook when the latest link moves;
per-request cache timestamps are excluded from release identity. Extend the inventory
coverage test along with the source pipeline. This schedule notices releases and opens
review tasks; it does not claim a year of timely updates or people-review evidence.

## Public corrections log

Every page links to `/corrections.html`, which works without JavaScript. Its retained
source is `sources/corrections.json`; the same JSON is published for download. The
initial log is honestly empty, not invented past events or people-review evidence.
Routine new features and source refreshes are not corrections.
`sources/corrections-metadata.json` is the single publication/date record for this
local log. Its date is the retained log snapshot date, not a Treasury release, a
build timestamp or an invented error date. The initial empty snapshot is evidenced
by its introducing commit. The SHA-256 binds this date to the exact ledger bytes;
when appending, update the snapshot date, hash and public evidence together. The
build validates this record and publishes it unchanged beside the downloadable log.

Append a verified error with `id` (stable lowercase hyphenated name), `date` (ISO date
the fix was applied), `page` (site-relative HTML path), `error`, `correction`, and
`source` (this repository's public commit or pull-request URL). Prefer full immutable
commit URLs. Verify that the change supports the error and fix: URL syntax is not
proof of a claim. Apply the same evidence standard for every party. Keep date order.
To correct an entry, append a new one naming its ID; never edit or delete the old one.
Rebuild with `.venv/bin/python scripts/build.py` and commit source and output.

```sh
.venv/bin/python scripts/corrections.py --base origin/main
.venv/bin/python -m unittest discover -s tests -p 'test_corrections.py' -v
```

CI compares entries against the PR base (or pre-push revision on main), rejecting
changed, reordered or dropped entries. First introduction is allowed only when the
verified base commit has no log. Invalid bases fail closed. Synthetic test fixtures
exercise nonempty logs; they are not published as real events. This Git-history guard
is not tamper-proof storage: changes to CI or repository history can defeat it.
Actual opposing political reviewers and published responses remain absent; this
work does not award Impartiality L4.

## Comprehension testing preparation

The versioned [eight-question testing kit](docs/comprehension-kit/README.md)
contains a neutral participant sheet, separate source-derived answer key, frozen
page revision, timed facilitator protocol and empty anonymous results template.
Run `python3 scripts/comprehension_kit.py` to check coverage, data consistency and
the pinned revision. CI also exercises stale-input and answer mutations. No real
participant tests or results exist; this prerequisite does not award Comprehension L4.
The kit is documentation only and does not alter live pages.

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
page size, prohibited words, static HTML and Flesch–Kincaid reading grade (at most 7
on every HTML page, including expanded content). See [reading-grade rules and
standalone report command](docs/reading-grade.md). This check also runs in the staged
rebuild, so harder copy cannot replace the last good site. Browser checks use JavaScript disabled
for content and layout, plus axe WCAG 2.2 AA at phone and desktop sizes; these are not
manual keyboard, screen-reader or user-test evidence. CI runs these checks on every PR.

The browser runner discovers every generated HTML page and checks both 360×800 and
1280×900 viewports, initial and all-details-expanded states and any expandable
buttons. It runs each page/viewport in a fresh Chromium process group with a five-minute
hard deadline; a timeout, worker failure or missing/partial report fails the suite.
CI discovers the same pages dynamically and runs one job per page, without cancelling
other pages on failure. The suite manifest lists every expected page/viewport and its
completion; per-worker JSON records the URL, HTML hash, states, timings, axe/browser
versions, rule results (including colour contrast), full violations and incomplete
results. Axe cannot infer the background behind SVG axis text (`imgNode`). Those
raw incomplete results are retained, and a supplemental automated WCAG luminance
calculation checks every SVG label at 4.5:1 and data line/point at 3:1 against its
computed solid background. Unsupported paint, overlapping graphics behind text and
any other incomplete result fail closed. This is not human review. A pass means
every expected state finished with zero violations and completed contrast checks,
not proof of complete WCAG conformance.

```sh
EVIDENCE_DIR=test-results/browser npm run test:browser
# Run a single CI shard for diagnosis (not complete site evidence):
CHECK_PAGE=history-gdp.html EVIDENCE_DIR=/tmp/gdp-check npm run test:browser
```

`BROWSER_TIMEOUT_MS` overrides the per-page/viewport deadline for diagnosis; it never
turns a timeout into success. Evidence is retained on CI failures as well as successes.

Serve `site/` with any static HTTP server (for example `python3 -m http.server 8000
--directory site`). There is no client-side JavaScript. Vercel serves the committed
`site/` directory unchanged, with no build step; see [configuration](vercel.json).

## Party-offer snapshot

`parties.html` covers every party with an MP in Parliament's **9 July 2024**
Commons roster, in alphabetical order, with one selected qualitative fiscal offer
from its 2024 election manifesto. This is historical, not today's roster or plans.
Independent MPs and the Speaker are identified separately, not treated as parties.
The page publishes shared field limits and distinguishes party claims from independent
assessment. Costings and independent assessments not supplied in this dataset are
explicitly unavailable, not zero or a claim that none exist elsewhere. It does not
claim full costed-plan coverage or any people-based rubric level.

The open JSON contains the summary, exact supporting excerpt, PDF page, source URL,
download date and hash. Some party-issued documents are retained from the British
Manifesto Archive where party hosting was unavailable; hosting is labelled per source.
Party documents retain their own copyright and are not claimed to be OGL licensed.
The retained PDF is reopened with `pdftotext` during validation rather than trusting
only an editable transcript. Both PDF and transcript byte hashes must match the
manifest, and every excerpt must occur on its cited page in both retained text and
fresh PDF extraction. Full extracted layouts are not compared byte-for-byte:
Poppler versions differ in whitespace and overlapping-text order. Changed raw
PDF/transcript bytes or missing/moved quotes still fail; validation never rewrites
provenance to accommodate a tool version.

The same refresh command above checks all retained party/roster URLs. A changed
manifesto stops the staged build for evidence review rather than silently updating a
curated claim. Review a changed document, update its hash, transcript and supported
excerpt in `sources/party-offers.json`, then rerun the full checks; do not just accept
a new hash. Adding a new election or roster date is an explicit dataset update.
Scheduled party discovery detects revisions at these retained URLs only: it does not
find new manifesto URLs, new elections or changes to today's roster. It must not be
read as proof of current party-policy coverage or complete release discovery.

The home-page browser checks click all eight answer links at 360×800 and 1280×900,
with JavaScript enabled and disabled. They check the link's initial position, unique
native fragment target, substantive answer text and the full answer paragraph's
landing position within the viewport, rather than just counting links. The home
navigation includes direct links for debt interest, pensions versus defence and each
ten-year question, so readers need not pass the spending chart to reach them.

Browser checks can also run against the deployed site, comparing returned HTML hashes
with local output before no-JavaScript, mobile and axe checks:

```sh
LIVE_URL=https://unpoliticaldeepseeksuperagent.vercel.app EVIDENCE_DIR=/tmp/live-evidence npm run test:browser
```

## Project disclosures and error reports

Every generated page links to [About this project](site/about.html) and the public
[GitHub error-report form](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/new).
A GitHub sign-in is required to submit; reports can be read without an account.
Do not include private information. The disclosure page distinguishes verified repository
ownership and automated maintenance from the still unconfirmed site operator/legal
publisher and funding statement. It does not claim Openness L3.
The generator reuses the site's existing styles and adds static footer links to every
HTML output; CI checks those links, the login notice, local destinations and mutations
that remove them, as well as the normal reading-grade and browser checks.

## Data and methods

- Chapter 4 Tables 4.3 and 4.4 supply the latest year and exactly ten years earlier.
  We use Treasury's published real health figures in 2025-26 prices (ONS GDP deflators,
  30 June 2026) and TME shares of GDP from the same vintage, not a spliced series.
  Missing exact baselines, changed units/status or definitions fail the build.
  Derived changes use rounded official inputs, so are approximate. Inputs, cell
  locators and formulas are downloadable as `data/comparisons.json` and CSV.
  TME includes accounting adjustments and is distinct from expenditure on services.

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
  [Cash charts](site/history-cash.html), [real charts](site/history-real.html) and
  [GDP-share charts](site/history-gdp.html) cover the same 22 series and 23 years.
  Native links preserve the chosen area without JavaScript; each chart has a data table.
  Axes include a marked zero, negative receipts remain negative, and missing points
  break the line. Scales differ across areas and views. No values are interpolated.
  The independent history checker reopens all three raw tables, checks every cell,
  reconciles each year and verifies cash equals real in the base year.
  Real amounts are the Treasury's official published transformation, not a new
  independently estimated deflator series: `real_t = nominal_t × D_2025-26 / D_t`,
  where `D` is the ONS GDP deflator released 30 June 2026, as identified in
  `4_3!A28` and `4_1!B51` of the hash-pinned workbook. At the base year the
  multiplier is exactly one, so all 22 functional rows and the three aggregate
  nominal/real pairs must match exactly at published precision (zero tolerance).
  Changed base-year values of £0.1bn fail, including every generated annual series.
  Both cash and real functional areas reconcile to TES within £0.6bn
  (12 independently rounded amounts × £0.05bn); TES plus adjustments reconciles
  to TME within £0.15bn (three amounts × £0.05bn). All 23 overlapping TME years
  must also match Table 4.1 in cash, real and GDP share within £0.1bn or 0.1
  percentage point (two rounded amounts). No cross-vintage totals are equated.
  Mutation tests exercise base-year changes, these bounds and rejection just
  beyond them. The build runs this independent checker before publishing, so
  failures leave last-good generated output untouched. This verifies the
  base-year identity, not a recalculation of every non-base-year deflator.
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
