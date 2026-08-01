import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import collect_yahoo_sns as yahoo
import collect_bing_sns as base


TERMS = [
    "飲食店 集客マーケティング会社", "美容サロン 集客マーケティング会社",
    "クリニック 広告マーケティング会社", "歯科 集患マーケティング会社",
    "不動産 集客マーケティング会社", "住宅 工務店 販促マーケティング",
    "学習塾 生徒募集 マーケティング会社", "ホテル 旅館 集客支援会社",
    "自動車販売 集客支援会社", "小売店 販促デジタル支援",
    "フランチャイズ 集客支援会社", "観光 集客プロモーション会社",
    "地域イベント プロモーション会社", "地域企業 広報マーケティング会社",
]
tasks = [(city, term, 0) for city in base.CITIES[36:] for term in TERMS]
found = []
with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [executor.submit(yahoo.search, task) for task in tasks]
    for index, future in enumerate(as_completed(futures), 1):
        found.extend(future.result())
        if index % 50 == 0:
            print(f"queries={index}/{len(tasks)} raw={len(found)}", flush=True)
deduped, seen = [], set()
for row in found:
    key = base.host(row["url"])
    if key in seen:
        continue
    seen.add(key)
    deduped.append(row)
fields = ["company_name", "url", "address", "phone", "maps_url", "area_hint", "query"]
with Path("data/sns_partner_candidates_wave9.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(deduped)
print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))
