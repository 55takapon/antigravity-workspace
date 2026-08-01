import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import collect_yahoo_sns as yahoo
import collect_bing_sns as base


TERMS = [
    "飲食店 プロモーション会社", "美容室 販促企画会社",
    "クリニック 広告制作会社 Web", "不動産 プロモーション会社 Web",
    "工務店 販促支援会社", "学習塾 広報支援会社",
    "店舗撮影 SNS運用会社", "インフルエンサーマーケティング会社",
    "LINEマーケティング会社", "コンテンツ制作 SNS運用会社",
    "ホームページ制作 Web広告運用", "中小企業 広報マーケティング支援",
]
tasks = [(city, term, 0) for city in base.CITIES[:36] for term in TERMS]
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
with Path("data/sns_partner_candidates_wave8.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(deduped)
print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))
