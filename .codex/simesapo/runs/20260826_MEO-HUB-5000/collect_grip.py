import argparse
import csv
import json
import math
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


BASE = "https://db.grip.website"
UA = "Mozilla/5.0 (compatible; SimesapoResearch/1.0; +https://simesapo.com/)"
CATEGORIES = {"2-1": 6404, "2-2": 1312, "2-4": 219}
LEGAL = ("株式会社", "有限会社", "合同会社", "合資会社", "合名会社", "一般社団法人", "一般財団法人")
DENY_NAME = ("ホールディングス", "銀行", "信用金庫", "証券")
rate_lock = threading.Lock()
last_request = 0.0


def norm_name(value):
    return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]", "", (value or "").lower())


def norm_domain(value):
    host = urlparse(value or "").netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def get(url, timeout=25, stream=False):
    global last_request
    with rate_lock:
        wait = 0.2 - (time.monotonic() - last_request)
        if wait > 0:
            time.sleep(wait)
        last_request = time.monotonic()
    response = requests.get(url, timeout=timeout, allow_redirects=True, stream=stream, headers={"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
    response.raise_for_status()
    if not stream:
        response.encoding = response.apparent_encoding or "utf-8"
    return response


def list_page(category, page):
    url = f"{BASE}/business/{category}" if page == 1 else f"{BASE}/business/{category}/page/{page}"
    soup = BeautifulSoup(get(url).text, "html.parser")
    return [urljoin(BASE, a.get("href")) for a in soup.select("a.sec-db__list-link[href]")]


def field(text, label, next_labels):
    marker = f"\n{label}\n"
    start = text.find(marker)
    if start < 0:
        return ""
    start += len(marker)
    end = len(text)
    for next_label in next_labels:
        idx = text.find(f"\n{next_label}\n", start)
        if idx >= 0:
            end = min(end, idx)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def parse_detail(url):
    try:
        response = get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        name = re.split(r"[（(]", title)[0].strip()
        text = soup.get_text("\n", strip=True)
        official = field(text, "企業のURL", ("電話番号", "代表者名", "法人番号", "従業員数"))
        address = field(text, "所在地", ("企業のURL", "電話番号", "代表者名"))
        phone = field(text, "電話番号", ("代表者名", "法人番号", "従業員数"))
        body_start = text.rfind("最終更新日時：")
        body_end = text.find("所在地", body_start + 1) if body_start >= 0 else -1
        business = re.sub(r"\s+", " ", text[body_start:body_end])[:1600] if body_start >= 0 and body_end > body_start else ""
        if not name or not official:
            return {"source_url": url, "company_name": name, "decision": "drop", "reason": "required_missing"}
        if not any(token in name for token in LEGAL):
            return {"source_url": url, "company_name": name, "url": official, "decision": "drop", "reason": "not_legal_entity"}
        if any(token in name for token in DENY_NAME):
            return {"source_url": url, "company_name": name, "url": official, "decision": "drop", "reason": "non_provider_company_type"}
        try:
            check = get(official, timeout=(5, 10), stream=True)
            final_url = check.url
            check.close()
        except requests.RequestException:
            return {"source_url": url, "company_name": name, "url": official, "decision": "drop", "reason": "official_unreachable"}
        return {
            "company_name": name, "url": final_url, "address": address, "phone": phone,
            "maps_url": "", "status": "MEOハブ候補", "source_url": url,
            "business_description": business, "decision": "keep", "reason": "",
        }
    except requests.RequestException as exc:
        return {"source_url": url, "decision": "drop", "reason": f"detail_error:{type(exc).__name__}"}


def write_csv(path, rows):
    fields = sorted({key for row in rows for key in row})
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--existing", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()
    existing = json.loads(Path(args.existing).read_text(encoding="utf-8-sig"))
    names = {norm_name(x.get("company_name")) for x in existing if x.get("company_name")}
    domains = {norm_domain(x.get("url")) for x in existing if x.get("url")}
    jobs = [(category, page) for category, count in CATEGORIES.items() for page in range(1, math.ceil(count / 20) + 1)]
    links = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(list_page, category, page) for category, page in jobs]
        for index, future in enumerate(as_completed(futures), 1):
            try:
                links.extend(future.result())
            except requests.RequestException:
                pass
            if index % 50 == 0:
                print(json.dumps({"list_pages": index, "links": len(links)}, ensure_ascii=False), flush=True)
    links = list(dict.fromkeys(links))
    kept, audit = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(parse_detail, link) for link in links]
        for index, future in enumerate(as_completed(futures), 1):
            row = future.result()
            if row.get("decision") == "keep":
                name, domain = norm_name(row.get("company_name")), norm_domain(row.get("url"))
                if name in names:
                    row["decision"], row["reason"] = "drop", "existing_name"
                elif not domain or domain in domains:
                    row["decision"], row["reason"] = "drop", "existing_domain"
                else:
                    names.add(name)
                    domains.add(domain)
                    kept.append(row)
            audit.append(row)
            if index % 50 == 0:
                write_csv(args.out, kept)
                write_csv(args.audit, audit)
                print(json.dumps({"details": index, "kept": len(kept)}, ensure_ascii=False), flush=True)
    write_csv(args.out, kept)
    write_csv(args.audit, audit)
    print(json.dumps({"done": True, "links": len(links), "kept": len(kept)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
