// Actual generated application, matched LibDem card state. No image editing.
import { chromium } from 'playwright';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const [stage, root] = process.argv.slice(2);
if (!['before', 'after'].includes(stage) || !root) throw Error('Usage: before|after SITE_DIR');
const output = resolve('docs/evidence/context-w6');
const html = await readFile(resolve(root, 'parties.html'));
const browser = await chromium.launch();
const report = { stage, capturedAt: new Date().toISOString(), browserVersion: browser.version(), htmlSha256: createHash('sha256').update(html).digest('hex'), target: 'local-generated-output', state: 'LibDem heading scrolled to top; JavaScript disabled; light; reduced motion', captures: [] };
try {
 for (const [name,width,height] of [['mobile',360,800],['desktop',1280,900]]) {
  const page = await browser.newPage({viewport:{width,height},javaScriptEnabled:false,colorScheme:'light',reducedMotion:'reduce'});
  await page.goto(pathToFileURL(resolve(root,'parties.html')).href);
  const card = page.locator('#party-17').locator('..');
  await page.locator('#party-17').evaluate(el => el.scrollIntoView({block:'start'}));
  const screenshot = `${stage}-libdem-${name}.png`;
  await page.screenshot({path:resolve(output,screenshot)});
  const cardScreenshot = `${stage}-libdem-card-${name}.png`;
  await card.screenshot({path:resolve(output,cardScreenshot)});
  report.captures.push({viewport:{width,height},screenshot,cardScreenshot,noticeCount:await card.locator('.revision-notice').count(),text:await card.innerText(),horizontalOverflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)});
  await page.close();
 }
} finally { await browser.close(); }
await writeFile(resolve(output,`${stage}-libdem-report.json`),JSON.stringify(report,null,2)+'\n');
console.log(`Captured ${stage} LibDem card at mobile and desktop.`);
