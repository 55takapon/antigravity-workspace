from __future__ import annotations

import csv
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HELPERS = Path(__file__).resolve().parents[1] / "20260805_next300"
sys.path.insert(0, str(HELPERS))
from collect_aca import HEADERS, discover, host

HERE = Path(__file__).parent
SOURCE = "https://www.display.or.jp/memberslist/memlist-result.php"

response = requests.post(
    SOURCE,
    data={"area_num": "", "pref_name": "", "index_name": ""},
    headers=HEADERS,
    timeout=60,
)
response.raise_for_status()
soup = BeautifulSoup(response.content.decode("utf-8"), "html.parser")
rows = []
for card in soup.select(".memInfo"):
    heading = card.find("h4")
    if not heading:
        continue
    name = " ".join(heading.get_text(" ", strip=True).split())
    official = ""
    for anchor in card.select("a[href]"):
        candidate = anchor.get("href", "").strip()
        if candidate.startswith(("http://", "https://")):
            official = candidate
            break
    if not official or not host(official):
        continue
    rows.append({
        "company_name": name,
        "url": official,
        "address": "",
        "phone": "",
        "contact_url": "",
        "区分": "H｜店舗内装・設計施工・什器・設備支援",
        "検出ワード": "日本ディスプレイ業団体連合会公式構成員：店舗・商業空間の企画設計・施工支援",
        "source_url": "https://www.display.or.jp/memberslist/memlist.php",
    })

unique = {host(row["url"]): row for row in rows if host(row["url"])}
results = []
with ThreadPoolExecutor(max_workers=20) as pool:
    futures = [pool.submit(discover, row) for row in unique.values()]
    for future in as_completed(futures):
        results.append(future.result())
results.sort(key=lambda row: row["company_name"])
output = HERE / "display_federation_crawled.csv"
with output.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)
print({
    "listed_with_url": len(rows),
    "unique_domains": len(unique),
    "contact_found": sum(bool(row["contact_url"]) for row in results),
    "company_confirmed": sum(row.get("company_confirmed") == "yes" for row in results),
    "output": str(output),
})
