// Explicitly permitted read-only browser verification; all API operations use gh.
// No credentials, prior storage state, form submissions, or issue mutations.
// Run from repository root: node docs/evidence/openness/check-github-anonymous.mjs
import { chromium } from 'playwright';
import { writeFile } from 'node:fs/promises';
const browser = await chromium.launch();
const context = await browser.newContext({ storageState: { cookies: [], origins: [] } });
const report = { checkedAt: new Date().toISOString(), tool: 'Playwright Chromium', anonymous: true, initialCookies: await context.cookies(), results: [] };
try {
  for (const route of ['issues/new', 'issues']) {
    const page = await context.newPage();
    const navigationResponses = [];
    page.on('response', response => {
      if (response.request().isNavigationRequest()) navigationResponses.push({ url: response.url(), status: response.status(), location: response.headers().location ?? null });
    });
    try {
      const response = await page.goto(`https://github.com/jnyross/UnpoliticalDeepSeekSuperAgent/${route}`, { waitUntil: 'domcontentloaded', timeout: 60000 });
      report.results.push({ route, status: response.status(), finalUrl: page.url(), title: await page.title(), navigationResponses, bodyText: (await page.locator('body').innerText()).slice(0, 16000) });
      await page.screenshot({ path: `docs/evidence/openness/github-${route.replaceAll('/', '-')}.png`, fullPage: false });
    } catch (error) { report.results.push({ route, error: error.message, navigationResponses }); }
    await page.close();
  }
  await writeFile('docs/evidence/openness/github-anonymous.json', JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally { await browser.close(); }
