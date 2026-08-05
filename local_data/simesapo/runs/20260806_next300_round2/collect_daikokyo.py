from __future__ import annotations
import csv,re,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
HELPERS=Path(__file__).resolve().parents[1]/"20260805_next300"
sys.path.insert(0,str(HELPERS))
from collect_aca import HEADERS,discover,host
HERE=Path(__file__).parent; BASE='https://www.daikokyo.or.jp/meibo_list.php?parts={}'
def expand(n):
 n=' '.join(n.split()); reps={'(株)':'株式会社','（株）':'株式会社','(有)':'有限会社','（有）':'有限会社','(同)':'合同会社','（同）':'合同会社'}
 for a,b in reps.items():
  if n.startswith(a):n=b+n[len(a):]
  elif n.endswith(a):n=n[:-len(a)]+b
 return re.sub(r'\s+(?:大阪)?(?:支店|営業所|事業所|本社)$','',n).strip()
rows=[]
for part in ['03','05','06','07']:
 src=BASE.format(part);r=requests.get(src,headers=HEADERS,timeout=40);r.raise_for_status();s=BeautifulSoup(r.text,'html.parser')
 for tr in s.select('table.tbl_list tr'):
  tds=tr.find_all('td',recursive=False)
  if len(tds)<3:continue
  url=next((a['href'] for a in tds[1].select('a[href^="http"]') if host(a['href'])), '')
  direct=[x.strip() for x in tds[0].find_all(string=True,recursive=False) if x.strip()]
  raw=next((x for x in direct if re.search(r'\(株\)|（株）|\(有\)|（有）|\(同\)|（同）',x)), '')
  name=expand(raw)
  if not url or not re.search(r'株式会社|有限会社|合同会社',name):continue
  service=' '.join(tds[2].get_text(' ',strip=True).split())[:160]
  rows.append({'company_name':name,'url':url,'address':'','phone':'','contact_url':'','区分':'S｜屋外広告・看板・サイン・店舗外装支援','検出ワード':'大阪屋外広告美術協同組合公式組合員：'+service,'source_url':src})
unique={host(x['url']):x for x in rows};out=[]
with ThreadPoolExecutor(max_workers=20) as pool:
 fs=[pool.submit(discover,x) for x in unique.values()]
 for f in as_completed(fs):out.append(f.result())
out.sort(key=lambda x:x['company_name']);p=HERE/'daikokyo_crawled.csv'
with p.open('w',encoding='utf-8-sig',newline='') as h:
 w=csv.DictWriter(h,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
print({'listed':len(rows),'unique_domains':len(unique),'contact_found':sum(bool(x['contact_url']) for x in out),'company_confirmed':sum(x['company_confirmed']=='yes' for x in out),'output':str(p)})
