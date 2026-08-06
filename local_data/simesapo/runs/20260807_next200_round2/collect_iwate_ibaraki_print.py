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
from collect_interior import legal_name

SOURCES = [
    "https://www.iwate-print.net/about/member.html",
    "https://www.ibaraki-printing.org/11_a_ichiran_1_20.html",
    "https://www.ibaraki-printing.org/11_a_ichiran_21_26.html",
]
OUTPUT = Path(__file__).parent / "iwate_ibaraki_print_crawled.csv"


def main() -> None:
    rows = []
    for source in SOURCES:
        response = requests.get(source, headers=HEADERS, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        for tr in soup.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            name = legal_name(cells[0].get_text(" ", strip=True))
            if not re.search(r"株式会社|有限会社|合同会社", name):
                continue
            links = []
            for anchor in tr.find_all("a", href=True):
                href = urljoin(source, anchor["href"].strip())
                if href.startswith("http") and host(href) not in {host(source), ""}:
                    links.append(href)
            if not links:
                continue
            text = tr.get_text(" ", strip=True)
            phone_match = re.search(r"(?:電話|TEL)[］\].：:\s]*([0-9()（）\-ー―‐]+)", text, re.I)
            rows.append({
                "company_name": name,
                "url": links[0],
                "address": text[:180],
                "phone": phone_match.group(1) if phone_match else "",
                "contact_url": "",
                "区分": "S｜地域印刷・販促・Web支援",
                "検出ワード": "県印刷工業組合公式会員：印刷・販促・企画制作",
                "source_url": source,
            })
    unique = {host(row["url"]): row for row in rows if host(row["url"])}
    results = []
    with ThreadPoolExecutor(max_workers=18) as pool:
        futures = [pool.submit(discover, row) for row in unique.values()]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: row["company_name"])
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print({
        "listed_with_official_url": len(rows),
        "unique_domains": len(unique),
        "contact_found": sum(bool(row["contact_url"]) for row in results),
        "company_confirmed": sum(row.get("company_confirmed") == "yes" for row in results),
        "output": str(OUTPUT),
    })


if __name__ == "__main__":
    main()
