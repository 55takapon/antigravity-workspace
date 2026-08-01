import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import collect_yahoo_sns as yahoo
import collect_bing_sns as base


TERMS = [
    "地元企業 Webプロモーション会社", "中小企業 広告制作 マーケティング",
    "店舗 販促ツール Web制作会社", "店舗撮影 Web集客 支援会社",
    "地域メディア運用 広告代理店", "SNSキャンペーン 企画会社",
    "Webキャンペーン 制作運用会社", "デジタルコンテンツ 制作会社 マーケティング",
    "ブランドサイト SNS運用支援", "企業動画 SNS広告 支援会社",
    "地域PR Web制作会社", "集客コンサル 制作会社",
]
tasks = [(city, term, 0) for city in base.CITIES[:40] for term in TERMS]
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
with Path("data/sns_partner_candidates_wave18.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(deduped)
print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))
