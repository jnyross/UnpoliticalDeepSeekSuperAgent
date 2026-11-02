// Run from repository root after npm ci. No production files are modified.
// Baseline: node docs/evidence/openness/capture-footer.mjs before <git-sha>
// Working tree: node docs/evidence/openness/capture-footer.mjs after
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { chromium } from 'playwright';
const [label = 'after', revision] = process.argv.slice(2);
assert.match(label, /^[a-z0-9-]+$/);
const output = 'docs/evidence/openness';
const html = revision ? execFileSync('git', ['show', `${revision}:site/index.html`]) : await readFile('site/index.html');
await mkdir(output, { recursive: true });
const server = createServer((request, response) => {
  response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  response.end(html);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
let browser;
try {
  browser = await chromium.launch({ headless: true });
  const report = {
    capturedAt: new Date().toISOString(),
    baselineSha: revision || null,
    baseRevision: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
    htmlSha256: createHash('sha256').update(html).digest('hex'),
    source: revision ? `git show ${revision}:site/index.html` : 'working-tree site/index.html',
    javaScriptEnabled: false,
    browserVersion: browser.version(),
    scenario: 'Footer scrolled into view; exact viewport screenshot, not full-page',
    screenshots: [],
  };
  for (const viewport of [{ name: 'mobile', width: 360, height: 800 }, { name: 'desktop', width: 1280, height: 900 }]) {
    const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, javaScriptEnabled: false });
    const page = await context.newPage();
    await page.goto(`http://127.0.0.1:${server.address().port}/`, { waitUntil: 'networkidle' });
    await page.locator('footer').scrollIntoViewIfNeeded();
    const screenshot = `${output}/${label}-${viewport.name}.png`;
    await page.screenshot({ path: screenshot, fullPage: false });
    report.screenshots.push({ viewport, screenshot, footerText: await page.locator('footer').innerText() });
    await context.close();
  }
  await writeFile(`${output}/${label}-baseline.json`, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally {
  await browser?.close();
  server.close();
}
