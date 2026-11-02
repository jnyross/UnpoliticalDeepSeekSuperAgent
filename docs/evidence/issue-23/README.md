# Issue 23 visual comparison

Actual Chromium captures of the generated application, not mockups. All pairs use
360 × 1000 CSS pixels, the light theme, JavaScript disabled, and the same state.

- Before: `7dcfa18bba3d912505ebb658ab5caf666ad0acf8` (unchanged generated HTML
  copied before edits).
- After: the changed revision containing this directory; the PR identifies its
  commit. Screenshots are regenerated from the same rendered HTML committed there.

| Scenario | Before | After |
| --- | --- | --- |
| Spending page at `#total` | ![Before spending](index-before.png) | ![After spending](index-after.png) |
| Party page at top, no expanded state | ![Before parties](parties-before.png) | ![After parties](parties-after.png) |
| History page at top, default details state | ![Before history](history-before.png) | ![After history](history-after.png) |
| Cash chart page at top, default details state | ![Before cash](history-cash-before.png) | ![After cash](history-cash-after.png) |
| Real chart page at top, default details state | ![Before real](history-real-before.png) | ![After real](history-real-after.png) |
| GDP chart page at top, default details state | ![Before GDP](history-gdp-before.png) | ![After GDP](history-gdp-after.png) |
| Income page at `#non-tax` | ![Before income](income-before.png) | ![After income](income-after.png) |

These are automated visual captures, not people-based comprehension or accessibility evidence.
