from __future__ import annotations

import argparse, csv, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

UA={"User-Agent":"Mozilla/5.0 (compatible; SimesapoResearch/1.0)"}
LABEL=re.compile(r"お問い合わせ|お問合せ|問い合わせ|ご相談|contact|inquiry|メールフォーム",re.I)
PATH=re.compile(r"contact|inquiry|toiawase|otoiawase|form|soudan",re.I)

def is_form(url):
    try:
        r=requests.get(url,headers=UA,timeout=20,allow_redirects=True); r.raise_for_status()
        if "html" not in r.headers.get("content-type","").lower(): return None
        s=BeautifulSoup(r.text,"html.parser")
        for f in s.find_all("form"):
            if f.find(["input","textarea","select"]): return r.url
        embeds=" ".join(t.get("src","") for t in s.find_all(["iframe","script"]) if t.get("src"))
        if re.search(r"google\.com/forms|contact-form|ninja-forms|pardot|form\.movabletype|hubspot",embeds,re.I): return r.url
    except requests.RequestException: pass
    return None

def repair(row):
    if found:=is_form(row.get("contact_url", "")): row["contact_url"]=found; return row,"kept"
    try:
        r=requests.get(row["url"],headers=UA,timeout=20,allow_redirects=True); r.raise_for_status()
        soup=BeautifulSoup(r.text,"html.parser"); base_host=(urlparse(r.url).hostname or "").removeprefix("www.")
        links=[]
        for a in soup.find_all("a",href=True):
            u=urljoin(r.url,a["href"]); host=(urlparse(u).hostname or "").removeprefix("www.")
            if host==base_host and (LABEL.search(a.get_text(" ",strip=True)) or PATH.search(urlparse(u).path)):
                if u not in links: links.append(u)
        for u in links[:8]:
            if found:=is_form(u): row["contact_url"]=found; return row,"repaired"
    except requests.RequestException: pass
    return None,"unresolved"

p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--output",required=True); a=p.parse_args()
rows=list(csv.DictReader(open(a.input,encoding="utf-8-sig",newline="")))
out=[]; stats={}
with ThreadPoolExecutor(max_workers=12) as ex:
    futs={ex.submit(repair,dict(r)):i for i,r in enumerate(rows)}; got=[]
    for f in as_completed(futs):
        row,status=f.result(); stats[status]=stats.get(status,0)+1
        if row: got.append((futs[f],row))
out=[r for _,r in sorted(got)]
with open(a.output,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(out)
print({"input":len(rows),"valid":len(out),**stats,"output":a.output})
