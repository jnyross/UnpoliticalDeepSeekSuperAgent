# Context wave eight — three additions, observed warning and remaining limits

Refs [#56](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/56).
Scored/baseline revision: `9864a10c5a5beb5d49f10a9eb19bcbd00d5d155b`.

## Useful completed result

Reuse the completed [22-source audit](../context-w6/README.md) and
[IFS/calendar follow-up](../context-w7/README.md), merged in #58/#64. This run fetches
only the three sources subsequently added by #65/#67, not the old 23 sources or the
eleven already investigated calendar alternatives. Inventory delta: **23 → 26**,
three additions, no removals.

The actual [incremental report](incremental-reconciliation.json) ran on
**2 November 2026, 10:06:50–10:07:07 UTC**:

| New retained source | Actual result | Interpretation |
|---|---|---|
| Conservative costings archive PDF | **HTTP 429: Too Many Requests; unknown**. Retained PDF hash matches its manifest. | Current remote bytes could not be verified. No remote hash/body invented, no rate-limit bypass or alternate identity, no unchanged verdict. #65's prior successful archive provenance is not a new live response. |
| LibDem costings PDF | **Unchanged**, 3,303,719 bytes, SHA-256 `378f7ccaafcd18eea51a86b422db98462602f22fabd1418d48180a46a5f68ff3`. | Successful official fetch matches independently hashed retained bytes and manifest. Historical URL check, not new-publication discovery. |
| NI Department of Education childcare announcement | **Raw bytes changed**, 36,982 bytes; SHA-256 `26f83f3cdfaa7887b7e0372ff923e813a18e2b0065f9ad2c9be5c26f3efda421` versus retained `23c4be542a61206e7dafc01b05a2ff7fffde8374c8a824641662275a12e645cb`. | Existing reconciliation yields a new source-scoped warning; publish it beside the DUP programme while retaining the prior LibDem warning. No figures or source baselines are refreshed. |

**The audit exits 1**, accurately retaining the archive failure while completing the
other independent checks. This is **not a fully successful three-source live audit**.
The finite implemented result is the warranted new warning and truthful reusable
evidence, not a fabricated unchanged verdict or a completed rubric level.

The same report confirms **all 91 pre-change production files** exactly match the
baseline, including all nine HTML pages, three new sources, published source/data
records and the then-single LibDem notice. This distinguishes the deployed pre-change
state from the subsequent local warning rebuild. It does not claim that the new
warning was already deployed at the initial observation time.

### Raw change is not demonstrated changed financial meaning

A [separate independent DE response check](independent-de-check.json), with its own
genuine timestamps and raw bytes, confirms the observed hash. The extracted visible
text is unchanged from the retained transcript, including the £25m/2024-25 programme
statement, prior approval and 23 May 2024 publication date. No revised financial
estimate or changed release date is demonstrated. The existing conservative raw-byte
warning is retained rather than silently dismissed or used to refresh claims.

[Section/source review](section-audit.md) verifies the DE programme reference and
publication date are DUP-only. The two new costings PDFs are downloadable audit
supplements, not party-card evidence references: they are monitored but currently
have **no card date/notice destination**. This real scope limitation is explicit;
we do not claim universal revision-display coverage. Neither supplement supplied a
known observed revision requiring a current card warning. The Conservative table's
2029-30 year and LibDem's £1,420m/2028-29 row are not silently transferred to their
separately cited manifesto/release claims.

## Exact next-update clause remains unearned

No genuinely new applicable next-release appointment was found in these fixed 2024
additions. Fiscal columns, policy commencement dates, archive capture dates and
retrieval/detection times are not publisher announcements of the next release.
Reuse #64's bounded official calendar findings, with their dated and incomplete-search
limitations; do not repeat that investigation as unfinished work or imply it establishes
a current global absence. The ONS PSF appointment is still not an OBR databank date.

The literal Context L4 check remains:

> Each section shows the date of the data and the next scheduled update, and the site never shows data that has since been revised without saying so.

**Keep #56 open; no L4 claim.** Exact applicable HMT PSS/PESA Chapter 4/OBR databank
next dates remain unestablished in the retained verified evidence. Current archive
revision status is also unknown, and supplemental notice-display scope is limited.
Preserve the honest product-spec no-announcement fallback; cadence, polling and
unrelated publication dates are not substitutes. Daily detection/deployment does not
prove instantaneous never-stale behavior. No human can legitimately supply invented
publisher dates, and this evidence-only residue is not a request to bypass access.

## Actual Before and After application evidence

**Before:** actual baseline `9864a10c5a5beb5d49f10a9eb19bcbd00d5d155b`, copied from
its committed application before rebuilding. **After:** this PR's actual generated
party page with the observed DE notice. Exact HTML hashes, capture timestamps and
matched viewport/state are retained with the captures. Later evidence-only commits
preserve those changed party-page bytes.

Matching screenshots and capture metadata are provided alongside this guide: default
light theme, JavaScript disabled, initial disclosures, DUP card aligned at the
viewport top, **360×800 mobile / 1280×900 desktop**. No mockups or edited screenshots.

| View | Before | After |
|---|---|---|
| Mobile | [Before](before/dup-360x800.png) | [After](after/dup-360x800.png) |
| Desktop | [Before](before/dup-1280x900.png) | [After](after/dup-1280x900.png) |

[Capture metadata and independent response reproduction](independent-followup.md)
retain exact HTML hashes, notice-card IDs and current-state checks. The matching
mobile comparison was visually inspected by the worker.
Only the DUP's local warning changes; its approved-programme qualifications and
funding/status fields remain intact. The existing LibDem warning remains unchanged.
These are agent/browser checks, not people, manual keyboard or screen-reader evidence.

## Reproduce and validation

From repository root with README dependencies:

```sh
# Only the three added source URLs plus exact current production bytes:
python3 docs/evidence/context-w8/reconcile.py
# Separate single DE response and visible-text/consumed-span comparison:
python3 docs/evidence/context-w8/independent-de-check.py
.venv/bin/python scripts/build.py --check
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

Capture scripts overwrite their own named evidence outputs with a **new** observation;
preserve the retained historical reports first. An unavailable source exits nonzero
and remains unknown. The reconciliation script never mutates source baselines, opens
issues, refreshes figures, writes revision state or timing history. The new persisted
notice is exactly `reconciled_notices` from the saved report, applied to
`sources/revision-status.json`, then rendered with `.venv/bin/python scripts/build.py`.

Only generated `parties.html` and public revision status change. Reviewed the static
warning/link: no inventoried controls, states or task semantics changed, so only the
party-page hash was refreshed via `.venv/bin/python scripts/manual_access.py --write`.
No manual check results were created. Existing failure/unchanged/incorporation
regressions are reused rather than a duplicate watcher or state machine.

Actual final validation: deterministic build passes with no generated drift;
**263 Python tests pass**; the changed party page passes both full automated browser
viewports (no-JavaScript content, overflow/size, axe and supplemental contrast), in
addition to the matched capture assertions. Head CI is recorded in the PR.
#49 continues to own scheduled execution, delivery idempotency and persistence
evidence; this is not a scheduled event,
a synthetic release, a timing-ledger update or a duplicate issue-opening run.
