from __future__ import annotations
import csv,re
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import urljoin,urlparse
import requests
from bs4 import BeautifulSoup

HERE=Path(__file__).parent
LIST='https://messe.nikkei.co.jp/exhibitor/area/RT/ja/'
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; SimesapoResearch/1.0)'}
LEGAL=re.compile(r'(?:株式会社|有限会社|合同会社)[\s　]*[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶー・&＆.\-]{1,35}|[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶー・&＆.\-]{1,35}[\s　]*(?:株式会社|有限会社|合同会社)')
MAJOR=('NEC','エプソン','大塚商会','オムロン','キーエンス','ミライト・ワン','日本HP','東芝','Google','兼松','日立','富士通','パナソニック','ソフトバンク','NTT','楽天','LINEヤフー','セブン銀行','三井住友','TOPPAN','大日本印刷','DNP','リコー','キヤノン','シャープ')
BADHOST=('messe.nikkei.co.jp','twitter.com','x.com','facebook.com','linkedin.com','youtube.com','youtu.be')
def host(u):return (urlparse(u).hostname or '').lower().removeprefix('www.')
def clean_name(v):return re.sub(r'\s+','',v).strip('|｜-–—:：.,。')
def fetch_detail(url):
    try:
        r=requests.get(url,headers=HEADERS,timeout=20);r.raise_for_status();s=BeautifulSoup(r.text,'html.parser')
        title=(s.title.get_text(' ',strip=True).split('|')[0] if s.title else '').strip()
        if not title or any(x.lower() in title.lower() for x in MAJOR):return None
        text=re.sub(r'\s+',' ',s.get_text(' ',strip=True))
        ext=[]
        for a in s.find_all('a',href=True):
            href=urljoin(url,a['href']);h=host(href)
            if h and not any(b in h for b in BADHOST):ext.append(href)
        if not ext:return None
        roots=sorted({x for x in ext if urlparse(x).path in ('','/')},key=len)
        official=roots[0] if roots else sorted(ext,key=len)[0]
        contact=next((x for x in ext if re.search(r'contact|inquiry|toiawase|otoiawase|form',x,re.I)), '')
        evidence=''
        m=re.search(r'展示内容\s*(.+?)(?:出展エリアと分類|企業情報)',text)
        if m:evidence=m.group(1)[:180]
        return {'display_name':title,'url':official,'contact_url':contact,'evidence':evidence,'source_url':url}
    except Exception:return None
def crawl(row):
    try:
        r=requests.get(row['url'],headers=HEADERS,timeout=18,allow_redirects=True);r.raise_for_status();s=BeautifulSoup(r.text,'html.parser');h=host(r.url)
        contacts=[row['contact_url']] if row['contact_url'] and host(row['contact_url'])==h else []
        profiles=[]
        for a in s.find_all('a',href=True):
            href=urljoin(r.url,a['href']);signal=(a.get_text(' ',strip=True)+' '+href).lower()
            if host(href)!=h:continue
            if re.search(r'contact|inquiry|form|toiawase|otoiawase|お問い合わせ|お問合せ|問合せ|ご相談|資料請求',signal):contacts.append(href)
            if re.search(r'company|corporate|profile|about|会社概要|企業情報',signal):profiles.append(href)
        pages=[(r.url,s)]
        for purl in list(dict.fromkeys(profiles))[:4]:
            try:
                pr=requests.get(purl,headers=HEADERS,timeout=15);pr.raise_for_status();pages.append((pr.url,BeautifulSoup(pr.text,'html.parser')))
            except Exception:pass
        scored=[]
        key=re.sub(r'[^A-Za-z0-9一-龥ぁ-んァ-ヶー]','',row['display_name']).lower()
        for purl,ps in pages:
            txt=re.sub(r'\s+',' ',ps.get_text(' ',strip=True))
            for m in LEGAL.finditer(txt):
                name=clean_name(m.group());nk=re.sub(r'株式会社|有限会社|合同会社|[^A-Za-z0-9一-龥ぁ-んァ-ヶー]','',name).lower()
                score=(8 if key and (key in nk or nk in key) else 0)+(4 if any(x in txt[max(0,m.start()-30):m.end()+30] for x in ('会社名','商号','会社概要')) else 0)+(2 if name.startswith(('株式会社','有限会社','合同会社')) else 0)
                if 4<=len(name)<=45 and not any(x in name for x in ('こちら','お問い合わせ','サービス','運営する')):scored.append((score,name,purl))
        scored.sort(reverse=True);name=scored[0][1] if scored and scored[0][0]>=4 else ''
        return {**row,'company_name':name,'url':r.url,'contact_url':list(dict.fromkeys(contacts))[0] if contacts else '','fetch':'ok'}
    except Exception as e:return {**row,'company_name':'','contact_url':'','fetch':type(e).__name__}
def main():
    r=requests.get(LIST,headers=HEADERS,timeout=30);r.raise_for_status();s=BeautifulSoup(r.text,'html.parser')
    area=(urlparse(LIST).path.strip('/').split('/')[2] if '/area/' in urlparse(LIST).path else 'RT')
    details=list(dict.fromkeys(urljoin(LIST,a['href']) for a in s.find_all('a',href=True) if f'/exhibitor/info/{area}/ja/' in a['href']))
    base=[]
    with ThreadPoolExecutor(max_workers=14) as p:
        fs=[p.submit(fetch_detail,u) for u in details]
        for f in as_completed(fs):
            x=f.result()
            if x:base.append(x)
    out=[]
    with ThreadPoolExecutor(max_workers=12) as p:
        fs=[p.submit(crawl,x) for x in base]
        for f in as_completed(fs):out.append(f.result())
    out.sort(key=lambda x:x['display_name'])
    with (HERE/'retailtech_crawled.csv').open('w',encoding='utf-8-sig',newline='') as h:
        w=csv.DictWriter(h,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
    print({'details':len(details),'base':len(base),'legal':sum(bool(x['company_name']) for x in out),'contact':sum(bool(x['contact_url']) for x in out),'both':sum(bool(x['company_name'] and x['contact_url']) for x in out)})
if __name__=='__main__':main()
