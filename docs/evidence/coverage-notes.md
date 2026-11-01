# Coverage history visual evidence

## Before

Baseline revision: `3d2a973` (the complete SHA is in the baseline capture report).
After integrating concurrent upstream work, the actual static application from
that revision was served locally by the existing Playwright capture harness.
This baseline includes the upstream ten-year answers but has no full history page.

- [Before, mobile](coverage-before-index-html-mobile.png)
- [Before, desktop](coverage-before-index-html-desktop.png)
- [Baseline capture metadata](coverage-before-browser-report.json)

## After

The changed revision is identified by the `coverage-after-browser-report.json`
content hashes (the final commit contains these exact tested generated HTML bytes).
Use the report's `baseRevision` only as the parent code context, not the changed
HTML revision. Matching home-page screenshots show the new history navigation;
additional history-page captures show the new content (there was no history page
at baseline).

Both capture runs use Chromium, 360×800 mobile and 1280×900 desktop, default light
theme, initial state, full-page captures. They are actual application captures,
not mockups or evidence of people testing. After browser checks also expand all
native details elements and check WCAG/overflow; the screenshots show initial state.

- [After, mobile home](coverage-after-index-html-mobile.png)
- [After, desktop home](coverage-after-index-html-desktop.png)
- [After, mobile history](coverage-after-history-html-mobile.png)
- [After, desktop history](coverage-after-history-html-desktop.png)
- [Changed-page hashes and automated checks](coverage-after-browser-report.json)
