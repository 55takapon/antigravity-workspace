import csv
import html
import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

import collect_bing_sns as base


TERMS = ["SNS運用代行 株式会社", "Instagram運用代行 株式会社", "TikTok運用代行 株式会社", "SNSマーケティング 株式会社"]
EXTRA_BLOCKED = ("search.yahoo.co.jp", "yahoo.co.jp", "listing.yahoo.co.jp", "digi-mado.jp", "stock-sun.com", "kingprotea.jp", "monochro-marketing.co.jp", "kame-rad.co.jp", "comperu.jp")
local = threading.local()


def session():
    if not hasattr(local, "session"):
        value = requests.Session()
        value.headers["User-Agent"] = "Mozilla/5.0"
        local.session = value
    return local.session


def search(task):
    city, term, page = task
    query = f"{city} {term} -おすすめ -比較 -ランキング -求人 -まとめ"
    try:
        response = session().get("https://search.yahoo.co.jp/search", params={"p": query, "ei": "UTF-8", "b": page * 10 + 1}, timeout=(5, 20))
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rows = []
        for anchor in soup.select("a[href]"):
            url = html.unescape(anchor.get("href", "")).strip()
            domain = base.host(url)
            title = anchor.get_text(" ", strip=True)
            if not domain or not title or urlparse(url).scheme not in ("http", "https"):
                continue
            blocked = base.BLOCKED + EXTRA_BLOCKED
            if any(domain == b or domain.endswith("." + b) for b in blocked):
                continue
            if any(word in title for word in ("おすすめ", "比較", "ランキング", "求人", "一覧", "選！", "選｜", "選【")):
                continue
            rows.append({"company_name": base.clean_name(title), "url": url, "address": "", "phone": "", "maps_url": "", "area_hint": city, "query": query})
        time.sleep(random.uniform(0.35, 0.7))
        return rows
    except requests.RequestException:
        time.sleep(1.0)
        return []


def main():
    tasks = [(city, term, page) for city in base.CITIES for term in TERMS for page in range(3)]
    found = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(search, task) for task in tasks]
        for index, future in enumerate(as_completed(futures), 1):
            found.extend(future.result())
            if index % 50 == 0:
                print(f"queries={index}/{len(tasks)} raw={len(found)}", flush=True)

    deduped, seen = [], set()
    for row in found:
        domain = base.host(row["url"])
        if domain in seen:
            continue
        seen.add(domain)
        deduped.append(row)
    fields = ["company_name", "url", "address", "phone", "maps_url", "area_hint", "query"]
    with Path("data/sns_yahoo_candidates_wave5.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(deduped)
    print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
