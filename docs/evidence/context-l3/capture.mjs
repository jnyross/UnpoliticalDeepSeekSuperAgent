// Actual static application captures; identical state in each revision.
import { chromium } from 'playwright';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { mkdir } from 'node:fs/promises';
const [stage, root = 'site'] = process.argv.slice(2);
if (!['before', 'after'].includes(stage)) throw Error('Use before or after');
await mkdir(`docs/evidence/context-l3/${stage}`, { recursive: true });
const browser = await chromium.launch({ headless: true });
for (const width of [360, 1280]) {
  const page = await browser.newPage({ viewport: { width, height: 1600 }, javaScriptEnabled: false, colorScheme: 'light' });
  for (const view of ['cash', 'real', 'gdp']) {
    await page.goto(pathToFileURL(resolve(root, `history-${view}.html`)).href + '#tme');
    await page.locator('#tme summary').click();
    // Scroll to the same section rather than the document's bottom-clamped anchor.
    await page.locator('#tme').evaluate(el => el.scrollIntoView());
    await page.screenshot({ path: `docs/evidence/context-l3/${stage}/${view}-${width}.png` });
  }
  await page.close();
}
await browser.close();
