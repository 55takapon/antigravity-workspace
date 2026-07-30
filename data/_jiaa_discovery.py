import csv
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = ROOT / "data" / "_exclude_plus_existing_webmarketing_live.json"
OUT = ROOT / "data" / "_jiaa_candidates.csv"


def clean(value):
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(re.sub(r"\s+", " ", value)).strip()


def domain(url):
    host = urlparse(url).netloc.lower().split("@")[-1].split(":")[0]
    return host.removeprefix("www.")


page = requests.get("https://www.jiaa.org/jiaa/kaiin/", timeout=30)
page.raise_for_status()
links = re.findall(
    r'<a[^>]+href=["\'](https?[^"\']+)["\'][^>]*>(.*?)</a>',
    page.text,
    re.I | re.S,
)

raw = json.loads(EXCLUDE.read_text(encoding="utf-8"))
if isinstance(raw, dict):
    pools = []
    for value in raw.values():
        if isinstance(value, list):
            pools.extend(value)
else:
    pools = raw

existing_names = set()
existing_domains = set()
existing_phones = set()
for row in pools:
    if not isinstance(row, dict):
        continue
    name = str(row.get("company_name") or row.get("会社名") or "").strip()
    url = str(row.get("url") or row.get("URL") or "").strip()
    phone = re.sub(r"\D", "", str(row.get("phone") or row.get("電話番号") or ""))
    if name:
        existing_names.add(re.sub(r"\s+", "", name).lower())
    if url:
        existing_domains.add(domain(url))
    if phone:
        existing_phones.add(phone)

seen = set()
rows = []
for url, label in links:
    name = clean(label)
    dom = domain(html.unescape(url))
    key = (re.sub(r"\s+", "", name).lower(), dom)
    if not name or not dom or dom == "jiaa.org" or key in seen:
        continue
    seen.add(key)
    rows.append(
        {
            "company_name": name,
            "url": html.unescape(url),
            "domain": dom,
            "existing_name": key[0] in existing_names,
            "existing_domain": dom in existing_domains,
        }
    )

with OUT.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

fresh = [r for r in rows if not r["existing_name"] and not r["existing_domain"]]
print(json.dumps({"jiaa_links": len(rows), "fresh": len(fresh), "out": str(OUT)}, ensure_ascii=False))
for row in fresh:
    print(f'{row["company_name"]}\t{row["url"]}')
