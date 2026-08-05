from __future__ import annotations

import csv
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HELPERS = Path(__file__).resolve().parents[1] / "20260805_next300"
sys.path.insert(0, str(HELPERS))
from collect_aca import HEADERS, discover, host

HERE = Path(__file__).parent
CIDS = [1, 5, 8, 11, 13, 14, 15, 18, 19, 20, 21, 27, 40, 41, 42, 43, 44, 45, 46, 47]

def expand_name(name: str) -> str:
    name = " ".join(name.split())
    replacements = {
        "（株）": "株式会社", "(株)": "株式会社", "㈱": "株式会社",
        "（有）": "有限会社", "(有)": "有限会社", "㈲": "有限会社",
        "（同）": "合同会社", "(同)": "合同会社",
    }
    for old, new in replacements.items():
        if name.startswith(old):
            name = new + name[len(old):]
        elif name.endswith(old):
            name = name[:-len(old)] + new
    return name.strip()

rows = []
for cid in CIDS:
    source = f"https://www.jpm.jp/branch/all.php?cid={cid}"
    response = requests.get(source, headers=HEADERS, timeout=35)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for anchor in soup.select('a[href^="http"]'):
        name = expand_name(anchor.get_text(" ", strip=True))
        url = anchor.get("href", "")
        if not re.search(r"株式会社|有限会社|合同会社", name):
            continue
        if host(url) in {"", "google.co.jp", "jpm.jp", "jpmsouzoku.jp"}:
            continue
        rows.append({
            "company_name": name,
            "url": url,
            "address": "",
            "phone": "",
            "contact_url": "",
            "区分": "K｜地域不動産・賃貸管理・物件活用支援",
            "検出ワード": "日本賃貸住宅管理協会公式会員：地域の賃貸管理・不動産活用支援",
            "source_url": source,
        })

unique = {host(row["url"]): row for row in rows}
results = []
with ThreadPoolExecutor(max_workers=18) as pool:
    futures = [pool.submit(discover, row) for row in unique.values()]
    for future in as_completed(futures):
        results.append(future.result())
results.sort(key=lambda row: row["company_name"])
output = HERE / "jpm_remaining_crawled.csv"
with output.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)
print({"prefectures": len(CIDS), "listed": len(rows), "unique_domains": len(unique), "contact_found": sum(bool(r["contact_url"]) for r in results), "company_confirmed": sum(r["company_confirmed"] == "yes" for r in results), "output": str(output)})
