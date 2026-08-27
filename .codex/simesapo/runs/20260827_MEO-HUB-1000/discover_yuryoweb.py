import csv,json,re,sys,time,threading,requests
from pathlib import Path
from urllib.parse import unquote,urlsplit
from concurrent.futures import ThreadPoolExecutor,as_completed
from xml.etree import ElementTree as ET
from prepare_pool import nk,dk,pk
BASE=Path(__file__).parent;OLD=BASE.parent/'20260826_MEO-HUB-5000';sys.path.insert(0,str(OLD))
import collect_yuryoweb_pilot as old
from verify_official import write
lock=threading.Lock();last=0
class Session:
 def get(self,u,**kw):
  global last
  with lock:
   wait=max(0,.75-(time.monotonic()-last))
   if wait:time.sleep(wait)
   last=time.monotonic()
  return requests.get(u,headers={'User-Agent':old.UA},**kw)
s=Session()
def locs(u):
 ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
 tree=ET.fromstring(old.get(s,u).text)
 return [e.text.strip() for e in tree.findall('s:url/s:loc',ns)+tree.findall('s:sitemap/s:loc',ns) if e.text]
existing=json.loads((BASE/'existing_live.json').read_text(encoding='utf-8-sig'));names={nk(r.get('company_name')) for r in existing};domains={dk(r.get('url')) for r in existing}
seen=set()
for p in OLD.glob('*.csv'):
 for r in csv.DictReader(p.open(encoding='utf-8-sig',newline='')):
  if 'yuryoweb.com/company_info/' in r.get('source_url',''):seen.add(unquote(r['source_url']).rstrip('/'))
urls=[]
for m in locs('https://yuryoweb.com/sitemap.xml'):
 if '/company_info-sitemap' in m:urls.extend(locs(m))
todo=[u for u in dict.fromkeys(urls) if urlsplit(u).hostname=='yuryoweb.com' and urlsplit(u).path.startswith('/company_info/') and unquote(u).rstrip('/') not in seen and nk(unquote(urlsplit(u).path).rstrip('/').split('/')[-1]) not in names][:3000]
(BASE/'yuryoweb_expected.json').write_text(json.dumps({'scheduled':len(todo)}),encoding='utf-8')
print(json.dumps({'sitemap':len(urls),'previous_sources':len(seen),'scheduled':len(todo)}),flush=True)
def parse(u):
 try:return old.parse_detail(s,u) or {'source_url':u,'reject_reason':'required_missing'}
 except Exception as e:return {'source_url':u,'reject_reason':type(e).__name__}
rows=[];audit=[]
with ThreadPoolExecutor(max_workers=4) as pool:
 for i,f in enumerate(as_completed([pool.submit(parse,u) for u in todo]),1):
  r=f.result();n,d=nk(r.get('company_name')),dk(r.get('url'))
  if n and d and n not in names and d not in domains:rows.append(r);names.add(n);domains.add(d)
  else:r['reject_reason']=r.get('reject_reason') or 'existing_or_missing'
  audit.append(r)
  if i%100==0:write(BASE/'yuryoweb_discovered.csv',rows);write(BASE/'yuryoweb_discovery_audit.csv',audit);print(json.dumps({'examined':i,'new_candidates':len(rows)}),flush=True)
write(BASE/'yuryoweb_discovered.csv',rows);write(BASE/'yuryoweb_discovery_audit.csv',audit)
print(json.dumps({'done':True,'examined':len(todo),'new_candidates':len(rows)}),flush=True)
