# Keyboard protocol — version 1

This is an **unperformed protocol**, not a report. Accessibility L4 remains unmet.
Follow the [coverage and inventory contract](README.md#coverage-contract-both-protocols)
and fill the [blank record](record-template.md) or generated task rows only from
real observations. Perform this protocol without a pointing device and with AT off;
record browser, OS, versions and any keyboard-navigation preference (including macOS
full keyboard access). Do not silently change preferences to conceal a problem.

## Set up each matrix cell

Use every page in [inventory.json](inventory.json), each at **360×800** and
**1280×900** CSS-pixel viewport, in **every listed state**: `initial`,
`all-details-expanded` and any `expanded-<target-id>` as applicable. Record zoom
(start at 100%), viewport and JavaScript setting. The site's core content must work
without JavaScript; use it disabled for this baseline and record any additional
JavaScript-enabled run separately. Open the exact URL, then move into the document
using browser keyboard commands. A browser reload is allowed; DOM scripts, mouse
clicks and automation cannot stand in for the interactions below.

Establish each state as defined in the [state contract](README.md#coverage-contract-both-protocols):
reload for initial; open all native details for `all-details-expanded`; reload and
open the named control for `expanded-<target-id>`. Use Tab/Shift+Tab and supported
native keys (normally Enter/Space for `summary` or a button), including nested
controls/ancestors as required. Record anything that cannot be reached/opened and
do not silently mark expanded coverage complete. Start each task from a known
position; note the route used.

## Common tasks — repeat once per page/viewport/state

### `navigation`

1. Tab from the start of the document. Find the skip link, if supplied; activate it
   and check that focus/next Tab really reaches main content rather than merely
   changing scroll position. Record missing or ineffective bypass of repeated content.
2. Traverse all navigation links in both directions. Record their visible labels,
   order, current-page indication and whether destinations match those labels.
   Activate links with Enter, inspect the destination and return using keyboard
   browser navigation. Include footer/help/source links, not just the main menu.
3. Check that links and controls remain reachable at both widths, with no keyboard
   trap. Page navigation, returning, and scrolling must not require a pointer.

### `structure`

1. Read visible content from top to bottom using keyboard scrolling. Record the
   page title/main heading and section/subsection order. Compare the visible
   navigation, main content and footer regions with the intended reading sequence.
   Note ambiguous/missing headings, unexplained jumps, or content only available by
   hover. Semantic heading/landmark announcements are checked separately in the
   [screen-reader protocol](screen-reader.md#structure).
2. At the narrow viewport, verify that content, expanded explanations, chart labels,
   table equivalents and links are not clipped or overlapped. Distinguish an
   intentionally scrollable data table from page-wide horizontal scrolling.
3. Ensure meaningful labels, units, period/status and explanatory text are available
   without a pointer, including inside expanded content. Note actual missing content,
   not just whether the page appears generally readable.

### `focus`

1. Traverse the **entire** interactive sequence with Tab and then Shift+Tab. Record
   the order (including repeated controls), starting/ending positions and unexpected
   jumps. Noninteractive text need not be a Tab stop.
2. At every stop, verify a visible, distinguishable focus indicator. Check that focus
   is not obscured by sticky content, viewport edges, overflow or expanded panels,
   and that scrolling brings it into view without losing its logical position.
3. Operate controls, close/reopen disclosures, follow links and return. Verify focus
   remains predictable, does not disappear into hidden descendants and is not trapped.
   For any defect, identify the exact target/label and preceding/following focus stops.

## Target tasks — repeat for every listed target and task

Use each target's `id`, `label`, `kind` and **every entry in `tasks`**. Duplicate
labels are separate occurrences. Do not replace this loop with “one table checked”
or “all controls passed”. In initial state, document any target hidden by a closed
ancestor; perform its exposed-content checks in expanded state as well.

### `disclosure`

For **every** native `details`/`summary` and every `aria-expanded` control:

1. Reach the specific control with Tab; record its label, initial visible state,
   focus indicator and the content it controls. Check the whole control is usable
   without hover or a small pointer-only affordance.
2. Toggle it open and closed with the supported keyboard activation. For native
   `summary`, check Enter and Space. For other controls, use keys appropriate to
   the exposed role; record keys and actual behavior, not assumptions from markup.
3. Check that revealed content is readable/reachable, hidden descendants are not
   Tab stops when closed, the control stays reachable, and focus is sensible after
   closing (including when focus had been inside). Check nested controls separately.
4. Restore the matrix cell's starting state. Record a separate finding for each
   broken target. AT state/name announcements belong to the screen-reader task.

### `table`

For **every table**, including chart equivalents and tables inside disclosures:

1. Read its visible title/caption, column and row headings, units, dates, data status
   and notes. Check the relationships remain understandable at this viewport.
2. Reach all table links/controls using Tab. Do not expect noninteractive cells to
   be focusable. If the table overflows, use keyboard scrolling to reach its full
   width and all rows; record the required method and whether context is retained.
3. Check that no values/headers are cut off or accessible only by mouse hover.
   For an equivalent to a chart, compare labels, categories/series, periods, units,
   values and caveats with the chart. Record concrete mismatches or missing rows.

### `chart`

For **every SVG**, not just one chart per page:

1. Identify what the graphic conveys, its visible title/description, series/key,
   units, period, source and status/caveats. If an SVG is decorative, document its
   actual purpose rather than inventing a data equivalent.
2. Find the linked/adjacent text or table equivalent using only the keyboard,
   opening disclosures as necessary. Check that it conveys the same substantive
   information without interpreting shapes or colour alone. Identify the equivalent
   table's target ID where present; absence is a finding, not an automatic exemption.
3. Compare the displayed chart and equivalent across series and dates, including
   first/last points and exceptions. Record specific differences or clipping and
   whether relevant explanatory text is reachable. Run the equivalent table's own
   `table` task as well; this comparison does not replace it.

### `view-link`

For **every occurrence** of a link to a cash, real or GDP history view:

1. Tab to it and record its exact visible label, source context and focus visibility.
   Check the label/context distinguishes the destination and basis (cash, real or
   GDP share), including any current-view indication.
2. Activate with Enter. Record final URL and whether the intended view loads with
   the correct heading, basis/units, chart and equivalent table. Note errors or
   confusing unchanged content. Do not infer success solely from the href.
3. Return using the keyboard, inspect restored focus/location, and restore the source
   state before checking the next occurrence. Destination pages still require their
   own complete inventory matrix.

Record expected/observed behavior and outcome **per task**, not a prefilled pass.
Unperformed rows stay unperformed; a blocked task retains the concrete blocker.
