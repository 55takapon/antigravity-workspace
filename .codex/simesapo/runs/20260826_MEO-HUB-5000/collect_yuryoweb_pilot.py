import argparse
import csv
import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


UA = "Mozilla/5.0 (compatible; SimesapoResearch/1.0; +https://simesapo.com/)"
LEGAL = ("株式会社", "有限会社", "合同会社", "合資会社", "合名会社", "一般社団法人", "一般財団法人")
HUB_TERMS = (
    "MEO", "Googleビジネスプロフィール", "Googleマップ", "ローカルSEO",
    "Webマーケティング", "webマーケティング", "集客", "販促", "広告運用",
    "SNS運用", "Instagram運用", "LINE公式", "保守管理", "保守・運用",
    "運用代行", "コンサルティング", "ブランディング",
)
RECURRING_TERMS = ("運用", "保守", "管理", "代行", "サポート", "コンサルティング", "月額", "定期")
STORE_TERMS = (
    "店舗", "飲食店", "レストラン", "美容室", "サロン", "クリニック", "病院",
    "歯科", "整体", "ホテル", "旅館", "スクール", "学習塾", "不動産",
    "自動車", "士業", "地域",
)


def norm_name(value):
    return re.sub(r"[\s　・･.,，。'\"()（）\-‐‑‒–—―]", "", (value or "").lower())


def norm_phone(value):
    return re.sub(r"\D", "", value or "")


def norm_domain(value):
    if not value:
        return ""
    value = value.strip()
    if not re.match(r"^https?://", value, re.I):
        value = "https://" + value
    host = urlparse(value).netloc.lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def clean_url(value):
    value = (value or "").strip()
    if not value or value == "非公開":
        return ""
    if not re.match(r"^https?://", value, re.I):
        value = "https://" + value
    parsed = urlparse(value)
    return f"{parsed.scheme}://{parsed.netloc}/" if parsed.netloc else ""


def extract_field(text, label, next_labels):
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


