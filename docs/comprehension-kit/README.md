# Reproducible comprehension testing kit (version 1)

This is preparation only. No participants have been recruited and no responses,
timings or results are supplied. Completing this kit **does not award Comprehension
L4**. That still requires at least five real people who do not follow politics to
each answer at least seven of eight correctly in under five minutes, with actual
results recorded. The owner has decided not to run people checks; this protocol
is available for future authorized use, not authorization to recruit.

## Separate materials

- Give participants only [participant.md](participant.md) and the frozen home page.
  Print the sheet or show it separately; it contains no answer links or key.
- Keep [answer-key.md](answer-key.md), this protocol, and
  [version.json](version.json) facilitator-only during the session.
- [results-template.csv](results-template.csv) is intentionally header-only.
  Do not populate it with examples, automated answers or simulated timings.

The questions are verbatim from the fixed rubric. To remove ambiguity without
changing those questions, Q7 refers only to the home page, and Q8 refers to Q3's
debt-interest figure. These scope instructions appear on the participant sheet
before timing. All eight questions are scored separately, with no partial points.

## Freeze and reproduce the page

The full immutable page commit and preparation date are in `version.json` and the
answer key. The preparation date is **not** a test date. From an existing clone:

```sh
REV=$(python3 -c 'import json; print(json.load(open("docs/comprehension-kit/version.json"))["page_revision"])')
git worktree add --detach /tmp/comprehension-page "$REV"
# In that worktree, install the README dependencies, then:
(cd /tmp/comprehension-page && /absolute/path/to/venv/bin/python scripts/build.py --check)
python3 -m http.server 8000 --directory /tmp/comprehension-page/site --bind 127.0.0.1
```

Use an unused worktree path and port if needed. Start at
`http://127.0.0.1:8000/index.html` with no fragment. Do **not** refresh the data or
use the moving production URL as if it were this frozen revision. The pinned
commit retains the entire site and raw sources. Its existing independent build
checks reopen the official workbooks. External source links may later change;
use the retained official workbook for verification of this vintage.

From the kit checkout, run:

```sh
python3 scripts/comprehension_kit.py
python3 -m unittest discover -s tests -p 'test_comprehension_kit.py' -v
```

This verifies all eight questions, the regenerated key, current input hashes and
the same input bytes at the pinned commit. A full-history clone is needed
(`git fetch --unshallow` if the clone is shallow). It fails on changes to the
home page, spending/comparison data or their sources so a stale kit cannot pass.
Other site sections are not the tested scope. Existing CI runs the new tests
alongside the independent data/build checks; no live content is modified.

For a future reviewed page version, preserve the old kit from Git history and
explicitly regenerate with `python3 scripts/comprehension_kit.py --write
--revision FULL_PAGE_COMMIT --date YYYY-MM-DD` (on one line). Use a committed
revision containing exactly the current page/input bytes; check the new key and
protocol before committing. Do not silently replace a kit used in a session.

## Future facilitator protocol (not a record of tests performed)

1. Obtain consent to retain anonymous responses and timing before the session.
   Ask “Do you follow politics?” Record only `yes`, `no` or `declined`; only a
   voluntary `no` qualifies for the rubric. Do not infer eligibility from answers
   or collect names, contacts, political leaning, age or demographic details.
   Use an anonymous session ID; keep no identity mapping in this repository.
2. Record the actual UTC session date, full page commit, full kit commit, browser
   version, viewport in CSS pixels and JavaScript state. Use the same setup for
   all participants in a cohort; default 360×800, light theme, JavaScript off.
   Record deviations factually. Start with a fresh page at the top, no search
   highlights, previous answers, key, facilitator notes or pre-opened source tabs.
3. Keep the page and the question section concealed. Give/read only the
   instructions at the top of the participant sheet, explain how to enter
   answers and ask whether the participant is ready. No page tour or hints.
   Start the monotonic stopwatch when saying “start” and revealing the page and
   all eight questions together. Reading the questions counts within five minutes.
4. Do not coach, explain fiscal terms or indicate correctness. Participants may
   scroll and follow source links. For Q8 record their demonstrated route within
   the timed response if not written. Stop the watch when they declare completion;
   otherwise stop at 300 seconds. Freeze answers immediately. Voluntary stopping
   is allowed. If interruption or assistance occurs, mark the session invalid;
   do not pause and resume the clock as if uninterrupted.
5. Retain the actual elapsed seconds to at least 0.1 second, rounded **up** to
   0.1 second (never down across the limit). Set `stop_reason` to `completed`,
   `timeout`, `withdrew` or `interrupted`. A time of exactly 300 seconds fails
   “under five minutes”. Do not delete failures or cherry-pick successes.
6. Score frozen answers against the separate key. Copy each response faithfully,
   omitting unsolicited personal identifiers before any public record. Mark
   q1_score through q8_score as 0 or 1; sum them for total_correct. Record only
   short factual protocol deviations, not sensitive or evaluative notes.
7. `qualifies` is `yes` only when consent is yes, politics_following is no,
   protocol_valid is yes, stop_reason is completed, elapsed_seconds is less than
   300, and total_correct is at least 7. Otherwise it is `no`. Empty cells are
   unavailable evidence, never assumed passes. Withdrawn consent means retain
   no responses: record no personal data and no qualifying outcome.

## Recording future real evidence

Copy the header-only CSV to a separate dated cohort record; preserve the template
empty. Quote CSV fields containing commas, quotes or line breaks. Each anonymous
row records q1_response through q8_response, the binary scores, total, timing,
eligibility and exact revisions. Preserve the frozen kit/page via immutable Git
commit links, not branch names. Put the actual authorized record and a short
summary of all sessions (eligible count, qualifying count, exclusions, limitations)
in a reviewed evidence PR; do not publish identifiers or claim unperformed checks.
No cohort summary exists yet. Five qualifying records are still required; an
independent scorer decides the rubric level. Automated checks here establish only
coverage and source consistency, not usability or people evidence.
