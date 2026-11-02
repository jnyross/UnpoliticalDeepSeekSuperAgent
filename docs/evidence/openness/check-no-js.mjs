// Run from repository root: node docs/evidence/openness/check-no-js.mjs
import assert from 'node:assert/strict';
import { readFile, readdir, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { chromium } from 'playwright';
const server = createServer(async (request, response) => {
  try {
    const pathname = new URL(request.url, 'http://localhost').pathname;
    assert.match(pathname, /^\/[a-z-]+\.html$/);
    const body = await readFile(`site${pathname}`);
    response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' }); response.end(body);
  } catch { response.writeHead(404); response.end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browser = await chromium.launch();
const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 360, height: 800 } });
const report = { checkedAt: new Date().toISOString(), javaScriptEnabled: false, viewport: { width: 360, height: 800 }, pages: [], passed: false };
try {
  for (const file of (await readdir('site')).filter(f => f.endsWith('.html')).sort()) {
    const page = await context.newPage();
    const response = await page.goto(`http://127.0.0.1:${server.address().port}/${file}`);
    assert.equal(response.status(), 200);
    const footer = page.locator('footer');
    const about = footer.getByRole('link', { name: 'About this project and methods' });
    const reportLink = footer.getByRole('link', { name: 'Report an error on GitHub' });
    const reportHref = await reportLink.getAttribute('href');
    const correctionsHref = file === 'corrections.html' ? null : await footer.locator('a[href="corrections.html"]').getAttribute('href');
    if (file !== 'corrections.html') assert.equal(correctionsHref, 'corrections.html');
    assert.equal(await about.getAttribute('href'), 'about.html');
    assert.equal(reportHref, 'https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/issues/new');
    await about.click(); await page.waitForURL('**/about.html');
    assert.equal(await page.title(), 'About this project | UnpoliticalAF');
    report.pages.push({ page: file, aboutHref: 'about.html', correctionsHref, reportHref, aboutNavigationPassed: true });
    if (file === 'index.html') await page.screenshot({ path: 'docs/evidence/openness/about-mobile.png', fullPage: true });
    await page.close();
  }
  report.passed = true;
  await writeFile('docs/evidence/openness/no-js-navigation.json', JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally { await browser.close(); server.close(); }
