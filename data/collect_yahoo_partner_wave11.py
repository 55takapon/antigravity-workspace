import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import collect_yahoo_sns as yahoo
import collect_bing_sns as base


TERMS = [
    "ソーシャルメディア コンサルティング会社", "Instagram コンテンツ制作 運用会社",
    "LINE公式 自動化 マーケティング会社", "UGC マーケティング 支援会社",
    "インフルエンサー施策 運用会社", "ショート動画 SNSマーケティング会社",
    "広告クリエイティブ 運用会社", "Webサイト 運用改善 支援会社",
    "顧客管理 CRM マーケティング支援", "LPO Web広告 改善会社",
    "ECサイト 集客運用 支援会社", "中小企業 コンテンツ制作 マーケティング",
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
with Path("data/sns_partner_candidates_wave11.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(deduped)
print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))
