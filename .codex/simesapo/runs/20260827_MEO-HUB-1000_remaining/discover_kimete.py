import sys,json,csv,time,re,hashlib
from pathlib import Path
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup
BASE=Path(__file__).parent
sys.path.insert(0,str(BASE.parent/'20260827_MEO-HUB-1000'))
from prepare_pool import nk,dk
CACHE=BASE/'kimete_cache';CACHE.mkdir(exist_ok=True)
def fetch(u,kind):
 p=CACHE/(hashlib.sha256((u+('list-v2' if kind=='list' else '')).encode()).hexdigest()+'.json')
 if p.exists():return json.loads(p.read_text(encoding='utf-8'))
 time.sleep(1)
 try:
  r=requests.get(u,timeout=25,headers={'User-Agent':'Mozilla/5.0'})
  if r.status_code in (403,429):raise RuntimeError('Source access restricted')
  if r.status_code!=200:return []
  r.encoding='utf-8';s=BeautifulSoup(r.text,'html.parser');out=[]
  if kind=='list':
   for a in s.select('a[href]'):
    if not re.fullmatch(r'https?://homepage-kimete\.com/company/[^/]+/?',a['href']):continue
    title=a.select_one('h2,h3,h4')
    name=title.get_text(' ',strip=True) if title else a.get_text('\n',strip=True).split('\n')[0]
    out.append({'company_name':name,'source_url':a['href']})
  else:
   h=s.select_one('h1');name=h.get_text(' ',strip=True) if h else ''
   for a in s.select('a[href]'):
    v=a['href'];label=a.get_text(' ',strip=True)
    if v.startswith(('http://','https://')) and dk(v)!=dk(u) and label.startswith(('http://','https://','www.')):
     out.append({'company_name':name,'source_url':u,'url':v,'phone':'','address':''})
  p.write_text(json.dumps(out,ensure_ascii=False),encoding='utf-8');return out
 except requests.RequestException:return []
def save(rows):
 p=BASE/'kimete_raw.tmp'
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['company_name','source_url','url','phone','address']);w.writeheader();w.writerows(rows)
 p.replace(BASE/'kimete_raw.csv')
if __name__=='__main__':
 e=json.loads((BASE/'existing_live.json').read_text(encoding='utf-8'));names={nk(r.get('company_name')) for r in e};domains={dk(r.get('url')) for r in e};out={};seen=set()
 for page in range(1,333):
  u='https://homepage-kimete.com/search/'+('' if page==1 else f'page/{page}/')
  for row in fetch(u,'list'):
   n=nk(row['company_name'])
   if n in names or n in seen:continue
   seen.add(n)
   for candidate in fetch(row['source_url'],'detail'):
    d=dk(candidate['url'])
    if d not in domains and nk(candidate['company_name']) not in names:out.setdefault(d,candidate)
  save(list(out.values()));print('page',page,'details',len(seen),'new_raw',len(out),flush=True)
 print('done',len(out),flush=True)
