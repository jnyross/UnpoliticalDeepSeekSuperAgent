# Issue 54, wave 8 — bounded new-source alternatives

Research date: 2 November 2026. **No new exact matching native table verified. Stop after this bounded search; no audit occurrences upgraded.** No shared code, sources, policy claims, scopes, fiscal years or generated pages changed. Publisher material remains publisher copyright. Search-result snippets were discovery aids only, never verification.

## Target and boundaries

The target was a newly verified, publisher-native RF/IFS **2024** table or workbook explicitly costing **GB two-child-limit abolition at £2.5bn in 2024-25**, or an exact SDLP-native table for the selected **£1.2bn annual-average windfall revenue** claim. Fiscal cost is not household income change, a poverty rate, a later-year cost, a full-rollout estimate, or a combined-policy cost. No conversion, rounding, fiscal-year inference or scope substitution is permitted.

Read the [wave 7 disposition](../../accuracy-w7/alternatives/README.md) first. Did not repeat Conservative archive work, Lib Dem costings/release work, TUV/Reform work, or fetch the already-known RF Catastrophic Caps report again. The new RF/IFS discovery queries below sought other publications/data; returning the already-known report in search results does not make it new evidence.

## Newly evaluated RF candidates — accessible, but no matching table established

1. **Old age tendencies**, publisher date **26 June 2024**, [publication](https://www.resolutionfoundation.org/publications/old-age-tendencies/), retained [raw HTML](rf-old-age-tendencies.html), [response metadata](rf-old-age-tendencies.html.metadata.json). HTTP 200. The actual publisher article was fetched and read, not merely its search snippet. In the retained HTML, lines 590–594 discuss **2028-29 household income impacts in 2024-25 prices**, including combined **LHA freeze, benefit-cap freeze and continuing two-child-limit rollout**; the accompanying Figure 4 is not a £2.5bn 2024-25 GB abolition costing row. No native table or workbook link was discovered on this fetched page. The linked PDF was not downloaded or inspected, so this is **not** an assertion about every page of that PDF.
2. **Growing for gold?**, publisher date **14 June 2024**, [publication](https://www.resolutionfoundation.org/publications/growing-for-gold/), retained [raw HTML](rf-growing-for-gold.html), [response metadata](rf-growing-for-gold.html.metadata.json). HTTP 200. The publisher article was fetched and read. Retained HTML lines 610–612 introduce **Figure 5: Current plans lead to rising child poverty among larger families**. That is a poverty projection, not the required fiscal cost/year table. No matching native table or workbook link was discovered on the fetched page. Its linked PDF was not inspected; no broader absence claim is made.

Neither is accepted as an alternative source for the audited cash estimate. The January RF prose estimate remains exactly as reported in wave 7, with unchanged GB exclusions and take-up uncertainty.

## New IFS candidate URLs — concrete access limitation

Direct source fetches through the fetch tool and retained HTTP requests encountered **403 challenge pages**, not readable source documents:

| Candidate | Retained response | Raw response metadata |
| --- | --- | --- |
| [Benefit changes set to take effect during the next parliament](https://ifs.org.uk/publications/benefit-changes-set-take-effect-during-next-parliament) | [HTML](ifs-benefit-changes.html) | [metadata](ifs-benefit-changes.html.metadata.json) |
| [The two-child limit: poverty, incentives and cost](https://ifs.org.uk/articles/two-child-limit-poverty-incentives-and-cost) | [HTML](ifs-two-child.html) | [metadata](ifs-two-child.html.metadata.json) |
| [Child poverty: trends and policy options](https://ifs.org.uk/publications/child-poverty-trends-and-policy-options) | [HTML](ifs-child-poverty.html) | [metadata](ifs-child-poverty.html.metadata.json) |

These are discovery candidates, **not verified 2024 publications, not verified amount/year matches and not verified table locations**. Publication date and contents could not be established from these retained challenge bodies. No PDF/workbook URL was independently verified behind them. A separate fetch-tool-only attempt at [Without reform, the two-child limit will affect 670,000 additional children by the end of the next parliament](https://ifs.org.uk/news/without-reform-two-child-limit-will-affect-670000-additional-children-end-next-parliament) likewise returned 403. No snippet text was promoted into evidence to bypass this limitation.

## Newly retrieved SDLP archival copy — prose confirmed, no native table

New successful **HTTP 200** download from the independent CAIN/Ulster archive: [2024 SDLP manifesto](https://cain.ulst.ac.uk/issues/politics/docs/sdlp/sdlp_2024-07-04_ge_man.pdf), retained [PDF](sdlp-cain-2024.pdf), [response metadata](sdlp-cain-2024.pdf.metadata.json), [layout transcript](sdlp-cain-2024.txt), and [physical/printed page 15 rendering](sdlp-page15.png). This is a **party-authored document preserved by an archive**, not a newly discovered independent costing or a fresh successful SDLP-host download.

Read the rendered original page, not a snippet: under **2. Further fiscal devolution and taxation**, the paragraph says SDLP MPs will support a new government's plan for a windfall tax on oil and gas giants with **“projected annual average income of £1.2bn”**. Transcript lines 294–298. This passage is visibly prose, with no row, column, fiscal year or averaging period. The nearby three-year Budget discussion does **not** establish the windfall averaging period. This retrieval does not solve the pre-existing missing native table. No Labour or Lib Dem costing was substituted on the strength of the phrase “new government's plan.”

## Search bounds and honest stopping point

Discovery was bounded to RF/IFS two-child-limit costing/data terms and SDLP windfall costings. Representative exact queries included:

- `site:resolutionfoundation.org 2024 "two-child" "table" "2.5"`
- `site:resolutionfoundation.org "Catastrophic" "xlsx"`
- `site:resolutionfoundation.org "two-child" "xlsx" 2024`
- `site:ifs.org.uk 2024 "two-child limit" "2.5" table`
- `site:ifs.org.uk "2024" "two-child" "2024–25"`
- `site:ifs.org.uk "2024" "two-child" "xlsx"`
- `"SDLP" "windfall" "costings" 2024`
- `"SDLP" "windfall tax" "annual average"`
- `"SDLP" "windfall" "table" 2024 manifesto`

The finite candidate checks above yielded no exact table. This is **not proof no such source exists**. The concrete limits are unreadable IFS candidate bodies, no matching tabular download discovered on the two new RF pages inspected, and an accessible SDLP original-design page that remains prose. Do not count any as a native table upgrade; retain the existing claims/scopes/years and stop bounded research.

## Reproducibility

Each retained network body has a sibling metadata JSON with requested/final URL, retrieval timestamp, HTTP status, raw response headers, byte count and SHA256. The SDLP PDF has 48 pages (PDF 1.6). Derived transcript: `pdftotext -layout INPUT.pdf OUTPUT.txt`. Derived image: `pdftoppm -f 15 -singlefile -scale-to 1600 -png INPUT.pdf OUTPUT_PREFIX`. The first download command failed because `python` was absent (exit 127); rerunning with installed `python3` succeeded. All subsequent extraction/fetch commands exited 0.
