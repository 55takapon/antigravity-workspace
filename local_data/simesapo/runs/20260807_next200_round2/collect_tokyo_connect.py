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
from collect_interior import legal_name

SEARCH = "https://connect.tokyo-printing.or.jp/corp_search/wp?page={}"
OUTPUT = Path(__file__).parent / "tokyo_connect_crawled.csv"


def fetch_search(page: int) -> list[tuple[str, str, str]]:
    source = SEARCH.format(page)
    response = requests.get(source, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "html.parser")
    found = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if "/corp_search/wp_detail/" not in href:
            continue
        text = anchor.get_text(" ", strip=True)
        name = legal_name(re.split(r"\s+\d{3}-\d{4}\s+", text, maxsplit=1)[0])
        if not re.search(r"株式会社|有限会社|合同会社", name):
            continue
        if re.search(r"支社|支店|営業所|事業所|工場$", name):
            continue
        found.append((name, href, text))
    return found


def fetch_detail(item: tuple[str, str, str]) -> dict[str, str] | None:
    name, detail_url, summary = item
    try:
        response = requests.get(detail_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        official = ""
        for anchor in soup.find_all("a", href=True):
            if "ウェブサイトはこちら" in anchor.get_text(" ", strip=True):
                official = anchor["href"].strip()
                break
        if not official.startswith("http") or host(official) in {"connect.tokyo-printing.or.jp", "tokyo-printing.or.jp", ""}:
            return None
        phone_match = re.search(r"(?:TEL|電話番号)[：:\s]*([0-9()（）\-ー―‐]+)", soup.get_text(" ", strip=True), re.I)
        return {
            "company_name": name,
            "url": official,
            "address": summary[:180],
            "phone": phone_match.group(1) if phone_match else "",
            "contact_url": "",
            "区分": "S｜地域印刷・販促・Web支援",
            "検出ワード": "東京都印刷工業組合Connect公式会員：印刷・販促・企画・Web制作",
            "source_url": detail_url,
        }
    except Exception:
        return None


def main() -> None:
    detail_items: list[tuple[str, str, str]] = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(fetch_search, page) for page in range(1, 84)]
        for future in as_completed(futures):
            detail_items.extend(future.result())
    details = {item[1]: item for item in detail_items}

    official_rows = []
    with ThreadPoolExecutor(max_workers=28) as pool:
        futures = [pool.submit(fetch_detail, item) for item in details.values()]
        for future in as_completed(futures):
            row = future.result()
            if row:
                official_rows.append(row)
    unique = {host(row["url"]): row for row in official_rows if host(row["url"])}

    results = []
    with ThreadPoolExecutor(max_workers=24) as pool:
        futures = [pool.submit(discover, row) for row in unique.values()]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: row["company_name"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print({
        "directory_entries": len(details),
        "official_domains": len(unique),
        "contact_found": sum(bool(row["contact_url"]) for row in results),
        "company_confirmed": sum(row.get("company_confirmed") == "yes" for row in results),
        "output": str(OUTPUT),
    })


if __name__ == "__main__":
    main()
