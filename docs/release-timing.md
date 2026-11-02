# Prospective release and deployment timing

This is automated measurement infrastructure for issue #38, not an independent
scorer or a claim of Freshness level 4. The [rubric](rubric.md) requires:

> Over the past year, every update went live within four weeks of its source being published.

A new ledger cannot establish a real year of timely updates. It does not establish
that discovery found every release, either. Missing dates, discovery failures,
unknown historical deployments and gaps in observation remain visible limitations.
No people-review evidence is created by these checks.

## Observe and report

Use the setup dependencies in the [README](../README.md), including Poppler for
validation of retained PDF evidence. From the repository root:

```sh
python scripts/discover.py --report discovery-report.json
python scripts/release_timing.py observe \
  --ledger measurements/release-timing.jsonl \
  --discovery discovery-report.json \
  --revision "$(git rev-parse HEAD)" \
  --evidence-url https://github.com/OWNER/REPO/actions/runs/RUN_ID
python scripts/release_timing.py report --ledger measurements/release-timing.jsonl
```

Replace the evidence URL with an actual public run containing the observation.
The revision must be the checked-out full Git commit. The initial checked-in
baseline may instead link the input repository commit: that URL identifies the
retained snapshot, not a historical Actions run. Its timestamp is the real current
instrument observation, not the commit time and not evidence of when the source
was first discovered or deployed. Historical first observations remain unknown.
Discovery is optional for
`observe`; when supplied, retained source baselines, discovered versions and
per-source errors are recorded. Existing source inventory and manifests determine
source identities, not manually entered figures. A discovered version is not a
claim that the site already uses it.

To verify delivery of the retained snapshot without discovery or refreshing data:

```sh
python scripts/release_timing.py observe \
  --ledger measurements/release-timing.jsonl \
  --revision "$(git rev-parse HEAD)" \
  --evidence-url https://github.com/OWNER/REPO/actions/runs/RUN_ID \
  --live-url https://unpoliticaldeepseeksuperagent.vercel.app
```

This first checks deterministic generated output against retained sources. It
fetches **every local file** under `site/`, including JSON, CSV, source evidence,
styles and other assets, not just HTML. Each response must equal the local bytes.
A missing file, changed bytes, network error or failed build check cannot produce
a successful live observation. Failed live attempts are recorded as unavailable
evidence and exit unsuccessfully. This verifies the local file set; it does not
prove that the host serves no additional, untracked paths. Fetches occur in
sequence, so it is a verified polling observation rather than an atomic deployment
transaction or a continuous availability guarantee.

## What the timestamps mean

- **Publication/vintage:** the official date or timestamp for that source version,
  where available. The historical Commons roster's `as_of` date describes its
  snapshot vintage, not publication time, so publication remains unknown there.
  A retained URL revision may have no publisher timestamp. Do not
  substitute download time, an HTTP cache timestamp or observation time for it.
- **First observed:** the first time this ledger observed that source version.
  Baselines present when measurement starts are observed now, not backdated.
- **First verified live:** the earliest successful all-file verification recorded
  for that source version. This is not the historical first instant it went live;
  the site might already have served it before measurement started. Historical
  first-live fields remain unknown, including for initial retained baselines.
- **Revision and site fingerprint:** bind the observation to checked-out code and
  the exact verified file set. A ledger-only commit with the same source versions
  and site fingerprint is not a new deployment measurement.

Date-only publication evidence is not an exact midnight release. The report uses
a UTC calendar-day uncertainty interval and reports lower/upper elapsed-seconds
bounds rather than inventing a precise publication instant. That convention is
not proof of the publisher's timezone or time of day. Unknown publication dates
have unknown publication-to-live delays. Even where a delay is available, it is
to the **first verified** live observation, not a recovered historical deployment
time. Do not turn baseline measurements into retrospective four-week pass/fail
claims. Polling delays, failed attempts and missing evidence must be considered
when interpreting the JSON report.

## Append-only evidence

