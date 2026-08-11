#!/usr/bin/env python3
"""Select and deeply audit a reproducible random sample of 100 from 461 candidates."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import random
import re
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
RUN = ROOT / ".codex" / "simesapo" / "runs" / "20260812_sheet2_full_audit"
SOURCE = RUN / "partner_fit_audit_2850.csv"
OUT = RUN / "sample100_deep_audit.csv"
SEED = 20260812
sys.path.insert(0, str(DIST / "shared"))

import requests  # noqa: E402

UA = "Mozilla/5.0 (compatible; SimesapoDeepAudit/1.0)"
POSITIVE = (
    "web制作", "ホームページ制作", "ウェブ制作", "サイト制作", "webマーケ", "デジタルマーケ",
    "集客支援", "集客コンサル", "広告運用", "広告代理", "販促支援", "販売促進", "sns運用",
    "動画制作", "ブランディング", "プロモーション", "seo対策", "meo対策", "開業支援",
    "出店支援", "マーケティング支援", "運用代行", "コンサルティング",
)
LOCAL_CLIENT = (
    "店舗", "医院", "クリニック", "歯科", "美容室", "サロン", "飲食店", "宿泊施設", "ホテル", "旅館",
    "観光", "不動産会社", "工務店", "建設会社", "リフォーム会社", "自動車販売", "整備工場", "写真館",
    "葬儀社", "小売店", "地域企業", "中小企業", "多店舗", "フランチャイズ",
)
DELIVERY = ("制作実績", "導入事例", "支援実績", "クライアント", "お客様", "取引実績", "事例紹介")
WEAK = (
    "saas", "posシステム", "予約システム", "教材", "研修サービス", "機器販売", "機器メーカー", "商材販売",
    "卸売", "厨房機器", "オフィス家具", "賃貸管理", "不動産仲介", "内装工事", "清掃サービス", "設備保守",
)
LINK_HINTS = (
    "会社概要", "企業情報", "会社案内", "about", "company", "profile", "事業内容", "service", "business",
    "実績", "works", "case", "portfolio", "制作", "支援", "contact", "問い合わせ",
)


def norm(value: str) -> str:
    return re.sub(r"[\s\u3000]+", "", unicodedata.normalize("NFKC", value or "")).lower()


def domain(value: str) -> str:
    if "://" not in value:
        value = "https://" + value
    host = (urlparse(value).hostname or "").lower().strip(".")
    return host[4:] if host.startswith("www.") else host


def visible(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def fetch(session: requests.Session, url: str) -> tuple[int, str, str]:
    try:
        r = session.get(url, timeout=(5, 12), allow_redirects=True, headers={"User-Agent": UA})
        ctype = r.headers.get("content-type", "")
        raw = r.text[:2_000_000] if "html" in ctype.lower() or not ctype else ""
        return r.status_code, r.url, raw
    except requests.RequestException:
        return 0, url, ""


def links(base: str, raw: str) -> list[str]:
    host = domain(base)
    scored = []
    for href, anchor in re.findall(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', raw):
        u = urljoin(base, href)
        label = norm(visible(anchor) + " " + href)
        if domain(u) != host or not u.startswith(("http://", "https://")):
            continue
        score = sum(norm(h) in label for h in LINK_HINTS)
        if score:
            scored.append((score, u))
    result = []
    for _, u in sorted(scored, key=lambda x: -x[0]):
        if u not in result:
            result.append(u)
        if len(result) >= 5:
            break
    return result


def snippets(content: str, terms: tuple[str, ...], limit: int = 6) -> list[str]:
    sentences = re.split(r"(?<=[。！？])|[\n\r]+", content)
    out = []
    for sentence in sentences:
        compact = re.sub(r"\s+", " ", sentence).strip()
        if 15 <= len(compact) <= 260 and any(norm(t) in norm(compact) for t in terms):
            out.append(compact)
        if len(out) >= limit:
            break
    return out


def audit(row: dict) -> dict:
    session = requests.Session()
    status, final_url, raw = fetch(session, row["url"])
    page_texts = [visible(raw)] if raw else []
    evidence_urls = [final_url] if raw else []
    for link in links(final_url, raw) if raw else []:
        s, u, body = fetch(session, link)
        if 0 < s < 500 and body:
            page_texts.append(visible(body))
            evidence_urls.append(u)
    contact_status, contact_final, contact_raw = fetch(session, row["contact_url"])
    form_exists = bool(contact_status and contact_status < 400 and re.search(r"(?is)<form\b", contact_raw) and re.search(r"(?is)<(input|textarea|select)\b", contact_raw))
    combined_display = " ".join(page_texts)
    combined = norm(combined_display)
    positive_hits = [x for x in POSITIVE if norm(x) in combined]
    client_hits = [x for x in LOCAL_CLIENT if norm(x) in combined]
    delivery_hits = [x for x in DELIVERY if norm(x) in combined]
    weak_hits = [x for x in WEAK if norm(x) in combined]

    positive_evidence = snippets(combined_display, POSITIVE)
    client_evidence = snippets(combined_display, LOCAL_CLIENT)
    delivery_evidence = snippets(combined_display, DELIVERY)

    # Decision contract: HOLD only when one specific missing fact can settle the case.
    if not status or status >= 500:
        decision = "保留"
        reason = "公式サイト取得不能"
        resolver = "公式サイトの復旧後に事業内容を1回確認"
    elif not form_exists:
        decision = "保留"
        reason = "実フォームを確認できない"
        resolver = "問い合わせURLをブラウザで1回確認"
    elif positive_hits and client_hits and (delivery_hits or len(positive_hits) >= 2):
        decision = "採用確定"
        reason = "受託支援・地域顧客接点・実績または複数サービス・実フォームを確認"
        resolver = ""
    elif weak_hits and not positive_hits:
        decision = "除外確定"
        reason = "SaaS・設備・商材・管理等が中心で集客受託根拠なし"
        resolver = ""
    elif positive_hits and not client_hits:
        decision = "除外確定"
        reason = "受託支援はあるが地域事業者ハブの根拠なし"
        resolver = ""
    elif client_hits and not positive_hits:
        decision = "除外確定"
        reason = "地域顧客接点はあるがWeb・広告・販促等の受託根拠なし"
        resolver = ""
    else:
        decision = "除外確定"
        reason = "GBP提携先としての肯定根拠を公式サイトで確認できない"
        resolver = ""

    return {
        "sample_order": row["sample_order"], "source_sheet_row": row["sheet_row"], "company_name": row["company_name"],
        "url": row["url"], "contact_url": row["contact_url"], "proposal_class": row["proposal_class"],
        "existing_evidence": row["existing_evidence"], "decision": decision, "reason": reason, "resolver": resolver,
        "official_status": status, "contact_status": contact_status, "form_exists": "yes" if form_exists else "no",
        "positive_hits": " / ".join(positive_hits), "client_hits": " / ".join(client_hits),
        "delivery_hits": " / ".join(delivery_hits), "weak_hits": " / ".join(weak_hits),
        "positive_evidence": " || ".join(positive_evidence), "client_evidence": " || ".join(client_evidence),
        "delivery_evidence": " || ".join(delivery_evidence), "evidence_urls": " / ".join(evidence_urls),
        "contact_final_url": contact_final,
    }


def main() -> None:
    with SOURCE.open("r", encoding="utf-8-sig", newline="") as fh:
        eligible = [r for r in csv.DictReader(fh) if r["classification"] == "keep_partner_fit"]
    if len(eligible) != 461:
        raise SystemExit(f"STOP: expected 461 eligible rows, got {len(eligible)}")
    eligible.sort(key=lambda r: int(r["sheet_row"]))
    rng = random.Random(SEED)
    selected = rng.sample(eligible, 100)
    selected.sort(key=lambda r: int(r["sheet_row"]))
    for order, row in enumerate(selected, 1):
        row["sample_order"] = order
    sample_signature = hashlib.sha256("|".join(r["sheet_row"] for r in selected).encode()).hexdigest()

    results = []
    with ThreadPoolExecutor(max_workers=18) as pool:
        futures = {pool.submit(audit, row): row for row in selected}
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: int(r["sample_order"]))
    with OUT.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    counts = {}
    for row in results:
        counts[row["decision"]] = counts.get(row["decision"], 0) + 1
    print(json.dumps({
        "population": len(eligible), "sample": len(results), "seed": SEED, "signature": sample_signature,
        "counts": counts, "adoption_rate": round(counts.get("採用確定", 0) / 100, 4),
        "hold_rate": round(counts.get("保留", 0) / 100, 4), "output": str(OUT),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
