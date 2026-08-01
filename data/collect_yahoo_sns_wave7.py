import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import collect_yahoo_sns as yahoo
import collect_bing_sns as base


TERMS = [
    "SNS集客支援会社", "Instagram集客支援会社", "SNSコンサル会社",
    "SNS運用サポート会社", "SNSアカウント運用会社", "インスタグラム集客支援",
    "TikTokマーケティング会社", "動画マーケティング会社",
    "SNSプロモーション会社", "SNSブランディング会社",
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
with Path("data/sns_yahoo_candidates_wave7.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader(); writer.writerows(deduped)
print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))
