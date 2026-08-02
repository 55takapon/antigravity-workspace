from __future__ import annotations

import csv
import json
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse

import argparse
import requests

HERE = Path(__file__).parent

def norm(v): return re.sub(r"\s+", "", unicodedata.normalize("NFKC", v or "").lower())
def cname(v): return re.sub(r"株式会社|有限会社|合同会社|\(株\)|\(有\)|\(同\)|[・･.,，．_/'\"()（）\[\]［］:-]", "", norm(v))
def domain(v): return re.sub(r"^www\.", "", (urlparse(v).hostname or "").lower())

existing = json.loads((HERE / "existing_master.json").read_text(encoding="utf-8"))
existing_names = {cname(r.get("company_name", "")) for r in existing if r.get("company_name")}
existing_domains = {domain(r.get("url", "")) for r in existing if r.get("url")}
first_domains = {domain(r["url"]) for r in csv.DictReader((HERE / "full_candidates_precontact.csv").open(encoding="utf-8-sig"))}

def fetch(row):
    s = requests.Session(); s.headers["User-Agent"] = "Mozilla/5.0 prospect-discovery/1.0"
    try:
        r = s.get(row["url"], timeout=15, allow_redirects=True); r.raise_for_status(); r.encoding = r.apparent_encoding or r.encoding
    except requests.RequestException:
        row["prep_status"] = "fetch_failed"; return row
    scored = []
    for match in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", r.text, re.I | re.S):
        href = urljoin(r.url, match.group(1)); label = norm(re.sub(r"<[^>]+>", " ", match.group(2)))
        if urlparse(href).netloc and ("contact" in href.lower() or "inquiry" in href.lower() or "お問い合わせ" in label or "お問合せ" in label):
            score = 3 if ("contact" in href.lower() or "inquiry" in href.lower()) else 1
            scored.append((score, href.split("#")[0]))
    row["url"] = r.url
    row["contact_url"] = sorted(scored, reverse=True)[0][1] if scored else ""
    row["prep_status"] = "prepared"
    return row

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="additional_candidates.csv")
parser.add_argument("--output", default="additional_prepared.csv")
args = parser.parse_args()
rows = list(csv.DictReader((HERE / args.input).open(encoding="utf-8-sig", newline="")))
rows = [r for r in rows if cname(r["company_name"]) not in existing_names and domain(r["url"]) not in existing_domains and domain(r["url"]) not in first_domains]
with ThreadPoolExecutor(max_workers=8) as ex: rows = list(ex.map(fetch, rows))
with (HERE / args.output).open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print({"new_after_dedupe": len(rows), "prepared": sum(r["prep_status"] == "prepared" for r in rows), "contact": sum(bool(r["contact_url"]) for r in rows)})
