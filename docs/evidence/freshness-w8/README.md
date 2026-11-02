# Wave eight: verified new-publication coverage, not another receipt repair

Refs [#49](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/49).
Scored baseline: `9864a10c5a5beb5d49f10a9eb19bcbd00d5d155b`.
Reuses #62's source discovery and #66's completed write-ahead receipt/serialization
repair. No receipt identity, production release or review task is manufactured here.
This is useful additional coverage, **not a claim of full Freshness L3 or L4**.

## Implemented scopes and explicit boundaries

| Source family | Verified official listing | Retained initial links | What a candidate means / limits |
|---|---|---:|---|
| DUP retained manifesto | [Policy papers and consultations](https://mydup.com/policies/policy-consultations) | 14 PDF pointers | New document URL in the unique `ul.accordion-controls`. The exact S3 host AND `/my-dup/` path are constrained. Anchors can be images/“here”; labels explicitly say the publisher title was not extracted. This does not invent enclosing policy titles, download the PDFs or establish dates. |
| SNP retained manifesto | [Manifesto page](https://www.snp.org/manifesto/) | 11 PDF pointers | National, regional and accessible-format links between verified `primary` / `footer` markers. Current page concerns the **2026 Scottish Parliament election**, not the UK 2024 offers. A new pointer requires a jurisdiction/content review, never automatic replacement of the historical UK page. |
| RF retained two-child analysis | [Social-security research publications](https://www.resolutionfoundation.org/publications/?theme=social-security) | 25 heading links | The publisher's filter was verified, not inferred from its query string: heading/category classes and link sets differ from unfiltered publications. Select `h2.entry-title` within the unique results container, not duplicate “Continued”/“READ MORE” anchors. Covers the returned first page, not all RF commentary or an exhaustive archive. |

Pinned canonical baselines:
[DUP](party-offers-dup-baseline.json), [SNP](party-offers-snp-baseline.json),
[RF](party-evidence-rf-two-child-2024-baseline.json).
They start from genuine captured publisher listings and produce **zero initial new
candidates**. They are not invented historical logs or a synthetic backlog to open
on the tracker. Fixtures demonstrate new-link detection against those baseline rules.

The inventory still has **26 entries**, but retained-URL-only entries fall from **20
to 17**. Nine entries have some collection/latest/current-roster/listing discovery;
that does NOT mean every publication of all nine families is covered. All historical
snapshot checks remain in place. Historical/archive allowlists are unchanged; new
`listing_allowed_hosts` separately constrain publisher pages and their pointer hosts.
New listing candidates do not become false historical-revision warnings.

## Minimal extension of existing machinery

The existing listing parser now supports either its original verified ID boundaries
or one explicit class-bound container, with optional heading-parent selection. Missing,
ambiguous, duplicate or unclosed boundaries fail closed. It does not infer headings,
follow arbitrary hosts, execute scripts, guess pagination or crawl the whole site.

A listing candidate's `sha256` is explicitly marked as canonical listing links/labels,
**not unfetched document bytes**. The existing timing adapter records the actual listing
URL/fingerprint with unknown publication/vintage, rather than attributing that hash to
a PDF or making up a source publication date. This is metadata interpretation only:
no persisted-main measurements, PR permission or timing-ledger rewrite is claimed.

Combined checks are independent: an unavailable old/archive URL cannot suppress a
verified new-publication candidate, and a failed listing cannot discard a verified
historical revision. Partial failures retain updates, per-check error metadata and the
global error/nonzero exit; they are not reported as unchanged. The original issue
receipts, canonical keys, open/closed pagination, recovery and serialization are reused.

## Genuine requests, failures and correction

The [first 26-entry live audit](live-discovery.json) is deliberately retained, including
its errors. It exposed a real selector mistake: DUP has two `section-single-policy`
sections, so the parser correctly refused an ambiguous boundary. The final selector is
the unique `ul.accordion-controls`, not a relaxed accept-first rule.

The [corrected targeted live check](verified-adapter-run.json), **10:36:43–10:36:46 UTC
on 2 November 2026**, checks all three new combined adapters (retained snapshots AND
publisher listings): **zero errors, zero new candidates**. No issues are opened and no
source baseline, notice or static page is changed by either read-only audit.

The first audit's other error is the retained Conservative archive costings URL:
**HTTP 429**. It remains unknown, not unchanged; repeated requests were not hammered
to evade rate limits. That source is still retained-URL-only and is not misrepresented
as a working official publisher listing. Known raw-byte revision findings in the audit
are not automatically interpreted as changed financial claims.

## Alternatives checked rather than invented

[NI research](ni/README.md) records 19 bounded requests, exact safe fragments and
original/fragment hashes. Alliance/SDLP/UUP/TUV routes have actual 403 and alternate-host
DNS/TLS/sitemap limits. Sinn Féin's live policy collection is partly ROI, marked under
construction and shows only 9/64 rows with unresolved pagination; no complete NI
coverage is asserted. DUP's seven-link policy-category listing was also verified, but
this implementation watches the more useful actual PDF pointers instead.

[Independent-evidence research](evidence-listings/README.md) records 18 bounded
requests. RF's social-security filter works; its budget listing is a different family.
Full Fact economy works but is not comprehensive for the retained politics buyback
check. IFS topic/election pages return 403; a 200 `/rss.xml` with one “Home” item is not
a verified publication feed. NI Education's genuine early-years topic has featured
items only; its advertised news filter returned **byte-identical unfiltered news**,
and a childcare search did not demonstrate filtering. These alternatives are not
quietly registered as complete adapters.

[GB request evidence](gb/requests.json) records verified Conservative pages, Reform
and Plaid 403s, an unavailable guessed Green route and the successful SNP page.
Full response scripts/browser tokens are not retained: exact safe listing excerpts
or extracted links are distinguished from original-response hashes. SNP fragment
provenance is [explicit](gb/snp-fragment-provenance.json); no excerpt is called a full
raw response. Publisher copyright remains the publisher's; none is a new OGL claim.

## Scheduled evidence and precise permission residue

The [schedule-only API query](scheduled-runs.json) still reports no visible scheduled
run; [workflow metadata](workflow-state.json) says active. No scheduler defect, cron
execution, backdated release or manual-as-scheduled event is fabricated.
[Timing metadata](timing-run-metadata.json) retains the actual event/revision/outcome of
run 41420149048. Its previously documented Actions PR-creation permission failure is
separate from update-issue creation; no setting grant, successful main persistence,
branch-as-PR or real-year history is inferred. This ticket does not rebuild or bypass
that earlier ticket's permission residue.

## Reproduce and verify

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_publication_discovery.py' -v
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python scripts/build.py --check
python3 scripts/discover.py --report /tmp/new-read-only-discovery.json
```

Network-free fixtures cover new/unchanged/repeated/error paths, heading-only links,
separate host rules, nested/ambiguous/missing containers, explicit unavailable titles,
partial-error delivery, no historical warnings, listing-only timing metadata and
all three retained live excerpts. New-candidate issue writes use a fake transport and
temporary receipts, never production tasks or simulated people evidence. The full
suite, deterministic build, focused independent code review and head CI results are
recorded in the PR. No application HTML/data changes: Before/After UI evidence does
not apply. The remaining 17 snapshot-only entries, limited listing windows and genuine
scheduled/all-source operational evidence keep #49 open (`Refs`, not `Closes`).
