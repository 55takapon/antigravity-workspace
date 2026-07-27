import csv
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

BASE = Path("data")
PREFS = {
    "神奈川県": "14_kanagawa",
    "埼玉県": "11_saitama",
    "千葉県": "12_chiba",
    "茨城県": "08_ibaraki",
    "群馬県": "10_gunma",
    "栃木県": "09_tochigi",
}

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 Chrome/120 Safari/537.36"})


def norm_url(url):
    url = (url or "").strip().lower()
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^www\.", "", url)
    return url.split("/")[0].rstrip("/")


def norm_name(name):
    return re.sub(
        r"株式会社|有限会社|合同会社|一般社団法人|（株）|\(株\)|[\s　・,，.。/／｜|（）()\[\]【】「」\-ー]",
        "",
        (name or "").lower(),
    )


def external(url):
    host = urlparse(url).netloc.lower()
    return host and "biz.ne.jp" not in host and "schema.org" not in host and "googletagmanager" not in host


def collect_pref(label, code):
    url = f"https://www.biz.ne.jp/list/web/{code}/"
    html = session.get(url, timeout=20).text
    soup = BeautifulSoup(html, "html.parser")
    records = []
    for h in soup.find_all(["h3", "h2"]):
        name = h.get_text(" ", strip=True)
        if not name or len(name) > 60:
            continue
        block = h.find_parent()
        for _ in range(5):
            if block and len(block.get_text(" ", strip=True)) < 250:
                block = block.find_parent()
        if not block:
            continue
        text = block.get_text("\n", strip=True)
        if "ホームページ制作" not in text and "Web" not in text and "ウェブ" not in text:
            continue
        urls = []
        for a in block.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("http") and external(href):
                urls.append(href)
        if not urls:
            continue
        addr = ""
        m = re.search(rf"{label}[^\n\r　]*[^\n\r]*", text)
        if m:
            addr = m.group(0)
        records.append(
            {
                "company_name": name,
                "url": urls[0],
                "address": addr,
                "phone": "",
                "maps_url": "",
                "prefecture": label,
            }
        )
    return records


exclude = json.loads((BASE / "_exclude_plus_existing_kanto2.json").read_text(encoding="utf-8"))
exu = {norm_url(r.get("url", "")) for r in exclude if r.get("url")}
exn = {norm_name(r.get("company_name", "")) for r in exclude if r.get("company_name")}

all_records = []
input_counts = Counter()
for label, code in PREFS.items():
    got = collect_pref(label, code)
    input_counts[label] = len(got)
    all_records.extend(got)

kept = []
seen_u = set()
seen_n = set()
drop = Counter()
kept_pref = Counter()
for rec in all_records:
    u = norm_url(rec["url"])
    n = norm_name(rec["company_name"])
    if not u or not n:
        drop["blank"] += 1
    elif u in exu or n in exn:
        drop["existing"] += 1
    elif u in seen_u or n in seen_n:
        drop["batch_dup"] += 1
    else:
        seen_u.add(u)
        seen_n.add(n)
        kept.append(rec)
        kept_pref[rec["prefecture"]] += 1

out = BASE / "list_kanto_non_tokyo_biz_filtered.csv"
with out.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["company_name", "url", "address", "phone", "maps_url"])
    w.writeheader()
    w.writerows([{k: r.get(k, "") for k in ["company_name", "url", "address", "phone", "maps_url"]} for r in kept])

(BASE / "_kanto_non_tokyo_biz_stats.json").write_text(
    json.dumps(
        {
            "input_counts": input_counts,
            "kept_pref": kept_pref,
            "drop": drop,
            "input_total": len(all_records),
            "kept_total": len(kept),
        },
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
print("input", len(all_records), dict(input_counts))
print("kept", len(kept), dict(kept_pref), "drop", dict(drop))
