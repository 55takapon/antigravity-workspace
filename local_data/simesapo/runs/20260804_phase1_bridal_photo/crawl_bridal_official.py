from __future__ import annotations

import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

HERE = Path(__file__).parent
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SimesapoResearch/1.0)"}
LEGAL = re.compile(r"(?:株式会社|有限会社|合同会社|一般社団法人|一般財団法人|特定非営利活動法人)[\s　]*[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶー・&＆.\-]{1,35}|[A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龥ぁ-んァ-ヶー・&＆.\-]{1,35}[\s　]*(?:株式会社|有限会社|合同会社)")
BAD_PREFIX = ("会社名", "代表", "お問い合わせ", "こちら", "について", "運営", "より", "とは", "する", "した", "できる", "すべて", "全て", "提供", "Copyright")


def domain(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def clean_name(value: str) -> str:
    value = re.sub(r"\s+", "", value).strip("|｜-–—:：.,。")
    return value


def name_score(name: str, brand: str, context: str) -> int:
    if not 4 <= len(name) <= 42 or any(name.startswith(x) for x in BAD_PREFIX):
        return -100
    score = 0
    if brand.lower().replace(" ", "") in name.lower().replace(" ", ""):
        score += 8
    if "会社概要" in context or "会社名" in context or "法人名" in context:
        score += 5
    if name.startswith(("株式会社", "有限会社", "合同会社", "一般社団法人", "一般財団法人")):
        score += 2
    if any(x in name for x in ("こちら", "フォーム", "サービス", "ページ", "サイト")):
        score -= 8
    return score


def fetch_page(url: str):
    response = requests.get(url, headers=HEADERS, timeout=18, allow_redirects=True)
    response.raise_for_status()
    if "html" not in response.headers.get("content-type", ""):
        return response.url, None
    return response.url, BeautifulSoup(response.text, "html.parser")


def crawl(row: dict) -> dict:
    try:
        final, soup = fetch_page(row["url"])
        if soup is None:
            raise ValueError("non_html")
        base_domain = domain(final)
        profile = []
        contacts = []
        for a in soup.find_all("a", href=True):
            href = urljoin(final, a.get("href", ""))
            signal = (a.get_text(" ", strip=True) + " " + href).lower()
            if domain(href) != base_domain:
                continue
            if re.search(r"company|corporate|profile|about|会社概要|企業情報|運営会社", signal):
                profile.append(href)
            if re.search(r"contact|inquiry|form|toiawase|otoiawase|お問い合わせ|お問合せ|問合せ|ご相談", signal):
                contacts.append(href)
        pages = [(final, soup)]
        for href in list(dict.fromkeys(profile))[:4]:
            try:
                page_url, page_soup = fetch_page(href)
                if page_soup:
                    pages.append((page_url, page_soup))
            except Exception:
                pass
        scored = []
        for page_url, page_soup in pages:
            text = re.sub(r"\s+", " ", page_soup.get_text(" ", strip=True))
            for match in LEGAL.finditer(text):
                name = clean_name(match.group())
                context = text[max(0, match.start()-30):match.end()+30]
                scored.append((name_score(name, row["brand"], context), name, page_url))
        scored.sort(reverse=True)
        best = scored[0] if scored and scored[0][0] >= 2 else (0, "", "")
        return {**row, "company_name": best[1], "name_source": best[2], "contact_url": list(dict.fromkeys(contacts))[0] if contacts else "", "crawl": "ok"}
    except Exception as exc:
        return {**row, "company_name": "", "name_source": "", "contact_url": "", "crawl": type(exc).__name__}


def main():
    with (HERE / "bridal_pdf_seed.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    results = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(crawl, row) for row in rows]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: r["brand"])
    fields = list(results[0].keys())
    with (HERE / "bridal_crawled.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(results)
    print({"input": len(rows), "name": sum(bool(r["company_name"]) for r in results), "contact": sum(bool(r["contact_url"]) for r in results)})


if __name__ == "__main__":
    main()
