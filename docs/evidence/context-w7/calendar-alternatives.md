# Wave 7 / issue #56 — bounded official calendar alternatives

Baseline: `278cc11526ea50a612c4644e2dd521c479bfe5db`. Actual requests: **2 November 2026, 08:23:31–08:25:05 UTC**, in two short batches. This is a calendar investigation, **not** a rerun of the 22-source audit. No UI, generated pages, source manifests, GitHub resources or retained production source snapshots were changed.

## Finding

**An exact next update remains unestablished for HMT Public Spending Statistics, PESA, and the OBR public finances databank.** The alternatives below do not justify filling those gaps with dates. The ONS calendar does announce **20 November 2026, 7:00am** for *Public sector finances, UK: October 2026* and its time series, marked **Confirmed**. That is an **ONS PSF release**, not an OBR databank publication appointment. The time is quoted as published, not converted using an assumed browser time zone.

This investigation strengthens a scoped “no exact date established in the checked official evidence” limitation; it does **not** prove that no announcement exists anywhere. It does not award Context L4. The [product specification](<../../product-spec.md#L50-L55>) permits an explicit no-announcement fallback, unlike a literal requirement for a scheduled update date in every section.

## Existing evidence read before requesting alternatives

- [Repository instructions](<../../../AGENTS.md>) and [product specification](<../../product-spec.md>).
- [Retained release calendar](<../../../sources/release-calendar.json>): `spending` and `history` have null next dates, checked 1 November 2026. HMT guidance names November, February and April without a day or explicit year; PESA annual frequency is not a scheduled 2027 date. Existing upcoming lookups use `filter_content_store_document_type=upcoming_statistics` and return zero results.
- [Income manifest](<../../../sources/income-manifest.json>) and [retained OBR data page](<../../../sources/income-release.txt>): databank vintage 28 October 2026; “around 2 working days” is cadence, not an exact next date. There is no `income` entry in the retained release calendar.
- [Prior independent section audit](<../context-w6/section-audit.md#L9-L25>) and [calendar refresh implementation](<../../../scripts/release_calendar.py>): byte integrity and section annotation coverage do not establish all-channel future schedules.

## Bounded alternatives and interpretation

| Family / actual official alternative | Observed evidence | Exact next date disposition |
|---|---|---|
| HMT [statistics announcements listing](<https://www.gov.uk/government/statistics/announcements?organisations%5B%5D=hm-treasury>) | Official redirects lead to the current research/statistics finder, preserving HMT and adding `content_store_document_type=upcoming_statistics`. Its retained response says **0 results**. [Readable extraction](<calendars/20261102T082331.814923Z/hmt-announcements.view.txt#L59-L74>); [redirect and final-response metadata](<calendars/20261102T082331.814923Z/hmt-announcements.metadata.json>). | No announcement returned by that dated listing; absence is bounded to this finder, not every HMT channel. |
| HMT [alternative announcement-format search API](<https://www.gov.uk/api/search.json?filter_format=statistics_announcement&filter_organisations=hm-treasury&count=100>) | **40 total, 40 returned**, not an empty result. Spending matches are “Public Spending Statistics – 2015/16”, “Public Spending Statistics – February Update”, and “Public Spending Statistics release: July 2017”; their search `public_timestamp` values are in 2016/2017. The returned search fields do not supply an exact future PSS/PESA release appointment. [Full retained API view](<calendars/20261102T082331.814923Z/hmt-announcements-api.view.txt>). | The older `statistics_announcement` format is a useful alternative to the empty upcoming filter, but is not itself a future-only calendar. Search indexing/public timestamps are not release dates. No future exact date established. |
| PESA [term search using announcement format](<https://www.gov.uk/api/search.json?filter_format=statistics_announcement&q=public%20expenditure%20statistical%20analyses&count=100>) | **3,804 total, first 100 returned**. The query is broad/relevance-based and includes unrelated departments and statistics. HMT spending matches in the returned subset are the same old titles above; it does not establish an exact next PESA date. [Retained view](<calendars/20261102T082331.814923Z/pesa-announcements-api.view.txt>). | **Not an exhaustive negative PESA search.** No pagination or broad discovery followed; the returned subset offers no exact date evidence. |
| HMT [PSS collection content API](<https://www.gov.uk/api/content/government/collections/national-statistics-release>) and [PESA collection content API](<https://www.gov.uk/api/content/government/collections/public-expenditure-statistical-analyses-pesa>) | Both responses are **byte-identical** to their corresponding baseline calendar snapshots. Collections list published releases, led by July 2026 / PESA 2026. [PSS view](<calendars/20261102T082331.814923Z/hmt-spending-collection.view.txt>); [PESA view](<calendars/20261102T082331.814923Z/hmt-pesa-collection.view.txt>). | No newly established next publication date. A past `publishing_scheduled_at` field is not the next update. Quarterly PSS timing must not be substituted for annual PESA Chapter 4. |
| OBR [data page](<https://obr.uk/data/>) | “We will release updated databases as soon as possible”; newest public finances databank shown as **28 October 2026**; “Updated around 2 working days after the monthly public finance release.” [Extracted evidence](<calendars/20261102T082331.814923Z/obr-data.view.txt#L47-L61>). | No exact next databank date. “As soon as possible” and “around 2 working days” are not appointments. Raw response hash differs from the retained production HTML; this calendar check does not establish a consumed numerical-data revision. |
| OBR [current-year databank listing](<https://obr.uk/public-finances-databank-2026-27/>) — linked from data page | “Each month we produce a public finances databank”; latest listed item is **Public finances databank – October 2026 EFO, 28 October 2026**. [Listing extraction](<calendars/20261102T082505.133006Z/obr-databanks-year.view.txt#L47-L69>). | Published-vintage corroboration, not an exact next date. Do not extrapolate the next month/day from the listing. |
| OBR [home/news listing](<https://obr.uk/>) | Recent news includes “October 2026 forecast timetable” and “Autumn 2026 forecast date announced”; featured EFO is already published **28 October 2026**. [Extracted listing](<calendars/20261102T082331.814923Z/obr-home.view.txt#L42-L84>). | No explicit future databank appointment in the inspected listing. An EFO timetable is a different publication, and an announcement headline is not an exact databank date. This was not an exhaustive OBR news/archive search. |
| OBR [monthly public-finances commentary listing](<https://obr.uk/monthly-public-finances-briefing/>) — linked from data page | Describes OBR **brief analysis on the same day** as Treasury/ONS monthly statistics, and points to ONS release dates. [Extracted explanation](<calendars/20261102T082505.133006Z/obr-monthly-listing.view.txt#L47-L60>). | Same-day **commentary** is not the **databank**, whose data page separately says around two working days. Do not transfer the ONS date to either an exact databank appointment or a guaranteed commentary event. |
| ONS [PSF keyword-filtered upcoming calendar](<https://www.ons.gov.uk/releasecalendar?keywords=public%20sector%20finances&release-type=type-upcoming>) | 39 keyword results; first page explicitly lists October 2026 PSF time series and bulletin at **20 November 2026 7:00am, Confirmed**. It also lists November 2026 PSF at **22 December 2026 7:00am**. [Exact retained date text](<calendars/20261102T082505.133006Z/ons-psf-keywords.view.txt#L114-L178>). | Exact dates are established **for the named ONS publications only**. They do not establish the OBR databank next date. No working-day arithmetic or cadence inference performed. |

### Complete HMT search date-field inspection (offline)

The HMT format-search response has `start=0`, `total=40`, and **40 result objects**; therefore this specific result set is complete without a second page (request `count=100`). Every returned record was inspected, not just matching titles. The only record-level date/time field is `public_timestamp`: all 40 range from **2016-05-26T14:47:14Z** to **2017-09-07T15:24:42Z**. Recursive date/time-field inspection also finds `organisations[].public_timestamp` and `expanded_organisations[].public_timestamp`, always **2026-10-28T15:09:46Z** — organisation metadata, not release appointments. No returned date field is future-valued relative to this 2 November 2026 capture. No `release_date`, `scheduled_publication`, or equivalent appointment field is present. This is complete inspection of the **40-record search response**, not a claim to have inspected the full linked announcement pages or every official calendar channel.

## Actual request errors and limitations

- **No HTTP or transport failures:** all **11 top-level GETs** returned final HTTP 200. The HMT announcements request traversed two official redirects (301 then 302), retained in its metadata. No requests were retried. No bodies reached the size limit.
- **Actual parameter error, retained rather than hidden:** the first [ONS request](<https://www.ons.gov.uk/releasecalendar?query=public%20sector%20finances&release-type=type-upcoming>) used `query=`, which the calendar ignored. It returned **405 unfiltered upcoming results**, page 1/41. The response is **not** evidence of an absent PSF announcement. Inspection of the [raw calendar form](<calendars/20261102T082331.814923Z/ons-psf-calendar.body#L488-L503>) established `name="keywords"`; one corrected request returned the relevant exact ONS dates. [Initial extraction](<calendars/20261102T082331.814923Z/ons-psf-calendar.view.txt#L73-L157>).
- The PESA term search's large result count is a **search-specificity/coverage limitation**, not a network error or a finding that no PESA announcement exists.
- Empty HMT upcoming results, old format-search records, and published-release collections cannot prove comprehensive absence of announcements. No polling or recurring/month-offset arithmetic was used. Genuine retrieval timestamps and HTTP `Date`/cache headers are observations, **not release dates**.
- Captured raw response bodies and hashes are separate evidence copies. No replacement of production provenance or next-release claims is performed here. General site navigation/cookie text remains in readable HTML extractions; those are conveniences, not replacements for raw bytes.

## Raw responses, timestamps, URLs and SHA-256

The [first batch report](<calendars/20261102T082331.814923Z/report.json>) records eight requests, UTC start/finish instants, requested/final URLs, HTTP status, response headers, redirect metadata, body byte counts, errors (`null` for these requests) and full SHA-256 values. The [second batch report](<calendars/20261102T082505.133006Z/report.json>) records the three bounded follow-ups. Per-request metadata duplicates these fields beside the raw body. Hashes below apply to the **raw final HTTP response body bytes**, not readable extraction files.

| Raw body | SHA-256 |
|---|---|
| [HMT announcements](<calendars/20261102T082331.814923Z/hmt-announcements.body>) | `471a95fa9fee36d1169d978b0871bd8388ce3e50f0dfc0c37839fd797dfc5050` |
| [HMT announcement-format API](<calendars/20261102T082331.814923Z/hmt-announcements-api.body>) | `0233a332681369db8f91a515b50cd35f05073681a437fb3317c03547becf377b` |
| [PESA announcement search API](<calendars/20261102T082331.814923Z/pesa-announcements-api.body>) | `4e8ebd4784305139f23bf61b4fabf06fd8be8a6771dc8d413f0a8f62ee5b8003` |
| [PSS collection API](<calendars/20261102T082331.814923Z/hmt-spending-collection.body>) | `3dccf60170db1f2133028f7137c081fd858bb23d59588db397a1caab9d6aa299` |
| [PESA collection API](<calendars/20261102T082331.814923Z/hmt-pesa-collection.body>) | `bab32764830a7a7e53d3faaf621f7494ce94b9be4f5e9b0737cf06dca8ad8dbd` |
| [OBR data](<calendars/20261102T082331.814923Z/obr-data.body>) | `150b6b9307cd6b164753f9e0f8163877d4e2c3a6653576544f121f7b7ba9be13` |
| [OBR home](<calendars/20261102T082331.814923Z/obr-home.body>) | `7510d326b0ed7c371c1cfa5960f6a72232a2c13698f21cde23cf55995359031b` |
| [ONS initial ignored-query response](<calendars/20261102T082331.814923Z/ons-psf-calendar.body>) | `d3af87d2eb251c657c603aff0fc4417d783505ec612cb95540605ebb5b80fd0a` |
| [ONS corrected keyword response](<calendars/20261102T082505.133006Z/ons-psf-keywords.body>) | `1d622ae6fdc67db41a4d2a86f50c5d08174032eb9e8cbf35d8c188fd9b5837d2` |
| [OBR current-year databanks](<calendars/20261102T082505.133006Z/obr-databanks-year.body>) | `0a8589c10fe3b069bc7858c76153fdd6bd5c7145868ecbbca0917a34278aa2ae` |
| [OBR commentary listing](<calendars/20261102T082505.133006Z/obr-monthly-listing.body>) | `69866569ba59f39dd0f5865fd0b3f1f87244d8f8bc422cc3216ea23fc255baab` |

## Reproduce the bounded capture

From the repository root, using only the Python standard library and the retained [standalone capture script](<capture_calendars.py>):

```sh
python3 docs/evidence/context-w7/capture_calendars.py
python3 docs/evidence/context-w7/capture_calendars.py --only ons-psf-keywords obr-databanks-year obr-monthly-listing
```

These are the actual commands used. Each run creates a new real-UTC-stamped directory without overwriting previous evidence; later responses may differ. Defaults are eight named GETs, at most four workers, a 25-second socket timeout and 4 MiB response-body limit; follow-up command makes three GETs. No automatic retries, full-source audit, external dependencies, release-date parsing/inference, or production refresh. HTTP error bodies would be retained with their actual status/hash; a transport exception has its real timestamp/message and null body/hash, never fabricated response bytes. After writing the report the CLI exits 1 if any record contains an error, truncation or JSON parse failure (otherwise 0). This exit-status safeguard was added during self-review without another network run; the retained 11 responses genuinely succeeded.

Offline integrity command, also executed successfully for the retained runs:

```sh
python3 - <<'PY'
from pathlib import Path
import hashlib, json
count = 0
for report in sorted(Path('docs/evidence/context-w7/calendars').glob('*/report.json')):
    for record in json.loads(report.read_text())['records']:
        assert record['status'] == 200 and record['error'] is None
        assert not record['truncated']
        body = report.parent / record['body_file']
        assert hashlib.sha256(body.read_bytes()).hexdigest() == record['sha256']
        count += 1
print(f'PASS: {count} raw response hashes verified; no errors/truncation')
PY
```

**Remaining:** an explicit publisher announcement identifying the next exact PSS date, next applicable PESA Chapter 4 update, and next OBR databank date. Maintain scoped no-announcement limitations until such evidence exists; ONS PSF, EFO, OBR commentary, cadence and retrieval timestamps are not substitutes.
