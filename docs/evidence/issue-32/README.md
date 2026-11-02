# Issue 32: partial party costings and assessments

These are real Chromium application captures, not mockups or people-test evidence.

- **Before revision:** `32595b84443fce9f6e0070e896170784f53d92aa` (research-only PR, application still unchanged from main `a2a09439bf25027b1f81ef797f4f4324df95e88b`).
- **After revision:** `942bb250c4828c4091564b5c6dcb8a483dcfc715` (partial implementation). Later evidence-only commits do not change application bytes.
- Matching settings: Chromium/Playwright, light theme, JavaScript disabled, mobile **360×800**, desktop **1280×900**. Same historical party page and party-card elements; screenshots crop the whole card, not a simulated viewport. Full-page and viewport captures are also retained.
- Scenario: initial page, no interactive expanded state exists on the party page. Parties remain in identical alphabetical order and styling. Selected proposals change only where an evidenced costing/assessment is now supplied.

## Matching mobile comparison

| Party | Before | After |
|---|---|---|
| Conservative | [Before](<parties.html/mobile/before-party-4.png>) | [After](<parties.html/mobile/after-party-4.png>) |
| Labour | [Before](<parties.html/mobile/before-party-15.png>) | [After](<parties.html/mobile/after-party-15.png>) |
| Liberal Democrat | [Before](<parties.html/mobile/before-party-17.png>) | [After](<parties.html/mobile/after-party-17.png>) |

## Matching desktop comparison

| Party | Before | After |
|---|---|---|
| Conservative | [Before](<parties.html/desktop/before-party-4.png>) | [After](<parties.html/desktop/after-party-4.png>) |
| Labour | [Before](<parties.html/desktop/before-party-15.png>) | [After](<parties.html/desktop/after-party-15.png>) |
| Liberal Democrat | [Before](<parties.html/desktop/before-party-17.png>) | [After](<parties.html/desktop/after-party-17.png>) |

## Reproduction

The existing browser runner captures the actual static application and records HTML hashes, browser versions and accessibility results:

```sh
CHECK_PAGE=parties.html EVIDENCE_LABEL=before EVIDENCE_DIR=docs/evidence/issue-32 npm run test:browser -- --capture-only
EVIDENCE_LABEL=after EVIDENCE_DIR=docs/evidence/issue-32 npm run test:browser
```

The first command was run on the Before revision. The second was run after the implementation. Card crops were captured from `site/parties.html` in Playwright, with `javaScriptEnabled:false`, `colorScheme:'light'`, matching viewport sizes above and element locator `[data-party-id="4"]` (also IDs `15` and `17`). Baseline captures have not been regenerated from changed output.

The browser checks are automated only, not manual keyboard, screen-reader, user-test or political-review evidence. Partial delivery follows the owner's follow-up decision on issue 32: **no Coverage L4 claim; issue 32 remains open**.
