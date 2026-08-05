from __future__ import annotations

import csv
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HELPERS = Path(__file__).resolve().parents[1] / "20260805_next300"
sys.path.insert(0, str(HELPERS))
from collect_aca import HEADERS, discover, host

HERE = Path(__file__).parent
SOURCE = "https://tenso-chain.or.jp/member/"

response = requests.get(SOURCE, headers=HEADERS, timeout=30)
response.raise_for_status()
response.encoding = response.apparent_encoding
soup = BeautifulSoup(response.text, "html.parser")
anchors = soup.find_all("a", href=True)
rows = []
for index, anchor in enumerate(anchors):
    name = re.sub(r"\s+", "", anchor.get_text(" ", strip=True))
    if not re.search(r"株式会社|有限会社|合同会社", name) or host(urljoin(SOURCE, anchor["href"])) != host(SOURCE):
        continue
    official = ""
    for next_anchor in anchors[index + 1:index + 5]:
        candidate = urljoin(SOURCE, next_anchor["href"])
        next_name = re.sub(r"\s+", "", next_anchor.get_text(" ", strip=True))
        if re.search(r"株式会社|有限会社|合同会社", next_name) and host(candidate) == host(SOURCE):
            break
        if host(candidate) not in {host(SOURCE), "", "facebook.com"}:
            official = candidate
            break
    if not official:
        continue
    rows.append({
        "company_name": name,
        "url": official,
        "address": "",
        "phone": "",
        "contact_url": "",
        "区分": "H｜店舗内装・設計施工・什器・設備支援",
        "検出ワード": "日本店装チェーン公式会員：商業施設・店舗の企画設計・施工・什器制作",
        "source_url": SOURCE,
    })

unique = {host(row["url"]): row for row in rows if host(row["url"])}
results = []
with ThreadPoolExecutor(max_workers=18) as pool:
    futures = [pool.submit(discover, row) for row in unique.values()]
    for future in as_completed(futures):
        results.append(future.result())
results.sort(key=lambda row: row["company_name"])
output = HERE / "tenso_crawled.csv"
with output.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)
print({"paired": len(rows), "unique_domains": len(unique), "contact_found": sum(bool(row["contact_url"]) for row in results), "company_confirmed": sum(row.get("company_confirmed") == "yes" for row in results), "output": str(output)})
