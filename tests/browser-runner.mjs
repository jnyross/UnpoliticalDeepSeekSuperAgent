import assert from 'node:assert/strict';
import { readdir, mkdir, readFile, writeFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import path from 'node:path';

// Each page/viewport gets a fresh browser and a hard process-group deadline.
// A timed-out renderer cannot leave a partial report masquerading as a pass.
const root = path.resolve(process.env.SITE_DIR || 'site');
const output = path.resolve(process.env.EVIDENCE_DIR || 'test-results/browser');
const label = process.env.EVIDENCE_LABEL || 'after';
assert.match(label, /^[a-z0-9-]+$/);
async function pages(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  return (await Promise.all(entries.map(entry => entry.isDirectory() ? pages(path.join(dir, entry.name))
    : entry.name.endsWith('.html') ? [path.relative(root, path.join(dir, entry.name))] : []))).flat().sort();
}
const allPages = await pages(root);
const selected = process.env.CHECK_PAGE ? allPages.filter(page => page === process.env.CHECK_PAGE) : allPages;
assert.ok(selected.length, 'No matching HTML pages');
const timeoutMs = Number(process.env.BROWSER_TIMEOUT_MS || 300000);
assert.ok(Number.isSafeInteger(timeoutMs) && timeoutMs > 0, 'Invalid deadline');
await mkdir(output, { recursive: true });
const reportPath = path.join(output, `${label}-suite.json`);
const report = { startedAt: new Date().toISOString(), target: process.env.LIVE_URL || 'local-generated-output',
  timeoutMs, discoveredPages: allPages, selectedPages: selected, completed: false, passed: false,
  expected: selected.flatMap(page => ['mobile', 'desktop'].map(viewport => ({ page, viewport }))), results: [] };
const save = () => writeFile(reportPath, JSON.stringify(report, null, 2) + '\n');
await save();
for (const task of report.expected) {
  const dir = path.join(output, task.page.replaceAll('/', '_'), task.viewport);
  await mkdir(dir, { recursive: true });
  const result = { ...task, startedAt: new Date().toISOString(), status: 'running' };
  report.results.push(result);
  await save();
  const outcome = await new Promise(resolve => {
    const child = spawn(process.execPath, ['tests/browser.mjs', ...process.argv.slice(2)], {
      env: { ...process.env, CHECK_PAGE: task.page, CHECK_VIEWPORT: task.viewport, EVIDENCE_DIR: dir },
      stdio: 'inherit', detached: true,
    });
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; process.kill(-child.pid, 'SIGKILL'); }, timeoutMs);
    child.once('error', error => { clearTimeout(timer); resolve({ error: error.message }); });
    child.once('exit', (code, signal) => { clearTimeout(timer); resolve({ code, signal, timedOut }); });
  });
  Object.assign(result, outcome, { finishedAt: new Date().toISOString(), status: 'failed' });
  try {
    assert.equal(outcome.code, 0, `Worker failed: ${JSON.stringify(outcome)}`);
    const worker = JSON.parse(await readFile(path.join(dir, `${label}-browser-report.json`), 'utf8'));
    assert.equal(worker.completed, true);
    assert.equal(worker.passed, true);
    assert.equal(worker.pages.length, 1);
    assert.equal(worker.pages[0].path, task.page);
    assert.equal(worker.pages[0].viewports.length, 1);
    const viewport = worker.pages[0].viewports[0];
    assert.equal(viewport.viewport.name, task.viewport);
    assert.equal(viewport.completed, true);
    if (!process.argv.includes('--capture-only')) {
      assert.ok(viewport.states.length > 0);
      assert.deepEqual(viewport.states.map(state => state.name), viewport.expectedStates);
      for (const state of viewport.states) {
        assert.equal(state.completed, true);
        assert.equal(state.contrastCompleted, true);
        assert.deepEqual(state.violations, []);
      }
    }
    result.status = 'passed';
    result.evidence = path.relative(output, path.join(dir, `${label}-browser-report.json`));
  } catch (error) { result.error = error.message; }
  await save();
}
report.completed = report.results.length === report.expected.length && report.results.every(result => result.status === 'passed');
report.passed = report.completed;
report.finishedAt = new Date().toISOString();
await save();
assert.ok(report.passed, `Incomplete or failed browser suite; see ${reportPath}`);
console.log(`Complete: ${report.results.length} page/viewport checks; ${reportPath}`);
