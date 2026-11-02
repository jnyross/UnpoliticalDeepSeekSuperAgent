# Access issue #26: automated evidence

For the separate issue #37 prerequisite, see the [versioned manual check materials](manual/README.md).
These protocols and blank records contain no performed people checks and do not award Access L4.

Runner revision: `158326d2a6960c60020ee99fedf5963d714092d8`.
No generated HTML, source data or UI changed from integrated baseline `7dcfa18`
(the concurrent income-page work in PR #28 is included).
Before/After screenshots are not applicable to this test-infrastructure-only change.

The JSON summary and compressed raw report bundles in this directory record complete
local and production runs. The raw bundles retain the suite manifest and every
page/viewport report, including all axe incomplete nodes and supplemental SVG
contrast measurements; screenshots are omitted because no UI change is made.

Reproduce (Node.js 22+, pinned npm dependencies and Playwright Chromium installed):

```sh
EVIDENCE_REVISION=$(git rev-parse HEAD) EVIDENCE_DIR=/tmp/generated npm run test:browser
LIVE_URL=https://unpoliticaldeepseeksuperagent.vercel.app EVIDENCE_REVISION=$(git rev-parse HEAD) EVIDENCE_DIR=/tmp/deployed npm run test:browser
```

Every production HTML response must have the same SHA-256 as generated output.
Checks cover all discovered pages at 360×800 and 1280×900, default and expanded
native details, plus any expandable buttons. The full axe WCAG 2.2 AA tag set is
retained, including colour contrast. Axe's SVG `imgNode` incompletes are not hidden:
strict supplementary computed-colour checks cover labels and data marks, rejecting
unsupported paint/geometry. This is automated evidence, not people evidence or a
claim of comprehensive WCAG conformance. CI uploads full per-page evidence even
when checks fail; a timeout, partial report or nonzero worker exit fails the suite.

The independent source checks and one-command build still pass. PDF validation
was also verified with actual Poppler 24.02.0 (Ubuntu) and 26.01.0. Their layout
outputs differ for five retained manifestos, but all 13 cited quotations occur on
their cited pages under both versions. Exact PDF and retained transcript SHA-256
checks remain enforced; neither provenance nor generated site bytes were rewritten.
