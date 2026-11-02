# Wave 6 Reform: verified exact selected-package pair

Research retrieved 2026-11-02 UTC. Research files only; no application data or scripts changed. This is **not** a whole-manifesto audit or a Coverage L4 claim.

## Positive result: switch selected policy to NHS waiting-list-elimination package

**Party design and own-cost claim:** Reform UK, *Our Contract with You* (2024), **PDF page 9 / printed page 7**, NHS. [Official party publishing-CDN PDF](https://assets.nationbuilder.com/reformuk/pages/253/attachments/original/1718625371/Reform_UK_Our_Contract_with_You.pdf?1718625371). Normal public GET returned 200 application/pdf. Retained [PDF](<reform-contract.pdf>) SHA-256 `500dca6b808f47e271394c803dc36ca4b5681fffb1bae41276385f224ba03eb3`, identical to the existing source-index hash. HTTP Last-Modified is 17 June 2024; the publication is plainly the 2024 election document, not a 2025 pledge.

- [Extracted text](<reform-contract.txt#L338-L395>): headline says healthcare needs reforms to “enjoy zero waiting lists.” The page proposes frontline staff basic-rate tax relief for three years, training/fee measures, independent provision, private healthcare tax relief, a voucher scheme and efficiency changes.
- Exact own-cost label, whitespace-normalised from [lines 391–392](<reform-contract.txt#L391-L392>): **“NHS PLEDGES COSTS = £17 BILLION PA”**.
- This £17bn is the party's **annual NHS-package cost claim**, not an independent cost estimate, not the cost of a single voucher measure, and not an independently verified affordable spending total. The passage does not specify a fiscal year or nominal/real price base. Do not relabel it 2024–25 or a five-year total. The whole NHS package must be the selected component, not one submeasure.

**Matched allowed-body expert assessment:** Institute for Fiscal Studies, Paul Johnson (Director), *General election 2024 manifesto analysis: Opening remarks*, **24 June 2024**, **PDF page 6**. [Official IFS PDF](https://ifs.org.uk/sites/default/files/2024-06/Paul%20Johnson%27s%20Opening%20Remarks.pdf). Direct ordinary GET returned 200 application/pdf; no cache/proxy, protection bypass, or article-mirror substitution was used. Retained [PDF](<ifs-opening-remarks.pdf>), [text](<ifs-opening-remarks.txt#L201-L216>), [PDF metadata](<ifs-opening-remarks-pdfinfo.txt>), [HTTP metadata and SHA-256](<request-metadata.json>).

Exact full sentence, line-break-normalised:

> In any case, the claim that they could eliminate NHS waiting lists at a cost of £17 billion a year is demonstrably wrong, while the vast tax cuts would cost even more than stated, by a margin of tens of billions of pounds per year.

Safe selected-component quote (contiguous exact substring):

> the claim that they could eliminate NHS waiting lists at a cost of £17 billion a year is demonstrably wrong

Attribute this explicitly to **Paul Johnson, Institute for Fiscal Studies**, and link to the official PDF. It directly assesses the same NHS outcome-and-annual-cost claim, unlike the previously retained Full Fact NHS-claims roundup. No inference from general manifesto criticism is necessary. It supplies a judgement, **not** a replacement IFS estimate of the true cost. There is no verified alternative amount here. IFS's following clause about tax cuts must not be assigned to NHS costs.

### Date and identity verification

The PDF body opens “General election 2024 manifesto analysis” and “Opening remarks by Paul Johnson, Director, Institute for Fiscal Studies”. [PDF metadata](<ifs-opening-remarks-pdfinfo.txt>) gives creation/modification **24 June 2024 08:58:51 UTC**. HTTP Last-Modified is **24 June 2024 09:01:01 GMT**. Independent allowed-body publisher corroboration: [Full Fact, 24 June 2024](https://fullfact.org/politics/ifs-conservative-labour-manifestos/) discusses Johnson launching the IFS manifesto analysis that morning and links the matching IFS event. Its [retained body](<fullfact-ifs-manifestos.html>) and [text](<fullfact-ifs-manifestos.txt>) supply the publication date and event attribution. Full Fact's broad quote about Reform/Greens is **not** used as the exact NHS fiscal assessment.

### Proposed content semantics for parent

- Offer: Eliminate NHS waiting lists through Reform's NHS package.
- Excerpt: “enjoy zero waiting lists.” (manifesto PDF9/printed7; existing source text lines 437–444.)
- Cost: £17bn per year, **party claim** for NHS pledges (same page; existing source text 505–506).
- Year: Annual; no fiscal year stated in this passage.
- Scope: Selected NHS waiting-list-elimination package, not whole manifesto and not one submeasure's allocation. Neither source provides a separately verified regional allocation.
- Baseline: Party's annual package claim; independently verified counterfactual cost/price base not supplied. IFS disputes attaining zero waiting lists at that amount.
- Assessment: exact substring above; attribution Paul Johnson, Institute for Fiscal Studies; official PDF page6.
- Status: 2024 election proposal, not current implemented policy.

## Raw extraction and TUV scope follow-up

[Raw-mode IFS text](<ifs-opening-remarks-raw.txt#L163-L165>) is retained using `pdftotext -raw` for the application's fresh-page validator. Exact matched assessment remains on PDF page 6. Layout and raw text both preserve the same whitespace-normalised quote.

The complete IFS opening-remarks body was also checked for TUV-adopted components. It does **not** give a specific judgement on Reform's £20,000 personal allowance / £70,000 higher-rate threshold, or on its employer-NI charge for foreign workers with the £50,000/five-staff/healthcare exemptions. Its statement that the “vast tax cuts would cost even more than stated” is an aggregate judgement, not a component-specific assessment, and **must not be transferred to either TUV selected component**. Conservative pensioner allowances and NI policies discussed earlier in the PDF are different policies.

## Concrete bounded candidate register

1. Official IFS 2024 opening-remarks PDF: **200, full substantive body**, exact positive match above. Search-discovered standard official download, not a protected article bypass.
2. Official IFS *The public finances in the coming Parliament* June2024 PDF: **200**, [retained PDF](<ifs-public-finances.pdf>) and [text](<ifs-public-finances.txt>); comparative aggregate Reform chart, not needed for exact NHS judgement. Its chart explicitly says Reform figures average over Parliament, unlike other parties' 2029–30 figures; do not interchange them.
3. [IFS Reform UK manifesto reaction](https://ifs.org.uk/articles/reform-uk-manifesto-reaction): **403 challenge**, retained [response](<ifs-reform-reaction.html>), not substantive evidence. No bypass attempted.
4. [IFS 2024 manifesto-analysis event](https://ifs.org.uk/events/general-election-2024-ifs-manifesto-analysis): **403 challenge**, retained [response](<ifs-event.html>), not substantive evidence.
5. [Full Fact IFS manifesto report](https://fullfact.org/politics/ifs-conservative-labour-manifestos/): **200**, full body, useful identity/date corroboration, but its own broad Reform quote is not a specific NHS cost judgement.
6. Searches for RF Reform-2024 fiscal analysis and verified syndicated IFS/WiredGov alternatives did not produce a better exact candidate before the positive official PDF match; no universal claim of source absence follows. Search snippets were discovery only and are not evidence.

[Additional response metadata](<additional-request-metadata.json>) records exact URLs, timestamps, headers, status and body SHA-256 for candidates 3–5 and the official manifesto. All positive quotations above are supported by retained complete bodies, not search snippets. Third-party copyright applies; these bodies are not automatically OGL.
