# Issue #56 — independent retained section-evidence audit

Audit date: 2 November 2026. Initial scope: baseline committed generated HTML, retained calendar/manifests, renderer, tests and documentation. The matrix and static findings below describe baseline `693386bc035b0a3489718bee9712922748c181b7`, before the main worker's revision-notice rebuild. **No UI/source-manifest edits, GitHub changes or people checks were performed by this independent auditor.** A subsequent bounded live-response check and actual Before/After browser captures are recorded separately at the end; the main worker owns the comprehensive live/deployment audit.

## Coverage matrix

Counts are section/article headings immediately followed by a date block, plus history disclosure summaries with date blocks. A chart and its disclosed table count separately. All 195 existing blocks contain a data period and next-release statement; this is not 195 independent sources or scheduled dates.

| Page/sections | Local blocks | Data period and publication/update evidence | Next-release evidence and limitation |
|---|---:|---|---|
| [Spending](../../../site/index.html): total, explanation, ten-year comparison, source, method | 5 | 2025-26; comparison 2015-16–2025-26. Published 2026-07-16, updated 2026-07-29; source-scoped main/trends workbooks. | Calendar `spending`: null exact date; official guidance and retained upcoming-statistics searches. November/February/April is cadence, not a dated appointment. |
| [Income](../../../site/income.html): forecasts, tax, non-tax, borrowing/debt, sources | 5 | 2025-26 outturn; forecasts/sources also 2026-27–2031-32, debt explicitly end-March. Published/updated 2026-10-28. | **No `income` calendar entry.** Renderer uses [income manifest](../../../sources/income-manifest.json) and hashed [retained OBR page](../../../sources/income-release.txt), as of 2026-11-01. It states no announcement on that retained page and normally about two working days after monthly public-finance releases. Neither is an exact next release date or proof about every OBR announcement channel. |
| [History tables](../../../site/history.html): source and fixed-decade sections; annual and fixed-decade disclosures | 37 (2 section + 35 disclosure) | 2003-04–2025-26, with extra fixed TME snapshots 1985-86/1995-96. Published/updated 2026-07-16, separately from July spending-page revision. | Calendar `history`: null; annual PESA guidance and retained searches do not announce a day. A PSS update need not revise PESA Chapter 4. Period annotation is family-wide; see below. |
| [Cash history](../../../site/history-cash.html) | 44 (22 chart + 22 table) | 2003-04–2025-26; published/updated 2026-07-16. | Same PESA evidence; no exact next date. No extra fixed-TME years asserted here. |
| [Real history](../../../site/history-real.html) | 44 (22 chart + 22 table) | Same years/vintage; 2025-26 price basis explained in page copy. | Same PESA limitation. |
| [GDP-share history](../../../site/history-gdp.html) | 44 (22 chart + 22 table) | Same years/vintage; GDP basis explained in page copy. | Same PESA limitation. |
| [Party offers](../../../site/parties.html): three explanatory/source sections, 13 offers | 16 | Roster explicitly as of 2024-07-09, not a publication date. Manifestos have year-only 2024 publication; missing updates explicitly unspecified. Cards add applicable costing/assessment publication dates. | Calendar `parties` records a fixed snapshot, null next date and limits. Renderer uses generic fixed-snapshot wording rather than that entry's checked-date/source link. It does not demonstrate that no newer party plan exists; archive PDFs are not official forward calendars. |
| [About](../../../site/about.html), [corrections](../../../site/corrections.html) | 0 | Project/ledger policy, not fiscal-data sections; deliberately excluded by section tests. | No fiscal update schedule asserted. Page-date tests require a visible full date but do not establish section-level fiscal provenance. |

## What is demonstrated, and what is not

