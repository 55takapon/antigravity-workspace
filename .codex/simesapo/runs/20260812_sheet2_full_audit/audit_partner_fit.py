#!/usr/bin/env python3
"""Full-sheet mechanical audit for enterprise scale and GBP partner fit."""

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
RUN = ROOT / ".codex" / "simesapo" / "runs" / "20260812_sheet2_full_audit"
MASTER = DIST / "custmize" / "enterprise_filter"
OUT = RUN / "partner_fit_audit_2850.csv"
sys.path.insert(0, str(DIST / "shared"))
from sheets_io import get_client  # noqa: E402
import requests  # noqa: E402

SHEET_ID = "1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ"
UA = "Mozilla/5.0 (compatible; SimesapoPartnerAudit/1.0)"

POSITIVE = (
    "web制作", "ホームページ制作", "ウェブ制作", "サイト制作", "webマーケ", "デジタルマーケ",
    "集客支援", "集客コンサル", "広告運用", "広告代理", "販促支援", "販売促進", "sns運用",
    "動画制作", "ブランディング", "プロモーション", "seo対策", "meo対策", "開業支援",
    "出店支援", "店舗開発", "マーケティング支援", "制作実績", "運用代行",
)
HUB = (
    "店舗", "医院", "クリニック", "歯科", "美容室", "サロン", "飲食店", "宿泊施設", "ホテル",
    "旅館", "観光", "不動産会社", "工務店", "建設会社", "リフォーム会社", "自動車販売",
    "整備工場", "写真館", "葬儀社", "小売店", "地域企業", "中小企業", "多店舗", "フランチャイズ",
    "クライアント", "導入事例", "支援実績",
)
WEAK = (
    "saas", "クラウドサービス", "posシステム", "予約システム", "販売管理システム", "教材",
    "研修サービス", "機器販売", "機器メーカー", "商材販売", "卸売", "厨房機器", "オフィス家具",
    "賃貸管理", "不動産仲介", "内装工事", "清掃サービス", "設備保守", "信用調査", "企業データベース",
)
MEMBERSHIP = ("公式会員", "公式賛助会員", "組合公式", "協会公式", "公式出展", "公式名簿")
ABOUT_HINTS = ("会社概要", "企業情報", "会社案内", "about", "company", "profile", "事業内容", "service", "business")
HARD_MAJOR_NAMES = ("帝国データバンク", "東京商工リサーチ")
HARD_MAJOR_DOMAINS = {"tdb.co.jp", "tsr-net.co.jp"}


def norm(value: str) -> str:
    return re.sub(r"[\s\u3000]+", "", unicodedata.normalize("NFKC", value or "")).lower()


