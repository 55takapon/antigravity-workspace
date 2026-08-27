import csv,json,hashlib,sys
from pathlib import Path
from urllib.parse import urlsplit
BASE=Path(__file__).parent
CACHE=BASE.parent/'20260827_MEO-HUB-1000'/'official_cache'
batch=sys.argv[1];domains=sys.argv[2:]
for r in csv.DictReader((BASE/f'review_batch_{batch}.csv').open(encoding='utf-8-sig')):
 if domains and not any(d in r['url'] for d in domains):continue
 print('\nCOMPANY',r['company_name'],r['url'],'CONTACT',r['contact_url'],r['phone'],r['generic_email'])
 urls=[r['url'],*[e['url'] for e in json.loads(r['evidence_detail'])]]
 for u in dict.fromkeys(urls):
  p=CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.json')
  if not p.exists():continue
  d=json.loads(p.read_text(encoding='utf-8'));print('PAGE',u,d.get('title',''));print(d.get('text','')[:18000])
