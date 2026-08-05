from __future__ import annotations

import csv
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

import requests
import urllib3
from bs4 import BeautifulSoup

HELPERS = Path(__file__).resolve().parents[1] / "20260805_next300"
sys.path.insert(0, str(HELPERS))
from collect_aca import HEADERS, discover, host

HERE = Path(__file__).parent
BASE = "https://search.orca.med.or.jp/support/providers/{}"
LEGAL_RE = re.compile(r"株式会社|有限会社|合同会社")
BRANCH_SUFFIX_RE = re.compile(r"[ \u3000]+[^ \u3000]*(?:事業所|営業所|支店|センター|事務所|支社|サポート部).*$")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def provider(provider_id: int):
    url = BASE.format(provider_id)
    try:
        response = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        if not response.ok:
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        heading = soup.find("h1")
        name = " ".join(heading.get_text(" ", strip=True).split()) if heading else ""
        name = BRANCH_SUFFIX_RE.sub("", name).strip()
        if not LEGAL_RE.search(name) or "医師会" in name:
            return None
        text = soup.get_text(" ", strip=True)
        match = re.search(r"URL[：:]?\s*(https?://[^\s<]+)", text)
        official = match.group(1).rstrip(".,、。)）") if match else ""
        if not official:
            for anchor in soup.select('a[href^="http"]'):
                candidate = anchor["href"]
                if host(candidate) not in {"", "orca.med.or.jp", "search.orca.med.or.jp"}:
                    official = candidate
                    break
        if not official or not host(official):
            return None
        return {
            "company_name": name,
            "url": official,
            "address": "",
            "phone": "",
            "contact_url": "",
            "区分": "J｜医療IT・診療所システム導入支援",
            "検出ワード": "ORCA公式認定サポート事業所：医療機関への日医IT導入・運用支援",
            "source_url": url,
        }
    except requests.RequestException:
        return None

raw = []
with ThreadPoolExecutor(max_workers=24) as pool:
    futures = [pool.submit(provider, provider_id) for provider_id in range(1, 801)]
    for future in as_completed(futures):
        row = future.result()
        if row:
            raw.append(row)
unique = {host(row["url"]): row for row in raw}
results = []
with ThreadPoolExecutor(max_workers=18) as pool:
    futures = [pool.submit(discover, row) for row in unique.values()]
    for future in as_completed(futures):
        results.append(future.result())
results.sort(key=lambda row: row["company_name"])
output = HERE / "orca_crawled.csv"
with output.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)
print({"provider_pages": 800, "eligible_records": len(raw), "unique_domains": len(unique), "contact_found": sum(bool(r["contact_url"]) for r in results), "company_confirmed": sum(r["company_confirmed"] == "yes" for r in results), "output": str(output)})
