from __future__ import annotations

import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from collect_jja_candidates import fetch_candidate

HERE = Path(__file__).parent
CANDIDATES = [
    {"company_name": "株式会社プロブレイン", "url": "https://pbtokyo.co.jp/", "source_url": "https://pbtokyo.co.jp/"},
    {"company_name": "株式会社トキツカゼ", "url": "https://www.tokitsukaze-edu.jp/", "source_url": "https://www.tokitsukaze-edu.jp/"},
    {"company_name": "合同会社CROP", "url": "https://oneread.jp/", "source_url": "https://oneread.jp/service/"},
    {"company_name": "株式会社TSパートナーズ", "url": "https://jukugo-cloud.com/", "source_url": "https://jukugo-cloud.com/"},
    {"company_name": "VISH株式会社", "url": "https://www.buscatch.com/scholaplus/", "source_url": "https://www.buscatch.com/scholaplus/"},
    {"company_name": "テクノピアン株式会社", "url": "https://www.technosms.com/lp/", "source_url": "https://www.technosms.com/lp/"},
    {"company_name": "株式会社cantik", "url": "https://cantik.co.jp/school/", "source_url": "https://cantik.co.jp/school/"},
    {"company_name": "株式会社クスール", "url": "https://cshool.jp/", "source_url": "https://cshool.jp/"},
    {"company_name": "合同会社ウノマス", "url": "https://unomas.jp/lp-juku/", "source_url": "https://unomas.jp/lp-juku/"},
    {"company_name": "EYL Holdings株式会社", "url": "https://eyl-holdings.co.jp/education-school-dx/", "source_url": "https://eyl-holdings.co.jp/education-school-dx/"},
    {"company_name": "株式会社スタディクラウド", "url": "https://studycloud.co.jp/", "source_url": "https://studycloud.co.jp/"},
]

verified = []
with ThreadPoolExecutor(max_workers=8) as pool:
    futures = [pool.submit(fetch_candidate, item) for item in CANDIDATES]
    for future in as_completed(futures):
        row = future.result()
        if row:
            verified.append(row)
verified.sort(key=lambda row: row["company_name"])

with (HERE / "education_supplement_seed.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["company_name", "url", "contact_url", "区分", "検出ワード", "source_url"])
    writer.writeheader()
    for row in verified:
        writer.writerow({
            "company_name": row["company_name"], "url": row["url"], "contact_url": "",
            "区分": "S｜業界特化Web制作・店舗支援ハブ",
            "検出ワード": f"教育業界ハブ：{row['evidence']}", "source_url": row["source_url"],
        })
pages = [{"idx": idx, "base_url": row["url"], "links": row["links"]} for idx, row in enumerate(verified)]
(HERE / "education_supplement_pages.json").write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"input": len(CANDIDATES), "official_service_verified": len(verified)}, ensure_ascii=False))
