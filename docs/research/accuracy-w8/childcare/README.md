# Wave 8: DUP £25m approved 2024-25 childcare package — bounded research

## Result: native table footnote verified; standalone programme row not found

The selected offer in [party-offers.json](../../../../sources/party-offers.json#L303-L331) is the **already-approved Northern Ireland £25m early-learning/childcare package for 2024-25**, not the separate unpriced workplace-nursery/capital-grant election promises, not recurring spending, and not new Westminster money. Initial [wave-7 research](../../coverage-w7/dup/README.md) and the retained May 23 DE announcement remain the direct programme/approval evidence.

A genuine official native PDF provides new **table-footnote evidence** for the same earmarked allocation, but not an individual programme row. Do not represent this as a standalone £25m table cell or a Department of Education-published table.

## Exact best locator

- Publisher: **Northern Ireland Department of Finance** (not Department of Education).
- Publication: *PUBLIC EXPENDITURE 2023-24 PROVISIONAL OUTTURN AND 2024-25 JUNE MONITORING*.
- [Official raw PDF](https://www.finance-ni.gov.uk/sites/default/files/publications/dfp/PUBLIC%20EXPENDITURE%202023-24%20PROVISIONAL%20OUTTURN%20AND%202024-25%20JUNE%20MONITORING.pdf), [retained identical PDF](june-monitoring-statement-2024-25.pdf).
- PDF page **28**, printed page **28**, **Table H: Departmental Outcome – Non Ring-fenced Resource (£ millions)**.
- Row **DE**, column **Executive Allocations**: **98.2** (£m), an aggregate, **not** the programme amount.
- Column heading bears footnote **1**. Exact footnote: **“Includes allocations to DE of £25m for Childcare Strategy and £43.7m for EA Pay and Grading Review”**.
- Exact year/round: **2024-25 June Monitoring**. Table title itself does not repeat the year; the document/section does.
- The same PDF printed/PDF page **6**, section **Prior Commitments**, explicitly links the £25m set aside in Budget 2024-25 to Executive-agreed Education Minister proposals, now transferred to DE as an **earmarked allocation**. This is the strongest same-programme scope bridge, reinforced by the DE EQIA below.
- [Deterministic extraction, table and footnote](june-monitoring-statement-2024-25.txt#L892-L926); [scope bridge](june-monitoring-statement-2024-25.txt#L148-L160).
- PDF SHA-256: `afec2f8d028e3aa628d246b20a31771ec2288918697f46187895bedcdfa56a83`.
- [Request metadata/hash](requests-statement.json). PDF metadata reports creation July 1, 2024; this is not a claim to have verified the landing-page publication date.

## Official near-matches retained and rejected as standalone programme rows

1. **Department of Education, EQIA Consultation Report on the 2024-25 Resource Budget**. [Official PDF](https://www.education-ni.gov.uk/sites/default/files/consultations/education/DE%20Resource%20Budget%202024-25%20-%20Equality%20Impact%20Assessment%20Consultation.pdf), [retained PDF](budget-eqia-2024-25.pdf), [extraction](budget-eqia-2024-25.txt#L160-L221). Printed/PDF p5 paragraphs **3.6–3.7**: £25m set aside for Executive Early Learning and Childcare Strategy, then transferred to DE in June Monitoring. P6 paragraph **4.1** repeats £25m for 2024-25 held centrally pending approval. **Table 1** p6 contains only aggregate Resource DEL **2,874.4m**; no childcare row. This source verifies exact year/scope and the June-monitoring bridge but is prose for £25m.
2. **Department of Education Annual Report and Accounts 2024-25**. [Official PDF](https://www.education-ni.gov.uk/sites/default/files/2025-11/2024-25%20Annual%20Report%20and%20Accounts%20-%20Department%20of%20Education.pdf), [retained PDF](annual-report-2024-25.pdf), [extraction](annual-report-2024-25.txt#L2118-L2173). Printed **p43 / PDF p48** says £25m provided to implement Executive Early Learning & Childcare Strategy during 2024-25. Again **prose**, not separate table row. Printed p44's **£55m for 2025-26 is a different year and rejected**.
3. **DoF 2024-25 June Monitoring – Financing and Spending Tables**. [Official PDF](https://www.finance-ni.gov.uk/sites/default/files/publications/dfp/June%20Monitoring%202024-25%20-%20Financing%20and%20Spending%20Tables_0.pdf), [retained PDF](june-monitoring-2024-25.pdf), [extraction](june-monitoring-2024-25.txt). Tables 1–4 are aggregate NI financing/spending; no named childcare row. Table 1 unallocated/earmarked 25.6 and movement -24.9 must **not** be substituted for the £25m programme.

Raw request metadata for these PDFs: [initial DE requests](requests-initial.json), [aggregate monitoring tables](requests-monitoring.json). All contain original/final URL, response status/headers, byte count, SHA-256 and retrieval UTC timestamp. Text is `pdftotext -layout` extraction, not a recreated publisher table.

## Search/attempt log and bound

Research performed November 2, 2026. Searches targeted education-ni.gov.uk 2024-25 / 2024/25 childcare budget/monitoring; then finance-ni.gov.uk June monitoring, Childcare Strategy, 25.0/25.000 and XLSX/budget allocations. DE EQIA and Annual Report were downloaded successfully (HTTP 200). Broader DoF search found the official native June-monitoring financing tables and full statement above (HTTP 200). No verified XLSX or standalone DE programme row was located.

Guessed landing pages `https://www.finance-ni.gov.uk/publications/2024-25-june-monitoring`, `https://www.finance-ni.gov.uk/publications/june-monitoring-2024-25`, and `https://www.finance-ni.gov.uk/publications/2024-25-june-monitoring-round` each returned **404**. These are unsuccessful discovery attempts, not provenance for the successful PDFs. The official news page [Executive agrees 2024-25 Budget](https://www.finance-ni.gov.uk/news/executive-agrees-2024-25-budget) returned 200, dates the budget announcement April 25, 2024, and confirms the £25m set-aside in prose; it was not retained as new table evidence. An initial local download command failed because `python` was unavailable; retried successfully using `python3`, with no source content inferred from that failure.

**Disposition:** useful verified native-table-footnote plus exact-year corroboration. Strict request for a **DE-published 2024-25 standalone £25m programme table row remains unverified** after this bounded search. A consumer accepting table footnotes may cite Table H / DE / Executive Allocations / footnote 1 with the scope bridge; otherwise retain the explicit row gap. No generated table is publisher evidence. No shared code or source registry edits made.
