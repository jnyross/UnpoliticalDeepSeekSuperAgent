# Wave 8 — independent section/date audit

Baseline: `9864a10c5a5beb5d49f10a9eb19bcbd00d5d155b`; issue #56. Offline incremental review of the three sources added by merged #65/#67, not a repeat of the prior 22-source audit/calendar investigation. Read [AGENTS](../../../AGENTS.md), [section annotator](../../../scripts/section_dates.py#L100-L121), its [existing tests](../../../tests/test_section_dates.py), party manifests and retained source text. No UI, source-baseline, manifest or GitHub changes in this check.

## Actual scope and findings

| Addition | Retained evidence and supplemental comparison | Current party-card dates/notices |
| --- | --- | --- |
| Conservative costings | [Manifest](../../../sources/party-offers.json#L718-L735) retains publication **2024**, year precision only. Archive capture 11 June is not a publication day. [Table 2](../../../sources/conservative-costings-2024.txt#L65-L140) gives welfare savings £12,000 million in **2029-30**, following £4,000/8,000/10,000/11,000 million in 2025-26 through 2028-29; [additional notes](../../../sources/conservative-costings-2024.txt#L230-L240) specify nominal terms. This is an exact monetary equivalent of the selected £12 billion claim, with extra fiscal context. | [Conservative card](../../../site/parties.html#L8-L9): manifesto 2024 and RF analysis 2024-06-14; updates not supplied. “Annual saving; this passage gives no fiscal year” describes its cited manifesto passage, not all retained documents. Supplement is linked by [audit locator](../../../sources/party-figure-locators.json#L2-L22), **not** card `evidence`; its date and any future notice are therefore not included in the card. |
| LibDem costings | [Manifest](../../../sources/party-offers.json#L737-L752) retains publication **2024**, no exact day. [Revenue table](../../../sources/libdem-costings-2024.txt#L116-L151) has **£1,420 million in 2028-29** for share buybacks. The [selected release](../../../sources/libdem-buyback-2024.txt#L58-L59) says **around £1.4bn a year**. These differ in exact amount and specificity, though an approximate £1.4bn is not thereby false. Do not silently turn 1,420 into 1,400 or transfer the supplemental fiscal year to the release. | [LibDem card](../../../site/parties.html#L12-L13): manifesto 2024, release 2024-05-31, Full Fact 2024-06-06; updates not supplied. “The release gives no fiscal year” remains specifically true. Existing saved release notice appears here only. Costings PDF is an [unmatched supplemental audit locator](../../../sources/party-figure-locators.json#L50-L63), not card evidence; it has no card date/notice destination. |
| DE childcare | [Official announcement](../../../sources/de-childcare-2024.txt#L37-L43) explicitly published **23 May 2024**, £25m for **2024/25**, after Executive approval. It is programme context, not an independent assessment or the cost of separate new Westminster pledges. | [DUP card](../../../site/parties.html#L9-L10) includes manifesto 2024 plus **2024-05-23**, and its Year field correctly says 2024-25 package, not recurring annual promise. The [programme evidence reference](../../../sources/party-offers.json#L304-L333) brings `party-evidence-de-childcare-2024` into the DUP-only notice scope. Existing regression explicitly checks this. |

All three sources are registered as [retained-URL snapshot checks](../../../config/release-sources.json#L218-L244). Registration permits detection/persistence, **not** automatic display on every party card: [annotation](../../../scripts/section_dates.py#L103-L119) follows the manifesto plus each card's `evidence` values, not supplemental audit locators or every `evidence_sources` entry. Thus the two costings PDFs are monitored supplements without a UI notice destination. This is a real scope limitation, not evidence of an incorrectly dated displayed source. If supplemental evidence becomes card evidence later, explicitly map its notice/date scope and distinguish its fiscal year; do not broadcast every supplement to every card.

## Calendar applicability and disposition

**No genuinely new applicable next-release-calendar evidence in these three historical documents.** Conservative forecast columns, “next April,” policy commencement dates and the first fiscal event refer to the 2024 election scenario, not an announcement of the next statistical publication. LibDem's 2028-29 table and “next Parliament” investment period are policy horizons. DE's 2024/25 package and intention for a longer-term strategy announce no next publication date. None supplies a current dated next release or justifies changing the fixed-snapshot schedule message. Publication date, save/detection date, fiscal data period and future release date must remain distinct.

**Necessary fix from this offline comparison: none to displayed dates or current card notice plumbing.** Preserve supplemental mismatch and scope limitations above. The parent separately owns live-three-source reconciliation, any warranted retained notice publication, and deployment verification; offline results do not establish present URL health, current policy or live deployment state. No people evidence or new dates have been inferred.

## Commands and results

Existing regressions only; no source refresh, broad audit, calendar search or rebuild performed by this check:

```sh
python3 -m unittest discover -s tests -p test_section_dates.py
# 10 tests; one error: system interpreter lacks cmudict. Following && command did not run.
.venv/bin/python -m unittest discover -s tests -p test_section_dates.py
# 10 tests OK
.venv/bin/python -m unittest discover -s tests -p test_party_audit.py
# 16 tests OK, including exact Conservative supplemental equivalence/fiscal-column
# checks and LibDem 1420-not-1400 mismatch preservation.
PYTHONPATH=tests .venv/bin/python -m unittest \
  test_discover.SnapshotTests.test_independent_evidence_collection_reuses_snapshot_safety \
  test_discover.InventoryTests.test_every_retained_party_source_and_roster_is_registered_once
# 2 tests OK; mocked/offline retained-evidence adapter and inventory registration.
```

The section tests cover all section stamps, source-scoped revision notices, DUP programme dates/notice locality and grade gate. Passing tests establish saved-data behavior, not successful live discovery or human review.
