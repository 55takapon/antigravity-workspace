import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import collect_yahoo_sns as yahoo
import collect_bing_sns as base


TERMS = [
    "販促デザイン Webマーケティング会社", "グラフィックデザイン SNS運用会社",
    "イベント企画 デジタルプロモーション会社", "プレスリリース SNS広報支援",
    "採用広報 コンテンツ制作会社", "オウンドメディア SNS運用支援",
    "店舗アプリ 集客マーケティング会社", "会員アプリ CRM 販促支援",
    "予約システム 店舗集客支援会社", "多店舗 販売促進 デジタル支援",
    "地域商店 販促プロモーション会社", "印刷 Web販促 支援会社",
]
tasks = [(city, term, 0) for city in base.CITIES[20:] for term in TERMS]
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
with Path("data/sns_partner_candidates_wave13.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fields)
    writer.writeheader()
    writer.writerows(deduped)
print(json.dumps({"queries": len(tasks), "raw": len(found), "domains": len(deduped)}, ensure_ascii=False))
