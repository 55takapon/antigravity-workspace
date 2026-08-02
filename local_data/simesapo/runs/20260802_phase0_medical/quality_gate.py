from __future__ import annotations

import csv
import html
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

HERE = Path(__file__).parent
MASTER = Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\custmize\enterprise_filter")


def norm(v: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", v or "").lower())


def company_norm(v: str) -> str:
    v = norm(v)
    return re.sub(r"株式会社|有限会社|合同会社|一般社団法人|一般財団法人|\(株\)|\(有\)|\(同\)|[・･.,，．_/'\"()（）\[\]［］-]", "", v)


def domain(v: str) -> str:
    if not re.match(r"^https?://", v or "", re.I): v = "https://" + (v or "")
    return re.sub(r"^www\.", "", (urlparse(v).hostname or "").lower())


def text_of(source: str) -> str:
    source = re.sub(r"<(script|style|noscript)\b[^>]*>.*?</\1>", " ", source, flags=re.I|re.S)
    return norm(html.unescape(re.sub(r"<[^>]+>", " ", source)))


def get(session, url):
    try:
        r=session.get(url, timeout=15, allow_redirects=True, headers={"User-Agent":"Mozilla/5.0 list-quality-audit/1.0"})
        if r.status_code >= 400: return "", url
        r.encoding=r.apparent_encoding or r.encoding
        return r.text, r.url
    except requests.RequestException:
        return "", url


def load_enterprise():
    names=set(); domains=set()
    for file in ("confirmed_enterprise_exclusions.csv", "jpx_listed_companies_20260630.csv"):
        with (MASTER/file).open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                name=r.get("company_name") or r.get("name") or r.get("match_value") or ""
                if name: names.add(company_norm(name))
                d=domain(r.get("url") or r.get("domain") or "") if (r.get("url") or r.get("domain")) else ""
                if d: domains.add(d)
    return names,domains


ENT_NAMES, ENT_DOMAINS = load_enterprise()
BLOCK = re.compile(r"(?:営業|売り込み|セールス|勧誘).{0,30}(?:お断り|禁止|不可|ご遠慮|受け付けておりません|固くお断り)|(?:お断り|禁止|不可|ご遠慮).{0,30}(?:営業|売り込み|セールス|勧誘)")
SERVICE = re.compile(r"(?:歯科|医科|医療|医院|クリニック|病院).{0,80}(?:ホームページ|web|ウェブ).{0,40}(?:制作|作成|運用|マーケティング|集患)|(?:ホームページ|web|ウェブ).{0,40}(?:制作|作成|運用|マーケティング).{0,80}(?:歯科|医科|医療|医院|クリニック|病院)")


def inspect(row):
    session=requests.Session(); url=row["url"]; root=f"{urlparse(url).scheme or 'https'}://{urlparse(url).netloc}/"
    pages=[]
    for u in dict.fromkeys([url,root,urljoin(root,"company/"),urljoin(root,"about/"),urljoin(root,"profile/"),row.get("contact_url","")]):
        if not u: continue
        source,final=get(session,u)
        if source: pages.append((final,text_of(source)))
    combined="".join(t for _,t in pages)
    cname=company_norm(row["company_name"])
    company_ok=bool(cname and cname in company_norm(combined))
    service_ok=bool(SERVICE.search(combined))
    block=bool(BLOCK.search(combined))
    ent=(cname in ENT_NAMES) or (domain(url) in ENT_DOMAINS)
    if not row.get("contact_url"): decision="drop_no_contact"
    elif ent: decision="drop_enterprise"
    elif block: decision="drop_sales_prohibited"
    elif not service_ok: decision="review_service_evidence"
    elif not company_ok: decision="review_company_identity"
    else: decision="accept"
    row.update({"decision":decision,"company_identity_ok":str(company_ok).lower(),"service_evidence_ok":str(service_ok).lower(),"sales_prohibited":str(block).lower(),"enterprise_match":str(ent).lower(),"proposal_category":"S｜業界特化Web制作","evidence_term":"歯科・医療機関向けホームページ制作・運用"})
    return row


rows=list(csv.DictReader((HERE/"candidates_with_contacts.csv").open(encoding="utf-8-sig",newline="")))
with ThreadPoolExecutor(max_workers=8) as ex: out=list(ex.map(inspect,rows))
with (HERE/"quality_gate_results.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)
from collections import Counter
print(dict(Counter(r["decision"] for r in out)))
