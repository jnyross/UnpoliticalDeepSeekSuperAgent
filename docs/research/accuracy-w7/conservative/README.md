# Wave 7 / issue 54: Conservative £12bn welfare savings native table

Research completed 2026-11-02 UTC. **Resolved: accessible public archive of the actual party costings supplement supplies an exact £12bn annual welfare row and fiscal year.** Research artifacts only; no shared source registry, offers, independent assessment, code or generated data changed.

## Verified exact native locator

- Document: Conservative Party, **Costings Document**, accompanying the 2024 manifesto; native PDF metadata title `Costings Document.indd`, creation 11 June 2024 07:13:42 UTC, modification 07:13:44 UTC.
- **Physical PDF page 4 of 8; no printed page folio visible.**
- **Table 2: Welfare Reform and Tackling the Tax Gap**.
- Units: **£ million**. Row: **Welfare reform**, footnote **1**. Column **2029-30**. Exact native amount **12,000** = **£12 billion**.
- Other columns in the same row: 2025-26 **4,000**; 2026-27 **8,000**; 2027-28 **10,000**; 2028-29 **11,000**. This is an annual profile, not a cumulative £12bn Parliament total, and £12bn does not apply to every preceding year.
- Footnote 1: “On 8 June 2024, the Conservative Party set out its plans to deliver £12 billion a year of welfare savings by the end of the Parliament.” It lists disability-benefit reform, capability-for-work assessment, fit notes, sanctions, Universal Credit rollout and fraud measures. It discusses working-age health/disability benefit claimants and spending relative to current forecasts.
- Table introduction says these are taxpayer savings from welfare reform and tax avoidance/evasion measures. **Use the welfare row alone**: the separate tax-gap row is **6,000** in 2029-30; combined total **18,000** is not the selected welfare claim.
- Introduction on physical page 2 identifies the five-year fiscal forecast period and 2029-30 as the target fiscal-rules year.

