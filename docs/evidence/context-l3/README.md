# Context L3: chart-local accounting scope

## Decision and source audit

The retained PESA 2026 workbook qualifies TME as excluding temporary effects of
banks being classified to the public sector. Keep that meaning: this is not a
claim that all bank-related spending is excluded. Use the site's existing neutral
warning paragraph above each TME chart, and repeat it in the adjacent data-table
caption so it survives reading the table alone. No data, axes, status or colours
change. The annual and fixed-decade tables receive the same qualification.

Audit of series-local definition notes in the retained workbook:

| Definition or break | Cash note | Real/GDP note | Affected chart sections |
| --- | --- | --- | --- |
| COFOG defence differs from NATO; pensions in social protection | 4_2!A28 | 4_3!A29 / 4_4!A29 | defence |
| Network Rail enters functional services from 2015-16, but TME includes it throughout | 4_2!A31 | 4_3!A32 / 4_4!A32 | transport, economic-affairs, services-total |
| TfL subsidiary scope from 2011-12 | 4_2!A32 | 4_3!A33 / 4_4!A33 | transport, economic-affairs, services-total |
| Student-loan scope from 2011-12 | 4_2!A33 | 4_3!A34 / 4_4!A34 | education |
| VAT treatment from 2010-11 | 4_2!A34 | 4_3!A35 / 4_4!A35 | eu-transactions |
| TME bank-classification exclusion | 4_2!A35 | 4_3!A36 / 4_4!A36 | tme (added) |

Table 4.1 note B53 supplies the same exclusion for the fixed-decade TME table.
The enterprise note (4_2!A30, 4_3!A31, 4_4!A31) describes events affecting amounts
(financial interventions, Covid and living costs), not a changed definition or
series break. It remains retained in the source notes. Price-base and GDP-vintage
notes already appear in each view and local section metadata. Tests now assert
all the definition warnings above *inside each affected chart section*, before
its figure, across all three views. They separately assert the TME table captions
and source-note cells against the actual hash-checked workbook. Page-wide notes
alone cannot satisfy these assertions.

## Reproducible visual comparison

Before: `456ff75943f51a3f8b2e8ccc1e16e8b9850b2c3c` (unmodified baseline site).
After: `addee2b0fea4d2a4cb0b39aa76573db6bdd35a5c`. Both are real Chromium application captures,
not mockups. Same light theme, JavaScript disabled, TME anchor, data table open,
viewport height 1600, width 360 or 1280. The capture script scrolls the TME section
to the viewport top after opening the table. There are no client-side scripts.

Run with the desired revision's generated site present:

```sh
node docs/evidence/context-l3/capture.mjs before
node docs/evidence/context-l3/capture.mjs after
```

| View / width | Before | After |
| --- | --- | --- |
| Cash / 360 | [Before](before/cash-360.png) | [After](after/cash-360.png) |
| Real / 360 | [Before](before/real-360.png) | [After](after/real-360.png) |
| GDP share / 360 | [Before](before/gdp-360.png) | [After](after/gdp-360.png) |
| Cash / 1280 | [Before](before/cash-1280.png) | [After](after/cash-1280.png) |
| Real / 1280 | [Before](before/real-1280.png) | [After](after/real-1280.png) |
| GDP share / 1280 | [Before](before/gdp-1280.png) | [After](after/gdp-1280.png) |

These are automated browser captures, not manual accessibility or people evidence.
