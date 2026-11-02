# Manual accessibility evidence kit — version 1 (issue #37)

**Status: preparation only; no manual checks or user tests are reported here.**
Accessibility L4 remains **unmet**. These protocols, the inventory and generated
unperformed rows are useful prerequisites, not people evidence, a WCAG conformance
claim, or an award of any rubric level. Real people must perform and record the
checks; do not simulate them or infer a manual pass from automation.

Use the [keyboard protocol](keyboard.md), [screen-reader protocol](screen-reader.md)
and [blank human record](record-template.md). Existing
[automated evidence and reproduction commands](../README.md) remain separate.
The [repository instructions](../../../../AGENTS.md) prohibit invented people evidence;
the [rubric](../../../rubric.md) defines the gated level. Completing this kit alone
does not satisfy that level's real-people requirement.

## Prepare a revision-bound inventory

Run these commands from the repository root using the repository's configured
Python environment (`python3` below). Build/check prerequisites and pinned browser
setup are in the [root README](../../../../README.md#reproduce-and-check-without-network-access).
Do not refresh official sources just to prepare a manual session.

```sh
python3 scripts/manual_access.py
# Only when intentionally creating/updating the reviewed inventory:
python3 scripts/manual_access.py --write
python3 scripts/manual_access.py
python3 scripts/manual_access.py --records /tmp/manual-records.json
```

The default command validates retained [inventory.json](inventory.json) against
every generated HTML page, not a selected sample; run it before testing and after
any rebuild. Investigate drift rather than automatically overwriting it. Use
`--write` only for initial creation or after reviewing changed pages/controls and
updating protocols as needed, then validate again. When task semantics change,
bump `VERSION` in the generator and document the protocol-version change here;
regenerating an inventory is never manual evidence. The `--records` command produces
a blank record set: **every per-task row is unperformed and its environment is blank**. It does not
run a browser, supply a tester, or perform a check. Preserve a separate copy for each
real session; do not overwrite completed notes with a newly generated blank set.

Inventory page objects contain `path`, `sha256`, `states` and `targets` arrays.
Each target has `id`, `label`, `kind` and a `tasks` list. IDs identify concrete DOM
occurrences (for example `details:1` or `table:2`), not whole classes of controls.
They are revision-bound locators, not necessarily HTML `id` attributes or permanent
identifiers. Ordinals count inventoried elements of the same tag, not every element
of that tag: `a:1` is the first inventoried view link, not necessarily the first
link in the document or a CSS `nth-of-type(1)` match. Use optional `anchor`/`href`
fields when provided. Keep the page path and SHA-256 with each observation. If a
label repeats, use its occurrence and surrounding heading to identify the target.

The inventory includes **every** native `details`, control with `aria-expanded`,
`table`, `svg`, and link whose href points to a `history-(cash|real|gdp).html` view.
Do not reduce repeated controls to one representative example. If the browser exposes
another relevant control or the inventory appears incomplete, record the discrepancy
and correct/revalidate the inventory before claiming complete coverage.

## Coverage contract (both protocols)

Repeat independently for **every inventory page × each viewport (360×800 and
1280×900 CSS pixels) × every state in that page's `states` array**. Record actual
viewport dimensions, not just the device name or outer window size. Literal states:

- `initial`: fresh load preserving authored defaults.
- `all-details-expanded`: open every native disclosure, including nested ones, using
  the protocol's keyboard or AT interaction. Leave other controls at initial defaults.
- `expanded-<target-id>`: from a fresh load, expand that specific `aria-expanded`
  control (and any ancestor needed to reach it); record the resulting control state.

Never use script/DOM edits to establish manual states. Every page gets initial
coverage at both widths; applicable expanded states are additionally required at
both widths. A page with no expandable controls has only initial inventory rows,
not a fabricated expanded interaction. Every expandable target must still be
opened and closed during its own task. If a control cannot be expanded, record the
failure/blocker, observed partial state and affected rows; do not call that a
completed expanded state.

For each page/viewport/state/protocol combination:

1. Perform each common task: `navigation`, `structure`, `focus`.
2. For **each target**, perform **every task ID in that target's `tasks` list**:
   `disclosure`, `table`, `chart`, and/or `view-link`, as applicable. One target can
   require multiple tasks. A single page-level statement is not per-target evidence.
3. Give each task its own outcome and concrete notes, preserving the page path/hash,
   viewport, state, protocol, task ID and target ID (common tasks use target `page`).
   Use the generated blank rows as the checklist; the human template is an alternative
   writing format, not permission to omit rows.

Initial-state checks include whether hidden content is correctly unavailable.
A target inside a closed disclosure is not silently skipped: identify its closed
ancestor and observed unavailability, then test that target when exposed in expanded
state. If it is still unreachable there, record a failure or blocker rather than a
pass. For a disclosure target, operate it in both directions during its task, then
restore the named starting state. For a view link, return to the source URL and
restore its state before moving to the next target. Reload before the next matrix
cell so prior interaction cannot contaminate initial-state evidence.

## Reuse existing automation, without relabelling it

These are the existing complete browser commands, with separate evidence folders:

```sh
EVIDENCE_REVISION=$(git rev-parse HEAD) EVIDENCE_DIR=/tmp/generated npm run test:browser
LIVE_URL=https://unpoliticaldeepseeksuperagent.vercel.app EVIDENCE_REVISION=$(git rev-parse HEAD) EVIDENCE_DIR=/tmp/deployed npm run test:browser
```

The deployed run compares every HTML response's SHA-256 with generated output.
Retain its actual results separately; the commands above are instructions, not a
claim that they were run for this kit. Never substitute axe, screenshots, SVG
contrast calculations or an automation pass for the manual task rows.

For a local human session, the existing static-server command is:

```sh
python3 -m http.server 8000 --directory site
```

Use the actual server URL plus each inventory page path (for example the local
base is `http://localhost:8000/`). Record whether testing local or deployed bytes.
A local session is not proof of deployed behavior. For deployed evidence, first
verify byte equality with the live browser command above and retain that evidence;
record any redirect and the final tested URL. Do not assign a local hash to an
unverified deployment.

## Record and review evidence honestly

A real tester fills the [record template](record-template.md) or generated rows
**after each actual task**, with tested revision, page hash, exact URL, date/time
and timezone, browser/version, OS/version, AT/version (or explicitly none for a
keyboard-only run), viewport, settings, outcome and concrete findings. Leave unknown
fields blank and explain the gap; never populate them with guessed environments.
Record expected versus observed behavior, control names, focus/reading sequence,
announcements where relevant, reproducible steps and any evidence/issue link.

`unperformed` means no completed check, not a pass. Record failures and blockers
without erasing them; link a separate dated/revision-bound retest. If a format uses
not-applicable, give the specific reason (for example hidden by a named closed
ancestor in initial state), never use it to evade an existing target. A crash,
missing AT, unreachable page or inability to establish the requested viewport is a
blocker, not a success. Keep partial coverage visible. Only report coverage complete
when all required rows for both protocols are resolved with real observations and
any exceptions explicitly accounted for; this still does not itself award L4.

No tester, environment, result, participant count, finding or successful session is
asserted by these documents or by blank generated records.
