# Context level 4 — archived initial draft evidence

Superseded by the owner's 2 November 2026 decision accepting the explicit
no-announcement fallback. Current implementation and refreshed seven-page
comparison are in [final evidence](../context-l4-final/README.md). The limitation
notes below describe the initial stopped draft, not the final delivery status.

Actual Chromium application captures at 360×800 and 1280×900, same default light theme,
initial page state and reduced motion. Before captures use committed baseline
`462c62ace62505b8d052f4ed0496e109f7d906e0`. After captures use generated HTML from changed implementation revision
`bb595a3`; the After browser report identifies exact page SHA-256 hashes. Evidence-only
commits do not change those page bytes. Expanded states are tested automatically;
these are not people, keyboard-user or screen-reader evidence.

| Scenario | Before | After |
|---|---|---|
| Spending, mobile | [Before](before-index-html-mobile.png) | [After](after-index-html-mobile.png) |
| Historical table, mobile | [Before](before-history-html-mobile.png) | [After](after-history-html-mobile.png) |
| Cash history chart, mobile | [Before](before-history-cash-html-mobile.png) | [After](after-history-cash-html-mobile.png) |
| Real history chart, mobile | [Before](before-history-real-html-mobile.png) | [After](after-history-real-html-mobile.png) |
| GDP-share history chart, mobile | [Before](before-history-gdp-html-mobile.png) | [After](after-history-gdp-html-mobile.png) |
| Historical party offers, mobile | [Before](before-parties-html-mobile.png) | [After](after-parties-html-mobile.png) |

Focused first-section captures at the same 360×800 viewport:
[spending Before](before-index-html-section-mobile.png) /
[spending After](after-index-html-section-mobile.png), and
[cash chart Before](before-history-cash-html-section-mobile.png) /
[cash chart After](after-history-cash-html-section-mobile.png).
These capture the actual section element, not a reconstructed or edited image.

All desktop equivalents and viewport-only screenshots are retained alongside these.

## Missing prerequisite and limits

The official HMT upcoming-statistics responses retained on 1 November 2026 contain
no next scheduled date. Treasury guidance names November/February/April for spending
updates and annual PESA frequency, not an exact next date. Dates must not be invented.
The sections therefore show the product-spec fallback explicitly. The literal Context
L4 acceptance check is not claimed met; the PR remains an incomplete draft and is not
deployed to production. The Vercel preview redirects unauthenticated requests to
“Login – Vercel”, so its HTML could not be compared; no bypass was attempted.
This is not an owner-fact or people-evidence request.

Revision notices are tested with synthetic automated fixtures, not presented as real
publisher revisions. A live read-only discovery of all 17 inventory entries on
1 November 2026 returned no updates and no errors. Daily polling and deployment have a
latency window: the system cannot truthfully guarantee immediate detection at the
instant an upstream revision happens. Persistent notices prevent known revisions from
being silently erased by subsequent lookup failure or issue closure.
