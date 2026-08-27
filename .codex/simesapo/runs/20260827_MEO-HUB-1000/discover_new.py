import csv,json,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
BASE=Path(__file__).parent;OLD=BASE.parent/'20260826_MEO-HUB-5000'
sys.path.insert(0,str(OLD));import collect_webkanji as cw
from prepare_pool import nk,dk,pk
seen=set()
for p in OLD.glob('*.csv'):
 for r in csv.DictReader(p.open(encoding='utf-8-sig',newline='')):
  u=r.get('source_url','')
  if 'web-kanji.com/companies/' in u:seen.add(u)
xml=cw.get('https://web-kanji.com/sitemap-company.xml').text
urls=list(dict.fromkeys(cw.re.findall(r'<loc>(https://web-kanji\.com/companies/[^<]+)</loc>',xml)))
todo=[u for u in urls if u not in seen][:3000]
existing=json.loads((BASE/'existing_live.json').read_text(encoding='utf-8-sig'));names={nk(r.get('company_name')) for r in existing};domains={dk(r.get('url')) for r in existing}
print(json.dumps({'sitemap':len(urls),'previously_examined':len(seen),'scheduled':len(todo)}),flush=True)
rows=[];audit=[]
with ThreadPoolExecutor(max_workers=4) as pool:
 for i,f in enumerate(as_completed([pool.submit(cw.parse,u) for u in todo]),1):
  r=f.result();n,d=nk(r.get('company_name')),dk(r.get('url'))
  if r.get('decision')=='keep' and n not in names and d not in domains:
   rows.append(r);names.add(n);domains.add(d)
  elif r.get('decision')=='keep':r['decision']='drop';r['reason']='existing_or_duplicate'
  audit.append(r)
  if i%100==0:
   cw.write(BASE/'new_discovered.csv',rows);cw.write(BASE/'discovery_audit.csv',audit);print(json.dumps({'examined':i,'new_candidates':len(rows)}),flush=True)
cw.write(BASE/'new_discovered.csv',rows);cw.write(BASE/'discovery_audit.csv',audit)
print(json.dumps({'done':True,'examined':len(todo),'new_candidates':len(rows)}),flush=True)
