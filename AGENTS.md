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
- **Work around blockers; do not discard a whole level.** Split each unmet check
  into work that can be completed now and the precise evidence still unavailable.
  Build the useful parts, find verified alternative sources or methods, and test
  them. A blocked clause does not block other clauses or other dimensions.
  Impartiality 4, Comprehension 4 and Accessibility 4 still require real people,
  and Freshness 4 still requires a real year of history: do not claim those points
  from automated substitutes. But build useful prerequisites: the public corrections
  log, automated checks and reproducible testing materials, and timestamped release
  and deployment measurements. Label these finite issues `workaround` in addition
  to the dimension/next-level labels, quote the relevant requirement, and state
  explicitly that completing the issue does not award the gated level.
- **Owner facts are a clause, not a blanket stop.** For Openness, verify current
  repository visibility and reuse this public repository's issue tracker as a working
  error-reporting route. Publish only independently established operator/funding
  information. Build the methods, contact route and disclosure page even if an exact
  funding statement remains unavailable; label that residue precisely and do not
  invent a person, funding source, permission or historical event. File a separate
  `needs-owner` issue only for the genuinely missing fact after doing the available
  work. A repository already made public is not still waiting for permission.
- **Finish a plan, not an acknowledgment.** For every dimension, report the actual
  next check, verified blocker, alternative tried, useful work completed and remaining
  work. Never use only "needs people/history/owner facts" as the disposition.
  Search open AND closed issues and inspect merged evidence before opening anything:
  do not keep recreating completed workarounds. At most one active buildable issue
  per dimension per wave. A `needs-owner` issue may coexist as a record of the residue.
  A workaround's acceptance test is its specific useful result, not a false promise
  that it passes the entire rubric level.

After filing the wave's issues, include this machine-readable block in your final
tracking-issue comment (not in the initial acknowledgment). Use the wave and scored
commit from the request/scorecard, and include ALL eight dimension slugs:

```text
<!-- rubric-plan
{"wave": 4, "sha": "FULL_SCORED_COMMIT", "dimensions": {
  "accuracy": {"current_level": 4, "status": "complete"},
  "context": {"current_level": 1, "status": "issue", "issue": 31},
  "impartiality": {"current_level": 3, "status": "workaround", "issue": 33, "evidence": "Corrections log is absent at PATH", "remaining": "Two real reviewers are still required"}
}}
-->
```

The abbreviated example above must be expanded to all eight dimensions; do not copy
its example IDs or levels. `issue` references a real `rubric`, `dim:SLUG`, `level:N`
issue. `workaround` also requires its `workaround` label plus nonempty `evidence` and
`remaining`. Once all useful automated parts of a people/history-gated level are
complete, use `gated` with `evidence`, `remaining` and `completed_subparts` (a list of
specific checked results). For an owner residue, use `blocked` with an open
`needs-owner` issue, `missing_fact`, `evidence` and `completed_subparts`. `complete`
means the dimension is already at level 4. An empty completed-subparts list must be
explained by concrete evidence that no useful part can be done; it is not a shortcut.
- **Never claim, simulate or write up people evidence** (user tests, reviewer reads,
  manual keyboard or screen-reader checks), and never present a simulation as one.

Dimension slugs: `accuracy`, `impartiality`, `comprehension`, `context`, `coverage`,
`freshness`, `access`, `openness`.