Direct retained evidence: [native PDF, page 4](<conservative-costings-2024.pdf#page=4>), [layout extract, table and note](<conservative-costings-2024.txt#L80-L122>), [rendered native page](<table-2-page-4.png>), [PDF metadata](<pdfinfo.txt>). The rendered page was directly inspected, not merely inferred from search snippets. The table title, row, amounts, years, units and footnote are visible.

## Scope and provenance guardrails

The existing selection in [party offers](<../../../../sources/party-offers.json#L273-L300>) is “Reform working-age welfare to cut annual spending”, scope “Working-age welfare reform; UK manifesto claim”, £12bn annually against projected benefit spending. This supplement supports that selected **party claim** without switching to a different policy or total. Its row label is the broader literal wording “Welfare reform”; retain that native label and its note, rather than pretending the row itself says “disability benefits only”.

The original manifesto passage remains prose on physical page 24 with no fiscal year. The newly verified **supplement** supplies 2029-30 for its £12bn row; do not claim the original passage itself stated this year. The existing independently attributed Resolution Foundation assessment is separate evidence and must not be replaced by this official party supplement. The party note's assertion that £12bn is a “reasonable estimate” is not independent verification or a conclusion that savings will be delivered. No source proves the proposed savings were realised or that the policy is currently in force.

## Public access path and attempts

1. [Tax Policy Associates, 11 June 2024](https://taxpolicy.org.uk/2024/06/11/our-take-on-the-conservative-manifesto/) was fetched successfully with web_fetch during research; it expressly links the [publisher costings PDF](https://public.conservatives.com/static/documents/GE2024/Conservative-Costings-Document-GE2024.pdf). This establishes the publisher link rather than guessing a filename.
2. Publisher PDF ordinary HTTPS GET on **2026-11-02T08:23:17.854913Z** returned **403**, 17-byte denial body retained. No cookies, authentication, proxy tricks or protection bypass were attempted.
3. Public manifesto archive directory index GET on **2026-11-02T08:23:17.955405Z** also returned **403**. This directory-index failure does not establish that every archive PDF is inaccessible; it was not needed after the successful exact archive capture.
4. [Wayback public CDX query](https://web.archive.org/cdx/search/cdx?url=public.conservatives.com/static/documents/GE2024/Conservative-Costings-Document-GE2024.pdf&output=json&filter=statuscode:200&filter=mimetype:application/pdf&collapse=digest) on **2026-11-02T08:23:18.075001Z** returned **200** and one distinct digest for capture **20240611130512**, original status **200**, MIME **application/pdf**, SHA1/base32 **BIOYOGRH6TF5MCLDQFH6NEM6ZTDNM52O**. The CDX length 673523 is an archive-index field, not the downloaded PDF byte count.
5. [Public raw archived PDF](https://web.archive.org/web/20240611130512id_/https://public.conservatives.com/static/documents/GE2024/Conservative-Costings-Document-GE2024.pdf) GET begun **2026-11-02T08:23:50.808853Z**, response Date **2026-11-02T08:23:52Z**, returned **200 application/pdf**, **748262 bytes**. Public `id_` replay requests the unrewritten native archived file, not a bypass of publisher protection. Memento datetime **2024-06-11T13:05:12Z**. Original last-modified **2024-06-11T10:06:31Z**. Original URL and archived response headers are retained.

[Initial request metadata](<attempts-initial.json>) records timestamps, statuses, headers, response files and SHA256 hashes. [Archive download metadata](<archive-download.json>) records full successful URL, timestamp, status, headers, byte count and SHA256. [CDX response](<wayback-cdx.response.txt>) retains the discovery record. Denial bodies are [publisher](<official.response.txt>) and [archive index](<manifestos-index.response.txt>). Search queries included the exact filename and Conservative costings/welfare terms; search snippets were not used as table evidence.

## Integrity and extraction

- Native PDF SHA256: `77e183b447bed60d8c1f9efc63fd4b0c256588051e82268b5dc2c3521b2489f7`.
- Native PDF SHA1/base32: `BIOYOGRH6TF5MCLDQFH6NEM6ZTDNM52O`, independently calculated from downloaded bytes and **exactly matches CDX**.
- Native PDF MD5/base64: `RhGAuXKtcsgzLEMO6DRDZA==`, independently calculated and **exactly matches archived original content-md5**.
- Layout text SHA256: `ae508b4cc156db05128aec29a9aa3e0f14604b77ba878285eab61a44c601d80e`.
- Extraction: Poppler `pdftotext` version **26.01.0**, `-layout`, exit 0. Eight physical PDF pages. Page mapping verified by splitting text on form-feed; Table 2 occurs on physical page 4. `pdfinfo` succeeded and reports unencrypted native PDF 1.3. `pdftoppm` rendered page 4 successfully.
- Initial command used unavailable `python` (exit 127); rerun with installed `python3` succeeded. All HTTP attempts were ordinary unauthenticated requests. Every artifact is confined to this new research folder.

Reproduce from repository root:

```sh
pdftotext -layout docs/research/accuracy-w7/conservative/conservative-costings-2024.pdf docs/research/accuracy-w7/conservative/conservative-costings-2024.txt
pdfinfo docs/research/accuracy-w7/conservative/conservative-costings-2024.pdf
sha256sum docs/research/accuracy-w7/conservative/conservative-costings-2024.pdf docs/research/accuracy-w7/conservative/conservative-costings-2024.txt
```

## Remaining work / concrete gaps

No remaining access or native table/row/year gap for this **party £12bn annual welfare savings selection**. The live publisher still denies direct download, but its exact native archived file is retained and digest-verified. Integration into locators/source registries/UI, if chosen by the parent, is outside this bounded research-only task. The supplement is official costing evidence, **not an independent audit**, and must remain distinct from the existing RF assessment.
