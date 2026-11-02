// Actual local application captures; same card state on both revisions.
import {chromium} from 'playwright';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const [stage,revision]=process.argv.slice(2);
if(!['before','after'].includes(stage)||!revision) throw Error('stage revision required');
const dir=resolve('docs/evidence/impartiality-l3');
const html=await readFile('site/parties.html');
const browser=await chromium.launch();
const report={stage,revision,capturedAt:new Date().toISOString(),htmlSha256:createHash('sha256').update(html).digest('hex'),state:'JavaScript disabled; light theme; card heading scrolled to top',captures:[]};
try {
 for(const [name,width,height] of [['mobile',360,800],['desktop',1280,900]]) {
  const page=await browser.newPage({viewport:{width,height},javaScriptEnabled:false,colorScheme:'light',reducedMotion:'reduce'});
  await page.goto(pathToFileURL(resolve('site/parties.html')).href);
  for(const [party,id] of [['alliance',1],['reform',1036],['uup',38]]) {
   const heading=page.locator('#party-'+id); await heading.scrollIntoViewIfNeeded();
   await heading.evaluate(el=>el.scrollIntoView({block:'start'}));
   const card=heading.locator('..');
   const file=`${stage}-${party}-${name}.png`;
   await card.screenshot({path:resolve(dir,file)});
   report.captures.push({party,viewport:{width,height},file,text:await card.innerText(),horizontalOverflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)});
  }
  await page.close();
 }
} finally {await browser.close();}
await writeFile(resolve(dir,stage+'.json'),JSON.stringify(report,null,2)+'\n');
