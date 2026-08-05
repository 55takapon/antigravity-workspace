from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from collect_aca import HEADERS, discover, host
from collect_interior import legal_name

HERE = Path(__file__).parent
SOURCE = "https://www.ai-in-ko.or.jp/organization/member.html"


def main() -> None:
    response = requests.get(SOURCE, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "html.parser")
    rows = []
    for anchor in soup.find_all("a", href=True):
        name = legal_name(anchor.get_text(" ", strip=True))
        official = anchor["href"].strip()
        if not official.startswith("http") or not re.search(r"株式会社|有限会社|合同会社", name):
            continue
        if host(official) in {"ai-in-ko.or.jp", "facebook.com", ""}:
            continue
        rows.append({
            "company_name": name,
            "url": official,
            "address": "",
            "phone": "",
            "contact_url": "",
            "区分": "S｜地域印刷・販促物・ポスティング支援",
            "検出ワード": "愛知県印刷工業組合公式会員：商業印刷・販促物・企画制作",
            "source_url": SOURCE,
        })
    unique = {host(row["url"]): row for row in rows if host(row["url"])}
    results = []
    with ThreadPoolExecutor(max_workers=18) as pool:
        futures = [pool.submit(discover, row) for row in unique.values()]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: row["company_name"])
    output = HERE / "aichi_print_crawled.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print({"parsed": len(rows), "unique_domains": len(unique), "contact_found": sum(bool(row["contact_url"]) for row in results), "company_confirmed": sum(row.get("company_confirmed") == "yes" for row in results), "output": str(output)})


if __name__ == "__main__":
    main()
