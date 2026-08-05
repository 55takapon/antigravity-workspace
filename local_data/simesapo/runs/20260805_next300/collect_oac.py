from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from collect_aca import HEADERS, discover, host

HERE = Path(__file__).parent
SOURCE = "https://www.oac.or.jp/member/"


def main() -> None:
    response = requests.get(SOURCE, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    rows = []
    for h3 in soup.find_all("h3"):
        name = h3.get_text(" ", strip=True)
        if not re.search(r"株式会社|有限会社|合同会社", name):
            continue
        card = h3.parent
        official = next((a.get("href", "") for a in card.find_all("a", href=True) if a.get_text(" ", strip=True) == "Web"), "")
        if not official or host(official) in {"oac.or.jp", ""}:
            continue
        services = [token for token in card.get_text(" ", strip=True).split() if token not in {name, "詳細", "Web"}]
        evidence = "・".join(dict.fromkeys(services))[:150] or "広告・クリエイティブ制作"
        rows.append({
            "company_name": name,
            "url": official,
            "address": "",
            "phone": "",
            "contact_url": "",
            "区分": "S｜地域広告・販促・Web・クリエイティブ支援",
            "検出ワード": "日本広告制作協会公式会員：" + evidence,
            "source_url": SOURCE,
        })
    unique = {host(row["url"]): row for row in rows if host(row["url"])}
    results = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(discover, row) for row in unique.values()]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: row["company_name"])
    output = HERE / "oac_crawled.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print({"parsed": len(rows), "unique_domains": len(unique), "contact_found": sum(bool(row["contact_url"]) for row in results), "output": str(output)})


if __name__ == "__main__":
    main()
