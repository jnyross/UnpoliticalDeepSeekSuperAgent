import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile, readdir, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import { checkSVGContrast } from './svg-contrast.mjs';

const root = path.resolve(process.env.SITE_DIR || 'site');
const label = process.env.EVIDENCE_LABEL || 'after';
assert.match(label, /^[a-z0-9-]+$/);
const captureOnly = process.argv.includes('--capture-only');
const output = path.resolve(process.env.EVIDENCE_DIR || 'docs/evidence');
await mkdir(output, { recursive: true });
async function htmlFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = await Promise.all(entries.map(entry => entry.isDirectory()
    ? htmlFiles(path.join(dir, entry.name))
    : entry.name.endsWith('.html') ? [path.join(dir, entry.name)] : []));
  return files.flat().sort();
}
const allFiles = await htmlFiles(root);
const files = process.env.CHECK_PAGE ? allFiles.filter(file => path.relative(root, file) === process.env.CHECK_PAGE) : allFiles;
const viewports = [{ name: 'mobile', width: 360, height: 800 }, { name: 'desktop', width: 1280, height: 900 }]
  .filter(viewport => !process.env.CHECK_VIEWPORT || viewport.name === process.env.CHECK_VIEWPORT);
assert.ok(viewports.length, 'Unknown CHECK_VIEWPORT');
assert.ok(files.length, 'No HTML pages found');
const server = createServer(async (request, response) => {
  try {
    let pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    if (pathname.endsWith('/')) pathname += 'index.html';
    const filename = path.resolve(root, '.' + pathname);
    if (!filename.startsWith(root + path.sep)) throw new Error('Outside site');
    const content = await readFile(filename);
    const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json', '.csv': 'text/csv', '.svg': 'image/svg+xml', '.png': 'image/png' };
    response.writeHead(200, { 'Content-Type': types[path.extname(filename)] || 'application/octet-stream' });
    response.end(content);
  } catch {
    response.writeHead(404); response.end('Not found');
  }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const baseURL = process.env.LIVE_URL || `http://127.0.0.1:${server.address().port}`;
const report = {
  capturedAt: new Date().toISOString(),
  ...(process.env.EVIDENCE_REVISION
    ? { revision: process.env.EVIDENCE_REVISION }
    : { baseRevision: execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(), contentIdentity: 'Exact tested working-tree HTML is identified by pages[].sha256, not by baseRevision.' }),
  mode: captureOnly ? 'baseline-capture-only' : 'automated-checks',
  browser: 'Chromium',
  target: process.env.LIVE_URL || 'local-generated-output',
  startedAt: new Date().toISOString(),
  completed: false,
  pages: [],
};
let browser;
try {
  browser = await chromium.launch();
  report.browserVersion = browser.version();
  for (const filename of files) {
    const relative = path.relative(root, filename).split(path.sep).join('/');
    const bytes = await readFile(filename);
    const pageReport = { path: relative, bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex'), viewports: [] };
    report.pages.push(pageReport);
    if (!captureOnly) assert.ok(bytes.length < 500000, `${relative} must be below 500 KB`);
    for (const viewport of viewports) {
      const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      const response = await page.goto(`${baseURL}/${relative}`, { waitUntil: 'networkidle' });
      assert.equal(response.status(), 200);
      if (process.env.LIVE_URL) assert.equal(createHash('sha256').update(await response.body()).digest('hex'), pageReport.sha256, `${relative}: deployed HTML differs from tested local output`);
      const screenshot = `${label}-${relative.replace(/[^a-z0-9-]/gi, '-')}-${viewport.name}.png`;
      await page.screenshot({ path: path.join(output, screenshot), fullPage: true });
      await page.screenshot({ path: path.join(output, screenshot.replace('.png', '-viewport.png')), fullPage: false });
      const result = { viewport, url: page.url(), screenshot, completed: false, expectedStates: [], states: [] };
      pageReport.viewports.push(result);
      const content = await page.locator('main').textContent();
      if (!captureOnly) {
        assert.ok(content.trim().length > 100, `${relative}: substantive core content`);
        if (relative === 'parties.html') {
          const offers = JSON.parse(await readFile(path.join(root, 'data/party-offers.json'), 'utf8'));
          const cards = page.locator('.party-offer');
          assert.equal(await cards.count(), offers.parties.length, 'Every roster party has one template');
          await cards.first().screenshot({ path: path.join(output, `${label}-party-template-${viewport.name}.png`) });
          const fields = await cards.evaluateAll(nodes => nodes.map(node => [...node.querySelectorAll('dt')].map(dt => dt.textContent.trim())));
          assert.ok(fields[0].length >= 8, 'Party template records scope, baseline, year, status and evidence');
          fields.forEach(field => assert.deepEqual(field, fields[0], 'Identical fields and order for every party'));
        }
        if (relative === 'income.html') {
          const data = JSON.parse(await readFile(path.join(root, 'data/income.json'), 'utf8'));
          const forecasts = page.locator('#forecasts');
          assert.ok(await forecasts.isVisible(), 'Forecast content is visible');
          assert.equal(await forecasts.locator('tr.forecast').count(), data.forecast_years.length);
          assert.equal(await forecasts.locator('tr.outturn').count(), 1);
          for (const status of ['forecast', 'outturn']) {
            const borders = await forecasts.locator(`tr.${status} > :first-child`).evaluateAll(nodes => nodes.map(node => getComputedStyle(node).borderTopStyle));
            assert.ok(borders.every(border => border === (status === 'forecast' ? 'dashed' : 'solid')), `${status}: non-colour visual distinction`);
          }
          assert.match(await forecasts.innerText(), /Office for Budget Responsibility/);
          assert.match(await forecasts.innerText(), new RegExp(data.source.published));
          await forecasts.screenshot({ path: path.join(output, `${label}-forecasts-${viewport.name}.png`) });
          result.forecastStylesChecked = true;
        }
        assert.deepEqual(errors, [], `${relative}: browser errors`);
        const colours = await page.locator('body, body *').evaluateAll(nodes => [...new Set(nodes.flatMap(node => {
          const style = getComputedStyle(node);
          return [style.color, style.backgroundColor, style.borderTopColor, style.outlineColor];
        }))]);
        for (const colour of colours) {
          const channels = colour.match(/[\d.]+/g)?.slice(0, 3).map(Number);
          assert.ok(channels && Math.max(...channels) - Math.min(...channels) <= 50, `${relative}: non-neutral palette colour ${colour}`);
        }
        const noJS = await browser.newContext({ javaScriptEnabled: false, viewport: { width: viewport.width, height: viewport.height } });
        const plain = await noJS.newPage();
        await plain.goto(`${baseURL}/${relative}`);
        assert.equal((await plain.locator('main').textContent()).replace(/\s+/g, ' ').trim(), content.replace(/\s+/g, ' ').trim(), `${relative}: core content differs without JavaScript`);
        assert.ok(await plain.locator('main').isVisible(), `${relative}: no-JS main must be visible`);
        assert.equal((await plain.locator('main').innerText()).replace(/\s+/g, ' ').trim(), (await page.locator('main').innerText()).replace(/\s+/g, ' ').trim(), `${relative}: visible content differs without JavaScript`);
        const noJSDimensions = await plain.evaluate(() => ({ viewport: innerWidth, document: document.documentElement.scrollWidth, body: document.body.scrollWidth }));
        assert.ok(noJSDimensions.document <= noJSDimensions.viewport && noJSDimensions.body <= noJSDimensions.viewport, `${relative}: horizontal overflow without JavaScript`);
        result.noJavaScriptContentMatches = true;
        result.noJavaScriptDimensions = noJSDimensions;
        if (/^history-(cash|real|gdp)\.html$/.test(relative)) {
          // Exercise native view links with scripting disabled, preserving the area.
          const axisSize = await plain.locator('svg text').first().evaluate(node => {
            const matrix = node.getScreenCTM();
            return parseFloat(getComputedStyle(node).fontSize) * matrix.a;
          });
          assert.ok(axisSize >= 12, `${relative}: chart axis labels too small: ${axisSize}px`);
          const current = relative.match(/^history-(cash|real|gdp)/)[1];
          for (const view of ['cash', 'real', 'gdp'].filter(view => view !== current)) {
            await plain.locator(`#health a[href="history-${view}.html#health"]`).click();
            await plain.waitForURL(url => (url.pathname.endsWith(`/history-${view}.html`) || url.pathname.endsWith(`/history-${view}`)) && url.hash === '#health');
            assert.ok(await plain.locator('#health h2').isVisible());
            assert.ok(await plain.locator('#health figcaption').isVisible());
            await plain.locator('#health summary').click();
            assert.ok(await plain.locator('#health table').isVisible());
            await plain.goto(`${baseURL}/${relative}`);
          }
          result.noJavaScriptViewSwitches = true;
        }
        await noJS.close();
        const checkState = async name => {
          const dimensions = await page.evaluate(() => ({ viewport: innerWidth, document: document.documentElement.scrollWidth, body: document.body.scrollWidth }));
          assert.ok(dimensions.document <= dimensions.viewport && dimensions.body <= dimensions.viewport, `${relative} ${viewport.name} ${name}: horizontal overflow ${JSON.stringify(dimensions)}`);
          const state = { name, dimensions, startedAt: new Date().toISOString(), completed: false };
          result.states.push(state);
          await writeFile(path.join(output, `${label}-browser-report.json`), JSON.stringify(report, null, 2) + '\n');
          console.log(`Checking ${relative} ${viewport.name} ${name}`);
          const start = performance.now();
          const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
          Object.assign(state, {
            axeCompleted: true, finishedAt: new Date().toISOString(), durationMs: Math.round(performance.now() - start),
            runner: axe.testEngine, environment: axe.testEnvironment, options: axe.toolOptions,
            passedRules: axe.passes.map(({ id }) => id), inapplicableRules: axe.inapplicable.map(({ id }) => id),
            violations: axe.violations, incomplete: axe.incomplete,
          });
          assert.ok([...axe.passes, ...axe.inapplicable, ...axe.incomplete, ...axe.violations].some(rule => rule.id === 'color-contrast'), 'Contrast rule must run');
          assert.deepEqual(axe.violations, [], `${relative} ${viewport.name} ${name}: WCAG violations`);
          state.svgContrast = await checkSVGContrast(page, axe.incomplete);
          state.contrastCompleted = true;
          state.completed = true;
        };
        result.expectedStates.push('initial');
        await checkState('initial');
        if (await page.locator('details').count()) {
          result.expectedStates.push('all-details-expanded');
          await page.locator('details').evaluateAll(nodes => nodes.forEach(node => { node.open = true; }));
          await checkState('all-details-expanded');
        }
        const expandable = await page.locator('button[aria-expanded="false"]').elementHandles();
        for (const [index, button] of expandable.entries()) {
          if (await button.isVisible()) {
            result.expectedStates.push(`expanded-control-${index + 1}`);
            await button.click(); await checkState(`expanded-control-${index + 1}`);
          }
        }
      }
      result.completed = true;
      await context.close();
    }
  }
  report.completed = true;
  report.finishedAt = new Date().toISOString();
  report.passed = true;
  console.log(`${captureOnly ? 'Captured baseline' : 'Passed browser checks'}: ${files.length} pages at ${viewports.map(viewport => `${viewport.width}×${viewport.height}`).join(', ')}.`);
} catch (error) {
  report.passed = false;
  report.error = error.stack;
  throw error;
} finally {
  await writeFile(path.join(output, `${label}-browser-report.json`), JSON.stringify(report, null, 2) + '\n');
  if (browser) await browser.close();
  await new Promise(resolve => server.close(resolve));
}
