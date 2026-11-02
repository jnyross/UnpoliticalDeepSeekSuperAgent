// Automated actual saved-page captures, not human accessibility/user evidence.
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { mkdir, writeFile } from 'node:fs/promises';
const [stage, root] = process.argv.slice(2);
if (!['before', 'after'].includes(stage) || !root) throw Error('Use before|after ROOT');
const output = `docs/evidence/context-w8/${stage}`;
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const results = [];
for (const [width, height] of [[360, 800], [1280, 900]]) {
  const page = await browser.newPage({ viewport: { width, height }, javaScriptEnabled: false, colorScheme: 'light', deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(resolve(root, 'parties.html')).href);
  const card = page.locator('article[data-party-id="7"]');
  await card.evaluate(el => el.scrollIntoView({ block: 'start' }));
  const noticeCards = await page.locator('article:has(.revision-notice)').evaluateAll(els => els.map(el => ({ party_id: el.dataset.partyId, links: [...el.querySelectorAll('.revision-notice a')].map(a => a.getAttribute('href')) })));
  assert.deepEqual(noticeCards.map(c => c.party_id), stage === 'before' ? ['17'] : ['7', '17']);
  assert.equal(await card.locator('.revision-notice').count(), stage === 'before' ? 0 : 1);
  if (stage === 'after') assert.equal(noticeCards[0].links[0], 'https://www.education-ni.gov.uk/news/education-minister-announces-ps25million-package-measures-early-learning-and-childcare-northern-ireland');
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  assert.equal(overflow, false);
  await page.screenshot({ path: `${output}/dup-${width}x${height}.png` });
  results.push({ stage, root: resolve(root), width, height, party_id: 7, section_dates: await card.locator('.section-dates').innerText(), revision_notices: await card.locator('.revision-notice').count(), notice_cards: noticeCards, document_overflow: overflow, card_bounds: await card.boundingBox() });
  await page.close();
}
await browser.close();
await writeFile(`${output}/capture.json`, JSON.stringify(results, null, 2) + '\n');