The committed [JSONL ledger](../measurements/release-timing.jsonl) is append-only.
Events include sequence numbers, timezone-aware timestamps, evidence links and a
SHA-256 chain. `report` validates existing events before producing JSON; it fails
on invalid hashes, ordering, source/deployment evidence or broken chains rather
than silently repairing them. `observe` preserves prior bytes, validates the
candidate ledger and appends new evidence. Never edit old observations to make a
measurement look earlier or remove an error; investigate and retain the evidence.

To verify that an earlier ledger remains an unchanged prefix:

```sh
python scripts/release_timing.py report \
  --ledger measurements/release-timing.jsonl \
  --previous-ledger /path/to/previous-release-timing.jsonl
```

[CI](../.github/workflows/check.yml) runs unit fixtures, validates the JSON report
and compares the ledger with the PR base (or previous main-push revision). This
prefix check detects rewritten or removed historical lines even if someone
recomputes a self-consistent hash chain. The chain is an integrity check, not an
external trusted timestamp authority or a substitute for repository history.

## Scheduled collection and safe persistence

[Release discovery](../.github/workflows/discover.yml) observes immediately after
its discovery command, including when that command reports errors. It includes
the ledger in its existing validated revision-notice PR and uploads both the
ledger and JSON report with discovery evidence. Known notices and measurements
can be preserved even when some discovery sources fail; the job still surfaces
the discovery failure. A failed timing observation also does not suppress known
revision notices: the last-good ledger still must pass report validation alongside
the normal notice checks before publishing, and a final step surfaces either
discovery or timing failure. Invalid ledger contents or failed unit/site checks
still block publishing. It does not refresh retained figures.

[Deployment timing](../.github/workflows/deployment-timing.yml) runs on main pushes,
manual dispatch and completion of the main-branch **Discover official releases**
workflow. The completion trigger covers token-driven discovery merges that may
not emit another Actions push run. It accepts only scheduled/manual discovery
runs from this repository, not PR/fork execution, and never executes upstream
artifacts or trusts an upstream checkout. It also measures after failed discovery:
that failure is not cleared or bypassed, and live measurement does not rerun it.
After acquiring the shared persistence concurrency group, it checks out current
`main`, not an older queued push's snapshot. It performs no
release discovery, source refresh or committed-site rebuild. The observer's
read-only deterministic build check is still required. It verifies the fixed
production URL, with at most eight attempts and 45 seconds between failed
attempts, subject to the job timeout. This allows ordinary deployment propagation
without unbounded polling or claiming success after a mismatch.

Only after successful live verification, unit tests and ledger-report validation
does the deployment workflow open a **measurement-only PR**. Only the ledger is
staged. Its commit author is `jnyross-agent`, and generated PR text explicitly
identifies an automated agent, not a human. Exhausted verification failures leave
a failed job and uploaded ledger evidence; they do not publish a PR through
failed checks. Those failed-attempt artifacts are subject to GitHub retention and
expiry, and are not durable committed ledger history. A later successful retry in
the same run persists its earlier failed attempts along with success; a later run
does not automatically import an earlier exhausted run's artifact. Daily discovery
still records its own failures through its normal validated persistence path. The source-version/site-fingerprint deduplication makes the next
ledger-only main push a no-op after successful verification, preventing an
endless chain of measurement PRs. Changed site bytes can produce a new verified
snapshot without pretending the source version was newly published.

Discovery and deployment writers share non-cancelling concurrency. Deployment
has only contents/pull-request write permissions; it cannot open discovery issues.
Neither workflow uses admin bypass. Existing failed/cancelled PR checks block
merge; pending checks require normal auto-merge and branch protection remains in
force. Actions-token PRs may not start new Actions runs, so the producing workflow
runs its validations before creating a PR. The discovery-completion trigger covers
that workflow's token-driven merges; manual dispatch remains available after other
token-driven merges or to investigate a missed run. A protected branch requiring
additional checks may leave a visible unmerged PR rather than being bypassed. Keep failures
and artifacts available for investigation; do not treat a queued or unmerged PR
as committed evidence.
