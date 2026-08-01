import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup

import collect_bing_sns as base


TERMS = [
    "SNS運用代行 株式会社", "インスタ運用代行 株式会社", "Instagram運用代行 株式会社",
    "TikTok運用代行 株式会社", "SNSマーケティング 株式会社", "SNSコンサルティング 株式会社",
    "SNS広告運用 株式会社", "採用SNS運用 株式会社", "YouTube運用代行 株式会社",
    "LINE公式アカウント運用 株式会社", "ショート動画運用代行 株式会社",
    "SNSプロモーション 株式会社", "ソーシャルメディア運用 株式会社",
    "企業SNS運用 株式会社", "飲食店 SNS運用代行", "クリニック SNS運用代行",
    "美容業界 SNS運用代行", "不動産 SNS運用代行", "観光 SNSプロモーション",
    "SNS投稿代行 株式会社", "Instagram広告運用 株式会社", "Meta広告運用 株式会社",
]


def search(task):
    term, page = task
    query = f'"{term}" -おすすめ -比較 -ランキング -求人 -まとめ'
    try:
        response = requests.get(
            "https://www.bing.com/search",
            params={"q": query, "count": 10, "first": page * 10 + 1},
            headers={"User-Agent": "Mozilla/5.0"}, timeout=(5, 20),
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rows = []
        for item in soup.select("li.b_algo"):
            anchor = item.select_one("h2 a")
            if not anchor:
                continue
            url = base.decode_url(anchor.get("href", ""))
            domain = base.host(url)
            if not domain or any(domain == b or domain.endswith("." + b) for b in base.BLOCKED):
                continue
            rows.append({"company_name": base.clean_name(anchor.get_text(" ", strip=True)), "url": url, "address": "", "phone": "", "maps_url": "", "area_hint": "全国", "query": query})
        return rows
    except requests.RequestException:
        return []


tasks = [(term, page) for term in TERMS for page in range(8)]
found = []
with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [executor.submit(search, task) for task in tasks]
    for index, future in enumerate(as_completed(futures), 1):
        found.extend(future.result())
        if index % 20 == 0:
            print(f"queries={index}/{len(tasks)} raw={len(found)}", flush=True)

deduped, seen = [], set()
for row in found:
    domain = base.host(row["url"])
    if domain in seen:
        continue
    seen.add(domain)
    deduped.append(row)
fields = ["company_name", "url", "address", "phone", "maps_url", "area_hint", "query"]
with Path("data/sns_bing_candidates_wave4.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader(); writer.writerows(deduped)
print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))
