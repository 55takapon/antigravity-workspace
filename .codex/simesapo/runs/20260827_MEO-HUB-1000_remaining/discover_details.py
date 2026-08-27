import sys,json,csv,time,threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup
BASE=Path(__file__).parent
sys.path.insert(0,str(BASE.parent/'20260827_MEO-HUB-1000'))
from prepare_pool import nk,dk
LOCK=threading.Lock();LAST=0
CACHE=BASE/'detail_cache';CACHE.mkdir(exist_ok=True)
def detail(row):
 global LAST
 p=CACHE/(row['source_url'].rstrip('/').split('/')[-1]+'.json')
 if p.exists():return json.loads(p.read_text(encoding='utf-8'))
 with LOCK:
  wait=max(0,LAST+1-time.monotonic());LAST=time.monotonic()+wait
 if wait:time.sleep(wait)
 out=dict(row,url='',discovery_note='会社詳細の問い合わせリンク。公式性は別途確認必須')
 try:
  r=requests.get(row['source_url'],timeout=25,headers={'User-Agent':'Mozilla/5.0'});out['source_http_status']=r.status_code
  if r.status_code in (403,429):raise RuntimeError('Access restricted; stop collection')
  if r.status_code==200:
   r.encoding='utf-8';soup=BeautifulSoup(r.text,'html.parser');urls=[]
   for a in soup.select('a[href]'):
    u=a['href'];label=a.get_text(' ',strip=True);d=dk(u)
    if label not in ['お問い合わせ','ホームページ','公式サイト','公式ホームページ']:continue
    if not u.startswith(('http://','https://')) or any(x in d for x in ['goo.to','form.run','google.','yahoo.']):continue
    urls.append(u)
   urls=list(dict.fromkeys(urls))
   if len(urls)==1:out['url']=urls[0]
   else:out['discovery_note']='公式URLの明示なし、または複数候補'
 except requests.RequestException as e:out['source_error']=type(e).__name__
 p.write_text(json.dumps(out,ensure_ascii=False),encoding='utf-8');return out
def save(rows):
 p=BASE/'detail_raw.csv';temp=BASE/'detail_raw.tmp'
 fields=sorted({k for r in rows for k in r})
 with temp.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 temp.replace(p)
if __name__=='__main__':
 existing=json.loads((BASE/'existing_live.json').read_text(encoding='utf-8'));names={nk(r.get('company_name')) for r in existing};domains={dk(r.get('url')) for r in existing}
 items={}
 for p in (BASE/'advertising_cache').glob('*.json'):
  for r in json.loads(p.read_text(encoding='utf-8')):
   if nk(r['company_name']) not in names and not r['url']:items[r['source_url']]=r
 out={}
 print('todo',len(items),flush=True)
 with ThreadPoolExecutor(max_workers=6) as pool:
  for i,f in enumerate(as_completed([pool.submit(detail,r) for r in items.values()]),1):
   row=f.result();d=dk(row['url'])
   if d and d not in domains:out.setdefault(d,row)
   if i%25==0:save(list(out.values()));print('details',i,'new_raw',len(out),flush=True)
 save(list(out.values()));print('done',len(out),flush=True)
