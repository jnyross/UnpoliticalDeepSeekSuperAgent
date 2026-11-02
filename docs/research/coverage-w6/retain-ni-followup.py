#!/usr/bin/env python3
"""Ordinary public publisher GETs; no bypass, login or alternate headers."""
from pathlib import Path
from urllib.request import urlopen
from html.parser import HTMLParser
import hashlib,json,datetime
root=Path(__file__).parent
class Text(HTMLParser):
 def __init__(self): super().__init__(); self.out=[]; self.skip=0
 def handle_starttag(self,t,a):
  if t in ('script','style'): self.skip+=1
  if t in ('p','div','h1','h2','h3','li','tr','br'): self.out.append('\n')
 def handle_endtag(self,t):
  if t in ('script','style'): self.skip=max(0,self.skip-1)
  if t in ('p','div','h1','h2','h3','li','tr'): self.out.append('\n')
 def handle_data(self,d):
  if not self.skip:self.out.append(d)
records=[]
for name,url in [('ni-obr-march2024','https://obr.uk/efo/economic-and-fiscal-outlook-march-2024/'),('ni-obr-fuel-current','https://obr.uk/forecasts-in-depth/tax-by-tax-spend-by-spend/fuel-duties/'),('ni-rf-economic-battle-lines','https://www.resolutionfoundation.org/comment/economic-battle-lines/')]:
 record={'url':url,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  with urlopen(url,timeout=40) as r: body=r.read(); record.update(status=r.status,final_url=r.url,headers=dict(r.headers))
  (root/(name+'.html')).write_bytes(body)
  record.update(file=name+'.html',sha256=hashlib.sha256(body).hexdigest())
  parser=Text();parser.feed(body.decode('utf-8','replace'))
  text='\n'.join(line.strip() for line in ''.join(parser.out).splitlines() if line.strip())+'\n'
  (root/(name+'.txt')).write_text(text)
 except Exception as e: record['error']=str(e)
 records.append(record)
(root/'ni-followup-metadata.json').write_text(json.dumps(records,indent=2)+'\n')
