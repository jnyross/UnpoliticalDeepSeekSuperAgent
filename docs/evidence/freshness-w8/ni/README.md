# Wave 8 issue 49: bounded Northern Ireland publication-listing research

Automated public-GET research, 2026-11-02 UTC. No GitHub writes, application changes, historical source replacement or fabricated publication events. Read repository AGENTS, plan_discovery and release-sources before requesting sources. The first shell probe used unavailable `python` (exit 127); all requests actually made used `python3`.

## Small implementable candidate first: DUP

Official [Our Plan for Northern Ireland](https://mydup.com/policies) was linked as “All Policies” from the official homepage and returned successfully via `scripts.discover.fetch`, exact allowlist `mydup.com`. Select exactly one `section` with class token `policies-section` (optionally tighten to its `div.policies-grid`); collect anchors matching path `/policies/[a-z0-9-]+`, exact host `mydup.com`. Titles are anchor descendant text including `h3`. Seven links, no news monitoring. [Exact selected fragment](dup-policies-fragment.html), [canonical seven-link baseline](dup-policies-baseline.json), [request receipt](dup-policies-request.json). Baseline SHA256: `6f69ca086a49dbbc12455dd04718c26b29f4e32cc607d33da824979a0cb4b987`.

The existing adapter requires publisher-provided ID boundaries; there is no honest ID pair delimiting this listing. A validated, unique container tag/class selector is a small necessary extension. Detect new or title-changed links for review only; do not convert new links into adopted plans or overwrite 2024 snapshots. Retain historical archive host allowlists separately from new listing host allowlists.

### More publication-specific DUP alternative

[Policy Papers and Consultations](https://mydup.com/policies/policy-consultations), linked directly from the above grid, says “Current policy papers and consultations can be found here.” Select `section.section-single-policy` containing `ul.accordion-controls`, then `li.single-policy-key-objective`. Each row has `h4` title and PDF anchors under `.accordion-controls__content`; deduplicate figure and “here” links. [Exact fragment](dup-papers-fragment.html), [14-link canonical baseline](dup-papers-baseline.json), [receipt](dup-papers-request.json). PDF host `s3.eu-west-1.amazonaws.com` is evidenced by official-page links, **not** blanket approval of S3. Tight path `/my-dup/(?:resource-thumbnails/|resources1/)?[A-Za-z0-9-]+\\.pdf` (single regex escape before dot). This needs enclosing-row title extraction: generic anchor text alone produces blank/image or “here” titles. File content was not fetched, dated or adopted. Includes consultation responses, so keep review-only.

## Sinn Féin: usable official policy collection, bounded coverage caveat

`https://www.sinnfein.ie/` failed the exact-host redirect guard. Feasible alternative `https://sinnfein.ie/` succeeded and linked [Policies](https://sinnfein.ie/policies/), which also succeeded. [Exact listing fragment](sinnfein-policies-fragment.html), [nine-link canonical baseline](sinnfein-policies-baseline.json), [receipt](sinnfein-policies-request.json).

Selector: unique `div.facetwp-template` within `div.block-download`, then `article`; title is first `h5` (second `h5` is displayed date), target is `a[download]`, exact host `sinnfein.ie`, path `/wp-content/uploads/[0-9]{4}/[0-9]{2}/[A-Za-z0-9_-]+\\.pdf`. Anchor text includes “Download PDF” and screen-reader text, so row-title extraction is preferable.

**Do not claim full Northern Ireland coverage.** The page explicitly says “Under Construction” and “For now, please use the search below to browse policies.” The response's FacetWP settings advertised page 1, 9 per page, 64 total rows and 8 pages. The default visible set contains Republic of Ireland material (Garda, Irish GE24), not a verified UK manifesto collection or reliable complete newest-first feed. Only this public GET was assessed; no POST/API pagination guessed. The reported 2026 upload directory does not establish publication date. Treat this as official discovery surface evidence, with pagination/jurisdiction validation outstanding.

## Four concretely unavailable families

Tested route names below are **not verified listing URLs**: challenge responses cannot establish route existence. Retaining a 2024 manifesto from manifestos.org.uk is not an alternative official new-publication listing.

| Family | Public GET evidence and alternatives actually tried | Disposition |
| --- | --- | --- |
| Alliance | `https://www.allianceparty.org/` and `/manifestos` both HTTP 403; listing probe headers include `Cf-Mitigated: challenge`. Bare `https://allianceparty.org/manifestos` fails DNS (`No address associated with hostname`). | No verified listing selector. [Listing receipt](alliance-manifestos-request.json), [bare-host receipt](alliance-bare-request.json). |
| SDLP | `https://www.sdlp.ie/` and `/manifestos` HTTP 403, listing probe `Cf-Mitigated: challenge`. Bare `https://sdlp.ie/manifestos` also 403. | No verified listing selector. [Listing receipt](sdlp-manifestos-request.json), [bare-host receipt](sdlp-bare-request.json). |
| TUV | `https://tuv.org.uk/`, `/manifestos/`, and feasible WordPress sitemap alternative `/wp-sitemap.xml` all HTTP 403 Cloudflare. | No verified listing selector. [Listing receipt](tuv-manifestos-request.json), [sitemap receipt](tuv-sitemap-request.json). |
| UUP | `https://www.uup.org/` and `/manifestos` HTTP 403, listing probe `Cf-Mitigated: challenge`. Bare `https://uup.org/manifestos` fails TLS hostname validation; verification was not disabled. | No verified listing selector. [Listing receipt](uup-manifestos-request.json), [bare-host receipt](uup-bare-request.json). |

Useful remaining alternatives: ask publisher for a public policy/manifests index/feed or transport accommodation; verify the actual route using publisher-provided navigation when accessible. Do not bypass challenge/TLS or monitor broad news as a substitute. General search results for old PDFs were not adopted as new-publication listings.

## Evidence interpretation

Each `*-request.json` records URL, GET, exact host allowlist, transport, UTC start/finish, success/error, response length/hash when a body exists, and retained excerpt hash. `scripts.discover.fetch` uses urllib, 60-second per-request timeout, browser user agent and exact-host HTTPS redirect guard. Requests were finite, at most six concurrent. Failures without response bodies have no body hash.

Per parent instruction, full HTML responses containing scripts, form tokens, or CSP nonces were not retained. `response_sha256` hashes the **original full response bytes**; `retained_sha256` hashes the separately named safe exact fragment or extracted visible-response text. `response_file_not_retained` is an explicit absent-original marker, not a promised evidence file. [Fragment provenance](fragment-provenance.json) independently distinguishes raw-response versus selected-fragment hashes. No fragment is represented as a full response. Error visible text and challenge headers are evidence of transport failure, not evidence of a listing or publication. No release event inferred.
