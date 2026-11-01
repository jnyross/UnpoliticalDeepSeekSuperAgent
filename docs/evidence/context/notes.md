# Context L1 visual evidence

- Before application revision: `c2ce8c0` (merged Coverage L2 foundation).
- After application revision: `6f81826` (renderer, integration and generated HTML).
- Matching scenario: history page, initial state, services-total disclosure open as shipped,
  light theme, JavaScript disabled, at 360×800 and 1280×900.
- The `before-history-viewport-*` and `after-history-viewport-*` images are actual
  Chromium viewport captures of the corresponding committed HTML, not mockups.
  Baseline HTML was extracted with `git show c2ce8c0:site/history.html`; changed
  HTML comes from the current generated site. Both use the same browser/context settings.
- New chart pages did not exist in the baseline. `after-health-gdp-*` captures show
  the same real new page at the health fragment, with its GDP view selected and table
  initially collapsed. These are supplemental after-only evidence, not substitutes
  for the matched history-page comparison.
- Full-page HTTP application captures and browser check records are also retained.
  Before/after browser reports record HTML SHA-256, viewport and revision identities.
- No people checks, manual keyboard or screen-reader tests are claimed.
