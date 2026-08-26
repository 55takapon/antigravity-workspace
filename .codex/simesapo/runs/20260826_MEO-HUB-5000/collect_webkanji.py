import argparse
import csv
import html
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
DENY = ("web-kanji.com", "web-kanji.co.jp", "google.com", "youtube.com", "facebook.com", "instagram.com", "twitter.com", "x.com", "typekit.net", "visualwebsiteoptimizer.com", "douga-kanji.com", "ec-kanji.com", "eigyo-kanji.com", "hojokin-kanji.com", "jinji-kanji.com", "keiri-kanji.com", "lp-kanji.com", "oa-kanji.com", "security-kanji.com", "soumu-kanji.com", "system-kanji.com")
lock = threading.Lock(); last = 0.0

def nname(v): return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]", "", (v or "").lower())
def domain(v):
    h = urlparse(v or "").netloc.lower().split(":")[0]
    return h[4:] if h.startswith("www.") else h

def get(url, stream=False):
    global last
    with lock:
        wait = .50 - (time.monotonic() - last)
        if wait > 0: time.sleep(wait)
        last = time.monotonic()
    r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "ja-JP,ja;q=0.9"}, timeout=25, allow_redirects=True, stream=stream)
    r.raise_for_status(); return r

def parse(url):
    try:
        body = get(url).text
        title_match = re.search(r"<title>(.*?)</title>", body, re.I | re.S)
        title = html.unescape(re.sub(r"<[^>]+>", "", title_match.group(1))).strip() if title_match else ""
        name = title.split("の制作実績", 1)[0].strip()
        desc_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', body, re.I)
        desc = html.unescape(desc_match.group(1)).strip() if desc_match else title
        candidates = []
        for href, label in re.findall(r'href="(https?://[^"]+)"[^>]*>\s*(https?://[^<]+)\s*</a>', body, re.I):
            href = html.unescape(href).strip(); label = html.unescape(label).strip()
            d = domain(href)
            if not href.startswith("http") or not d or any(d == x or d.endswith("." + x) for x in DENY): continue
            if label.strip("/") in (href.strip("/"), d): candidates.append(href)
        if not name or not candidates: return {"source_url":url,"decision":"drop","reason":"required_missing"}
        official = candidates[0]
        phone = ""
        return {"company_name":name,"url":official,"address":"","phone":phone,"maps_url":"","status":"MEOハブ候補","source_url":url,"business_description":desc[:1200],"hub_evidence":"Web制作会社プロフィール","recurring_evidence":"","decision":"keep","reason":""}
    except requests.RequestException as e: return {"source_url":url,"decision":"drop","reason":type(e).__name__}

def write(path, rows):
    fields=sorted({k for r in rows for k in r})
    with open(path,"w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--existing",required=True); ap.add_argument("--out",required=True); ap.add_argument("--audit",required=True); ap.add_argument("--start",type=int,default=0); ap.add_argument("--end",type=int,default=2000); ap.add_argument("--workers",type=int,default=12); a=ap.parse_args()
    xml=get("https://web-kanji.com/sitemap-company.xml").text
    urls=re.findall(r"<loc>(https://web-kanji\.com/companies/[^<]+)</loc>",xml)[a.start:a.end]
    existing=json.loads(Path(a.existing).read_text(encoding="utf-8-sig")); names={nname(x.get("company_name")) for x in existing}; domains={domain(x.get("url")) for x in existing}
    kept=[]; audit=[]
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        fs=[pool.submit(parse,u) for u in urls]
        for i,f in enumerate(as_completed(fs),1):
            r=f.result(); n=nname(r.get("company_name")); d=domain(r.get("url"))
            if r.get("decision")=="keep" and n not in names and d and d not in domains:
                names.add(n); domains.add(d); kept.append(r)
            elif r.get("decision")=="keep": r["decision"]="drop"; r["reason"]="existing_or_duplicate"
            audit.append(r)
            if i%100==0: write(a.out,kept); write(a.audit,audit); print(json.dumps({"details":i,"kept":len(kept)},ensure_ascii=False),flush=True)
    write(a.out,kept); write(a.audit,audit); print(json.dumps({"done":True,"kept":len(kept)},ensure_ascii=False))

if __name__=="__main__": main()
