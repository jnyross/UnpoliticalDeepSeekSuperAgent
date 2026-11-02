# Wave seven: repair immediate-repeat issue delivery

Refs [#49](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/49).
Baseline/scored revision: `278cc11526ea50a612c4644e2dd521c479bfe5db`.
Reuses merged #62, its genuine roster response and the canonical release identity
`dbf2f8670557ea2c0c0854672dc669a1ba8e6f32bd2109896311f77626f15ff5`.
No new production issue is created and neither #59 nor duplicate #60 is closed.

## Diagnosis and chosen repair

#62's cache-revalidation header was insufficient protection: issue list/create are
separate remote operations. We do not know the exact upstream/cache delay behind
#59/#60, but the old algorithm necessarily duplicates when the immediate next list
omits a successful write. A later visible marker is not evidence about that write path.

Add a local **write-ahead delivery journal**, separate from source manifests, site
notices and measurement history. Serialize users of the same journal with a filesystem
lock. Persist/fsync a pending reservation before the GitHub create call; record the
returned issue URL after success with atomic file replacement. The journal is keyed
by case-normalized repository and the existing release key, not a new date/hash/identity.
Older repository-case aliases are reconciled; canonical GitHub URL casing is accepted.

- Successful receipt + stale list: already reported; no second create.
- Timeout/crash, unexpected create response or failed success-record write: pending
  receipt remains; refuse blind create until a remote marker resolves the uncertainty.
- Remote marker later visible (open or closed, any page): record reported, including
  reconciliation of a pending attempt. A later stale list cannot undo that receipt.
- Malformed/unwritable journal: fail closed, not a clean empty state. Failed list:
  no create/reservation. Known revision notices and last-good source data are preserved
  by the existing independent discovery/reporting logic.

The production discovery job is restricted to the triggering `main` ref, not merely
a checkout of main: Actions cache scope follows the triggering ref. This prevents a
non-main manual dispatch from writing production issues into an isolated receipt scope.
The scheduled workflow restores/saves only this small public journal through scoped
Actions cache entries, including pending attempts after errors, before later validation
or PR-persistence work. It also retains the hidden JSON file in the existing discovery
artifact. This does not need a source-data/measurement PR or bypass its permission gap.
No new deployment or measurement history is claimed from a cache entry. Cache/artifact
restoration is configuration (workflow validation is part of head CI), not presented
as an observed run of the changed scheduled workflow.

Cache retention is not guaranteed. A fresh workspace with no restored journal still
uses all-state remote markers and serialized delivery, not a distributed transaction.
Concurrent writers in separate workspaces must not run; restore the retained journal
when recovering a failed run. If a create attempt truly failed before creating anything,
its pending receipt intentionally requires verification before clearing/retrying.
The journal never silently turns an uncertain attempt into a second issue.

## Verification: write path, not only read-only success

The [eleven delivery fixtures](delivery-fixtures.txt) exercise the actual `open_updates`
implementation with the **real canonical roster key/evidence**, but an isolated fake
transport and temporary journal. The fake list deliberately stays empty even after
its fake create succeeds. This is explicitly automated fixture evidence, not a new
publisher release, real GitHub create or people evidence.

They verify exactly one write across immediate repeats, simultaneous separate Python
processes and another process restart; timeout-after-remote-acceptance reconciliation;
failed persistence before/after creation; invalid create response; corrupt journal;
failed list; and repository isolation. Existing unchanged/new/closed/later-page/error
source fixtures remain in place. An explicit local journal replaces neither marker
pagination nor the workflow's serialization.

The [live canonical check](canonical-marker-verification.json) performs two guarded
existing-marker calls. Any production write is rejected by a tripwire. Both return
already reported; the key remains identical. This supplements the write-path fixtures
but is **not** represented as a newly observed successful production create/repeat.
We cannot safely demonstrate another real create for this already-reported release
without deliberately duplicating the review task, which the request forbids.

Commands:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_issue_delivery.py' -v
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python scripts/build.py --check
gh api 'repos/jnyross/UnpoliticalDeepSeekSuperAgent/actions/workflows/discover.yml/runs?event=schedule&per_page=10'
```

The full suite and deterministic build passed; final results and workflow/browser CI
are recorded in the PR. No application HTML/data/source baseline changes: UI evidence
is not applicable. No manual keyboard, screen-reader or political-review evidence.

## Remaining acceptance is explicit

The [schedule-only API result](scheduled-runs.json), retrieved during the timestamped
canonical check, still returns zero visible runs after the 07:23 UTC slot. Absence is
an operational evidence gap, not proof of broken cron or a scheduled event to invent.
The [read-only workflow-state query](workflow-state.json) reports `active`; no disabled
workflow was found to repair. No manual dispatch is labelled scheduled.

Current inventory remains 23 entries with 17 retained-URL-only monitors. Reuse
[verified official listing alternatives and their limits](../freshness-w6/alternatives.md)
and the completed roster/LibDem adapters; this PR does not claim all-party new-plan
coverage or silently relabel historical evidence. The original permission residue
remains separate: timing run
[41404402948](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/actions/runs/41404402948)
was reported to fail at Actions PR creation after observation/tests. Journal caching
is not measurement persistence on main and does not assert that setting changed.

This completes the focused duplicate-write repair with reproducible failure cases,
not all of #49 or Freshness L3/L4. Use `Refs`, not `Closes`; the independent scorer
decides levels from genuine scheduled and source-coverage evidence.