def get(session, url, timeout=30):
    response = session.get(url, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"
    return response


def detail_links(session, page):
    url = "https://yuryoweb.com/company_info/" if page == 1 else f"https://yuryoweb.com/company_info/page/{page}/"
    soup = BeautifulSoup(get(session, url).text, "html.parser")
    links = []
    seen = set()
    for anchor in soup.select(".tax_company_title a[href]"):
        href = anchor.get("href", "")
        if href and href not in seen:
            seen.add(href)
            links.append((anchor.get_text(" ", strip=True), href))
    return links


def parse_detail(session, url):
    response = get(session, url)
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text("\n", strip=True)
    marker = text.rfind("の会社概要")
    if marker < 0:
        return None
    block = text[marker:marker + 7000]
    name = extract_field(block, "会社名", ("URL", "代表者名", "本社所在地"))
    official = clean_url(extract_field(block, "URL", ("実績紹介ページ", "⼝コミ", "口コミ", "代表者名", "本社所在地")))
    address = extract_field(block, "本社所在地", ("支社所在地", "対応エリア", "設⽴", "設立", "電話番号"))
    phone = extract_field(block, "電話番号", ("※", "メールアドレス", "資本⾦", "資本金", "スタッフ数", "事業内容"))
    business = extract_field(block, "事業内容", ("実績情報", "主要取引先", "公認パートナー", "制作価格帯", "サービス名", "制作会社のご担当者様", "よく一緒に見られている"))
    company_section_start = text.rfind(f"{name}のポイント", 0, marker)
    if company_section_start < 0:
        company_section_start = text.rfind(f"{name}のサービス", 0, marker)
    if company_section_start < 0:
        company_section_start = max(0, marker - 900)
    evidence_text = text[company_section_start:marker] + "\n" + business
    matched_hub = [term for term in HUB_TERMS if term.lower() in evidence_text.lower()]
    matched_recurring = [term for term in RECURRING_TERMS if term in evidence_text]
    matched_store = [term for term in STORE_TERMS if term in evidence_text]
    return {
        "company_name": name,
        "url": official,
        "address": address,
        "phone": "" if phone == "非公開" else phone,
        "maps_url": "",
        "status": "MEOハブ候補",
        "source_url": url,
        "business_description": business,
        "hub_evidence": " / ".join(matched_hub[:8]),
        "recurring_evidence": " / ".join(matched_recurring[:5]),
        "store_evidence": " / ".join(matched_store[:8]),
    }


def official_reachable(session, url):
    try:
        response = session.get(url, timeout=20, allow_redirects=True, stream=True)
        ok = response.status_code < 400 and norm_domain(response.url)
        final_url = clean_url(response.url) if ok else ""
        response.close()
        return bool(ok), final_url
    except requests.RequestException:
        return False, ""


def write_rows(path, rows, fields):
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
    parser.add_argument("--end-page", type=int, default=60)
    parser.add_argument("--target", type=int, default=550)
    parser.add_argument("--delay", type=float, default=1.0)
    args = parser.parse_args()

    existing = json.loads(Path(args.existing).read_text(encoding="utf-8-sig"))
    names = {norm_name(row.get("company_name")) for row in existing if row.get("company_name")}
    domains = {norm_domain(row.get("url")) for row in existing if row.get("url")}
    phones = {norm_phone(row.get("phone")) for row in existing if len(norm_phone(row.get("phone"))) >= 9}
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
    kept, audit = [], []
    fields = ["company_name", "url", "address", "phone", "maps_url", "status", "source_url", "business_description", "hub_evidence", "recurring_evidence", "store_evidence"]

    for page in range(args.start_page, args.end_page + 1):
        try:
            links = detail_links(session, page)
        except requests.RequestException as exc:
            audit.append({"source_url": f"page:{page}", "decision": "listing_error", "reason": str(exc)})
            continue
        time.sleep(args.delay)
        for listed_name, link in links:
            if norm_name(listed_name) in names:
                audit.append({"company_name": listed_name, "source_url": link, "decision": "drop", "reason": "existing_name_listing"})
                continue
            try:
                row = parse_detail(session, link)
            except requests.RequestException as exc:
                audit.append({"source_url": link, "decision": "detail_error", "reason": str(exc)})
                time.sleep(args.delay)
                continue
            time.sleep(args.delay)
            reason = ""
            if not row or not row["company_name"] or not row["url"]:
                reason = "required_missing"
            elif not any(token in row["company_name"] for token in LEGAL):
                reason = "not_legal_entity"
            elif norm_name(row["company_name"]) in names:
                reason = "existing_name"
            elif norm_domain(row["url"]) in domains:
                reason = "existing_domain"
            elif len(norm_phone(row["phone"])) >= 9 and norm_phone(row["phone"]) in phones:
                reason = "existing_phone"
            elif not row["hub_evidence"]:
                reason = "no_hub_evidence"
            elif not (row["recurring_evidence"] or row["store_evidence"]):
                reason = "weak_relationship_evidence"
            if reason:
                audit.append({**(row or {"source_url": link}), "decision": "drop", "reason": reason})
                continue
            ok, final_url = official_reachable(session, row["url"])
            time.sleep(args.delay)
            if not ok:
                audit.append({**row, "decision": "drop", "reason": "official_unreachable"})
                continue
            row["url"] = final_url
            domain = norm_domain(final_url)
            if domain in domains:
                audit.append({**row, "decision": "drop", "reason": "redirected_existing_domain"})
                continue
            names.add(norm_name(row["company_name"]))
            domains.add(domain)
            if len(norm_phone(row["phone"])) >= 9:
                phones.add(norm_phone(row["phone"]))
            kept.append(row)
            audit.append({**row, "decision": "keep", "reason": ""})
            if len(kept) >= args.target:
                break
        print(json.dumps({"page": page, "kept": len(kept), "checked": len(audit)}, ensure_ascii=False), flush=True)
        audit_fields = sorted({key for row in audit for key in row})
        write_rows(args.out, kept, fields)
        write_rows(args.audit, audit, audit_fields)
        if len(kept) >= args.target:
            break

    write_rows(args.out, kept, fields)
    audit_fields = sorted({key for row in audit for key in row})
    write_rows(args.audit, audit, audit_fields)
    print(json.dumps({"done": True, "kept": len(kept), "checked": len(audit), "out": args.out}, ensure_ascii=False))


if __name__ == "__main__":
    main()
