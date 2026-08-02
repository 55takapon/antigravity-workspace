from __future__ import annotations

import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from html.parser import HTMLParser

HERE = Path(__file__).parent

EXCLUDED = {
    "株式会社ITreat", "Kurumi株式会社", "株式会社ゼロメディカル",
    "株式会社デンタル・インターネット", "デンタルウェブ",
}
CORRECTIONS = {
    "株式会社Z-IT": "株式会社ジット",
    "株式会社メディアコンテンツファクトリー": "株式会社ホウエイヴェリティス",
    "FLEURIR": "有限会社アップルハウス",
}


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "a" and attrs.get("href"):
            self.current = {"href": attrs["href"], "text": "", "alt_title": attrs.get("title", "")}
        elif tag.lower() == "img" and self.current:
            self.current["alt_title"] += " " + attrs.get("alt", "")
    def handle_data(self, data):
        if self.current:
            self.current["text"] += data
    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.current:
            self.links.append(self.current)
            self.current = None


def fetch(row):
    url = row["url"]
    links = []
    text = ""
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 list-audit/1.0"})
        r.raise_for_status()
        r.encoding = r.apparent_encoding or r.encoding
        parser = LinkParser()
        parser.feed(r.text)
        text = re.sub(r"<[^>]+>", " ", r.text)[:120000]
        for a in parser.links:
            links.append({
                "href": urljoin(r.url, a["href"]),
                "text": re.sub(r"\s+", " ", a["text"]).strip()[:300],
                "alt_title": re.sub(r"\s+", " ", a["alt_title"]).strip()[:300],
            })
    except Exception as exc:
        text = f"FETCH_ERROR {type(exc).__name__}"
    return row, {"base_url": url, "links": links[:500]}, text


rows = []
seen = set()
for file in sorted(HERE.glob("new_candidates*.csv")):
    with file.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if not row.get("url") or row["company_name"] in EXCLUDED:
                continue
            row["company_name"] = CORRECTIONS.get(row["company_name"], row["company_name"])
            host = (urlparse(row["url"]).hostname or "").lower().removeprefix("www.")
            if not host or host in seen:
                continue
            seen.add(host)
            rows.append(row)

with ThreadPoolExecutor(max_workers=10) as pool:
    fetched = list(pool.map(fetch, rows))

with (HERE / "full_candidates_precontact.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["company_name", "url", "address", "phone", "maps_url", "contact_url"])
    w.writeheader()
    w.writerows(row for row, _, _ in fetched)

(HERE / "full_contact_batch.json").write_text(json.dumps([page for _, page, _ in fetched], ensure_ascii=False), encoding="utf-8")
(HERE / "full_home_text.json").write_text(json.dumps([{"company_name": row["company_name"], "url": row["url"], "text": text} for row, _, text in fetched], ensure_ascii=False), encoding="utf-8")
print(f"candidates={len(rows)} fetched={sum(not text.startswith('FETCH_ERROR') for _,_,text in fetched)}")
