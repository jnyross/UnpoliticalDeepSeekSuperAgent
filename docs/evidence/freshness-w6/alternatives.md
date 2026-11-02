# Bounded official new-release alternatives — Freshness wave six

## Scope and coordination

This is an automated, bounded source-discovery investigation, not a full party-plan
coverage audit and **not a Freshness L3 or Context L4 claim**. It demonstrates useful
official alternatives and precise remaining limitations; it does not independently
validate party policy costings or infer a next publication date.

Reuse the [Context wave-six audit](<../../../docs/evidence/context-w6/README.md>) and
[merged PR #58](https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/pull/58).
That audit already checked 22 retained source families and explicitly states that
retained-URL checks cannot find newly published manifesto URLs or a current roster.
Do not duplicate its complete audit or describe its manual run as scheduled evidence.

The [release registry](<../../../config/release-sources.json>) used retained-url-snapshot for
the historical roster and all thirteen party manifesto sources. The
[party manifest](<../../../sources/party-offers.json>) retains a 9 July 2024 roster and 2024
manifestos. Ten of the thirteen manifesto sources are archive-hosted with original
publisher download URL unverified. Byte monitoring of those URLs remains useful for
historical revisions, but cannot demonstrate official new-plan discovery.

## Fresh retained requests

The three responses below were fetched with **Python urllib only**, using public GETs,
35-second per-request timeout and a 2,000,000-byte response bound. No browser cookies,
authentication, protection bypass or embedded scripts were used. Raw response bytes
are retained as inert UTF-8 text files, not executable site pages. Party content
remains publisher copyright, not Open Government Licence.

[Request report](<../../../docs/evidence/freshness-w6/alternatives/request-report.json>) records
requested/final URLs, UTC start/finish, status, Content-Type, HTTP Date, size and hash.
All three fresh responses returned HTTP 200 with `text/html; charset=utf-8`.

| Official endpoint | UTC request interval on 2026-11-02 | Bytes | SHA-256 | Retained response |
|---|---|---:|---|---|
| [Conservative news](https://www.conservatives.com/news) | 06:25:37.293361–06:25:37.429814 | 37,466 | `50a121e690fdc4f50cce0b6d72c3efa087ec283174579345bd45ba480786239a` | [Listing](<../../../docs/evidence/freshness-w6/alternatives/conservative-news.html.txt>) |
| [Conservative CPC26 policies](https://www.conservatives.com/news/policies-announced-at-cpc26) | 06:25:37.429977–06:25:37.462078 | 38,710 | `e27be715074fe1501d96719de0c12b8eab267c71011148ca00844d531291d74f` | [Article](<../../../docs/evidence/freshness-w6/alternatives/conservative-cpc26.html.txt>) |
| [Liberal Democrat policy listing](https://www.libdems.org.uk/members/make-policy) | 06:25:37.462220–06:25:38.028958 | 163,891 | `9065faaa4a9489f57a77715df003b98028eba7aefd5f5acdef258d30ffea5713` | [Listing](<../../../docs/evidence/freshness-w6/alternatives/libdem-policy-listing.html.txt>) |

These are fresh observations, not the earlier exploratory responses. In particular,
the earlier 06:22:16 Liberal Democrat listing had the same length but another raw
hash (`f5430edfe347424f31d5d884e506412a3c5f2897fc75b8ee3299c2d68f003c67`).
That alone does not demonstrate a changed policy. Prefer normalized scoped links/text
for candidate identities; retain raw hashes as response evidence.

## Candidate 1: Parliament runtime-date current roster

The official [dated Commons API](https://members-api.parliament.uk/api/Parties/StateOfTheParties/1/2026-11-02)
returned HTTP 200 in the exploratory 06:21:18 UTC request, 5,095 bytes, SHA-256
`0625fdec6ea3df7aa9f9c2a30f68354036ab6db6f2546c5a4dd5646d2a62b6d6`.
The separately retained [current response](<../../../docs/evidence/freshness-w6/current-roster.json>)
and [request record](<../../../docs/evidence/freshness-w6/current-roster-request.json>) agree.
Existing normalized roster semantics hash:
`34794b6722b3fa54a56433cc954dc55228e32f9cb06254f2b3454b678e634068`.

The response has 17 rows and 650 seats, including Your Party (ID 1115, two seats)
and Restore Britain (ID 1117, one seat), absent from the retained 2024 roster.
Labour is 404 rather than 411, Conservative 118 rather than 121, Liberal Democrat
71 rather than 72, Independent 11 rather than six, Reform eight rather than five,
SNP eight rather than nine and Green five rather than four.

Meanwhile, an exploratory GET of the
[historical API](https://members-api.parliament.uk/api/Parties/StateOfTheParties/1/2024-07-09)
still returned the exact retained 4,522-byte hash
`0801b0ce9d9f1fccbd53fdb6343e9b96083cba802ade562132a46b26cc87efbe`.
This demonstrates the gap without declaring the historical snapshot itself incorrect.

Minimal safe adapter: compute the UTC date at execution, request that dated endpoint,
reuse identity/seat semantic validation, and generate a current-roster review candidate.
Keep the historical revision check and historical source dates. Deduplicate by source
and semantic hash, not the daily changing URL. Do not turn a current-roster candidate
into a historical source-revision notice or silently update retained offers.

Limits: the undated `/api/Parties/StateOfTheParties/1` returned 404. The populated
response reports `totalResults: 0`; use validated nonempty `items`, not that count.
Do not insist on exactly 650 seats because legitimate vacancies can occur. HTTP/schema
failure is unknown, not unchanged. Current membership does not establish any new
party's policy offer, independent assessment or publication date.

## Candidate 2: Liberal Democrat adopted-policy paper listing

The retained listing's `policy-papers` section states that it lists papers passed
at Conference and that the newest paper on the same topic supersedes previous papers.
It includes Policy Paper 166, A Liberal Vision for Primary Healthcare (2026),
165, Defending Democracy (2026), 164, Strength, Resilience and Partnership (2026),
163, Whole-Person Mental Health (2026), and 162, Revitalising Town Centres and
High Streets (2026), as well as 2025 papers and the retained 2024 manifesto.

Minimal safe adapter: extract only policy-paper section links on the exact official
host, with explicit `/conference/papers/` and approved document path patterns; bound
the number of child requests and response bytes. Retain canonical URL, title, listed
year and associated motion link, and emit a review candidate for newly seen papers.
Track normalized candidate links separately from incidental page-byte changes.

Exploratory verification (not retained attachment evidence): the
[Primary Healthcare landing page](https://www.libdems.org.uk/conference/papers/autumn-2026/primary-healthcare)
was readable and linked an
[official PDF](https://www.libdems.org.uk/fileadmin/user_upload/Primary_Healthcare_-_for_web_-_17_AUGUST_v.2_NEW_CONTENTS_PAGE.pdf).
A Python urllib GET of that PDF completed at 06:22:58.013199 UTC: HTTP 200,
`application/pdf`, `%PDF-1.7`, 13,471,181 bytes, SHA-256
`30af63ee01399b800d20d2a313a1d4ffbb7836f9fcedb346b5ba325bb27e28ab`.
The PDF body is not retained here. An attachment adapter needs an explicit larger
size bound, or should defer downloading attachments until review.

Limits: paper listing is not proof of a fully costed whole-party plan, and topic,
territorial scope, passed motion/amendments and financial implications need review.
The exploratory `/plan` request redirected to `/manifesto`, still titled Manifesto
2024: do not infer a new manifesto. Guessed `/members/make-policy/policy-papers`
and `/feed.rss` returned 404. The verified landing-page alternative is sufficient
without inventing an API or assuming an RSS endpoint exists.

## Candidate 3: Conservative announcement listing

The retained official news listing links the retained CPC26 article. The article is
dated 8 October 2026 and expressly claims: “Our Savings Plan will save £71 billion”.
It says this updates the £47 billion annual savings package announced at Conference
2025 and allocates £35.5 billion to deficit reduction against 2029–30 forecasts.
Those are attributed party claims, not validated savings or current public spending.

Minimal safe adapter: normalize same-host `/news/` article links from the listing,
bound child requests, retain article title/date and plan-related text, and create
review-only candidates using canonical URL and normalized relevant content. Do not
replace the selected 2024 manifesto quote, fiscal scope or costing automatically.

Limits: the news listing also contains non-policy stories; a finite latest-news page
is not a complete historical archive. No pagination or all-announcement completeness
was established. This demonstrates a newer official fiscal plan that the retained
2024 PDF cannot discover, not all-party release coverage or independent assessment.

## Failed or unestablished alternatives and remaining work

Exploratory unattended Python urllib GETs to Labour's
[posts API](https://labour.org.uk/wp-json/wp/v2/posts?per_page=3),
[updates](https://labour.org.uk/updates/) and
[Plan for Change](https://labour.org.uk/plan-for-change/) returned HTTP 403.
A separate web-fetch tool could read the updates page, but that tool-specific success
is not evidence that the unattended discovery transport can use it. No protection
bypass was attempted; API access remains unestablished. These exploratory error
responses were not retained in this three-response evidence set.

Other party and independent-assessment listing alternatives were not exhaustively
checked. The current-roster improvement is useful partial work; the Conservative
announcement adapter remains a candidate, not implemented coverage. The current-roster
and bounded Liberal Democrat conference-paper listing adapters are now implemented;
the listing baseline starts at the captured 14 links, not an invented historical log.
Full new-release discovery,
real scheduled operational evidence and any workflow-permission residue remain
separate acceptance questions under issue #49. **No full Freshness L3 claim.**
