# Scheduled validation history repair (#49)

Automated checks, not people evidence. These tests do not establish a year of
release history or a Freshness L4 claim.

## Controlled shallow/full checkout comparison

On 2 November 2026 a disposable checkout was cloned with `--depth 1` via `file://`
from this ticket's local repository at baseline
`456ff75943f51a3f8b2e8ccc1e16e8b9850b2c3c`. Its branch was named `main` to reproduce
the scheduled workflows' checkout. Only the two repaired workflows and their new
configuration regression tests were copied in; no pinned fixtures were changed.
The actual kit pin was read from `docs/comprehension-kit/version.json`:
`86bb51b462f8da2dcb24d7e291d9de181ea13978`.

```sh
git clone --depth 1 --branch agent/freshness-level-1-ae4e6fd80229 \
  file://<ticket-repository> <temporary-directory>/checkout
git switch -c main
python3 -m venv <temporary-directory>/venv
<temporary-directory>/venv/bin/python -m pip install -r requirements.txt
git rev-parse --is-shallow-repository
git rev-list --count HEAD
<temporary-directory>/venv/bin/python -m unittest discover -s tests -p 'test_comprehension_kit.py' -v
git fetch --unshallow origin
# Repeat history and test commands, then run the full suite:
<temporary-directory>/venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Results at unchanged HEAD:

| Checkout | Shallow | Reachable commits | Pinned kit suite |
|---|---|---:|---|
| Default depth 1 | true | 1 | 5 tests, 2 errors; `git show` exits 128 for the pinned `site/index.html` |
| Full history after fetch | false | 84 | 5 tests passed |

The complete full-history unit suite passed: 190 tests in 47.661 seconds,
including the two added workflow-history guards. The guards also reject the
original shallow configurations, options on unrelated actions, commented-out
options and environment variables. `git diff --check` passed.

Local Python was 3.14; Actions uses Python 3.12. CI separately validates that
runtime. Full history, rather than a hard-coded fetch of today's pin, makes future
reviewed kit revisions available without changing or skipping their checks.

## Live observation rehearsal

The existing `release_timing.py observe` path was also executed against the real
production URL using a disposable ledger and ticket issue URL as evidence. Every
local site file at `75368b12ba7e76ae25d82748d1c8453e17b74105` matched production bytes;
observation/report succeeded on 2 November 2026. This was a rehearsal, not persisted
repository evidence. Existing ledger entries were not replaced with its results.
## Real repaired Actions run

Manual dispatch of the repaired workflow at ticket head `1cde933` ran as
[41390518791](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/actions/runs/41390518791).
It checked out main with full history, verified every production byte, and passed
the full unit-fixture/report step on Python 3.12. Persistence was **not skipped**:
it committed 24 real ledger additions at `15e2014` and pushed
`automation/deployment-timing-41390518791-1`. GitHub then refused `createPullRequest`:
“GitHub Actions is not permitted to create or approve pull requests.” Thus the run
failed and those additions are **not** committed-main measurements. Artifacts alone
do not count. No ledger entries were fabricated or silently imported from a failed
artifact.

The missing prerequisite is the repository owner's Actions PR-creation permission
(Settings → Actions → General → Workflow permissions → Allow GitHub Actions to
create and approve pull requests). The agent also cannot inspect that setting: its
read-only permissions API request returned HTTP 403. Do not bypass the restriction
with another credential or a direct-main write. Keep the ticket PR as an incomplete
draft until permission is supplied and the real path can complete.

After integrating the concurrently merged publication metadata (#51) and context
work (#52), all 198 unit tests passed in 75.854 seconds, deterministic regeneration
passed, and corrected-page browser checks passed at mobile/desktop. The single
shared metadata record retains #51's publication/file fields and adds validated
date/hash/evidence fields. The initial hash/date evidence remains the real ledger
introduction, not a fabricated correction. Updated Before captures use main
`4ad9115`; After captures use UI revision `35d75ef` at identical viewport/theme/state.
