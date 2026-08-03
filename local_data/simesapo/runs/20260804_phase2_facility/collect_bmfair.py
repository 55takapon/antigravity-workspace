from __future__ import annotations
import csv,re,importlib.util
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup

HERE=Path(__file__).parent
LIST='https://www.bmfairtokyo.net/exhibitors/'
source=Path(__file__).parents[1]/'20260804_phase2_retail_dx'/'collect_retailtech.py'
spec=importlib.util.spec_from_file_location('common_collector',source)
common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common)

r=requests.get(LIST,headers=common.HEADERS,timeout=30);r.raise_for_status();r.encoding=r.apparent_encoding
s=BeautifulSoup(r.text,'html.parser');base=[]
for card in s.select('.exhibitor-item'):
    text=re.sub(r'\s+',' ',card.get_text(' ',strip=True))
    name=re.sub(r'^\d+-\d+\s*','',text).split(' お問い合わせはこちら')[0].split(' ホームページはこちら')[0].strip()
    links=[urljoin(LIST,a['href']) for a in card.find_all('a',href=True) if not a['href'].startswith(('mailto:','#'))]
    official=next((u for u in links if urlparse(u).hostname and 'bmfairtokyo.net' not in urlparse(u).hostname), '')
    if not name or not official:continue
    evidence=text
    for marker in ('ホームページはこちら','お問い合わせはこちら'):
        if marker in evidence:evidence=evidence.split(marker,1)[-1]
    base.append({'display_name':name,'company_name':name,'url':official,'contact_url':'','evidence':evidence[:180],'source_url':LIST})

out=[]
with ThreadPoolExecutor(max_workers=12) as pool:
    futures=[pool.submit(common.crawl,row) for row in base]
    for future in as_completed(futures):
        row=future.result()
        if not row.get('company_name') or len(row['company_name'])<4:row['company_name']=row['display_name']
        out.append(row)
out.sort(key=lambda x:x['display_name'])
fields=list(out[0].keys())
with (HERE/'bmfair_crawled.csv').open('w',encoding='utf-8-sig',newline='') as h:
    w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(out)
print({'cards':len(base),'legal':sum(bool(x['company_name']) for x in out),'contact':sum(bool(x['contact_url']) for x in out),'both':sum(bool(x['company_name'] and x['contact_url']) for x in out)})
