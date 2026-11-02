// Run from repository root after the full suite:
// node docs/evidence/openness/summarize-browser.mjs /tmp/openness-browser SOURCE_COMMIT
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
const [directory = '/tmp/openness-browser', sourceRevision] = process.argv.slice(2);
assert.ok(sourceRevision, 'Supply the committed source revision to verify tested HTML identities');
const suite = JSON.parse(await readFile(`${directory}/after-suite.json`, 'utf8'));
assert.equal(suite.passed, true);
assert.equal(suite.completed, true);
assert.equal(suite.results.length, suite.discoveredPages.length * 2);
const report = {
  command: `EVIDENCE_DIR=${directory} npm run test:browser`, sourceRevision,
  contentIdentity: 'Each tested working-tree HTML SHA-256 was independently compared with the named sourceRevision git blob.',
  startedAt: suite.startedAt, finishedAt: suite.finishedAt,
  completed: suite.completed, passed: suite.passed, exitCode: 0,
  pageViewportChecks: suite.results.length, results: [],
};
for (const result of suite.results) {
  const worker = JSON.parse(await readFile(`${directory}/${result.evidence}`, 'utf8'));
  assert.equal(result.status, 'passed');
  const page = worker.pages[0], viewport = page.viewports[0];
  assert.equal(page.sha256, createHash('sha256').update(execFileSync('git', ['show', `${sourceRevision}:site/${result.page}`])).digest('hex'));
  assert.equal(viewport.noJavaScriptContentMatches, true);
  assert.ok(viewport.noJavaScriptDimensions.document <= viewport.viewport.width);
  assert.ok(viewport.noJavaScriptDimensions.body <= viewport.viewport.width);
  for (const state of viewport.states) {
    assert.equal(state.completed, true);
    assert.equal(state.axeCompleted, true);
    assert.equal(state.contrastCompleted, true);
    assert.deepEqual(state.violations, []);
  }
  report.results.push({
    page: result.page, viewport: viewport.viewport, status: result.status,
    sha256: page.sha256, bytes: page.bytes,
    noJavaScriptContentMatches: viewport.noJavaScriptContentMatches,
    noJavaScriptDimensions: viewport.noJavaScriptDimensions,
    states: viewport.states.map(state => ({
      name: state.name, completed: state.completed, axeCompleted: state.axeCompleted,
      contrastCompleted: state.contrastCompleted, violations: state.violations,
      incompleteCount: state.incomplete.length, dimensions: state.dimensions,
    })),
  });
}
await writeFile('docs/evidence/openness/browser-summary.json', JSON.stringify(report, null, 2) + '\n');
console.log(`Saved compact summary: ${report.pageViewportChecks} checks, ${report.results.reduce((n, r) => n + r.states.length, 0)} states, all passed; completed ${report.finishedAt}`);
