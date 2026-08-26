import argparse
import csv
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


BASE = "https://houjin.goo.to"
UA = "Mozilla/5.0 (compatible; SimesapoResearch/1.0; +https://simesapo.com/)"
LEGAL = ("株式会社", "有限会社", "合同会社", "合資会社", "合名会社", "一般社団法人", "一般財団法人")
SERVICE = ("Web制作", "WEB制作", "ウェブ制作", "ホームページ制作", "ホームページ作成", "Webサイト制作", "WEBサイト制作", "ウェブサイト制作", "サイト制作", "サイト構築", "ECサイト構築", "Webマーケティング", "デジタルマーケティング", "インターネット広告", "広告代理店", "販売促進", "販促", "SNS運用", "MEO", "ブランディング")
ONGOING = ("運用", "保守", "管理", "代行", "支援", "コンサルティング", "サポート")
PROVIDER = ("制作", "構築", "支援", "代行", "運用", "保守", "コンサル", "広告代理", "受託", "提供")
NAME_DENY = ("ホールディングス", "銀行", "信用金庫", "証券", "クレディセゾン")
EXTERNAL_DENY = ("goo.to", "houjin.goo.to", "form.run", "google.com", "googletagmanager.com", "yahoo.co.jp", "finance.yahoo.co.jp", "minkabu.jp", "buffett-code.com", "jobtalk.jp", "vorkers.com", "x.com", "5ch.net", "prtimes.jp", "houjin-bangou.nta.go.jp", "edinet-fsa.go.jp", "kanpou.npb.go.jp")
rate_lock = threading.Lock()
last_request = 0.0


def norm_name(value):
    return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]", "", (value or "").lower())


def norm_phone(value):
    return re.sub(r"\D", "", value or "")


