# Freshness wave six: demonstrated discovery gaps and useful coverage

Refs [issue #49](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/49).
This is useful partial coverage, **not completion of Freshness L3**. No source figures,
historical offers, dates, static pages, notices or timing ledger are changed by this PR.
Baseline: `5928df7` (merged Context audit #58). The independent scorer awards levels.

## Decisions and implemented coverage

- Keep the existing four HMT/OBR release/latest adapters and all historical URL checks.
  Reuse [Context wave-six evidence](../context-w6/README.md), not a second interpretation
  of its 22-source comparison or an invented next-release date.
- The old roster monitor only checked 9 July 2024. Today's official dated Commons API
  has two newly represented party IDs (Your Party and Restore Britain), demonstrating
  the gap. Add a runtime **UTC-date** comparison, using validated party identity/seat
  semantics and source + semantic-hash issue keys. Poll dates, raw API timestamps,
  ordering and presentation do not create new candidate identities. Do not require a
  fixed seat total; vacancies can be legitimate. Keep the historical endpoint check.
- Add bounded Liberal Democrat adopted-policy listing discovery: only conference-paper
  links between the verified `policy-papers` and `register-for-conference` ID markers.
  The [actual response](libdem-policy-listing-response.html), [request record](libdem-policy-listing-request.json)
  and [canonical 14-link baseline](libdem-policy-listing-baseline.json) are retained.
  New/retitled links create review candidates; ordering, duplicated links and incidental
  HTML do not. The initial retained listing yields **zero candidates**: no synthetic backlog.
  Listing hashes are not paper-content hashes or publication dates. PDFs, motions,
  new direct-PDF links and full manifesto completeness are outside this adapter's scope.
- Neither a newer roster nor a new policy paper is a revision of the explicitly
  historical 2024 manifesto/roster. Both scopes are excluded from historical revision
  notices. Review and retain a deliberately dated new baseline before changing the site.
  A generic fiscal refresh does not advance the historical roster or approve new policy.
- [Verified alternatives](alternatives.md) retain official Conservative news/article and
  Liberal Democrat listing responses, plus failed/unestablished routes. Broad Conservative
  news was not turned into a noisy all-news issue generator. Labour unattended routes
  returned 403; a different tool's readable page is not proof of unattended access.

## Real operations: successes AND failure

[Current roster response](current-roster.json) was fetched at 06:21:56 UTC on
2 November 2026. Its request/hash record is [retained](current-roster-request.json).
The [real issue-opening report](roster-issue-report.json) records canonical
[update #59](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/59).
This is a genuine changed current composition, not a fabricated publisher release.

**Immediate repeat verification exposed a duplicate:** the second list/create call
opened [#60](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/60)
with the same marker. #60 is explicitly annotated as a duplicate; neither issue was
closed by the worker. The cause (stale cached/list visibility versus another delay)
is not established. Issue listing now requests `Cache-Control: no-cache`; a subsequent
read-only tripwire verified `already reported` and refused permission to create another
issue. This is a revalidation improvement, **not proof of atomic exactly-once delivery**.
The report preserves the failure rather than rewriting it as success. Local repeated,
closed-issue, duplicate-in-one-batch and later-page fixtures pass. Keep local issue-writing
runs serialized with Actions; remote list/create is not an atomic transaction.

The final [read-only discovery report](discovery-report.json), started at
06:31:54 UTC, checks all **22 inventory entries**, with zero lookup errors. It finds
one current-roster candidate and the previously known raw-byte Liberal Democrat
historical costing-page change; the new policy listing has no new links. It writes
only its report, not retained source data or the revision status. The raw costing-page
change remains conservatively monitored; it is not proof of a changed financial claim.

At investigation time the first post-wave 07:23 UTC cron slot had **not occurred**.
Only older manual run [41356197396](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/actions/runs/41356197396)
was visible (`workflow_dispatch`, revision `da59724c338e4ad9a363182e996968d5c4a50305`, success).
No manual/local call is labelled a scheduled run, and no missing pre-slot run is
called a scheduler defect. A genuine scheduled execution and its final revision,
source inventory, outcomes and artifact URL remain operational evidence to observe.
Timing persistence is separately owned by the previous ticket: the documented Actions
PR-creation permission failure is not presumed fixed or bypassed by this agent PR.

## Verification

Commands run from repository root with README dependencies:

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python -m unittest discover -s tests -p 'test*discover*.py'
.venv/bin/python scripts/build.py --check
.venv/bin/python scripts/check.py --self-test
.venv/bin/python scripts/check_history.py --self-test
.venv/bin/python scripts/check.py
.venv/bin/python scripts/manual_access.py
.venv/bin/python scripts/discover.py --report docs/evidence/freshness-w6/discovery-report.json
```

Results and final head CI are recorded in the PR. Fixtures use network/GitHub tripwires;
new, unchanged, repeated and unavailable cases do not manufacture production releases.
The deterministic build reports no generated changes. There is no UI change, so no
Before/After UI comparison is claimed or needed. No people evidence is supplied.

## Remaining acceptance, not hidden completion

Twelve other party-plan families remain historical-URL-only monitors. The new LibDem
adapter is a bounded conference-paper listing, not comprehensive plan discovery or
assessment discovery. Conservative news is verified but needs a precise plan-publication
selector/completeness strategy; Labour unattended access remains unestablished. Other
party listing routes were not exhaustively checked. Full all-source new-release coverage,
robust immediate-repeat live dedup evidence and a genuine scheduled run remain unresolved.
Issue #49 stays open (`Refs`, not `Closes`); this partial PR does not award L3 or L4.
