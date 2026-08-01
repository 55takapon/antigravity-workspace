import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import collect_yahoo_sns as yahoo
import collect_bing_sns as base


TERMS = [
    "飲食店 SNS運用支援会社", "美容室 Instagram運用代行", "クリニック SNS運用代行",
    "不動産 SNSマーケティング会社", "学習塾 SNS運用代行", "採用広報 SNS運用会社",
    "観光プロモーション SNS会社", "EC SNS運用代行", "ホテル SNS運用代行",
    "店舗 Instagram集客支援", "中小企業 SNS運用支援", "SNSコンテンツ制作会社",
]
tasks = [(city, term, 0) for city in base.CITIES for term in TERMS]
found = []
with ThreadPoolExecutor(max_workers=2) as executor:
    futures = [executor.submit(yahoo.search, task) for task in tasks]
    for index, future in enumerate(as_completed(futures), 1):
        found.extend(future.result())
        if index % 50 == 0:
            print(f"queries={index}/{len(tasks)} raw={len(found)}", flush=True)
deduped, seen = [], set()
for row in found:
    domain = base.host(row["url"])
    if domain in seen:
        continue
    seen.add(domain); deduped.append(row)
fields = ["company_name", "url", "address", "phone", "maps_url", "area_hint", "query"]
with Path("data/sns_yahoo_candidates_wave8.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader(); writer.writerows(deduped)
print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))
