# Corrections log comparison

Baseline application revision: `791d877` (main after PR #40).
Changed application revision: `eec99c1`; later test/evidence commits leave site bytes unchanged.

Both comparisons use Chromium, the default light theme and initial state, at
360×800 and 1280×900. These are actual application captures, not mockups or people tests.

## Before

The home-page captures in this directory show the baseline application without a
corrections footer link. `before-browser-report.json` identifies the baseline revision
and exact HTML hash. Full-page captures retain the footer for comparison.

The production `/corrections.html` route returned HTTP 404 before implementation was
deployed. `before-corrections-mobile.png` and `before-corrections-desktop.png` show that
actual response; `before-missing-route.json` retains the URL, status, viewport and time.
There was no existing corrections page to show. Vercel's platform error page uses its
own styling; it is not a prior application design.

## After

The per-page/per-viewport directories contain changed screenshots and automated reports.
`corrections.html/` shows the honest empty ledger, policy, JSON download and report route.
`index.html/` shows the same home-page scenario with the added footer link.
The all-page suite records expected/completed states, source hashes, no-JavaScript
parity, mobile overflow and axe results. These are automated checks, not political
reviewer, user-test, keyboard-only or screen-reader evidence.

This finite prerequisite does not award Impartiality L4; actual opposing political
reviewers and their published comments/responses remain absent.
