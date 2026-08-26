import argparse
import csv
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


BASE = "https://www.weblinks.jp"
UA = "Mozilla/5.0 (compatible; SimesapoResearch/1.0; +https://simesapo.com/)"
DETAIL_RE = re.compile(r"https://www\.weblinks\.jp/hpvendor/\d+-\d+$")
LEGAL = ("株式会社", "有限会社", "合同会社", "合資会社", "合名会社", "一般社団法人", "一般財団法人")
HUB = ("WEBマーケティング", "Webマーケティング", "ウェブマーケティング", "SNS", "広告", "販促", "集客", "運用", "保守", "管理", "コンサル", "ブランディング", "ホームページ制作", "WEB制作", "Web制作")
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
        wait = 1.0 - (time.monotonic() - last_request)
        if wait > 0:
            time.sleep(wait)
        last_request = time.monotonic()
    response = requests.get(url, timeout=timeout, allow_redirects=True, stream=stream, headers={"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
    response.raise_for_status()
    if not stream:
        response.encoding = response.apparent_encoding or "utf-8"
    return response


def list_page(page):
    url = f"{BASE}/hpvendor/page/{page}"
    soup = BeautifulSoup(get(url).text, "html.parser")
    found = {}
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").split("#")[0]
        if DETAIL_RE.fullmatch(href):
            found[href] = True
    return list(found)


def field(text, label, next_labels):
    start = text.find(label)
    if start < 0:
        return ""
    start += len(label)
    end = len(text)
    for marker in next_labels:
        idx = text.find(marker, start)
        if idx >= 0:
            end = min(end, idx)
    return re.sub(r"\s+", " ", text[start:end]).strip()


def parse_detail(url):
    try:
        soup = BeautifulSoup(get(url).text, "html.parser")
        text = soup.get_text("\n", strip=True)
        start = text.rfind("会社名")
        if start < 0:
            return {"source_url": url, "decision": "drop", "reason": "company_block_missing"}
        block = text[start:start + 5000]
        name = field(block, "会社名", ("代表者名", "創業年", "住所", "会社URL"))
        address = field(block, "住所", ("会社URL", "事業内容"))
        official = field(block, "会社URL", ("事業内容",))
        business = field(block, "事業内容", (f"{name}に相談する", "お客様について", "掲載をご希望"))
        if not name or not official:
            return {"company_name": name, "source_url": url, "decision": "drop", "reason": "required_missing"}
        if not any(token in name for token in LEGAL):
            return {"company_name": name, "url": official, "source_url": url, "decision": "drop", "reason": "not_legal_entity"}
        try:
            response = get(official, timeout=(5, 10))
            final_url = response.url
            official_text = BeautifulSoup(response.text[:500000], "html.parser").get_text(" ", strip=True)
        except requests.RequestException:
            return {"company_name": name, "url": official, "source_url": url, "decision": "drop", "reason": "official_unreachable"}
        evidence = business + " " + official_text[:30000]
        hits = [term for term in HUB if term.lower() in evidence.lower()]
        if not hits:
            return {"company_name": name, "url": final_url, "source_url": url, "business_description": business, "decision": "drop", "reason": "weak_hub_evidence"}
        return {
            "company_name": name, "url": final_url, "address": address, "phone": "", "maps_url": "",
            "status": "MEOハブ候補", "source_url": url, "business_description": business or re.sub(r"\s+", " ", official_text)[:1200],
            "hub_evidence": " / ".join(hits), "decision": "keep", "reason": "",
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
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--end-page", type=int, default=1500)
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()
    existing = json.loads(Path(args.existing).read_text(encoding="utf-8-sig"))
    names = {norm_name(x.get("company_name")) for x in existing if x.get("company_name")}
    domains = {norm_domain(x.get("url")) for x in existing if x.get("url")}
    links, empty = [], 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(list_page, p): p for p in range(args.start_page, args.end_page + 1)}
        for done, future in enumerate(as_completed(futures), 1):
            page_links = future.result()
            links.extend(page_links)
            if done % 50 == 0:
                print(json.dumps({"list_pages": done, "links": len(links)}, ensure_ascii=False), flush=True)
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
