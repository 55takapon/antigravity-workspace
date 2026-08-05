from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
import urllib3
from bs4 import BeautifulSoup

from collect_aca import HEADERS, discover, host

HERE = Path(__file__).parent
SOURCE = "https://jfea.jp/list/list_50.html"


def main() -> None:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    response = requests.get(SOURCE, headers=HEADERS, timeout=30, verify=False)
    response.raise_for_status()
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")
    rows = []
    for label in soup.find_all("th", class_="list"):
        if label.get_text(" ", strip=True) != "会社名":
            continue
        value = label.find_next("td", class_="list")
        if value is None:
            continue
        name = next((text.strip() for text in value.find_all(string=True, recursive=False) if text.strip()), "")
        homepage = value.find_next("a", class_="list_url")
        official = (homepage.get("href", "") if homepage else "").strip()
        if not official or not re.search(r"株式会社|有限会社|合同会社", name) or host(official) in {"jfea.jp", ""}:
            continue
        rows.append({
            "company_name": name,
            "url": official,
            "address": "",
            "phone": "",
            "contact_url": "",
            "区分": "H｜飲食店・厨房・開業・店舗設備支援",
            "検出ワード": "日本厨房工業会公式会員：業務用厨房設備機器の生産・販売・施工・コンサルティング",
            "source_url": SOURCE,
        })
    unique = {host(row["url"]): row for row in rows if host(row["url"])}
    results = []
    with ThreadPoolExecutor(max_workers=18) as pool:
        futures = [pool.submit(discover, row) for row in unique.values()]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: row["company_name"])
    output = HERE / "jfea_crawled.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print({"parsed": len(rows), "unique_domains": len(unique), "contact_found": sum(bool(row["contact_url"]) for row in results), "company_confirmed": sum(row.get("company_confirmed") == "yes" for row in results), "output": str(output)})


if __name__ == "__main__":
    main()
