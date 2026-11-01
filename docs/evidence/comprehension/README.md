# Issue 13 visual comparison

Actual static application captures, Chromium, default light appearance, initial page
state, reduced motion, matching 360×800 mobile and 1280×900 desktop viewports.
Full-page height changes because the page adds two answers; these are not mockups.

- Before revision: `e640d8ea5d966b0cdd54580b7f9e8140fed18810`.
- After content revision: `1565ed1` (later evidence/checker-only commits do not change HTML).
- Exact HTML SHA-256, browser version and viewport records are retained in the reports.
- Before: [desktop](before-index-html-desktop.png), [mobile](before-index-html-mobile.png), [report](before-browser-report.json).
- After: [desktop](after-index-html-desktop.png), [mobile](after-index-html-mobile.png), [report](after-browser-report.json).
- Additional [mobile comparison-section capture](after-comparison-mobile.png): actual page
  section at 360px viewport, JavaScript disabled. Useful for inspecting the new table
  without opening the long full-page image. The full-page pairs above are the comparison.

Capture/check command:

```sh
EVIDENCE_DIR=docs/evidence/comprehension EVIDENCE_LABEL=after EVIDENCE_REVISION=$(git rev-parse HEAD) node tests/browser.mjs
```

After report passes the no-JavaScript content, size, overflow and automated WCAG 2.2 AA
checks. These automated checks and agent visual inspection are not people testing,
manual keyboard checks or screen-reader evidence.
