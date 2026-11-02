# Section dates and revision notices — final comparison

The owner's [2 November 2026 decision](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/24#issuecomment-6566464188)
authorizes the product-spec fallback: explicitly say when no next release date is
announced. No future date is inferred from cadence. The independent scorer, not the
builder, determines the Context rubric level.

## Matching actual application captures

**Before:** current-main baseline `4a82258`, served directly from its committed `site/`.
**After:** integrated implementation `3322471`. Subsequent evidence-only commits have
the same HTML. Exact page SHA-256 hashes are retained in the browser reports.
Both sets use actual Chromium captures, 360×800 mobile / 1280×900 desktop,
default light theme, initial page state and reduced motion. No mockups or image edits.

| Page | Before, mobile | After, mobile |
|---|---|---|
| Spending | [Before](before-index-html-mobile.png) | [After](index.html/mobile/after-index-html-mobile.png) |
| Income | [Before](before-income-html-mobile.png) | [After](income.html/mobile/after-income-html-mobile.png) |
| History tables | [Before](before-history-html-mobile.png) | [After](history.html/mobile/after-history-html-mobile.png) |
| Cash history | [Before](before-history-cash-html-mobile.png) | [After](history-cash.html/mobile/after-history-cash-html-mobile.png) |
| Real history | [Before](before-history-real-html-mobile.png) | [After](history-real.html/mobile/after-history-real-html-mobile.png) |
| GDP-share history | [Before](before-history-gdp-html-mobile.png) | [After](history-gdp.html/mobile/after-history-gdp-html-mobile.png) |
| Party offers | [Before](before-parties-html-mobile.png) | [After](parties.html/mobile/after-parties-html-mobile.png) |

Desktop and viewport-only equivalents accompany every capture. The
[Before report](before-browser-report.json) identifies the baseline capture;
the [After suite](after-suite.json) links each page/viewport report. The After suite
must be complete and passed across all 14 page/viewport tasks, including initial and
expanded-detail states. These are automated checks, not people, keyboard-user or
screen-reader evidence.

## Verification

- Deterministic offline rebuild and independent source/CSV/JSON/HTML checks pass.
- 111 Python regressions pass, including section-local data/period/schedule notes,
  source-scoped persistent revision notices, lookup failures and updated baselines.
- Checker self-tests pass: 25 (data plus reading-grade regressions), 29 history;
  standalone reading-grade suite 16 also passes.
- Every page passes full-copy, words-only and prose grade ≤7 checks.
- [Live read-only discovery](live-discovery-report.json) on 2 November checks all
  18 registered sources, including OBR: no updates and no errors.
- Browser checks include JavaScript-disabled content/navigation, overflow, page size,
  axe WCAG 2.2 AA and the inherited supplemental SVG contrast checks.
- Source PDFs and saved transcripts retain strict hashes; fresh extraction checks
  each excerpt on the exact cited page. No private data or owner facts are invented.

The prior stopped-draft six-page comparison remains archived separately. Daily
polling has detection/deployment latency; no instantaneous upstream-revision or
people-evidence claim is made. Production verification is recorded separately after
merge; a protected preview was not bypassed.
