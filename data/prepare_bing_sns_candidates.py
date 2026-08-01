import csv
import json
import re
from pathlib import Path
from urllib.parse import urlparse


BLOCKED = (
    "bing.com", "google.com", "prtimes.jp", "wantedly.com", "indeed.com",
    "en-gage.net", "facebook.com", "instagram.com", "youtube.com", "x.com",
    "twitter.com", "tiktok.com", "note.com", "ameblo.jp", "wikipedia.org",
    "kakaku.com", "itreview.jp", "boxil.jp", "imitsu.jp", "comparaku.com",
)


def host(url):
    try:
        return urlparse(url).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def company_name(title):
    value = re.split(r"[|｜\-–—]| - ", title or "", maxsplit=1)[0].strip()
    value = re.sub(r"\s*(公式サイト|ホームページ|TOP|トップページ)\s*$", "", value, flags=re.I)
    return value[:120]


rows = []
seen = set()
for path in sorted(Path("data").glob("bing_sns_seg1_*.json")):
    for item in json.loads(path.read_text(encoding="utf-8")):
        url = (item.get("website") or "").strip()
        domain = host(url)
        if not domain or any(domain == b or domain.endswith("." + b) for b in BLOCKED):
            continue
        if domain in seen:
            continue
        seen.add(domain)
        rows.append({
            "company_name": company_name(item.get("title", "")),
            "url": url,
            "address": "",
            "phone": "",
            "maps_url": "",
            "area_hint": item.get("area", ""),
            "query": item.get("query", ""),
        })

fields = ["company_name", "url", "address", "phone", "maps_url", "area_hint", "query"]
with Path("data/sns_bing_candidates_wave2.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
print(f"candidates={len(rows)}")
