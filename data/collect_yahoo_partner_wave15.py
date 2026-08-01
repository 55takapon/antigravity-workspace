import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import collect_yahoo_sns as yahoo
import collect_bing_sns as base


TERMS = [
    "顧客体験 CX マーケティング支援会社", "リピーター 集客支援会社",
    "メールマーケティング 運用支援会社", "LINE販促 CRM 支援会社",
    "デジタルサイネージ 店舗販促会社", "デジタルクーポン 販促支援",
    "口コミマーケティング 支援会社", "ファンマーケティング 支援会社",
    "Webアクセス解析 改善支援会社", "SEO コンテンツ制作 支援会社",
    "EC運営 Web広告 支援会社", "地域企業 DXマーケティング支援",
]
tasks = [(city, term, 0) for city in base.CITIES[:50] for term in TERMS]
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
with Path("data/sns_partner_candidates_wave15.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(deduped)
print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))
