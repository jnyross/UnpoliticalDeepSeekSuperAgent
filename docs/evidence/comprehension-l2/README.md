# Direct answer navigation — issue 55

These are actual automated Chromium captures and checks, not people-test evidence
or an independently awarded rubric level.

- **Before:** `693386bc035b0a3489718bee9712922748c181b7`.
- **After application:** `d9c69d6a40614d04c03d4e2b063105dfc0e780fc`.
  Subsequent ticket commits change tests, documentation and evidence only.
- Matching scenario: home page, initial scroll position, light theme, Chromium,
  360×800 mobile and 1280×900 desktop. No expanded controls or mockups.

| Viewport | Before | After |
| --- | --- | --- |
| 360×800 | [Before](before-index-html-mobile-viewport.png) | [After](index.html/mobile/after-index-html-mobile-viewport.png) |
| 1280×900 | [Before](before-index-html-desktop-viewport.png) | [After](index.html/desktop/after-index-html-desktop-viewport.png) |

## Reproduce

```sh
.venv/bin/python scripts/build.py --check
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python scripts/check.py --self-test
.venv/bin/python scripts/check_history.py --self-test
.venv/bin/python scripts/manual_access.py
node --test tests/*.test.mjs
EVIDENCE_DIR=/tmp/answer-navigation npm run test:browser
# Focus the answer-navigation checks, or repeat against production:
CHECK_PAGE=index.html EVIDENCE_DIR=/tmp/answers npm run test:browser
LIVE_URL=https://unpoliticaldeepseeksuperagent.vercel.app CHECK_PAGE=index.html EVIDENCE_DIR=/tmp/live-answers npm run test:browser
```

Each home-page browser report includes `answerNavigation`: eight genuine native
clicks from fresh home-page visits, with JavaScript on and off at both sizes. It
records initial link geometry, required initial scroll, native fragment URL, unique
target and actual answer text/geometry. Each answer paragraph must fit in the
landing viewport without additional scrolling; each question uses one activation.
A second click from the debt-interest amount must reveal its exact source row and
workbook cell within the viewport. Source-data checks independently verify values.

The revision-bound comprehension kit and manual-access inventory were regenerated
because the home HTML changed; their records remain unperformed. Existing factual
figures, provenance, scope notes and static output checks are preserved.
