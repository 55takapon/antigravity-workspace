import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import collect_yahoo_sns as yahoo
import collect_bing_sns as base


TERMS = [
    "歯科 集客支援会社", "医療 Webマーケティング会社",
    "美容業界 販促支援会社", "飲食店 販促支援会社",
    "住宅会社 マーケティング支援", "工務店 集客支援会社",
    "士業 Web集客支援", "学習塾 Webマーケティング",
    "ホテル 集客支援会社", "地域プロモーション会社",
    "広告代理店 中小企業向け", "Webコンサルティング 地域企業",
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
    key = base.host(row["url"])
    if key in seen:
        continue
    seen.add(key)
    deduped.append(row)
fields = ["company_name", "url", "address", "phone", "maps_url", "area_hint", "query"]
with Path("data/sns_partner_candidates_wave3.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(deduped)
print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))
