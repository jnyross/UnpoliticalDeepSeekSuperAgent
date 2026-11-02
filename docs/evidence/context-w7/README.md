# Context wave seven — incremental evidence, not a repeated full audit

Refs [#56](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/56).
Baseline/scored revision: `278cc11526ea50a612c4644e2dd521c479bfe5db`.

## Result

The completed [wave-six 22-source audit](../context-w6/README.md) and merged
[#58](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/pull/58) are reused,
not rebuilt or described as a fresh all-source comparison. This follow-up is bounded
to the newly added IFS source, actual current deployment/notice state, and verified
official calendar alternatives. It changes no application code, source manifest,
notice, figures, generated page, release calendar or timing ledger.

### Added IFS source and current notices

[Incremental report](incremental-reconciliation.json), **2 November 2026,
08:23:32–08:23:53 UTC**:

- Current inventory has **23** entries; the only added ID versus the wave-six audit
  is `party-evidence-ifs-june2024-opening-remarks`. No old IDs were removed. The
  previous 22 source responses were **not** fetched or revalidated in this run.
- The official IFS opening-remarks PDF was successfully fetched: **96,037 bytes**,
  SHA-256 `4b1e23d31441a1a073206345451bb2fc81073369cd72ad97496dd112fb56103c`,
  equal to both the manifest and independently hashed retained PDF. The existing
  retained-URL discovery adapter reports **unchanged**, not unknown; zero errors.
  This does not discover all new IFS publications or prove future release timing.
- All **85 deployed files** match the current generated baseline byte-for-byte,
  including the IFS PDF, public source/data manifests, all nine HTML pages and
  revision status. Every compared file hash is retained in the report.
- Incremental reconciliation with the existing state machine leaves notice state
  exactly unchanged: one previously published LibDem raw-byte warning, original key
  and first-detection timestamp preserved; no new IFS notice. That warning is not
  evidence that a financial claim changed. No fresh LibDem byte/meaning claim is
  made here; reuse the distinct observations recorded in wave six.
- [Offline section check](section-check.json): Reform UK displays the IFS publication
  date **2024-06-24**, explicitly unspecified source-update date and fixed-snapshot
  no-next-release statement, with **zero** revision notices. The single existing
  warning remains local to Liberal Democrat. Since the production page hash matches,
  these checks describe the actual returned production bytes as well as local output.

### Official calendar alternatives and the exact remaining clause

[Calendar-alternative report](calendar-alternatives.md) retains the bounded official
requests, raw responses, timestamps, hashes, redirects and interpretation. It separates
HMT publication evidence, OBR databank timing and the ONS public-sector-finances
calendar; an ONS release date must not be substituted for an OBR databank update.
All **11 bounded requests** succeeded without truncation. The HMT upcoming finder
returned zero results; an alternative announcement-format API returned 40 old records,
not future appointments. Both HMT collections still match retained hashes. OBR's
pages supply only approximate databank timing, not an exact next date. ONS does
confirm **20 November 2026, 7:00am** for its October PSF bulletin/time series, but
this is explicitly **not** an OBR databank appointment. The broad PESA term search
returned only the first 100 of 3,804 records, so it is not an exhaustive negative.

**Context L4 remains unearned.** Its literal requirement is:

> Each section shows the date of the data and the next scheduled update, and the site never shows data that has since been revised without saying so.

The verified alternatives do not establish exact next updates for every displayed
source family. Retain the product specification's explicit no-announcement fallback,
not an inferred date or a renamed polling schedule. Fixed historical 2024 documents
also do not have an established next release date. A successful point-in-time check
and existing daily monitoring cannot prove instantaneous never-stale behavior.
No wording change, byte warning or bounded search awards the level; the independent
scorer decides. **Keep #56 open**, with precise missing evidence of publisher-announced
next updates rather than a request for invented owner dates or a duplicate watcher.

## Reproduce and validation

From repository root with README dependencies:

```sh
# Network: only the added IFS source, plus exact current production snapshot.
python3 docs/evidence/context-w7/reconcile.py
# Network: fixed bounded official calendar alternatives, not the old 22 sources.
python3 docs/evidence/context-w7/capture_calendars.py
python3 docs/evidence/context-w7/capture_calendars.py --only ons-psf-keywords obr-databanks-year obr-monthly-listing
# Offline: publication/date block and notice placement.
python3 docs/evidence/context-w7/check_sections.py
.venv/bin/python scripts/build.py --check
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

The incremental reconciliation and section-check commands regenerate their named
reports; preserve this historical evidence before rerunning. Calendar captures create
new UTC-stamped directories without overwriting older responses. Never describe a
fresh response as the saved observation. They do not refresh the site, publish notices, create
issues or persist timing history. Errors remain unknown/errors, not unchanged.

Actual results: added-source/deployment capture exited **0**; section check passed;
deterministic build reported **no generated changes**; **244 Python tests passed**.
The suite reuses existing notice persistence through failed/unchanged checks and exact
corresponding-revision incorporation regressions. No duplicate watcher/state machine
or synthetic release was added. Head CI results are recorded in the PR.

No UI change: Before/After UI evidence is not applicable to this documentation/evidence
follow-up. Previous actual application captures remain attached to the implementation
PRs; they are not misrepresented as new captures. No people tests, manual keyboard or
screen-reader outcomes, scorecard, release dates or history were fabricated.

## Coordination

[#49](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/49) separately
owns scheduled execution, issue-opening idempotency and timing-persistence work.
This follow-up supplies the newly registered source/current deployed-notice comparison,
not a second operational run. It does not treat manual capture as a schedule event,
claim all-source new-publication discovery, alter the canonical roster-release marker,
create a duplicate update issue, or assume Actions PR permissions changed.
