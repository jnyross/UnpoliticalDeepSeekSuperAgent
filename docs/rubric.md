<!-- Copied unchanged (dimensions and levels) from jnyross/un-political@8eb81d6c7075e4b4e89e4aa1cc398fbae12eb713 docs/rubric.md, where the product was called Un-political. Only the Scores section below is new. -->

# What "working well" means

Un-political is working well when anyone in the UK can open it, understand where public
money goes and what each party proposes, check every number against the official source,
and find no sign of which side the site is on.

This rubric scores the product against that goal. There are eight dimensions, each scored
0 to 4. Every level is a check that someone else can run and get the same answer. A level
counts only if every level below it is also met.

Maximum score: 32. A score is only valid with the date, the commit and the evidence for
each line.

## 1. Accuracy and traceability

| Level | Check |
|---|---|
| 0 | Numbers are typed by hand or have no stated source. |
| 1 | Every page names its source publication. |
| 2 | Every figure shown resolves to a source file, table, row label and year, and the raw source files are kept in the repo with their download URL, date and SHA-256 hash. |
| 3 | The build fails if the data does not reconcile: parts add up to their published totals within rounding, cross-table totals agree, and real-terms figures equal nominal figures in the base year. |
| 4 | Each figure on the page is regenerated from the raw files by one command, and a check confirms the published page matches the regenerated output exactly. |

## 2. Impartiality

| Level | Check |
|---|---|
| 0 | The site contains opinion, evaluative adjectives or party-coloured framing. |
| 1 | A published list of banned evaluative words ("massive", "slashed", "soaring", "savage", "generous", "reckless" and others) is checked automatically and none appear in page copy. |
| 2 | Charts never use party colours, and every year axis is shown without highlighting which party was in government unless every government is shown the same way. |
| 3 | Every party's offer is shown using the same template, with the same fields in the same order, and the same length limits. Judgements on whether a policy is good appear only as attributed quotes from named independent bodies (IFS, OBR, Resolution Foundation, Full Fact, NAO), with links. |
| 4 | A public corrections log exists, and a reviewer from each of at least two opposing political leanings has read the site and their comments, and the site's responses, are published. |

## 3. Plain-language comprehension

A fixed set of test questions, each with an answer that comes straight from the data.
Comparisons step back from the latest year in tens of years (ten years ago, twenty years ago, and so on back
to 1945-46), never chosen by hand:

1. What does the government spend the most on?
2. Out of every £100 of spending on services, how much goes on health?
3. How much was spent on paying interest on government debt in 2025-26?
4. Has health spending gone up or down in the last ten years once inflation is taken into account?
5. Is total spending a bigger or smaller share of the economy than ten years ago?
6. How much goes on pensions paid in old age, compared with defence?
7. Which numbers on the page are forecasts rather than actual spending?
8. Where can I check this number myself?

| Level | Check |
|---|---|
| 0 | The questions cannot be answered from the site. |
| 1 | All eight answers are on the site. |
| 2 | Each answer is reachable in two clicks or fewer from the home page, without scrolling past more than one screen of unrelated content. |
| 3 | Page copy scores at a reading age of 12 or lower (Flesch-Kincaid grade 7 or lower), checked automatically. |
| 4 | At least five people who do not follow politics answer at least seven of the eight correctly in under five minutes, and the results are recorded. |

## 4. Honest context

| Level | Check |
|---|---|
| 0 | Money figures appear with no adjustment or context. |
| 1 | Every money-over-time chart can show cash, inflation-adjusted and share-of-the-economy views, and says which one is shown. |
| 2 | Forecasts look different from actual figures (for example, dashed lines) and are labelled as forecasts with their source and date. |
| 3 | Breaks in a data series and definitions that differ from common use (for example, how defence spending is counted differently from NATO's measure) are flagged on the chart they affect, not only in a footnote. |
| 4 | Each section shows the date of the data and the next scheduled update, and the site never shows data that has since been revised without saying so. |

## 5. Coverage

| Level | Check |
|---|---|
| 0 | Nothing published. |
| 1 | Where the money goes in the latest year. |
| 2 | Plus the history of spending, overall and by area, over at least 20 years. |
| 3 | Plus where the money comes from (taxes and borrowing) and how much debt the country has. |
| 4 | Plus every party with MPs in the House of Commons, shown in the same template, with independent assessments of their costed plans. |

## 6. Freshness

| Level | Check |
|---|---|
| 0 | No data date shown. |
| 1 | Every page shows the publication and date of its data. |
| 2 | Refreshing the data for a new release is one command, documented in the README. |
| 3 | A scheduled check notices new releases of each source and opens an update for review. |
| 4 | Over the past year, every update went live within four weeks of its source being published. |

## 7. Accessibility and reach

| Level | Check |
|---|---|
| 0 | The content needs JavaScript or is unusable on a phone. |
| 1 | Every chart has a data table next to it, and the full content works with JavaScript turned off. |
| 2 | The page works on a 360-pixel-wide screen and each page is under 500 KB. |
| 3 | An automated WCAG 2.2 AA check passes with no errors, including colour contrast. |
| 4 | Checked by hand with a screen reader and keyboard only, with the results recorded. |

## 8. Openness

| Level | Check |
|---|---|
| 0 | No information on how the site works or who runs it. |
| 1 | A methods page explains where the data comes from and how it is processed, and the required Open Government Licence attribution appears on every page. |
| 2 | All data behind the site can be downloaded in an open format. |
| 3 | The page states who runs the site, how it is funded and how to report an error. |
| 4 | The code and data pipeline are public, and anyone can rebuild the site from them. |

## Scores

Every score is posted as a scorecard comment on the pinned **Rubric loop** issue by an
independent scorer that does not build the site. Each scorecard gives the date, the commit,
the live URL, the level and evidence for every dimension, and the total. Scorecards are
never edited or deleted; a new score is a new comment.

A level that needs people (Impartiality 4, Comprehension 4, Accessibility 4) or a year of
history (Freshness 4) is never scored as met without that evidence. The repository owner
has decided not to run people checks, so the highest honest score is 28/32.
