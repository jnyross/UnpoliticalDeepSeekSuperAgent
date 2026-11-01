import assert from 'node:assert/strict';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';

test('unknown page selection cannot pass an empty suite', () => {
  const result = spawnSync(process.execPath, ['tests/browser-runner.mjs'], {
    env: { ...process.env, CHECK_PAGE: 'not-a-page.html' }, encoding: 'utf8',
  });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /No matching HTML pages/);
});

test('deadline fails every affected shard and retains an incomplete manifest', async () => {
  const output = await mkdtemp(path.join(tmpdir(), 'browser-deadline-'));
  const result = spawnSync(process.execPath, ['tests/browser-runner.mjs'], {
    env: { ...process.env, CHECK_PAGE: 'index.html', BROWSER_TIMEOUT_MS: '1', EVIDENCE_DIR: output, EVIDENCE_LABEL: 'deadline' },
    encoding: 'utf8', timeout: 10000,
  });
  assert.notEqual(result.status, 0);
  const report = JSON.parse(await readFile(path.join(output, 'deadline-suite.json'), 'utf8'));
  assert.equal(report.passed, false);
  assert.equal(report.completed, false);
  assert.equal(report.expected.length, 2);
  assert.equal(report.results.length, 2);
  assert.ok(report.results.every(result => result.status === 'failed' && result.timedOut));
});
