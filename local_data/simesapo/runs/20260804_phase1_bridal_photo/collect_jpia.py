from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HERE = Path(__file__).parent
SOURCE = "https://jpia.jp/bannars/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SimesapoResearch/1.0)"}
EXCLUDE = ("キタムラ", "DNP", "大日本印刷", "富士フイルム", "三菱製紙", "ワタベウェディング", "プラザクリエイト")


def domain(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def crawl(row: dict) -> dict:
    try:
        response = requests.get(row["url"], headers=HEADERS, timeout=18, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        links = []
        base_domain = domain(response.url)
        for a in soup.find_all("a", href=True):
            href = urljoin(response.url, a["href"])
            signal = a.get_text(" ", strip=True) + " " + href
            if domain(href) == base_domain and re.search(r"contact|inquiry|form|toiawase|otoiawase|お問い合わせ|お問合せ|問合せ|ご相談", signal, re.I):
                links.append(href)
        return {**row, "url": response.url, "contact_url": list(dict.fromkeys(links))[0] if links else "", "fetch": "ok"}
    except Exception as exc:
        return {**row, "contact_url": "", "fetch": type(exc).__name__}


def main():
    response = requests.get(SOURCE, headers=HEADERS, timeout=25)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    raw = []
    for a in soup.find_all("a", href=True):
        img = a.find("img")
        if not img:
            continue
        name = re.sub(r"\s+", "", img.get("alt", "")).strip()
        href = urljoin(SOURCE, a["href"])
        if not name or not any(term in name for term in ("会社", "法人")):
            continue
        if any(term in name for term in EXCLUDE):
            continue
        if domain(href) in ("jpia.jp", ""):
            continue
        raw.append({"brand": name, "company_name": name, "url": href, "exhibit": "写真業界公式会員：写真・アルバム・撮影関連支援", "source_url": SOURCE})
    unique = {domain(r["url"]): r for r in raw}
    results = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(crawl, r) for r in unique.values()]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: r["company_name"])
    with (HERE / "jpia_candidates.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0].keys())); writer.writeheader(); writer.writerows(results)
    print({"raw": len(raw), "unique": len(unique), "contact": sum(bool(r["contact_url"]) for r in results)})


if __name__ == "__main__":
    main()
