# Working in this repository

This repository builds the product in [`docs/product-spec.md`](docs/product-spec.md)
from scratch. It is scored against [`docs/rubric.md`](docs/rubric.md). The work is done by
the dsh-superagent agent (`jnyross-agent`) on behalf of `jnyross`. No person reviews pull
requests: make reasonable decisions within the spec and rubric, record them in the PR,
and finish.

## The site

- The site is static. Generated pages and data live in `site/` and are committed.
  Vercel deploys `site/` on every merge to `main` (see `vercel.json`); there is no build
  step on Vercel.
- One documented command rebuilds data and pages from the official sources.
- Core content works without JavaScript. Each HTML page is under 500 KB and works at
  360 px wide. Every page carries Open Government Licence attribution.
- Keep `main` green: add checks to CI as the rubric asks for them, and run them before
  you merge.

## The rubric loop

The pinned issue labelled `rubric-loop` is the loop's tracking issue.

- **Scorecards.** An independent scorer, not you, scores each wave. Its scorecards are
  posted on the tracking issue as comments that contain `<!-- rubric-scorecard -->` and a
  JSON block with the level met for each dimension. Never edit or post scorecards.
- **Planning a wave.** When you are asked on the tracking issue to plan the next wave,
  read the newest scorecard. For each dimension, its next level is the lowest level not
  met (the rubric is cumulative). If that level is one an agent can meet and no open
  issue has its labels, open one issue for it:
  - Title: `[<Dimension> L<n>] <short goal>`
  - Labels: `rubric`, `dim:<slug>`, `level:<n>`
  - Body: the rubric check for that level, quoted exactly, as the acceptance test; the
    scorecard's reason it is not met; anything the builder must know; and
    `Done when: the quoted check passes on the deployed site, with the evidence in the PR.`
  - At most one issue per dimension per wave. Do not build anything in the planning
    ticket. Reply on the tracking issue with the issues you opened, or say that no level
    an agent can meet is left.
  - **First wave:** if the repository has no data pipeline yet, open exactly one issue
    instead, `[Foundation] Static pipeline, first page and checks`, labelled `rubric`
    and `foundation`, that sets up the pipeline, the first real page, CI and the README
    rebuild command. Parallel issues on an empty repository collide.
- **Building an issue.** One PR per issue, with `Closes #<issue>` in the description and
  the evidence (commands and their results) in the PR. Merge it yourself when it is ready.
- **Levels agents never file or claim.** Impartiality 4, Comprehension 4 and
  Accessibility 4 need people; the owner has decided not to run people checks.
  Freshness 4 needs a real year of history. Openness 3 (who runs the site, how it is
  funded, a public error-reporting route) and Openness 4 (a public repository) need
  facts or decisions from the owner: label any such issue `needs-owner` and never
  invent the facts.
- **Never claim, simulate or write up people evidence** (user tests, reviewer reads,
  manual keyboard or screen-reader checks), and never present a simulation as one.

Dimension slugs: `accuracy`, `impartiality`, `comprehension`, `context`, `coverage`,
`freshness`, `access`, `openness`.
