import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import collect_bing_sns as base


TERMS = [
    "店舗集客 SNS支援", "地域密着 SNS運用会社",
    "飲食店 SNSマーケティング会社", "美容 SNSマーケティング会社",
    "医療 SNSマーケティング会社", "不動産 SNSマーケティング会社",
    "中小企業 SNS広告運用", "地域広告代理店 Web集客",
    "Web制作 SNS運用支援", "店舗向け デジタルマーケティング",
    "販売促進 SNS支援会社", "地域ブランディング SNS",
]
tasks = [(city, term) for city in base.CITIES for term in TERMS]
found = []
with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [executor.submit(base.search, task) for task in tasks]
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
with Path("data/sns_partner_candidates_wave6.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(deduped)
print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))
