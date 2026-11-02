# Independent bounded DE follow-up and matched captures

Requested separately by the parent after the [offline section audit](section-audit.md). This is automated source/browser evidence, **not** human review, manual accessibility testing or deployment verification.

## One independent DE request

Command:

```sh
.venv/bin/python docs/evidence/context-w8/independent-de-check.py
```

[Reproduction script](independent-de-check.py) made one DE request, no retry and no archive request. [Metadata](independent-de-check.json) records URL, response headers, UTC start/completion and SHA-256: HTTP 200, **2026-11-02T10:10:05.984310+00:00** to **10:10:06.093627+00:00**. [Raw response](independent-de.raw.html.txt) SHA-256 `26f83f3cdfaa7887b7e0372ff923e813a18e2b0065f9ad2c9be5c26f3efda421` differs from retained baseline `23c4be542a61206e7dafc01b05a2ff7fffde8374c8a824641662275a12e645cb`.

However, [visible extraction](independent-de.visible.txt) using the repository's `html-blocks-v1` converter has **exactly the same bytes/hash** as baseline visible extraction: `44f9a22e36c841667ab90dc73f7670c4cfd3d36dc391d72e207ad57732703c1b`. The [visible diff](independent-de.visible.diff.txt) is empty. Both retained and observed text contain the exact programme quote (amount and 2024/25 period), Executive-approval quote and “Date published: 23 May 2024”. **No changed consumed claim, publication day or next release date is demonstrated.** A conservative raw-byte revision notice is consistent with the discovery contract; do not describe it as a proven fiscal/data correction, promote HTTP Last-Modified to publication date, or silently refresh source baselines. Extraction equality does not prove identical HTML behavior/styles or all non-text content.

## Matched actual-page captures

Baseline was copied from the scored checkout into `/tmp/context-w8-before-site` **before** the parent's rebuild. [Capture script](capture-dup.mjs) uses headless Chromium, JavaScript disabled, light scheme, device scale 1, the same DUP article (`data-party-id=7`) scrolled to its start, and exact 360×800 / 1280×900 viewports:

```sh
node docs/evidence/context-w8/capture-dup.mjs before /tmp/context-w8-before-site
node docs/evidence/context-w8/capture-dup.mjs after site
```

For independent reproduction, first materialize `site/` from commit `9864a10c5a5beb5d49f10a9eb19bcbd00d5d155b` into a separate baseline directory and pass that directory as the `before` root; never replace the current saved sources.

| View | Before | After |
| --- | --- | --- |
| Mobile 360×800 | [DUP before](before/dup-360x800.png) | [DUP after](after/dup-360x800.png) |
| Desktop 1280×900 | [DUP before](before/dup-1280x900.png) | [DUP after](after/dup-1280x900.png) |

[Before metadata](before/capture.json) and [after metadata](after/capture.json) retain actual section text, article bounds, notice count and all party-card notice destinations. Assertions require zero DUP notices before and exactly one after; only LibDem 17 has a notice before and only DUP 7 plus LibDem 17 after. The new DUP notice link must be the DE source URL. Both viewport states must have no horizontal document overflow. The data period/publication text is unchanged; the new warning is visible near the top of the matched DUP section. These are local saved-site captures, not proof of the deployed site.
