# Issue #54: native locators for selected party cash claims

Research date: 2 November 2026. This is source research, not a change to offers, scopes, baselines or policy years. Read [party offers](../sources/party-offers.json) and [party source index](../sources/party-source-index.json), retained extracts and relevant original PDFs. A PDF page is the one-based physical page, not necessarily its printed folio. A paragraph, section heading or repository-created evidence table is **not a native table/row locator**.

## Verified native tables in retained sources

| Claim | Exact native locator | Units and period | Retained evidence |
|---|---|---|---|
| Labour £7,350m revenue | Physical/printed page 127, **Public Services** table; **REVENUE (2028-29)** block; row **Total**, value **7,350** | £M; annual 2028-29, not a Parliament total | [Extract:5079–5135](../sources/manifesto-2024-labour.txt#L5079-L5135); [PDF page 127](../sources/manifesto-2024-labour.pdf#page=127) |
| Labour £4,835m public-service spending | Same table/page; **POLICIES FUNDED (2028-29)** block; row **Total including Barnett consequentials**, value **4,835** | £M; annual 2028-29. Includes Barnett; not total manifesto spending | [Extract:5133–5141](../sources/manifesto-2024-labour.txt#L5133-L5141); [PDF page 127](../sources/manifesto-2024-labour.pdf#page=127) |
| Reform £50bn annual savings | **Physical PDF page 25, printed page 23**; **FUNDING OF REFORM UK PLANS**, **SAVINGS PLEDGES** table; row **Slash wasteful Government spending**, continuation **Save £5 in 100 incl govt depts. quangos, commissions**; value **£50** | Column: **Annualised Savings Over 5 Year Electoral Term Amount in £ billions**. Annualised over a five-year electoral term; **no named fiscal year**. Do not multiply by five or label 2028-29 | [Extract:1459–1492](../sources/manifesto-2024-reform.txt#L1459-L1492); [PDF page 25](../sources/manifesto-2024-reform.pdf#page=25) |

Labour's immediately preceding explanation explicitly chooses 2028-29 as the highest annual policy cost: [extract:5057–5068](../sources/manifesto-2024-labour.txt#L5057-L5068). Original Labour [archive PDF](https://www.manifestos.org.uk/manifestos/2024/labour/manifesto.pdf#page=127).

Reform's original selection remains department savings, not the whole fiscal plan: [prose:270–276](../sources/manifesto-2024-reform.txt#L270-L276) says departments must improve efficiency/procurement without touching frontline services. The native row additionally names quangos/commissions; report that wording rather than silently broadening the selected scope. The £150bn/£160bn totals on the same table page are **not substitutes** for this £50bn row. [Publisher PDF](https://assets.nationbuilder.com/reformuk/pages/253/attachments/original/1718625371/Reform_UK_Our_Contract_with_You.pdf?1718625371#page=25).

## Prose-only retained claims: real locator, but no native table

| Claim/source | Verified locator | Honest disposition |
|---|---|---|
| Conservative £12bn annual working-age welfare savings | Physical PDF page 24; paragraph containing “will save taxpayers £12 billion a year”; [retained extract](../sources/manifesto-2024-conservative.txt#L1401), [publisher PDF](https://public.conservatives.com/static/documents/GE2024/Conservative-Manifesto-GE2024.pdf#page=24) | Prose claim; selected passage states no fiscal year. The retained PDF's physical page 80 is an imprint, **not a welfare costings table**. |
| Lib Dem £1.4bn annual buyback-tax revenue | Release **Why could this raise £1.4 billion?**, [extract:58–59](../sources/libdem-buyback-2024.txt#L58-L59), [publisher release](https://www.libdems.org.uk/news/article/share-buyback-tax-scheme) | Prose. £2.2bn before behavioural adjustment versus £1.4bn after; no named fiscal year. Manifesto policy is at [extract:384](../sources/manifesto-2024-libdem.txt#L384), not a cash-costing table. |
| SDLP £1.2bn annual average windfall-tax income | Physical PDF page 15, section **2. Further fiscal devolution and taxation**, [extract:252–256](../sources/manifesto-2024-sdlp.txt#L252-L256), [archive PDF](https://www.manifestos.org.uk/manifestos/2024/sdlp/manifesto.pdf#page=15) | Prose. No averaging years or detailed tax design supplied here. Do not substitute Labour's different windfall-tax row. |
| UUP £35m minimum annual Skills Fund | Physical PDF page 9, printed page 6, paragraph **We also pledge to invest in skills development**; [extract:322–334](../sources/manifesto-2024-uup.txt#L322-L334), [archive PDF](https://www.manifestos.org.uk/manifestos/2024/uup/manifesto.pdf#page=9) | Prose, not table. Levy-equivalent funding with annual minimum; no fiscal year. |
| RF £2.5bn two-child-limit abolition, used for Alliance/Green/Plaid/SNP | Opening summary [line 66](../sources/rf-two-child-2024.txt#L66); body section **The two-child limit is not meeting its own criteria for success, and should be abolished**, [lines 86–88](../sources/rf-two-child-2024.txt#L86-L88); uncertainty [footnote 10](../sources/rf-two-child-2024.txt#L105) | Prose estimate for **2024-25**; no native table/row for £2.5bn verified. Not a full party-plan cost. Keep current GB/specific-policy exclusions and benefit-take-up uncertainty. |

Qualitative DUP, Sinn Féin and TUV selected offers have no selected cash amount: do not invent a costing or remove those parties/scopes.

## Resolution Foundation: stronger exact alternative, not a fabricated table

The [publisher article](https://www.resolutionfoundation.org/publications/catastophic-caps/) was fetched and confirms the retained summary and body. Its linked [Catastrophic Caps PDF](https://www.resolutionfoundation.org/app/uploads/2024/01/Catastrophic-Caps.pdf) was downloaded to temporary research storage. It is nine image-only pages: ordinary `pdftotext -layout` returns only page breaks. Directly inspected rendered PDF pages 7 and 8:

- **PDF/printed page 7, opening paragraph**: “We estimate that abolishing the two-child limit would cost the Government around £2.5 billion in 2024-25”; it continues £3.6bn in 2024-25 prices by 2035. This is a more exact PDF paragraph locator, **not a table**.
- **PDF/printed page 8, paragraph beneath Figure 5**, heading **The cost of abolishing the two-child limit and benefit cap is low, but the benefit from removing them is high**: repeats £2.5bn in 2024-25 and £3bn with benefit-cap abolition.
- **Figure 5** is a chart of household income gains by income vigintile, not a public-expenditure table. Its bars do not provide the £2.5bn aggregate costing row. The retained equivalent is [lines 93–95](../sources/rf-two-child-2024.txt#L93-L95).
- Native PDF footnote numbering differs from the HTML's numbering; use retained HTML footnote 10 for the existing take-up caveat rather than transplanting its number to the PDF.

Do not replace £2.5bn with £3bn (two policies), £3.6bn (full rollout, different time/price basis), or a later-year estimate to manufacture table compliance. No verified scope/year-equivalent native table alternative was found for the selected RF amount in this research.

## External official alternatives discovered, not registered or substituted

### Lib Dem: verified native table, but different exact amount/year

[Tax Policy Associates' 10 June analysis](https://taxpolicy.org.uk/2024/06/10/2024-election-lib-dem-manifesto/) links the official [Funding a Fair Deal costing supplement](https://www.libdems.org.uk/fileadmin/groups/2_Federal_Party/Documents/PolicyPapers/Manifesto_2024/Funding_a_Fair_Deal_-_Liberal_Democrat_Manifesto_Costings_2024.pdf). Download and text extraction succeeded:

- **Physical PDF page 6 / printed page 5**, table **REVENUE**, column **£m 2028-29**, row **18 Introduce a 4% tax on share buybacks**, value **1,420**.
- **Physical PDF page 7 / printed page 6**, note 18 explicitly specifies **FTSE-100 listed companies**, confirming policy compatibility.
- This is **£1.42bn in 2028-29**, not the release's exact £1.4bn annual amount without a fiscal year. It is a useful *supplemental* native costing, not evidence that the existing release has a table or a reason to overwrite its year/scope. No new source files were added for it.

### Conservative: genuine costing-document URL identified, exact row not verified

[Tax Policy Associates' 11 June analysis](https://taxpolicy.org.uk/2024/06/11/our-take-on-the-conservative-manifesto/) links [Conservative Costings Document GE2024](https://public.conservatives.com/static/documents/GE2024/Conservative-Costings-Document-GE2024.pdf). Direct download returned HTTP 403; text-fetch tooling identified PDF content but could not decode it. Therefore **no table/page/row/year from this supplement is verified here**. A differently guessed URL returned 404 and is not evidence. Do not use another party's critique or an uninspected page number as the native source locator.

## Machine-readable supplemental locators

[Party figure locators](../sources/party-figure-locators.json) contains only the retained Labour and Reform native-table entries, and empty arrays for retained prose-only cash sources. Literal strings are normalizable substrings of their `pdftotext -layout` physical pages. Reform `year` is null: its native period header is preserved rather than inventing a fiscal year. Empty arrays record a real evidence gap, not missing research or a synthetic table. No existing source, offer, scope, code or generated page was changed by this research.
