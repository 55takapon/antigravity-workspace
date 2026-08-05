from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from collect_aca import HEADERS, discover, host

HERE = Path(__file__).parent
SOURCE = "https://fkr.or.jp/crm/member"
BLOCKED = {"981.jp", "fkr.or.jp", "fudosan-hiroba.co.jp", "google.com", "maps.google.com", "facebook.com", "instagram.com", "x.com"}


def extract_detail(name: str, detail_url: str) -> dict[str, str] | None:
    try:
        response = requests.get(detail_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        for anchor in soup.find_all("a", href=True):
            target = urljoin(response.url, anchor["href"])
            if host(target) not in BLOCKED and host(target):
                links.append(target)
        official = next((target for target in links if "ホームページ" in next((a.get_text(" ", strip=True) for a in soup.find_all("a", href=True) if urljoin(response.url, a["href"]) == target), "")), links[0] if links else "")
        if not official:
            return None
        return {
            "company_name": name,
            "url": official,
            "address": "",
            "phone": "",
            "contact_url": "",
            "区分": "H｜店舗物件・テナント仲介・出店支援",
            "検出ワード": "不動産競売流通協会公式会員：不動産売買・仲介・物件活用支援",
            "source_url": detail_url,
        }
    except Exception:
        return None


def main() -> None:
    response = requests.get(SOURCE, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "html.parser")
    entries = []
    for anchor in soup.find_all("a", href=True):
        name = re.sub(r"\s+", "", anchor.get_text(" ", strip=True))
        detail = urljoin(SOURCE, anchor["href"])
        if host(detail) != "981.jp" or "agent0about_" not in detail or not re.search(r"株式会社|有限会社|合同会社", name):
            continue
        entries.append((name, detail))
    raw = []
    with ThreadPoolExecutor(max_workers=18) as pool:
        futures = [pool.submit(extract_detail, name, detail) for name, detail in entries]
        for future in as_completed(futures):
            row = future.result()
            if row:
                raw.append(row)
    unique = {host(row["url"]): row for row in raw if host(row["url"])}
    results = []
    with ThreadPoolExecutor(max_workers=18) as pool:
        futures = [pool.submit(discover, row) for row in unique.values()]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: row["company_name"])
    output = HERE / "fkr_crawled.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print({"member_details": len(entries), "official_domains": len(unique), "contact_found": sum(bool(row["contact_url"]) for row in results), "company_confirmed": sum(row.get("company_confirmed") == "yes" for row in results), "output": str(output)})


if __name__ == "__main__":
    main()