def norm_domain(value):
    host = urlparse(value or "").netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def paced_get(url, timeout=25, stream=False):
    global last_request
    with rate_lock:
        wait = 0.25 - (time.monotonic() - last_request)
        if wait > 0:
            time.sleep(wait)
        last_request = time.monotonic()
    response = requests.get(url, timeout=timeout, allow_redirects=True, stream=stream, headers={"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
    response.raise_for_status()
    if not stream:
        response.encoding = response.apparent_encoding or "utf-8"
    return response


def list_page(page, category, list_base=""):
    suffix = "" if page == 0 else f"/page{page}"
    url = (list_base.rstrip("/") if list_base else BASE + f"/corporations/categories/{category}") + suffix
    soup = BeautifulSoup(paced_get(url).text, "html.parser")
    rows = []
    for card in soup.select("article.company-list-card"):
        anchor = card.select_one("a.cl-name[href]")
        if not anchor:
            continue
        text = card.get_text(" ", strip=True)
        address = ""
        match = re.search(r"((?:北海道|東京都|大阪府|京都府|.{2,3}県).{2,80}?(?:区|市|町|村).{0,80}?)(?:更新日|$)", text)
        if match:
            address = match.group(1).strip()
        rows.append({
            "company_name": anchor.get_text(" ", strip=True),
            "detail_url": urljoin(BASE, anchor.get("href")),
            "address": address,
            "list_text": text,
        })
    return rows


def pick_official(soup, text):
    candidates = []
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").strip()
        if not href.startswith("http"):
            continue
        domain = norm_domain(href)
        if not domain or any(domain == x or domain.endswith("." + x) for x in EXTERNAL_DENY):
            continue
        label = anchor.get_text(" ", strip=True)
        priority = 0 if "お問い合わせ" in label or "ホームページ" in label else 1
        candidates.append((priority, href))
    faq = re.search(r"ホームページは\s*(https?://[^\s]+)", text)
    if faq:
        candidates.insert(0, (-1, faq.group(1).rstrip("。")))
    return sorted(candidates)[0][1] if candidates else ""


def detail_candidate(item):
    try:
        response = paced_get(item["detail_url"])
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        official = pick_official(soup, text)
        if not official:
            return {**item, "decision": "drop", "reason": "official_missing"}
        start = text.find("業界分類")
        end = text.find("EXPO", start + 1) if start >= 0 else -1
        industry = text[start:end] if start >= 0 and end > start else ""
        faq_start = text.find(f"{item['company_name']}はどんな会社ですか")
        faq = text[faq_start:faq_start + 1000] if faq_start >= 0 else ""
        evidence = " ".join((item["list_text"], industry, faq))
        service_hits = [term for term in SERVICE if term.lower() in evidence.lower()]
        ongoing_hits = [term for term in ONGOING if term in evidence]
        provider_hits = [term for term in PROVIDER if term in evidence]
        if any(term in item["company_name"] for term in NAME_DENY):
            return {**item, "url": official, "decision": "drop", "reason": "non_provider_company_type"}
        if not service_hits:
            return {**item, "url": official, "decision": "drop", "reason": "weak_service_evidence"}
        if not provider_hits:
            return {**item, "url": official, "decision": "drop", "reason": "weak_provider_evidence"}
        try:
            check = paced_get(official, timeout=20, stream=True)
            final_url = check.url
            check.close()
        except requests.RequestException:
            return {**item, "url": official, "decision": "drop", "reason": "official_unreachable"}
        return {
            "company_name": item["company_name"], "url": final_url, "address": item["address"],
            "phone": "", "maps_url": "", "status": "MEOハブ候補", "source_url": item["detail_url"],
            "business_description": re.sub(r"\s+", " ", evidence)[:1200],
            "hub_evidence": " / ".join(service_hits), "recurring_evidence": " / ".join(ongoing_hits),
            "decision": "keep", "reason": "",
        }
    except requests.RequestException as exc:
        return {**item, "decision": "drop", "reason": f"detail_error:{type(exc).__name__}"}


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
    parser.add_argument("--start-page", type=int, default=0)
    parser.add_argument("--end-page", type=int, default=65)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--category", default="s-web-marketing")
    parser.add_argument("--list-base", default="")
    args = parser.parse_args()
    existing = json.loads(Path(args.existing).read_text(encoding="utf-8-sig"))
    names = {norm_name(x.get("company_name")) for x in existing if x.get("company_name")}
    domains = {norm_domain(x.get("url")) for x in existing if x.get("url")}
    phones = {norm_phone(x.get("phone")) for x in existing if len(norm_phone(x.get("phone"))) >= 9}
    items, audit = [], []
    for page in range(args.start_page, args.end_page + 1):
        try:
            page_rows = list_page(page, args.category, args.list_base)
        except requests.RequestException as exc:
            audit.append({"detail_url": f"page:{page}", "decision": "drop", "reason": f"list_error:{type(exc).__name__}"})
            continue
        for row in page_rows:
            if not any(token in row["company_name"] for token in LEGAL):
                audit.append({**row, "decision": "drop", "reason": "not_legal_entity"})
            elif norm_name(row["company_name"]) in names:
                audit.append({**row, "decision": "drop", "reason": "existing_name"})
            else:
                names.add(norm_name(row["company_name"]))
                items.append(row)
        print(json.dumps({"list_page": page, "queued": len(items)}, ensure_ascii=False), flush=True)
    kept = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(detail_candidate, item) for item in items]
        for index, future in enumerate(as_completed(futures), 1):
            row = future.result()
            if row.get("decision") == "keep":
                domain = norm_domain(row.get("url"))
                if not domain or domain in domains:
                    row["decision"], row["reason"] = "drop", "existing_domain"
                else:
                    domains.add(domain)
                    kept.append(row)
            audit.append(row)
            if index % 25 == 0:
                write_csv(args.out, kept)
                write_csv(args.audit, audit)
                print(json.dumps({"details": index, "kept": len(kept)}, ensure_ascii=False), flush=True)
    write_csv(args.out, kept)
    write_csv(args.audit, audit)
    print(json.dumps({"done": True, "queued": len(items), "kept": len(kept)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
