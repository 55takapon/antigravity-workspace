#!/usr/bin/env python3
"""Stratified mechanical quality audit for Sheet2: 5 rows per 50-company batch."""

from __future__ import annotations

import csv
import html
import json
import re
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
OUTPUT = ROOT / "local_data" / "simesapo" / "admin" / "sheet2_quality_sample_285.csv"
MASTER = DIST / "custmize" / "enterprise_audit_master.csv"
if not MASTER.exists():
    MASTER = ROOT / "local_data" / "simesapo" / "enterprise_audit_master.csv"
sys.path.insert(0, str(DIST / "shared"))
from sheets_io import get_client  # noqa: E402

import requests  # noqa: E402

SPREADSHEET_ID = "1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ"
OFFSETS = (0, 10, 20, 30, 40)
UA = "Mozilla/5.0 (compatible; SimesapoQualityAudit/1.0)"

SERVICE_TERMS = (
    "web制作", "ホームページ制作", "ウェブ制作", "サイト制作", "webマーケ", "デジタルマーケ",
    "集客支援", "集客コンサル", "広告運用", "広告代理", "販促支援", "販売促進", "sns運用",
    "動画制作", "ブランディング", "プロモーション", "seo対策", "meo対策", "開業支援",
    "出店支援", "店舗開発", "経営支援", "運営支援", "制作会社", "マーケティング支援",
)
CLIENT_TERMS = (
    "店舗", "医院", "クリニック", "歯科", "美容室", "サロン", "飲食店", "宿泊施設", "ホテル",
    "旅館", "観光", "不動産会社", "工務店", "建設会社", "リフォーム会社", "自動車販売",
    "整備工場", "写真館", "葬儀社", "小売店", "地域企業", "中小企業", "多店舗", "フランチャイズ",
    "クライアント", "お客様の集客", "顧客企業", "導入事例", "制作実績",
)
WEAK_ONLY_TERMS = (
    "saas", "クラウドサービス", "posシステム", "予約システム", "販売管理システム", "教材",
    "研修サービス", "機器販売", "機器メーカー", "商材販売", "卸売", "厨房機器", "オフィス家具",
    "賃貸管理", "不動産仲介", "内装工事", "清掃サービス", "設備保守",
)
LINK_HINTS = ("service", "business", "事業", "サービス", "solution", "実績", "works", "case", "支援")


def norm(value: str) -> str:
    return re.sub(r"[\s\u3000]+", "", unicodedata.normalize("NFKC", value or "")).lower()


def domain(value: str) -> str:
    value = (value or "").strip()
    if "://" not in value:
        value = "https://" + value
    host = (urlparse(value).hostname or "").lower().strip(".")
    return host[4:] if host.startswith("www.") else host


def visible_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def fetch(session: requests.Session, url: str) -> tuple[int, str, str]:
    try:
        response = session.get(url, timeout=(5, 10), allow_redirects=True, headers={"User-Agent": UA})
        ctype = response.headers.get("content-type", "")
        body = response.text[:2_000_000] if "html" in ctype.lower() or not ctype else ""
        return response.status_code, response.url, body
    except requests.RequestException:
        return 0, url, ""


