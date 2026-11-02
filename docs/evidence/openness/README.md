# Issue 34: public error reporting and disclosures evidence

## Capture identity

- Baseline commit: `791d8772fa5dcb12524d699f7fea4bc691c30a67`.
- Baseline overview HTML SHA-256: `516c6dabb9b22edbfb023df55052673aa620f7a19e727d587c057fe59d484a4e` (git blob `eb737cf8cf45af9bb7ad365442a7319928042936`). Captured from immutable git bytes, not reconstructed HTML.
- After overview HTML SHA-256: `3f8505a495771c5d9fba4b822edeecbefc6253a1b684982e03dd8651556c043f`.
- Corrected after About HTML SHA-256: `53f6f0b9411479aa0441a93800bdc16d1986a8f2d9de99e3d2c9847b918e5b3f`.
- After evidence identifies working-tree bytes; the baseline commit is not claimed to contain the new implementation.

## Actual screenshots

All footer screenshots use JavaScript disabled and the footer scrolled into view. The PNGs retain the exact viewport dimensions.

| Viewport | Before | After |
| --- | --- | --- |
| 360×800 | [Mobile before](<before-mobile.png>) | [Mobile after](<after-mobile.png>) |
| 1280×900 | [Desktop before](<before-desktop.png>) | [Desktop after](<after-desktop.png>) |

[Baseline capture metadata](<before-baseline.json>) and [after capture metadata](<after-baseline.json>) record timestamps, browser version, exact HTML hashes, viewport sizes, and visible footer text. [About mobile full-page capture](<about-mobile.png>) uses a 360×800 viewport with JavaScript disabled.

Agent visual inspection of both matching pairs found the original licence-only footer replaced by clearly visible About/methods and error-report links, a sign-in notice, and retained attribution. The new mobile footer wraps within the viewport. Initial About capture exposed an 8px horizontal overflow from the repository slug; the generator was corrected with a targeted link-wrapping rule before final recapture. This is an agent visual inspection, not human/user-test evidence.

[No-JavaScript navigation report](<no-js-navigation.json>) checks all eight pages: correct footer About and report hrefs, followed by a real click to the About page with JavaScript disabled.

## Anonymous GitHub access

[Anonymous browser report](<github-anonymous.json>) records a fresh Playwright context with no initial cookies or supplied credentials:

- `https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/new`: HTTP **302** to GitHub login, with the original URL retained in `return_to`; login returns HTTP **200** and displays “Sign in to GitHub”. [Login screenshot](<github-issues-new.png>).
- `https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues`: HTTP **200**, no login redirect, real public issue listing including issue 34. [Public listing screenshot](<github-issues.png>).
- Therefore reading reports is public; submitting a report needs a GitHub account/sign-in. No report was submitted during verification.

[Repository metadata](<github-repository.json>) was retrieved with `gh api repos/jnyross/UnpoliticalDeepSeekSuperAgent`, confirming `private: false`, `visibility: public`, and `has_issues: true`. This CLI check uses configured authentication and is not claimed as the anonymous check. Read-only browser navigation was explicitly permitted for anonymous verification; no curl or non-gh GitHub API operations were used.

## Tooling and automated checks

See [commands and methodology](<TOOLING.md>), [footer capture script](<capture-footer.mjs>), [no-JavaScript navigation script](<check-no-js.mjs>), and [anonymous verification script](<check-github-anonymous.mjs>). No production changes or commits were made by the evidence-capture agent.

`npm ci`: exit 0; five packages installed, six audited, zero vulnerabilities. Playwright 1.56.1 / Chromium 141.0.7390.37.

Full browser-suite results are collected separately under `/tmp/openness-browser`; the final summary is recorded below after the run completes.
