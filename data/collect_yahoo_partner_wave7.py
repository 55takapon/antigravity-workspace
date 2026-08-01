import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import collect_yahoo_sns as yahoo
import collect_bing_sns as base


TERMS = [
    "PR会社 SNS運用支援", "広報支援 デジタルマーケティング",
    "広告制作会社 Webマーケティング", "デザイン会社 SNS運用支援",
    "クリエイティブ会社 SNSマーケティング", "動画マーケティング SNS運用",
    "採用マーケティング SNS運用", "ECマーケティング SNS支援",
    "地域活性化 プロモーション会社", "観光マーケティング SNS支援",
    "店舗コンサルティング Web集客", "地域企業 ブランディング Web集客",
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
with Path("data/sns_partner_candidates_wave7.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(deduped)
print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))
