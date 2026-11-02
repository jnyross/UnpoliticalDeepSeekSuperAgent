import {chromium} from 'playwright';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
const stage=process.argv[2];
if(!['before','after'].includes(stage)) throw Error('stage required');
const browser=await chromium.launch();
try{for(const [name,width,height] of [['mobile',360,800],['desktop',1280,900]]){
 const page=await browser.newPage({viewport:{width,height},javaScriptEnabled:false,colorScheme:'light',reducedMotion:'reduce'});
 await page.goto(pathToFileURL(resolve('site/corrections.html')).href);
 await page.screenshot({path:resolve(`docs/evidence/impartiality-l3/${stage}-corrections-${name}.png`),fullPage:true});
 await page.close();
}}finally{await browser.close();}
