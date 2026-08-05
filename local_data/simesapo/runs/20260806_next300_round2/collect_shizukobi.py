from __future__ import annotations
import csv,re,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import requests
from bs4 import BeautifulSoup
HELPERS=Path(__file__).resolve().parents[1]/"20260805_next300"
sys.path.insert(0,str(HELPERS))
from collect_aca import HEADERS,discover,host
HERE=Path(__file__).parent; SOURCE='https://shizukobi.com/searches/'
r=requests.get(SOURCE,headers=HEADERS,timeout=40);r.raise_for_status();s=BeautifulSoup(r.text,'html.parser')
rows=[]
for card in s.select('.signs_search_box'):
    h=card.select_one('.signs_midashi h3'); u=None
    for tr in card.select('tr'):
        if tr.find('th') and tr.find('th').get_text(' ',strip=True)=='URL': u=tr.find('a',href=True)
    if not h or not u: continue
    name=' '.join(h.get_text(' ',strip=True).split())
    if not re.search(r'株式会社|有限会社|合同会社',name) or not host(u['href']): continue
    rows.append({'company_name':name,'url':u['href'],'address':'','phone':'','contact_url':'','区分':'S｜屋外広告・看板・サイン・店舗外装支援','検出ワード':'静岡県広告美術業協同組合公式組合員：看板・屋外広告・サイン制作施工','source_url':SOURCE})
unique={host(x['url']):x for x in rows};out=[]
with ThreadPoolExecutor(max_workers=14) as pool:
    fs=[pool.submit(discover,x) for x in unique.values()]
    for f in as_completed(fs):out.append(f.result())
out.sort(key=lambda x:x['company_name']);p=HERE/'shizukobi_crawled.csv'
with p.open('w',encoding='utf-8-sig',newline='') as h:
    w=csv.DictWriter(h,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
print({'listed':len(rows),'unique_domains':len(unique),'contact_found':sum(bool(x['contact_url']) for x in out),'company_confirmed':sum(x['company_confirmed']=='yes' for x in out),'output':str(p)})
