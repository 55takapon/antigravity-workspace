from __future__ import annotations

import argparse
import csv
import html
import re
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

HERE = Path(__file__).parent
MASTER = Path(r"C:\Users\hangy\.gemini\antigravity\.agent\skills\simesapo-sales-skills-dist\custmize\enterprise_filter")

def norm(v: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", v or "").lower())

def company_norm(v: str) -> str:
    return re.sub(r"株式会社|有限会社|合同会社|一般社団法人|一般財団法人|\(株\)|\(有\)|\(同\)|[・･.,，．_/'\"()（）\[\]［］-]", "", norm(v))

def domain(v: str) -> str:
    if not re.match(r"^https?://", v or "", re.I): v = "https://" + (v or "")
    return re.sub(r"^www\.", "", (urlparse(v).hostname or "").lower())

def text_of(source: str) -> str:
    source = re.sub(r"<(script|style|noscript)\b[^>]*>.*?</\1>", " ", source, flags=re.I | re.S)
    return norm(html.unescape(re.sub(r"<[^>]+>", " ", source)))

def get(session: requests.Session, url: str):
    try:
        r = session.get(url, timeout=12, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0 prospect-quality-audit/1.0"})
        if r.status_code >= 400: return "", url
        r.encoding = r.apparent_encoding or r.encoding
        return r.text, r.url
    except requests.RequestException:
        return "", url

def load_enterprise():
    names, domains = set(), set()
    for file in ("confirmed_enterprise_exclusions.csv", "jpx_listed_companies_20260630.csv"):
        with (MASTER / file).open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                name = row.get("company_name") or row.get("name") or row.get("match_value") or ""
                if name: names.add(company_norm(name))
                raw_domain = row.get("url") or row.get("domain") or ""
                if raw_domain: domains.add(domain(raw_domain))
    return names, domains

ENT_NAMES, ENT_DOMAINS = load_enterprise()
BLOCK = re.compile(r"(?:営業|売り込み|セールス|勧誘|協業|提携).{0,45}(?:お断り|禁止|不可|ご遠慮|受け付けておりません|固くお断り)|(?:お断り|禁止|不可|ご遠慮).{0,45}(?:営業|売り込み|セールス|勧誘|協業|提携)")
SERVICE = re.compile(r"(?:歯科|医科|医療|医院|クリニック|病院|動物病院|整骨院|接骨院|治療院|薬局).{0,100}(?:ホームページ|web|ウェブ|サイト).{0,60}(?:制作|作成|運用|マーケティング|集患)|(?:ホームページ|web|ウェブ|サイト).{0,60}(?:制作|作成|運用|マーケティング).{0,100}(?:歯科|医科|医療|医院|クリニック|病院|動物病院|整骨院|接骨院|治療院|薬局)")

def inspect(row):
    session = requests.Session()
    parsed = urlparse(row["url"])
    root = f"{parsed.scheme or 'https'}://{parsed.netloc}/"
    urls = [row["url"], root]
    for path in ("company/", "company.html", "about/", "about.html", "profile/", "profile.html", "contact/", "contact.html"):
        urls.append(urljoin(root, path))
    urls.append(row.get("contact_url", ""))
    texts = []
    for url in dict.fromkeys(u for u in urls if u):
        source, _ = get(session, url)
        if source: texts.append(text_of(source))
    combined = "".join(texts)
    cname = company_norm(row["company_name"])
    company_ok = bool(cname and cname in company_norm(combined))
    service_ok = bool(SERVICE.search(combined))
    block = bool(BLOCK.search(combined))
    ent = cname in ENT_NAMES or domain(row["url"]) in ENT_DOMAINS
    contact_ok = False
    if row.get("contact_url"):
        source, final = get(session, row["contact_url"])
        contact_ok = bool(source and ("form" in source.lower() or "<input" in source.lower() or "<textarea" in source.lower() or "docs.google.com/forms" in final))
    if not row.get("contact_url") or not contact_ok: decision = "drop_no_verified_contact"
    elif ent: decision = "drop_enterprise"
    elif block: decision = "drop_sales_prohibited"
    elif not service_ok: decision = "review_service_evidence"
    elif not company_ok: decision = "review_company_identity"
    else: decision = "accept"
    row.update(decision=decision, company_identity_ok=str(company_ok).lower(), service_evidence_ok=str(service_ok).lower(), sales_prohibited=str(block).lower(), enterprise_match=str(ent).lower(), contact_verified=str(contact_ok).lower(), proposal_category="S｜業界特化Web制作", evidence_term="歯科・医療関連事業者向けWeb制作・運用")
    return row

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="full_candidates_with_contacts.csv")
parser.add_argument("--output", default="quality_gate_full_results.csv")
args = parser.parse_args()
rows = list(csv.DictReader((HERE / args.input).open(encoding="utf-8-sig", newline="")))
with ThreadPoolExecutor(max_workers=8) as ex:
    out = list(ex.map(inspect, rows))
with (HERE / args.output).open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=out[0].keys())
    writer.writeheader(); writer.writerows(out)
print(dict(Counter(r["decision"] for r in out)))
