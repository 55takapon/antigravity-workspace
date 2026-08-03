from __future__ import annotations

import csv, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HERE=Path(__file__).parent
LIST='https://f-vr.jp/sogo-unicom/enq/web/funeral2026/corpname_search.cgi'
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; SimesapoResearch/1.0)'}
LEGAL=('株式会社','有限会社','合同会社','一般社団法人','一般財団法人')
MAJOR=('アスカネット','アルファクラブ','船井総合研究所','鎌倉新書','燦ホールディングス','ジャパンエレベーター','イオン','楽天','NTT','GMO','電通','リクルート')

def host(url):return (urlparse(url).hostname or '').lower().removeprefix('www.')

def detail(url):
    try:
        r=requests.get(url,headers=HEADERS,timeout=20);r.raise_for_status();s=BeautifulSoup(r.content,'html.parser')
        lines=[re.sub(r'\s+',' ',x).strip() for x in s.get_text('\n',strip=True).splitlines() if x.strip()]
        name=next((x for x in lines[:12] if any(k in x for k in LEGAL)),lines[0] if lines else '')
        if not any(k in name for k in LEGAL) or any(k.lower() in name.lower() for k in MAJOR):return None
        external=[]
        for a in s.find_all('a',href=True):
            href=urljoin(url,a['href']);h=host(href)
            if h and h!='f-vr.jp' and not href.startswith(('mailto:','tel:')):external.append(href)
        external=list(dict.fromkeys(external))
        if not external:return None
        # 同一ドメイン内で最短のURLを公式サイト候補とする。
        by_host={}
        for href in external:
            h=host(href)
            if h not in by_host or len(href)<len(by_host[h]):by_host[h]=href
        official=sorted(by_host.values(),key=len)[0]
        text=' '.join(lines)
        exhibit=''
        if '出展内容' in lines:
            i=lines.index('出展内容'); exhibit=' '.join(lines[i+1:i+4])[:180]
        return {'company_name':name,'url':official,'contact_url':'','evidence':exhibit or text[:180],'source_url':url}
    except Exception:return None

def crawl(row):
    try:
        r=requests.get(row['url'],headers=HEADERS,timeout=20,allow_redirects=True);r.raise_for_status();s=BeautifulSoup(r.text,'html.parser')
        base_host=host(r.url);links=[]
        for a in s.find_all('a',href=True):
            href=urljoin(r.url,a['href']); signal=(a.get_text(' ',strip=True)+' '+href).lower()
            if host(href)==base_host and re.search(r'contact|inquiry|form|toiawase|otoiawase|お問い合わせ|お問合せ|問合せ|ご相談|資料請求',signal):links.append(href)
        return {**row,'url':r.url,'contact_url':list(dict.fromkeys(links))[0] if links else '','fetch':'ok'}
    except Exception as e:return {**row,'contact_url':'','fetch':type(e).__name__}

def main():
    r=requests.get(LIST,headers=HEADERS,timeout=30);r.raise_for_status();s=BeautifulSoup(r.content,'html.parser')
    detail_urls=list(dict.fromkeys(urljoin(LIST,f.get('action')) for f in s.find_all('form',action=True) if 'detail.cgi?id=' in f.get('action','')))
    detailed=[]
    with ThreadPoolExecutor(max_workers=14) as p:
        fs=[p.submit(detail,u) for u in detail_urls]
        for f in as_completed(fs):
            x=f.result()
            if x:detailed.append(x)
    crawled=[]
    with ThreadPoolExecutor(max_workers=12) as p:
        fs=[p.submit(crawl,x) for x in detailed]
        for f in as_completed(fs):crawled.append(f.result())
    crawled.sort(key=lambda x:x['company_name'])
    with (HERE/'funeral_fair_candidates.csv').open('w',encoding='utf-8-sig',newline='') as h:
        w=csv.DictWriter(h,fieldnames=list(crawled[0].keys()));w.writeheader();w.writerows(crawled)
    print({'detail_urls':len(detail_urls),'legal_with_domain':len(detailed),'contact':sum(bool(x['contact_url']) for x in crawled)})

if __name__=='__main__':main()
