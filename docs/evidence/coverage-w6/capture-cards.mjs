import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
const label = process.env.EVIDENCE_LABEL || 'after';
const root = path.resolve(process.env.SITE_DIR || 'site');
const data = JSON.parse(fs.readFileSync(path.join(root, 'data/party-offers.json'), 'utf8'));
const selected = new Set(['reform', 'uup', 'tuv']);
const browser = await chromium.launch({ headless: true });
for (const [name, width, height] of [['mobile', 360, 800], ['desktop', 1280, 900]]) {
  const page = await browser.newPage({ viewport: { width, height }, javaScriptEnabled: false, colorScheme: 'light' });
  await page.goto('file://' + path.join(root, 'parties.html'));
  for (const party of data.parties.filter(p => selected.has(p.source_id))) {
    await page.locator(`[data-party-id="${party.id}"]`).screenshot({ path: `docs/evidence/coverage-w6/parties.html/${name}/${label}-party-${party.id}.png` });
  }
  await page.close();
}
await browser.close();
