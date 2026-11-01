# UnpoliticalDeepSeekSuperAgent

## Purpose

This repository is worked on by the dsh-superagent agent (jnyross-agent) on behalf of jnyross.

## Asking the agent

To request work, post a new comment on an issue with `@jnyross-agent <request>`; editing an existing comment does not trigger a request. Only allowed accounts can ask the agent for work. The agent opens a pull request and merges it itself; the issue closes when the pull request merges.

## What this repository builds

[`docs/product-spec.md`](docs/product-spec.md) describes the product, built from scratch.
[`docs/rubric.md`](docs/rubric.md) is how it is scored. [`AGENTS.md`](AGENTS.md) has the rules
the agent works by, including the rubric loop: an independent scorer scores each wave on the
pinned **Rubric loop** issue, the agent files one issue per next rubric level, builds and
merges them, and the loop repeats. `site/` is deployed by Vercel on every merge to `main`.

