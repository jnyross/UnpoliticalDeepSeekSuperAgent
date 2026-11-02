# Current-main comparison: partial party costings

This supersedes the earlier seven-page comparison after integration of current main's corrections and forecast work. It contains actual application captures, not mockups or people-test evidence.

- **Before:** `f6be665` (actual current-main static output exported with `git archive`, not a simulated baseline).
- **After:** `fdd417a` (merged-main implementation preserving the corrections footer). Evidence/inventory-only commits leave application bytes unchanged.
- Same scenarios: initial historical party page, Conservative/Labour/Liberal Democrat cards, no interactive expansion on that page.
- Same settings: light theme, JavaScript disabled, Chromium, **360×800** and **1280×900**. Full-card crops preserve the viewport width and encompass each real card's content; full-page and viewport captures are also retained.

| Party | Before, 360×800 | After, 360×800 | Before, 1280×900 | After, 1280×900 |
|---|---|---|---|---|
| Conservative | [Before](<parties.html/mobile/before-party-4.png>) | [After](<parties.html/mobile/after-party-4.png>) | [Before](<parties.html/desktop/before-party-4.png>) | [After](<parties.html/desktop/after-party-4.png>) |
| Labour | [Before](<parties.html/mobile/before-party-15.png>) | [After](<parties.html/mobile/after-party-15.png>) | [Before](<parties.html/desktop/before-party-15.png>) | [After](<parties.html/desktop/after-party-15.png>) |
| Liberal Democrat | [Before](<parties.html/mobile/before-party-17.png>) | [After](<parties.html/mobile/after-party-17.png>) | [Before](<parties.html/desktop/before-party-17.png>) | [After](<parties.html/desktop/after-party-17.png>) |

Capture commands:

```sh
SITE_DIR=/tmp/coverage-l4-main-baseline/site CHECK_PAGE=parties.html \
  EVIDENCE_LABEL=before EVIDENCE_DIR=docs/evidence/issue-32-final \
  npm run test:browser -- --capture-only
EVIDENCE_LABEL=after EVIDENCE_DIR=docs/evidence/issue-32-final npm run test:browser
```

The baseline directory was populated from `git archive f6be665 site`. Card crops use Playwright `javaScriptEnabled:false`, `colorScheme:'light'`, the matching viewport, the actual baseline/changed file URL, and locator `[data-party-id="4"]` (also `15`, `17`). No baseline image was regenerated from changed output.

The browser runner discovers all **eight** current application pages at both widths and checks initial and expanded states. Its reports include content hashes, complete axe results and supplemental SVG contrast results. These are automated checks only. They are not manual keyboard, screen-reader, user-test or political-review evidence. The independent scorer decides rubric levels; this partial delivery does not claim L4 and leaves issue 32 open.
