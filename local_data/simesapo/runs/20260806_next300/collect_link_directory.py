from __future__ import annotations

import argparse
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

parser = argparse.ArgumentParser()
parser.add_argument("--source", action="append", required=True)
parser.add_argument("--output", required=True)
parser.add_argument("--category", required=True)
parser.add_argument("--evidence", required=True)
parser.add_argument("--same-host", action="store_true")
args = parser.parse_args()

rows = []
for source in args.source:
    response = requests.get(source, headers=HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    soup = BeautifulSoup(response.text, "html.parser")
    for anchor in soup.find_all("a", href=True):
        name = legal_name(anchor.get_text(" ", strip=True))
        official = urljoin(source, anchor["href"].strip())
        if not official.startswith("http") or not re.search(r"株式会社|有限会社|合同会社", name):
            continue
        if re.search(r"支社|支店|営業所|営業部|グループ$", name):
            continue
        if not args.same_host and host(official) in {host(source), ""}:
            continue
        rows.append({
            "company_name": name,
            "url": official,
            "address": "",
            "phone": "",
            "contact_url": "",
            "区分": args.category,
            "検出ワード": args.evidence,
            "source_url": source,
        })

unique = {host(row["url"]): row for row in rows if host(row["url"])}
results = []
with ThreadPoolExecutor(max_workers=18) as pool:
    futures = [pool.submit(discover, row) for row in unique.values()]
    for future in as_completed(futures):
        results.append(future.result())
results.sort(key=lambda row: row["company_name"])

output = Path(args.output)
output.parent.mkdir(parents=True, exist_ok=True)
with output.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)
print({"parsed": len(rows), "unique_domains": len(unique), "contact_found": sum(bool(row["contact_url"]) for row in results), "company_confirmed": sum(row.get("company_confirmed") == "yes" for row in results), "output": str(output)})