- **No retained calendar/HTML next-date contradiction found.** [Calendar](../../../sources/release-calendar.json) entries are only `spending`, `history`, `parties`; all three have null `next_release`, checked 2026-11-01. HTML does not invent an exact date. All 15 entry/evidence hash references matched retained files; the regression also verifies retained Treasury cadence quotes and manifesto year precision. Hash agreement establishes retained-byte integrity, not current upstream truth.
- **Strict rubric evidence gap, not a hidden date.** [Context L4](../../rubric.md#L67) asks for a next scheduled update for each section. Existing fallback statements satisfy the different [product-spec wording](../../product-spec.md#L54-L55), not evidence of an exact scheduled date. The calendar's own final limitation says the literal scheduled-date requirement is not established. The earlier [final evidence note](../context-l4-final/README.md#L3-L6) leaves scoring to the independent scorer; this audit makes no L4 award.
- **Section-local precision limitation:** every [history-table](../../../site/history.html#L14-L15) disclosure gets the same family-wide annotation, including “fixed TME snapshots also 1985-86 and 1995-96.” Thus a General public services disclosure repeats years that only apply to TME elsewhere, not to values in that disclosure. [Renderer lines 64–69](../../../scripts/section_dates.py#L64-L69) explain why. The text explicitly qualifies these as TME snapshots, and nearby copy correctly limits them to TME: this is **not demonstrated fabrication of earlier functional values**, but the date block is not tailored to the individual table. The fixed-decade section also discusses unavailable years back to 1945-46; the date block describes retained data, not all requested snapshot slots.
- **Calendar coverage is not all-source calendar discovery.** Income's separately retained evidence is valid local provenance but is outside [calendar refresh](../../../scripts/release_calendar.py#L27-L35). Party costing/assessment dates likewise come from party evidence records, not a comprehensive publication calendar. A successful calendar-only refresh cannot establish live release timing for these other sources.
- **Revision visibility is detection-dependent.** [Revision state](../../../sources/revision-status.json) contains no notices and all nine generated pages contain zero revision-notice blocks. Tests exercise source-scoped notice injection (including OBR, trends isolation and selected party evidence); that proves renderer behavior under supplied notices, not that no source has since revised. [README](../../../README.md#L112-L122) explicitly acknowledges detection/deployment latency. Live sources must decide whether the currently empty state is accurate; no new stale-data claim is made here.

## Code/test checks and reproducibility

Read [section annotator](../../../scripts/section_dates.py), [calendar refresh](../../../scripts/release_calendar.py), [section regressions](../../../tests/test_section_dates.py), [calendar regressions](../../../tests/test_release_calendar.py), [page-date regressions](../../../tests/test_page_dates.py), source manifests, generated pages, [README section-date explanation](../../../README.md#L159-L172), product spec, rubric and prior evidence notes.

Executed offline, from repository root:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_section_dates.py' -v
.venv/bin/python -m unittest discover -s tests -p 'test_release_calendar.py' -v
.venv/bin/python -m unittest discover -s tests -p 'test_page_dates.py' -v
```

Results: **9 + 8 + 2 = 19 tests passed**. Initial use of unqualified `python` failed because it was unavailable; system `python3` lacked project dependencies (`cmudict`, `openpyxl`). The repository virtual environment resolved both; these were environment failures, not application regressions.

Coverage counts were independently calculated from committed HTML heading/summary patterns and `section-dates` blocks, not inferred from test names. Section regressions primarily check presence, selected periods, notice scoping and hash safety; they do not require a real future scheduled date or individually tailored history-table periods. Page-date checks establish only presence of readable dates. Calendar refresh preserves retained evidence on changes/failures and requires reviewed reinterpretation; it does not automatically derive a new schedule.

**Static disposition:** existing local date coverage and honest no-announcement fallback are demonstrated. Exact future schedules, current upstream revision completeness, and all-channel release-calendar coverage are not demonstrated by the static audit. No UI or source-manifest change is justified merely by those evidence limits.

## Subsequent targeted live check and actual UI evidence

The main worker's broader [live audit](live-audit.json) detected a byte change at the Liberal Democrat buyback costing source and rebuilt a source-scoped notice without refreshing the retained source baseline. This independent auditor then performed one bounded, separately timestamped request to the [party page](https://www.libdems.org.uk/news/article/share-buyback-tax-scheme) at 06:07:41–06:07:42 UTC on 2 November 2026. The [raw response](libdem-independent-response.html.txt) and [response report](libdem-independent-response-report.json) are evidence copies, not replacements for retained inputs.

That later response also differs in raw SHA-256 from baseline (`aa449d4c…` versus `f56adb3a…`), but **normalized visible text is identical** after removing scripts/styles, tags, HTML entities and whitespace differences. The consumed costing quote “estimating it would raise around £1.4bn a year.” and its complete £2.2bn/£1.4bn behavioral-response paragraph remain unchanged. This establishes a byte-level change, **not a demonstrated revision to the consumed figure or meaning**. The independently fetched hash differs from the main worker's earlier observed hash too; response timestamps/hashes must not be conflated. It does not follow that no other source changed.

Baseline HTML was copied before rebuild and served locally for actual Chromium captures. After uses the rebuilt working-tree HTML. Both matched captures scroll the Liberal Democrat heading to the top, use light theme, reduced motion, JavaScript disabled, and identical viewports. No mockups or edited images. HTML identities, browser version, complete card text and notice counts are retained in the [Before report](before-libdem-report.json) and [After report](after-libdem-report.json).

| State | 360×800 mobile | 1280×900 desktop |
|---|---|---|
| Before, no notice | [Capture](before-libdem-mobile.png) | [Capture](before-libdem-desktop.png) |
| After, one local source-revised notice | [Capture](after-libdem-mobile.png) | [Capture](after-libdem-desktop.png) |

Both widths have zero horizontal page overflow. After visibly places the saved-data warning above the selected offer; the consumed quote is unchanged. Full-card screenshots are linked by the reports; initial/full-page captures and automated checks are in the [Before browser report](before-browser-report.json) and [After browser report](after-browser-report.json). The focused existing browser suite passed for this page at both widths, including its initial states and JavaScript-disabled checks; this is automated evidence, not manual keyboard/screen-reader or people evidence. The [capture script](capture-party.mjs) reproduces the matched card state:

```sh
node docs/evidence/context-w6/capture-party.mjs before /tmp/context-w6-before-site
node docs/evidence/context-w6/capture-party.mjs after site
CHECK_PAGE=parties.html EVIDENCE_LABEL=after EVIDENCE_DIR=docs/evidence/context-w6 node tests/browser.mjs
```

The temporary baseline copy is not a committed deliverable; reproduce it from the recorded baseline revision. This addendum records a conservative byte-change warning and its visible result; it does not reinterpret the change as a revised financial estimate, clear the notice, award Context L4, or establish instantaneous revision coverage.
