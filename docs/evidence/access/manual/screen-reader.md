# Screen-reader protocol — version 1

This is an **unperformed protocol**, not screen-reader or participant evidence.
Accessibility L4 remains unmet. Follow the [inventory and coverage contract](README.md)
and complete the [blank record](record-template.md) or generated rows only after a
real session. Automated accessibility-tree inspection is not this protocol.

## Set up each matrix cell

Use a real screen reader with a supported browser. Record the **actual** AT name and
version, browser/version, OS/version, verbosity, browse/virtual-cursor versus focus
mode, keyboard preferences and any changed settings. Do not assert a tested pairing
in advance; one pairing's observations do not cover all screen readers.

Test **every inventory page**, at **360×800** and **1280×900** CSS-pixel viewport,
in **every listed state**: `initial`, `all-details-expanded` and any
`expanded-<target-id>` as applicable. Record zoom (start at 100%), JavaScript setting
and exact URL. Use JavaScript disabled for the core-content baseline; additional
enabled runs must be labelled separately. Follow the [state contract](README.md#coverage-contract-both-protocols):
fresh load/authored defaults for initial; AT/browser keyboard interaction to open
all native details for `all-details-expanded`; fresh load then expand the named
control for `expanded-<target-id>`, including ancestors as needed. Record unsuccessful
operations and affected tasks; an incomplete expansion is not completed coverage.

Use the AT's actual commands for headings, landmarks, links, tables and reading.
Record those commands where necessary to reproduce a finding; command names vary by
AT. Use both sequential reading and element navigation, not just the links list.
Repeat with visible focus inspection where applicable; a spoken focus announcement
alone cannot establish focus visibility. Keep each named state intact between tasks,
or reload/recreate it and note that action.

## Common tasks — per page/viewport/state

### `navigation`

1. Start at the document beginning and record the announced document title and initial
   context. Find repeated navigation and any skip link. Activate the skip link and
   check the reading cursor/focus actually reaches main content.
2. Navigate by links and through any links list. Check meaningful names, duplicate
   names in context, navigation grouping and current-page indication. Activate
   navigation/help/source/footer links and return, recording destination and focus
   or reading-position behavior. Do not mistake merely listing a link for testing it.
3. Check that the page can be entered, traversed and left without a pointer or trap,
   and that navigation remains available after expanding content at both widths.

### `structure`

1. Navigate the full heading list in order; record heading text and level. Check a
   clear main heading and useful hierarchy, including headings in expanded content.
   Record skipped/misleading levels or visually apparent headings not exposed as such.
2. Navigate landmarks/regions. Identify navigation, main and footer/content information
   where present; check names distinguish repeated regions. Check bypass of repeated
   material and that content is not stranded outside a sensible reading structure.
3. Read from start to end in reading mode. Verify order, names, abbreviations, units,
   data periods/status, caveats and source explanations make sense without visual
   layout. Hidden disclosure content must be absent when closed and available when
   expanded. Note repetition, missing content or unexpected announcements precisely.

### `focus`

1. Tab and Shift+Tab through every interactive element with the AT running; compare
   focus order with the reading order. Record names, roles and sequence, not just a
   generic “accessible” assessment. Noninteractive cells/text need not be Tab stops.
2. Inspect the visible focus indicator at every stop, including after scrolling and
   expanding controls. Check it is not lost, clipped or obscured at either viewport.
3. Switch between reading and interaction modes as needed; record unexpected mode
   changes, traps, focus in hidden content and loss of position after returning from
   links or toggling controls. Name the affected target and surrounding stops.

## Target tasks — every target, every listed task

Look up **each** target ID, label, kind and tasks in [inventory.json](inventory.json).
Repeat all listed tasks even where labels repeat or one target has several tasks.
A target hidden by a closed ancestor in initial state needs an explicit contextual
observation, then exposed-content testing in expanded state; it is not silently
removed from the matrix.

### `disclosure`

For **each** native `details`/`summary` and each `aria-expanded` control:

1. Find it through reading and keyboard focus navigation. Record the announced
   name, role and expanded/collapsed state, and compare with the visible state.
2. Activate using the AT/browser's supported keyboard interaction. Record keys,
   state-change announcements and whether the controlled content becomes readable
   in a sensible position. Do not count a changed icon as an announced state.
3. Read the revealed content and operate its links/nested controls. Close and reopen;
   check state announcements, hidden content's removal from reading/focus navigation,
   and sensible focus/cursor placement. Repeat separately for nested disclosures.
4. Restore the named starting state. Note actual utterances (exact or clearly marked
   paraphrase), label and target ID for each defect; do not invent expected speech.

### `table`

For **each table**, including every chart equivalent and disclosed table:

1. Find it with table navigation; record the announced caption/name and context.
   Check that its purpose, period, units and status are available, not only visual.
2. Use row/column/cell navigation to traverse **all rows and columns**, checking
   associated row/column headers and values. Record missing/wrong headers, flattened
   layout, ambiguous repeated labels or reading order that changes meaning.
3. Read notes, sources and links; interact with links/scrolling when needed. At the
   narrow width confirm the whole table remains accessible, not just its first cells.
4. If it is a chart equivalent, compare categories/series, dates, units, values and
   qualifications with that chart's description and visual presentation. Record its
   associated chart target ID and concrete omissions/mismatches. Do not waive the
   chart's own task because a table exists.

### `chart`

For **each SVG**:

1. Find it in sequential reading and graphic navigation where supported. Record its
   announced role, name and description (or observed exclusion if decorative).
   Determine whether the graphic conveys data or is genuinely redundant decoration;
   the mere presence of an SVG does not establish its purpose.
2. Check that chart subject, basis/units, period, series distinctions and substantive
   information are available without interpreting shape or colour. Record unhelpful
   filename-like names, excessive repeated graphics or missing explanations.
3. Locate and read the text/table equivalent using the AT, opening any containing
   disclosure with keyboard interaction. Compare all series/period coverage, units,
   values and caveats; identify the equivalent's table target ID. Missing or
   unreachable equivalent information is a finding, not a pass from an aria-label.
   Perform that table's full task separately.

### `view-link`

For **every occurrence** of a history cash/real/GDP link:

1. Find it both in context and using link navigation/list. Record its announced name,
   role, current-view indication and whether its basis/destination is distinguishable.
2. Activate using AT/keyboard. Record final URL, document title/heading, announced
   destination basis/units, and availability of the chart/table equivalent. Check
   that a URL change really corresponds to the intended view.
3. Return to the source and inspect focus/cursor restoration. Recreate the source
   state before the next target. Testing a destination here does not replace its
   full page matrix.

Give every task a real outcome and concrete observations. Preserve unperformed and
blocked rows; no default pass and no claimed screen-reader coverage without a human.
