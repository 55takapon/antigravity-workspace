import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import collect_yahoo_sns as yahoo
import collect_bing_sns as base


TERMS = [
    "店舗集客支援会社 SNS", "飲食店集客 SNS運用会社", "美容室集客 Instagram運用会社",
    "クリニック集客 SNS運用会社", "歯科医院 SNS集客支援会社", "不動産集客 SNS運用会社",
    "学習塾集客 SNS運用会社", "地域密着 広告代理店 SNS", "Web制作 SNS運用 中小企業",
    "店舗マーケティング会社 SNS", "多店舗集客 SNS運用会社", "LINE Instagram 店舗集客支援",
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
with Path("data/sns_partner_candidates_wave1.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader(); writer.writerows(deduped)
print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))