def relevant_links(base: str, raw: str) -> list[str]:
    host = domain(base)
    found = []
    for href, anchor in re.findall(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', raw):
        label = norm(visible_text(anchor) + " " + href)
        absolute = urljoin(base, href)
        if domain(absolute) != host or not absolute.startswith(("http://", "https://")):
            continue
        if any(norm(hint) in label for hint in LINK_HINTS) and absolute not in found:
            found.append(absolute)
        if len(found) >= 3:
            break
    return found


def load_enterprise_master() -> tuple[set[str], set[str], list[str]]:
    company_exact, domain_exact, company_contains = set(), set(), []
    if not MASTER.exists():
        return company_exact, domain_exact, company_contains
    with MASTER.open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            match_type = row.get("match_type", "")
            value = row.get("normalized_value") or row.get("match_value") or ""
            if match_type == "company_exact":
                company_exact.add(norm(value))
            elif match_type == "domain_exact":
                domain_exact.add(domain(value))
            elif match_type == "company_contains":
                company_contains.append(norm(value))
    return company_exact, domain_exact, company_contains


def audit_one(item: dict, master: tuple[set[str], set[str], list[str]]) -> dict:
    company_exact, domain_exact, company_contains = master
    session = requests.Session()
    status, final_url, home_raw = fetch(session, item["url"])
    contact_status, contact_final, contact_raw = fetch(session, item["contact_url"])
    pages = [visible_text(home_raw)]
    fetched_links = []
    if home_raw:
        for link in relevant_links(final_url, home_raw):
            s, u, raw = fetch(session, link)
            if s and s < 500 and raw:
                pages.append(visible_text(raw))
                fetched_links.append(u)
    combined = norm(" ".join(pages))
    service_hits = [term for term in SERVICE_TERMS if norm(term) in combined]
    client_hits = [term for term in CLIENT_TERMS if norm(term) in combined]
    weak_hits = [term for term in WEAK_ONLY_TERMS if norm(term) in combined]
    form_exists = bool(
        contact_status and contact_status < 400 and contact_raw
        and re.search(r"(?is)<form\b", contact_raw)
        and re.search(r"(?is)<(input|textarea|select)\b", contact_raw)
    )
    form_uncertain = bool(contact_status and contact_status < 500 and contact_raw and not form_exists)
    company_n = norm(item["company_name"])
    enterprise = company_n in company_exact or domain(item["url"]) in domain_exact
    enterprise_review = next((term for term in company_contains if term and term in company_n), "")

    if enterprise:
        classification = "exclude_enterprise"
        reason = "上場・大手マスター完全一致"
    elif not status or status >= 500:
        classification = "review_unreachable"
        reason = "公式サイト取得不可"
    elif not service_hits and weak_hits:
        classification = "likely_not_hub"
        reason = "SaaS・機器・商材・不動産管理等の単体支援のみ検出"
    elif not service_hits:
        classification = "review_weak_service"
        reason = "集客・制作・広告・販促等の受託根拠を機械確認できず"
    elif not client_hits:
        classification = "review_weak_hub"
        reason = "複数の地域事業者との顧客接点を機械確認できず"
    elif not form_exists:
        classification = "review_form"
        reason = "実フォームを機械確認できず" if form_uncertain else "問い合わせ先取得不可"
    elif enterprise_review:
        classification = "review_enterprise"
        reason = f"大手グループ語の部分一致: {enterprise_review}"
    else:
        classification = "strategic_valid"
        reason = "受託サービス・地域顧客接点・実フォームを確認"

    return {
        **item,
        "classification": classification,
        "reason": reason,
        "official_status": status,
        "contact_status": contact_status,
        "form_exists": "yes" if form_exists else "no",
        "service_hits": " / ".join(service_hits[:5]),
        "client_hits": " / ".join(client_hits[:5]),
        "weak_only_hits": " / ".join(weak_hits[:5]),
        "enterprise_review_term": enterprise_review,
        "final_url": final_url,
        "contact_final_url": contact_final,
        "evidence_pages": " / ".join(fetched_links[:3]),
    }


def main() -> None:
    client = get_client(str(DIST / "shared" / "gcp_service_account.json"))
    sh = client.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("シート2")
    values = ws.get("A2:P2851", value_render_option="FORMATTED_VALUE")
    if len(values) != 2850:
        raise SystemExit(f"STOP: expected 2850 rows, got {len(values)}")
    samples = []
    for batch in range(57):
        for offset in OFFSETS:
            idx = batch * 50 + offset
            row = values[idx] + [""] * (16 - len(values[idx]))
            samples.append({
                "batch_no": batch + 1,
                "sample_position": offset + 1,
                "sheet_row": idx + 2,
                "company_name": row[0],
                "url": row[1],
                "contact_url": row[5],
                "proposal_class": row[14],
                "existing_evidence": row[15],
            })
    if len(samples) != 285:
        raise SystemExit("STOP: sample count mismatch")

    master = load_enterprise_master()
    results = []
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(audit_one, item, master): item for item in samples}
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: (row["batch_no"], row["sample_position"]))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(results[0].keys())
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    counts = {}
    for row in results:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    summary = {
        "sample_count": len(results),
        "classification_counts": counts,
        "strategic_valid_rate": round(counts.get("strategic_valid", 0) / len(results), 4),
        "form_exists_rate": round(sum(row["form_exists"] == "yes" for row in results) / len(results), 4),
        "official_reachable_rate": round(sum(0 < int(row["official_status"]) < 500 for row in results) / len(results), 4),
        "output": str(OUTPUT),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