def domain(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if "://" not in value:
        value = "https://" + value
    host = (urlparse(value).hostname or "").lower().strip(".")
    return host[4:] if host.startswith("www.") else host


def text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def fetch(session: requests.Session, url: str) -> tuple[int, str, str]:
    try:
        r = session.get(url, timeout=(4, 9), allow_redirects=True, headers={"User-Agent": UA})
        ctype = r.headers.get("content-type", "")
        raw = r.text[:1_500_000] if "html" in ctype.lower() or not ctype else ""
        return r.status_code, r.url, raw
    except requests.RequestException:
        return 0, url, ""


def related_links(base: str, raw: str) -> list[str]:
    base_domain = domain(base)
    links = []
    for href, anchor in re.findall(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', raw):
        u = urljoin(base, href)
        label = norm(text(anchor) + " " + href)
        if domain(u) == base_domain and any(norm(h) in label for h in ABOUT_HINTS) and u not in links:
            links.append(u)
        if len(links) >= 2:
            break
    return links


def number_from(patterns: tuple[str, ...], content: str) -> int:
    for pattern in patterns:
        m = re.search(pattern, content, re.I)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                pass
    return 0


def load_existing_flags() -> dict[int, dict]:
    path = RUN / "enterprise_audit.csv"
    flags = {}
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                flags[int(row["row_number"])] = row
    return flags


def audit(item: dict, flags: dict[int, dict]) -> dict:
    session = requests.Session()
    status, final_url, raw = fetch(session, item["url"])
    pages = [text(raw)] if raw else []
    evidence_urls = []
    if raw:
        for link in related_links(final_url, raw):
            s, u, body = fetch(session, link)
            if 0 < s < 500 and body:
                pages.append(text(body))
                evidence_urls.append(u)
    combined_display = " ".join(pages)
    combined = norm(combined_display)
    sheet_evidence = norm(item["proposal_class"] + " " + item["existing_evidence"])
    positive_hits = [x for x in POSITIVE if norm(x) in combined]
    hub_hits = [x for x in HUB if norm(x) in combined]
    weak_hits = [x for x in WEAK if norm(x) in combined]
    membership_only = any(norm(x) in sheet_evidence for x in MEMBERSHIP) and not any(norm(x) in sheet_evidence for x in POSITIVE)

    employees = number_from((r"従業員(?:数)?[^0-9]{0,15}([0-9,]{2,7})\s*名", r"社員(?:数)?[^0-9]{0,15}([0-9,]{2,7})\s*名"), combined_display)
    offices = number_from((r"全国[^0-9]{0,15}([0-9,]{2,4})\s*(?:拠点|事業所|支店)", r"([0-9,]{2,4})\s*(?:拠点|事業所|支店)"), combined_display)
    capital_man = number_from((r"資本金[^0-9]{0,20}([0-9,]{2,8})\s*万円",), combined_display)
    listed = bool(re.search(r"(東証|証券コード|東京証券取引所|名古屋証券取引所|上場企業)", combined_display))
    national_scale = bool(re.search(r"(全国47都道府県|全国ネットワーク|全国展開|国内全域)", combined_display))

    existing = flags.get(item["sheet_row"], {})
    existing_class = existing.get("classification", "")
    hard_major = any(n in item["company_name"] for n in HARD_MAJOR_NAMES) or domain(item["url"]) in HARD_MAJOR_DOMAINS
    high_scale = listed or employees >= 1000 or offices >= 30 or hard_major
    review_scale = employees >= 300 or capital_man >= 10000 or offices >= 10 or national_scale

    if existing_class in ("exclude_confirmed_enterprise", "already_in_exclusion_list"):
        classification = "exclude_confirmed"
        reason = existing.get("reason", "既知除外一致")
    elif hard_major:
        classification = "exclude_obvious_major"
        reason = "明確な全国的大手・企業情報大手"
    elif high_scale:
        classification = "exclude_high_scale"
        reason = "公式サイトで上場または大規模シグナルを確認"
    elif existing_class in ("review_jpx_new", "review_group_new"):
        classification = "review_enterprise_match"
        reason = existing.get("reason", "上場・大手ルール一致")
    elif review_scale:
        classification = "review_large_scale"
        reason = "従業員・資本金・拠点・全国展開の規模シグナル"
    elif positive_hits and hub_hits:
        classification = "keep_partner_fit"
        reason = "公式サイトで受託支援と地域顧客接点を確認"
    elif membership_only and not positive_hits:
        classification = "review_membership_only"
        reason = "団体会員・出展者情報のみで、受託支援根拠を確認できず"
    elif weak_hits and not positive_hits:
        classification = "likely_not_partner"
        reason = "SaaS・設備・商材・管理等が中心で、集客受託導線を確認できず"
    elif positive_hits and not hub_hits:
        classification = "review_weak_hub"
        reason = "受託支援は確認できるが地域顧客ハブ性を確認できず"
    else:
        classification = "review_insufficient_evidence"
        reason = "公式サイトから提携適合性を機械確定できず"

    return {
        **item,
        "classification": classification,
        "reason": reason,
        "official_status": status,
        "final_url": final_url,
        "positive_hits": " / ".join(positive_hits[:6]),
        "hub_hits": " / ".join(hub_hits[:6]),
        "weak_hits": " / ".join(weak_hits[:6]),
        "membership_only": "yes" if membership_only else "no",
        "employees_detected": employees or "",
        "offices_detected": offices or "",
        "capital_man_detected": capital_man or "",
        "listed_signal": "yes" if listed else "no",
        "national_scale_signal": "yes" if national_scale else "no",
        "existing_enterprise_class": existing_class,
        "existing_enterprise_match": existing.get("match_value", ""),
        "evidence_urls": " / ".join(evidence_urls),
    }


def main() -> None:
    client = get_client(str(DIST / "shared" / "gcp_service_account.json"))
    sh = client.open_by_key(SHEET_ID)
    values = sh.worksheet("シート2").get("A2:P2851", value_render_option="FORMATTED_VALUE")
    if len(values) != 2850:
        raise SystemExit(f"STOP: expected 2850 rows, got {len(values)}")
    items = []
    for i, row in enumerate(values, 2):
        row = row + [""] * (16 - len(row))
        items.append({"sheet_row": i, "company_name": row[0], "url": row[1], "contact_url": row[5], "proposal_class": row[14], "existing_evidence": row[15]})
    flags = load_existing_flags()
    results = []
    with ThreadPoolExecutor(max_workers=28) as pool:
        futures = {pool.submit(audit, item, flags): item for item in items}
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: r["sheet_row"])
    with OUT.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    counts = {}
    for row in results:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    tdb = next((r for r in results if "帝国データバンク" in r["company_name"]), None)
    print(json.dumps({"total": len(results), "counts": counts, "tdb": tdb, "output": str(OUT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
