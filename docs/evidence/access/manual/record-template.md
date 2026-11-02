# Human manual-check record — version 1 (blank template)

**This is a blank format and instructions, not results.** No tester, environment,
manual session, pass or finding is asserted. Accessibility L4 remains unmet.
Use with the [coverage contract](README.md#coverage-contract-both-protocols),
[keyboard protocol](keyboard.md) and [screen-reader protocol](screen-reader.md).

## Instructions (not observations)

1. Validate [inventory.json](inventory.json) from the repository root with
   `python3 scripts/manual_access.py`. Generate blank task rows with
   `python3 scripts/manual_access.py --records /tmp/manual-records.json` if using the
   machine-readable checklist. Those rows are all `unperformed` and the environment
   is blank; generation is not execution of any manual task.
2. Copy this template for each actual session. Fill environment fields with observed
   facts, not intended setups. Record a stable tester reference without publishing
   personal information unnecessarily. Unknown fields stay blank with an explanation.
   For keyboard-only testing, explicitly record AT as none only when that is true.
3. Repeat the task block below for **every page × both viewports × every listed
   state (`initial`, `all-details-expanded`, `expanded-<target-id>` as applicable)
   × both protocols × each required common/target task**. Use each target's
   inventory ID and every entry in its `tasks` list. Common tasks are `navigation`,
   `structure`, `focus`; target tasks are `disclosure`, `table`, `chart`, `view-link`.
   A page-level summary never replaces individual task evidence.
4. Use outcomes `unperformed`, `pass`, `fail`, `blocked` or `not-applicable`.
   Fill outcomes/findings only from actual work. Keep unfinished tasks unperformed,
   report concrete blockers and preserve failures. A not-applicable outcome requires
   an exact reason and the exposed-state counterpart where relevant; it is not a
   way to skip an existing target.
5. Use the tested revision/hash, not a later HEAD. Record exact source and final URLs,
   date/time with timezone, any settings overrides and evidence locations. Automated
   byte-identity evidence establishes deployment identity, not manual task success.
6. Preserve original records. Add a dated, revision-bound retest rather than erasing a
   failed observation. Keep real people evidence separate from automated reports.

For machine records the generated environment fields include `tested_revision`,
`base_url`, `date_time_timezone`, `tester_reference`, `browser_version`, `os_version`,
`assistive_technology_version`, `keyboard_settings`, `zoom`, `theme`, `javascript`,
and `deployment_identity_evidence`. Each test row retains `page`, `html_sha256`,
`viewport`, `mode`, `state`, `target`, `task`, `outcome`, `observations` and
`finding_ids`. Preserve the generated identities. Put exact tested URL, actual
steps/keys, announcements and expected-versus-observed behavior in observations or
linked human notes; use finding IDs to join defect details. Leave environment and
observations blank until a real person supplies them.

## Session environment (blank)

- Protocol version:
- Tester reference:
- Tested full revision:
- Inventory version/location and validation command/result:
- Local or deployed:
- Base URL:
- Deployment byte-identity evidence (actual run/report URL or path):
- Date/time and timezone (start/end):
- Browser name and exact version:
- OS and exact version:
- AT name and exact version (or explicitly none for actual keyboard-only testing):
- AT reading/focus mode, verbosity and relevant settings:
- Keyboard-navigation preferences/settings:
- Zoom:
- Theme/high-contrast/other display settings:
- JavaScript setting:
- Unknown fields, setup limitations or deviations:

## Task observation (blank — duplicate for every required row)

- Protocol/mode (keyboard or screen-reader):
- Page path:
- Generated HTML SHA-256:
- Exact requested URL:
- Exact final URL (including redirect, query or fragment if present):
- Observation date/time and timezone (if different from session):
- Viewport in CSS pixels (360×800 or 1280×900):
- State (exact inventory state name):
- How this state was established; closed ancestor if relevant:
- Target ID (`page` for a common task):
- Target label, kind and surrounding heading/location:
- Task ID:
- Starting focus/reading position:
- Actual actions and keys, in order:
- Expected behavior (from protocol):
- Observed behavior (names, roles, states, focus/reading order and exact content):
- Actual AT announcements (exact or explicitly labelled paraphrase):
- Focus visibility/obscuring/scrolling observations:
- Chart/equivalent-table target IDs and information compared (if relevant):
- Link source, destination and return behavior (if relevant):
- Outcome:
- Concrete blocker or reason for not-applicable (if relevant):
- Finding IDs:
- Supporting evidence links/paths (only if actually captured):
- State/focus restoration and any task deviations:

## Finding detail (blank — repeat as needed)

- Finding ID:
- Short description:
- Affected revision, page hash and exact URL:
- Affected protocol, viewport, state, task and target ID:
- Environment/session reference:
- Minimal reproducible steps and keys:
- Expected behavior:
- Actual behavior and user impact:
- Supporting evidence (only actual captures/notes):
- Issue/fix reference (only if one exists):
- Retest date/time, revision, environment and task reference:
- Retest observation/outcome (leave blank until performed):

## Coverage summary (blank — not a pass declaration)

- Session record/checklist location:
- Required versus performed task counts, by protocol/viewport/state:
- Unperformed rows:
- Blocked rows and precise reasons:
- Failures/finding IDs:
- Explicit exceptions with reasons:
- Remaining real-person checks and retests:
- Limits on what this session establishes:

Do not treat a completed checklist as an automatic award of Accessibility L4 or a
claim of comprehensive WCAG conformance. The independent rubric assessment and its
real-people requirements remain separate.
