# Issue 34: public error reporting and disclosures evidence

## Capture identity

- Refreshed upstream baseline commit: `f6be6658f64f7f14b5a4b93aa0fdea761a273b95` (after the independently merged corrections work).
- Baseline overview HTML SHA-256: `af6c7e48c3472b36b7190091f32489f4c95cc317be4cb6ffdb74d368bc891cfa` (git blob `e60221f853637945f7ea38e9c1891791cff8195b`). Captured from immutable git bytes, not reconstructed HTML.
- After overview HTML SHA-256: `a793f9db346c922c65435e95c7e2353d38687e42a5ef80f51302409cdba3f8df`.
- After About HTML SHA-256: `e99b3253340aaffb8e02393c9de36f1f6a688160875d36c720637c09ec5d2076`.
- Changed source revision, committed by the parent agent during verification: `86bb51b462f8da2dcb24d7e291d9de181ea13978`.
- After evidence identifies working-tree bytes; the baseline commit is not claimed to contain the new implementation.

## Actual screenshots

All footer screenshots use JavaScript disabled and the footer scrolled into view. The PNGs retain the exact viewport dimensions.

| Viewport | Before | After |
| --- | --- | --- |
| 360×800 | [Mobile before](<before-mobile.png>) | [Mobile after](<after-mobile.png>) |
| 1280×900 | [Desktop before](<before-desktop.png>) | [Desktop after](<after-desktop.png>) |

[Baseline capture metadata](<before-baseline.json>) and [after capture metadata](<after-baseline.json>) record timestamps, browser version, exact HTML hashes, viewport sizes, and visible footer text. [About mobile full-page capture](<about-mobile.png>) uses a 360×800 viewport with JavaScript disabled.

Agent visual inspection of both refreshed matching pairs found the upstream Corrections/report link and licence attribution retained, with clearly visible About/methods and direct GitHub error-report links plus a sign-in notice added. The mobile footer wraps within the viewport. The refreshed About full-page capture is exactly 360px wide and includes the retained Corrections link. An initial pre-merge About capture had exposed an 8px overflow from the repository slug; the generator was corrected with a targeted link-wrapping rule before recapture. This is an agent visual inspection, not human/user-test evidence.

[No-JavaScript navigation report](<no-js-navigation.json>) checks all nine pages: correct footer About and report hrefs, followed by a real click to the About page with JavaScript disabled. It also asserts the retained Corrections href on the eight non-Corrections pages (the Corrections page has no redundant self-link, matching upstream).

## Anonymous GitHub access

[Anonymous browser report](<github-anonymous.json>) records a fresh Playwright context with no initial cookies or supplied credentials:

- `https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/new`: HTTP **302** to GitHub login, with the original URL retained in `return_to`; login returns HTTP **200** and displays “Sign in to GitHub”. [Login screenshot](<github-issues-new.png>).
- `https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues`: HTTP **200**, no login redirect, real public issue listing including issue 34. [Public listing screenshot](<github-issues.png>).
- Therefore reading reports is public; submitting a report needs a GitHub account/sign-in. No report was submitted during verification.

[Repository metadata](<github-repository.json>) was retrieved with `gh api repos/jnyross/UnpoliticalDeepSeekSuperAgent`, confirming `private: false`, `visibility: public`, and `has_issues: true`. This CLI check uses configured authentication and is not claimed as the anonymous check. Read-only browser navigation was explicitly permitted for anonymous verification; no curl or non-gh GitHub API operations were used.

## Tooling and automated checks

See [commands and methodology](<TOOLING.md>), [footer capture script](<capture-footer.mjs>), [no-JavaScript navigation script](<check-no-js.mjs>), and [anonymous verification script](<check-github-anonymous.mjs>). No production changes or commits were made by the evidence-capture agent.

`npm ci`: exit 0; five packages installed, six audited, zero vulnerabilities. Playwright 1.56.1 / Chromium 141.0.7390.37.

`EVIDENCE_DIR=/tmp/openness-browser-merged npm run test:browser`: **exit 0**, completed **18/18 page/viewport checks** (nine HTML pages, including Corrections, × 360×800 and 1280×900), with **26/26 state checks** passed. Final post-merge run: `2026-11-02T02:11:59.705Z`–`2026-11-02T02:17:15.515Z`. All checked axe violations arrays are empty; SVG contrast checks completed; no-JavaScript main content matched and document/body widths fit the viewport. Expanded disclosure states were checked on the history pages. Every tested HTML SHA-256 was independently verified against source revision `86bb51b462f8da2dcb24d7e291d9de181ea13978`.

The committed [compact browser summary](<browser-summary.json>) preserves per-page SHA-256 hashes, byte counts, viewport dimensions, no-JavaScript checks, state completion, axe results, and contrast completion. The [summary verification script](<summarize-browser.mjs>) checks suite completion and every tested HTML hash against the named source commit before writing the compact result. Full temporary runner output and screenshots remain under `/tmp/openness-browser-merged` and are intentionally not duplicated here. Earlier pre-merge eight-page evidence has been superseded by this complete nine-page run and refreshed before/after screenshots; the anonymous GitHub evidence was retained without a redundant rerun.
