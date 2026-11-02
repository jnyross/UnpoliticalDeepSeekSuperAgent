# UnpoliticalAF product specification (this repository)

This is the product this repository builds from scratch. It is adapted from the v1
UnpoliticalAF specification. It keeps that spec's requirements, but this is a separate,
unlinked build: no code, data or tooling comes from any earlier UnpoliticalAF or
Un-political repository. Every number is fetched from official sources by code in this
repository. The scoring standard is [`docs/rubric.md`](rubric.md).

## Outcome

A complete, plain-English and impartial account of UK public spending, taxation,
borrowing, debt and party proposals, which anyone in the UK can open on a phone,
understand, and check against the official source, finding no sign of which side the
site is on.

## Target and improvement loop

The target is the highest honest score on the eight-dimension rubric, unchanged
(`total / 32 * 10`, integer levels, each level requires every level below it).
The repository owner has decided not to run people checks, so Impartiality 4,
Comprehension 4 and Accessibility 4 cannot be met, and Freshness 4 needs a real year
of history. **The highest honest score is therefore 28/32.** Do not round, relax a
criterion, award partial levels, or simulate people evidence to go higher.

A gated score is not a reason to stop useful work. Complete independently useful
clauses, test verified alternatives, and prepare finite automated prerequisites.
Record these as workarounds with explicit acceptance evidence and the remaining
unmet clause; they do not award a partial rubric level. Before saying nothing is
left, account for all eight dimensions and inspect existing open and completed work.
The public corrections log is required even while real reviewer evidence is absent.

After each wave of merged work, an independent scorer that does not build the site
scores the deployed revision against every level, with dated checks and evidence, and
posts the scorecard on the pinned **Rubric loop** issue. Below target, the next wave of
issues targets the next unmet level of each dimension. Unknown or unperformed evidence
earns no point.

## Product requirements

1. **Spending.** Explain the latest compatible fiscal year's public spending by
   area, spending on services, debt interest, pensions and defence. Show meaningful
   shares such as health out of each £100 of spending on services. Name the
   denominator and accounting scope; do not equate different spending totals.
2. **Income.** Show the actual tax-type breakdown, non-tax receipts, borrowing
   and debt. Explain that borrowing is not tax, receipts are not all tax, and debt is
   a stock rather than annual borrowing. Reconcile only compatible accounting bases.
3. **History.** Include at least 20 years of total and functional spending history
   and fixed ten-year comparisons back to 1945-46 wherever data exists. Show missing
   years and definition breaks explicitly. Never invent values or cherry-pick years.
4. **Honest context.** Provide cash, inflation-adjusted and GDP-share views where
   comparable data supports them. Name the deflator, base year and source. Label
   actuals, estimates and forecasts with the source's own vintage. Keep forecast
   styling distinct. Put important scope and definition notes beside the chart.
   Each section shows publication/as-of dates and the next announced release date,
   or explicitly says that no next release date is announced.
5. **Party proposals.** Cover every party represented in the House of Commons (every
   party with at least one MP) at a dated roster snapshot. Apply identical fields,
   order, length limits and visual treatment. Use neutral alphabetical ordering and no
   party colours or editorial ratings. Separate official party claims from independent
   assessments. Policy judgements must be linked, attributed quotations from IFS, OBR,
   Resolution Foundation, Full Fact or NAO. Missing costings or assessments are stated
   as unavailable, not manufactured. Record proposal scope, baseline, year and status.
6. **Evidence.** Every displayed number resolves to a retained official source,
   file hash, publication, exact table/sheet/cell or series locator, fiscal year,
   unit, geography, accounting scope and actual/estimate/forecast status. Derived
   numbers name the formula and operands. Missing is not zero. Checks reopen raw
   data independently, reject changed hashes, and enforce source-justified rounding
   and reconciliation tolerances. One command rebuilds data and pages reproducibly.
7. **Plain language.** The following eight rubric questions are answerable
   within two clicks and without passing a screen of unrelated content:
   - What does government spend the most on?
   - Of every £100 spent on services, how much goes on health?
   - How much debt interest was paid in 2025-26, with its status labelled?
   - Has real health spending risen or fallen over the latest ten comparable years?
   - Is spending a larger or smaller share of GDP than ten comparable years ago?
   - How do old-age pensions compare with defence?
   - Which numbers are forecasts?
   - Where can I check this number?
   Add equally clear answers for the main taxes, receipts, borrowing and debt.
   Enforce reading grade 7 or below (Flesch-Kincaid), checked automatically.
8. **Impartiality.** Enforce a published banned evaluative-word list and a neutral
   palette. Apply any government annotations consistently to every government.
   Keep an append-only corrections log with date, page, error and correction, and
   apply the same evidence standard to every party.
9. **Accessibility.** Full core content works without JavaScript. Every chart has
   a semantic table alternative; colour never carries meaning alone. At 360px there
   is no lost content or unusable navigation. Each HTML page is below 500KB. All pages
   and expanded states have zero WCAG 2.2 AA axe violations at mobile and desktop
   widths, including contrast.
10. **Openness.** Publish methods, definitions, limitations, Open Government Licence
    attribution on every page, downloadable open datasets, raw-source references and a
    reproducible README. The repository stays private until the owner approves making
    it public; check current visibility before treating this as a blocker. Build a
    working public error-reporting route from this repository's issue tracker and
    publish verified operator/funding facts only. An unknown funding or operator fact
    is a precise remaining gap, not a reason to leave the route, methods or disclosure
    page unbuilt. Never invent these facts or claim the whole level before it is met.
11. **Freshness.** Provide a documented one-command refresh with validation, a
    reviewable version/diff report and safe retention of the last good data on errors.
    A scheduled GitHub Actions workflow in this repository notices new releases of each
    source (data families, party rosters and plans) and opens an update issue for review,
    without duplicates.
12. **Live completion.** Every merge to `main` deploys `site/` to Vercel. Checks run on
    each pull request: build, data reconciliation, page size, no-JavaScript content,
    WCAG and the banned-word list. The deployed pages must match the regenerated output.

## Starting point

Start from an empty site. Choose a simple, deterministic static pipeline (for example
Python that downloads official files, records their URL, date and SHA-256, and writes
HTML into `site/`). Official sources include HM Treasury Public Expenditure Statistical
Analyses (PESA), the Office for Budget Responsibility public finances databank and
historical database, and ONS public sector finances. Prefer each publisher's own files
over third-party copies.
