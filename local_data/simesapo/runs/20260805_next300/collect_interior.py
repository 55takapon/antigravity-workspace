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
SOURCE = "https://www.interior.or.jp/association/member/"
ALLOWED = re.compile(r"壁装材|ファブリック|照明|ブラインド|家具|住宅設備|住宅部品|住宅・施工|設計・デザイン|小売店")


def legal_name(value: str) -> str:
    value = re.sub(r"\s+", "", value).strip()
    for short, full in (("（株）", "株式会社"), ("(株)", "株式会社"), ("㈱", "株式会社"), ("（有）", "有限会社"), ("(有)", "有限会社"), ("㈲", "有限会社")):
        if value.startswith(short):
            value = full + value[len(short):]
        elif value.endswith(short):
            value = value[:-len(short)] + full
        else:
            value = value.replace(short, full)
    return value


def main() -> None:
    response = requests.get(SOURCE, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    rows = []
    for anchor in soup.find_all("a", href=True):
        official = urljoin(SOURCE, anchor["href"])
        name = legal_name(anchor.get_text(" ", strip=True))
        heading = anchor.find_previous("h2")
        category = heading.get_text(" ", strip=True) if heading else ""
        if not ALLOWED.search(category) or not re.search(r"株式会社|有限会社|合同会社", name):
            continue
        if host(official) in {"interior.or.jp", "", "accaii.com"}:
            continue
        rows.append({
            "company_name": name,
            "url": official,
            "address": "",
            "phone": "",
            "contact_url": "",
            "区分": "H｜店舗内装・設計施工・什器・設備支援",
            "検出ワード": f"インテリア産業協会公式会員：{category}",
            "source_url": SOURCE,
        })
    unique = {host(row["url"]): row for row in rows if host(row["url"])}
    results = []
    with ThreadPoolExecutor(max_workers=18) as pool:
        futures = [pool.submit(discover, row) for row in unique.values()]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: row["company_name"])
    output = HERE / "interior_crawled.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print({"parsed": len(rows), "unique_domains": len(unique), "contact_found": sum(bool(row["contact_url"]) for row in results), "company_confirmed": sum(row.get("company_confirmed") == "yes" for row in results), "output": str(output)})


if __name__ == "__main__":
    main()
