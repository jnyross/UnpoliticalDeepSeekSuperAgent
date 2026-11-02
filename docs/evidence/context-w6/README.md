# Context wave-six source/date/notice audit — issue #56

## Outcome and precise residue

The genuine [live audit](live-audit.json) checked **all 22 current inventory sources**,
including the four assessment/costing families added in #53. The run lasted
2026-11-02 **06:03:43–06:04:40 UTC**, against retained/site baseline
`693386bc035b0a3489718bee9712922748c181b7`. It found **21 unchanged sources, one
raw-byte HTML revision, zero lookup errors**. The Parliament adapter compares the
consumed party/seat semantics as designed; other retained snapshots compare raw bytes.

All **10 distinct retained official calendar endpoints** matched their retained
hashes, including the three upcoming-statistics searches (zero returned results).
All **81 deployed files** matched local baseline bytes, including the then-empty
notice state. The [section audit](section-audit.md) enumerates **195 date blocks**
on seven fiscal pages and the evidence/limitations for each section family.

The changed source is the Liberal Democrat historical share-buyback costing page:
retained SHA-256 `f56adb3a292de86e66ace5bbab6b81fd09004166e0922bc910e97e4f396c2f7c`,
observed SHA-256 `201dfea3b1da99aeea3ea6d646aeb44bb30eb2bec8cb3f39c0484578392acb60`.
The existing reconciliation produced one notice. This PR persists that genuine
notice and rebuilds the party page; it does not change source baselines, quotations
or numbers. `first_detected_at` is the audit's UTC run-start timestamp, following
the discovery report's checked-at convention, not an upstream revision time.
A [separate bounded response check](libdem-independent-response-report.json)
found another raw hash but identical normalized visible text and unchanged consumed
£2.2bn/£1.4bn context. Thus the observed change is **not evidence of a revised
financial claim**. Raw-byte monitoring deliberately conservatively flags such changes;
the warning is retained, not silently cleared on an unchanged or failed subsequent check.

**No Context L4 claim; Refs #56, not Closes.** Exact next release dates remain
unannounced/unestablished in the checked evidence. HMT cadence, OBR's approximate
post-monthly-release timing and fixed 2024 snapshots do not establish next scheduled
calendar dates. No comprehensive search of every announcement channel was performed.
Daily monitoring plus notice deployment cannot provide an instantaneous never-stale
guarantee. The existing product-spec fallback remains honest; the literal rubric
residue remains open for the independent scorer. No invented dates or people evidence.

## Reproduce

From repository root, with README dependencies installed:

```sh
python3 scripts/audit_context.py --output /tmp/context-audit.json \
  --live-url https://unpoliticaldeepseeksuperagent.vercel.app
.venv/bin/python scripts/build.py --check
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python scripts/check.py --self-test
.venv/bin/python scripts/check_history.py --self-test
EVIDENCE_DIR=/tmp/context-w6-browser npm run test:browser
```

The audit is read-only, reusing existing discovery and deployment verification rather
than adding a watcher. Its report retains each source baseline, retained-file hash,
request URL/hash/size/UTC start and finish, updates or explicit unknown/errors, notice
comparison, calendar comparisons and deployed-file hashes. Discovery scope remains
adapter-specific: retained-URL checks do not find new manifesto URLs or a current
roster. Reruns observe genuinely new timestamps/bytes and must not overwrite this
historical report as if it were the same observation. Exit zero means lookups completed,
not that `updates` is empty or that the rubric level is met.

To reproduce the applied notice without fetching or advancing any source baseline:
load `reconciled_revision_status` from the saved audit into
`sources/revision-status.json`, then run `.venv/bin/python scripts/build.py`.
Only `site/parties.html` and `site/sources/revision-status.json` change.

## Before and After — actual application, matching state

**Before:** baseline `693386bc035b0a3489718bee9712922748c181b7` committed `site/`,
copied before rebuild. **After:** this PR's rebuilt application with the single
observed notice. Exact HTML hashes and capture times are in the
[Before capture report](before-libdem-report.json) and
[After capture report](after-libdem-report.json). Evidence-only commits do not
change those HTML bytes. Both use actual Chromium, JavaScript disabled, default
light theme, the Liberal Democrat heading aligned to the viewport top, closed
disclosures, 360×800 mobile / 1280×900 desktop. No mockups or edited images.

| View | Before | After |
|---|---|---|
| Mobile | [Before](before-libdem-mobile.png) | [After](after-libdem-mobile.png) |
| Desktop | [Before](before-libdem-desktop.png) | [After](after-libdem-desktop.png) |
| Full card, mobile | [Before](before-libdem-card-mobile.png) | [After](after-libdem-card-mobile.png) |
| Full card, desktop | [Before](before-libdem-card-desktop.png) | [After](after-libdem-card-desktop.png) |

The notice appears only beside the Liberal Democrat offer, not all party cards.
The data date, no-announced-release fallback and existing offer remain intact.
The worker visually inspected the matching mobile comparison; this is not human
usability, manual keyboard or screen-reader evidence.

## Verification and operational coordination

- Full Python discovery suite: **209 tests passed**, including five new read-only
  audit fixtures for positive unchanged evidence, source errors with continued checks,
  changed snapshots/notices without mutation, changed calendars, and deployment failure.
- Existing discovery regressions cover failed/unchanged lookup persistence, repeated
  notices retaining their first detection, exact matching incorporation clearing only
  the applicable notice, date-only revisions and malformed-state preservation. These
  were reused, not replaced with a second watcher or duplicate state machine.
- Data/reading-grade checker self-tests: **25 passed**; history self-tests: **29 passed**.
- Offline rebuild validates independent source hashes/values, output copies, periods,
  reading grade, OGL, no active HTML, size and banned words. No source figures changed.
- Full final changed-site browser suite: **18/18 page/viewport checks passed** across
  all nine pages, both viewports, initial/expanded states, no-JavaScript content,
  overflow, axe and supplemental SVG contrast. Four Node runner/contrast regressions
  passed. These are automated checks only; head CI is recorded in the PR.
- Initial CI correctly caught the manual-preparation inventory's old party-page hash.
  Reviewed the added static notice/link: no inventoried controls, task semantics or
  states changed. Refreshed only the party-page hash with
  `.venv/bin/python scripts/manual_access.py --write`; no manual results were created.
  The full Python suite and final deterministic build were rerun after this refresh.

Coordination with [#49](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/49):
this bounded 22-source comparison is the reusable source evidence, not another
operational timing run. The audit neither opens update issues nor modifies the timing
ledger/workflows. The existing scored-SHA
[timing run](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/actions/runs/41393350277)
failed at Actions PR creation; this audit does not claim that permission changed,
that a manual audit is a scheduled event, or that measurements were persisted.
#49 separately owns genuine scheduled execution, issue-dedup operational evidence and
remaining persistence permission. This PR safely publishes the observed warning using
the already authorized agent PR path; it does not bypass protections or repair an
unproven scheduler defect.
