from __future__ import annotations
import csv,re
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup

HERE=Path(__file__).parent
SOURCE='https://sign-jp.org/member/'
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; SimesapoResearch/1.0)'}
MAJOR=('トピー実業','東芝','パナソニック','三菱','TOPPAN','大日本印刷','電通','博報堂','乃村工藝社','丹青社')

def host(u):return (urlparse(u).hostname or '').lower().removeprefix('www.')
def legal_name(v):
    v=re.sub(r'\s+','',v).strip()
    for mark,word in [('㈱','株式会社'),('㈲','有限会社'),('(株)','株式会社'),('(有)','有限会社')]:
        if v.startswith(mark):v=word+v[len(mark):]
        elif v.endswith(mark):v=v[:-len(mark)]+word
        else:v=v.replace(mark,word)
    return v
def crawl(row):
    try:
        r=requests.get(row['url'],headers=HEADERS,timeout=18,allow_redirects=True);r.raise_for_status()
        if 'html' not in r.headers.get('content-type',''):raise ValueError('non_html')
        s=BeautifulSoup(r.text,'html.parser');h=host(r.url);links=[]
        for a in s.find_all('a',href=True):
            href=urljoin(r.url,a['href']); signal=(a.get_text(' ',strip=True)+' '+href).lower()
            if host(href)==h and re.search(r'contact|inquiry|form|toiawase|otoiawase|お問い合わせ|お問合せ|問合せ|ご相談|見積',signal):links.append(href)
        return {**row,'url':r.url,'contact_url':list(dict.fromkeys(links))[0] if links else '','fetch':'ok'}
    except Exception as e:return {**row,'contact_url':'','fetch':type(e).__name__}
def main():
    r=requests.get(SOURCE,headers=HEADERS,timeout=30);r.raise_for_status();s=BeautifulSoup(r.text,'html.parser')
    raw=[]
    for table in s.find_all('table'):
        for tr in table.find_all('tr'):
            cells=tr.find_all('td')
            if len(cells)<3:continue
            name=legal_name(cells[0].get_text(' ',strip=True));a=cells[2].find('a',href=True)
            if not a or not name or not any(x in name for x in ('株式会社','有限会社','合同会社')):continue
            if any(x.lower() in name.lower() for x in MAJOR):continue
            url=urljoin(SOURCE,a['href'])
            if host(url) in ('sign-jp.org',''):continue
            raw.append({'company_name':name,'url':url,'address':cells[1].get_text(' ',strip=True),'contact_url':'','区分':'S｜地方広告・印刷・看板・ブランディング','検出ワード':'日本サイン協会公式会員：看板・屋外広告・サイン制作','source_url':SOURCE})
    unique={host(x['url']):x for x in raw}
    results=[]
    with ThreadPoolExecutor(max_workers=12) as p:
        fs=[p.submit(crawl,x) for x in unique.values()]
        for f in as_completed(fs):results.append(f.result())
    results.sort(key=lambda x:x['company_name'])
    with (HERE/'sign_members_crawled.csv').open('w',encoding='utf-8-sig',newline='') as h:
        w=csv.DictWriter(h,fieldnames=list(results[0].keys()));w.writeheader();w.writerows(results)
    print({'raw':len(raw),'unique_domain':len(unique),'contact':sum(bool(x['contact_url']) for x in results)})
if __name__=='__main__':main()
