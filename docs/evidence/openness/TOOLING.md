# Issue 34 evidence tooling

Run commands from the repository root. These capture/check generated output; they do not modify production source or generated pages.

```sh
npm ci
# Required only when Chromium is not already installed:
# npx playwright install chromium
node docs/evidence/openness/capture-footer.mjs before f6be6658f64f7f14b5a4b93aa0fdea761a273b95
node docs/evidence/openness/capture-footer.mjs after
node docs/evidence/openness/check-no-js.mjs
node docs/evidence/openness/check-github-anonymous.mjs
gh api repos/jnyross/UnpoliticalDeepSeekSuperAgent --jq '{html_url,private,visibility,has_issues}'
EVIDENCE_DIR=/tmp/openness-browser-merged npm run test:browser
node docs/evidence/openness/summarize-browser.mjs /tmp/openness-browser-merged 86bb51b462f8da2dcb24d7e291d9de181ea13978
# After deployment: fail if any public HTML differs from this checkout.
python3 docs/evidence/openness/check-deployed.py https://unpoliticaldeepseeksuperagent.vercel.app
```

Tool versions used: Node v22.23.2; npm 10.9.8; Playwright 1.56.1; Chromium 141.0.7390.37; gh 2.103.3. `npm ci` installed five packages, audited six, and reported zero vulnerabilities.

The refreshed upstream baseline was captured from immutable `git show f6be6658f64f7f14b5a4b93aa0fdea761a273b95:site/index.html` bytes, SHA-256 `af6c7e48c3472b36b7190091f32489f4c95cc317be4cb6ffdb74d368bc891cfa`. This avoids a race with parallel generation. Footer captures use JavaScript-disabled contexts, a local static HTTP server, `footer.scrollIntoViewIfNeeded()`, and viewport—not full-page—screenshots at 360×800 and 1280×900. HTML is self-contained. The JSON capture reports identify the exact tested HTML by SHA-256; working-tree after evidence is not falsely attributed to the baseline commit.

The anonymous GitHub verification is explicitly permitted read-only Playwright navigation with empty initial cookies/storage and no supplied credentials. It records navigation response status, redirects, final URL, title, and visible body text, and does not submit an issue. The separate `gh api` metadata query uses the configured CLI session; it establishes public visibility and enabled issues but is **not** claimed as anonymous-browser evidence.

Observed anonymously: `/issues/new` returns HTTP 302 to GitHub login with the original URL as `return_to`, followed by HTTP 200 on the sign-in page. `/issues` returns HTTP 200 with publicly visible real reports, including issue 34. Submitting a report needs a GitHub account; reading the list does not.

These are automated browser checks and agent screenshot inspections, not evidence from real-user tests or human accessibility review.
