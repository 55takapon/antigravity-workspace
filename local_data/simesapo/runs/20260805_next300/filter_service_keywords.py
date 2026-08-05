from __future__ import annotations

import argparse
import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SimesapoResearch/1.0)"}
parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--pattern", required=True)
args = parser.parse_args()
pattern = re.compile(args.pattern, re.I)

with Path(args.input).open(encoding="utf-8-sig", newline="") as handle:
    source = list(csv.DictReader(handle))


def check(row: dict[str, str]) -> dict[str, str] | None:
    if "（" in row.get("company_name", "") or "(" in row.get("company_name", ""):
        return None
    texts = []
    for url in dict.fromkeys([row.get("url", ""), row.get("profile_url", "")]):
        if not url:
            continue
        try:
            response = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
            if response.ok and "html" in response.headers.get("content-type", "").lower():
                texts.append(BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True))
        except requests.RequestException:
            pass
    return row if pattern.search(" ".join(texts)) else None


rows = []
with ThreadPoolExecutor(max_workers=18) as pool:
    futures = [pool.submit(check, row) for row in source]
    for future in as_completed(futures):
        row = future.result()
        if row:
            rows.append(row)
rows.sort(key=lambda row: row["company_name"])

with Path(args.output).open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print({"input": len(source), "service_confirmed": len(rows), "output": args.output})
