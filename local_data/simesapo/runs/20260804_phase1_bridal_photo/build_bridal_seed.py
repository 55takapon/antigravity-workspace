from __future__ import annotations

import csv
import html
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import requests

HERE = Path(__file__).parent
SOURCE_URL = "https://bridalnews.co.jp/wp-content/uploads/2026/07/22192f19f81f9289c39ca3f4d2b7b9e1.pdf"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SimesapoResearch/1.0)"}
LEGAL = re.compile(r"(?:株式会社|有限会社|合同会社|一般社団法人|一般財団法人)[\s　]*[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶー・&＆.\-]{1,40}|[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶー・&＆.\-]{1,40}[\s　]*(?:株式会社|有限会社|合同会社)")
EXCLUDE = ("シーボン", "ワタベウェディング", "日比谷花壇", "八芳園", "シャディ", "テイクアンドギヴ", "USEN", "リクルート", "富士フイルム", "DNP", "ADDIX")


def clean_url(value: str) -> str:
    value = value.replace(" ", "").replace("どこ", "").replace("（HP）", "")
    value = value.split("/https://", 1)[0].rstrip("）/") + ("/" if value.endswith("/") else "")
    if value.startswith("www."):
        value = "https://" + value
    return value


def parse_pdf() -> list[dict]:
    lines = (HERE / "bridal_pdf_columns.txt").read_text(encoding="utf-8").splitlines()
    rows = []
    for idx, line in enumerate(lines):
        if "URL：" not in line:
            continue
        url = clean_url(line.split("URL：", 1)[1].strip())
        if not url.startswith(("http://", "https://")) or "instagram.com" in url:
            continue
        tel_idx = idx - 1
        while tel_idx >= max(0, idx - 5) and "TEL：" not in lines[tel_idx]:
            tel_idx -= 1
        address_idx = tel_idx - 1 if tel_idx >= 0 else idx - 1
        brand = lines[address_idx - 1].strip() if address_idx > 0 else ""
        if not brand or "出展品目" in brand:
            continue
        exhibit = ""
        for pos in range(address_idx - 2, max(-1, address_idx - 8), -1):
            if "出展品目" in lines[pos]:
                exhibit = lines[pos].replace("出展品目", "").strip()
                break
        if any(term.lower() in brand.lower() for term in EXCLUDE):
            continue
        rows.append({"brand": brand, "url": url, "exhibit": exhibit, "source_url": SOURCE_URL})
    return rows


def fetch(row: dict) -> dict:
    try:
        response = requests.get(row["url"], headers=HEADERS, timeout=18, allow_redirects=True)
        response.raise_for_status()
        text = html.unescape(re.sub(r"<[^>]+>", " ", response.text))
        text = re.sub(r"\s+", " ", text)
        names = []
        for match in LEGAL.findall(text):
            name = re.sub(r"\s+", "", match).strip("|｜-–—:：")
            if 4 <= len(name) <= 45 and name not in names:
                names.append(name)
        return {**row, "url": response.url, "legal_names": "|".join(names[:8]), "fetch": "ok"}
    except Exception as exc:
        return {**row, "legal_names": "", "fetch": type(exc).__name__}


def main() -> None:
    raw = parse_pdf()
    fetched = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(fetch, row) for row in raw]
        for future in as_completed(futures):
            fetched.append(future.result())
    fetched.sort(key=lambda row: row["brand"])
    with (HERE / "bridal_pdf_seed.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["brand", "url", "exhibit", "legal_names", "fetch", "source_url"])
        writer.writeheader(); writer.writerows(fetched)
    print({"parsed": len(raw), "fetched": sum(r["fetch"] == "ok" for r in fetched), "legal_found": sum(bool(r["legal_names"]) for r in fetched)})


if __name__ == "__main__":
    main()
