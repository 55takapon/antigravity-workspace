import argparse, csv, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--output",required=True); a=p.parse_args()
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; SimesapoResearch/1.0)"}
def host(u): return (urlparse(u).hostname or "").lower().removeprefix("www.")
def fetch(url):
    r=requests.get(url,headers=HEADERS,timeout=22,allow_redirects=True); r.raise_for_status(); r.encoding=r.apparent_encoding
    return r.url,BeautifulSoup(r.text,"html.parser")
def check(row):
    try: base,page=fetch(row["url"])
    except Exception: return None
    texts=[page.get_text(" ",strip=True)]; links=[]
    for a in page.select("a[href]"):
        href=urljoin(base,a.get("href","")); signal=a.get_text(" ",strip=True)+" "+href
        if host(href)==host(base) and re.search(r"事業|サービス|制作|広告|Web|ホームページ|販促|企画|business|service",signal,re.I): links.append(href)
    for href in list(dict.fromkeys(links))[:5]:
        try: texts.append(fetch(href)[1].get_text(" ",strip=True))
        except Exception: pass
    text=" ".join(texts)
    digital=any(w in text for w in ["Webサイト", "WEBサイト", "ホームページ制作", "ウェブサイト", "Web制作", "WEB制作", "MEO", "SNS運用"])
    adjacent=[w for w in ["広告", "マーケティング", "ブランディング", "動画制作", "映像制作", "SNS", "集客", "販促企画", "企画制作"] if w in text]
    continuous=any(w in text for w in ["運用", "保守", "サポート", "継続", "コンサルティング"])
    if not (digital and adjacent and continuous): return None
    row=dict(row); row["区分"]="S｜地域広告・販促・Web支援"; row["検出ワード"]="公式サイト確認：Web制作＋"+"・".join(adjacent[:3])+"＋継続支援"
    return row
with open(a.input,encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
with ThreadPoolExecutor(max_workers=18) as pool: checked=list(pool.map(check,rows))
accepted=[r for r in checked if r]
with open(a.output,"w",encoding="utf-8-sig",newline="") as f:
    fields=list(accepted[0]) if accepted else []
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(accepted)
print({"input":len(rows),"digital_hubs":len(accepted),"output":a.output})
