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
from collect_aca import HEADERS, company_key, discover, host

HERE = Path(__file__).parent
SOURCE = "https://www.super.or.jp/?page_id=73"
LEGAL_RE = re.compile(r"株式会社|有限会社|合同会社")

response = requests.get(SOURCE, headers=HEADERS, timeout=40)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")
section_names = {
    "店舗設備・システム・設計・エネルギー",
    "店舗用品・資材",
    "情報・サービス・販売促進・研究・メディア",
}
rows = []
for heading in [h for h in soup.find_all(["h2", "h3"]) if h.get_text(" ", strip=True) in section_names]:
    section = heading.get_text(" ", strip=True)
    for element in heading.find_all_next():
        if element is not heading and element.name in {"h2", "h3"}:
            break
        if element.name != "a" or not element.get("href", "").startswith(("http://", "https://")):
            continue
        name = " ".join(element.get_text(" ", strip=True).split())
        if not name or not host(element["href"]):
            continue
        rows.append({
            "company_name": name,
            "url": element["href"],
            "address": "",
            "phone": "",
            "contact_url": "",
            "区分": "I｜小売・スーパー向け店舗設備・販促・システム支援",
            "検出ワード": "全国スーパーマーケット協会公式賛助会員：" + section,
            "source_url": SOURCE,
        })

def legal_name(row):
    result = discover(row)
    if result.get("fetch") != "ok":
        return result
    texts = []
    for url in dict.fromkeys([result.get("profile_url", ""), result.get("url", "")]):
        if not url:
            continue
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.ok and "html" in r.headers.get("content-type", "").lower():
                page = BeautifulSoup(r.text, "html.parser")
                texts.extend(x.get_text(" ", strip=True) for x in page.find_all(["title", "h1", "h2", "h3", "td", "dd", "p"]))
        except requests.RequestException:
            pass
    target = company_key(row["company_name"])
    candidates = []
    listed = re.sub(r"\s+", " ", row["company_name"]).strip()
    listed_pattern = re.escape(listed).replace(r"\ ", r"\s*")
    if LEGAL_RE.search(listed):
        candidates.append(listed)
    for text in texts:
        clean = re.sub(r"\s+", " ", text).strip(" |｜-–—:：")
        if LEGAL_RE.search(clean) and target and target in company_key(clean) and len(clean) <= 70:
            for legal in ("株式会社", "有限会社", "合同会社"):
                if re.search(re.escape(legal) + r"\s*" + listed_pattern, clean, re.I):
                    candidates.append(legal + listed)
                if re.search(listed_pattern + r"\s*" + re.escape(legal), clean, re.I):
                    candidates.append(listed + legal)
    if candidates:
        result["company_name"] = min(candidates, key=len)
        result["company_confirmed"] = "yes"
    else:
        result["company_confirmed"] = "no"
    return result

unique = {host(row["url"]): row for row in rows}
results = []
with ThreadPoolExecutor(max_workers=18) as pool:
    futures = [pool.submit(legal_name, row) for row in unique.values()]
    for future in as_completed(futures):
        results.append(future.result())
results.sort(key=lambda row: row["company_name"])
output = HERE / "super_equipment_crawled.csv"
with output.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)
print({"listed": len(rows), "unique_domains": len(unique), "contact_found": sum(bool(r["contact_url"]) for r in results), "legal_name_confirmed": sum(r["company_confirmed"] == "yes" for r in results), "output": str(output)})
