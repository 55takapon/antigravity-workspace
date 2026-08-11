#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
RUN = ROOT / ".codex" / "simesapo" / "runs" / "20260812_sheet2_bc_rescue"
RUN.mkdir(parents=True, exist_ok=True)
CREDS = DIST / "shared" / "gcp_service_account.json"
FULL_AUDIT = ROOT / ".codex" / "simesapo" / "artifacts" / "20260812_sheet2_full_audit" / "partner_fit_audit_2850.csv"
SHEET_ID = "1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ"
TAB = "シート2"
AUDIT_OUT = RUN / "bc_rescue_audit.csv"
BACKUP_OUT = RUN / "sheet2_bc_before_write.csv"
UA = "Mozilla/5.0 (compatible; SimesapoBCRescueAudit/1.0)"
TODAY = "2026-08-12"

sys.path.insert(0, str(DIST / ".codex_pydeps"))
sys.path.insert(0, str(DIST / "shared"))
from sheets_io import get_client  # noqa: E402
import requests  # noqa: E402

B_PATTERN = re.compile(r"地域印刷|地方広告|地域広告|屋外広告|販促・広告クリエイティブ")
C_PATTERN = re.compile(r"業界特化|治療院特化|美容サロン|店舗事業者特化|飲食店DX|士業特化|ブライダル特化")

CLIENT_TERMS = (
    "店舗", "医院", "クリニック", "歯科", "美容室", "サロン", "飲食店", "宿泊施設", "ホテル", "旅館",
    "学習塾", "スクール", "フィットネス", "ジム", "整備工場", "自動車販売", "動物病院", "ペットサロン",
    "写真館", "結婚式場", "葬儀社", "工務店", "リフォーム会社", "地域企業", "中小企業", "法人", "企業",
)
SERVICE_TERMS = (
    "web制作", "ウェブ制作", "ホームページ制作", "サイト制作", "webマーケティング", "デジタルマーケティング",
    "広告運用", "広告代理", "sns運用", "line運用", "販促支援", "販売促進", "集客支援", "集客コンサル",
    "ブランディング", "プロモーション", "seo対策", "meo対策", "動画マーケティング", "広報支援",
)
RECURRING_TERMS = (
    "運用代行", "広告運用", "sns運用", "line運用", "保守運用", "保守・運用", "運用保守", "更新代行",
    "継続支援", "継続サポート", "月額", "定期", "伴走支援", "改善支援", "運営支援", "コンサルティング",
    "アクセス解析", "効果測定", "公開後", "アフターサポート", "サポート契約", "年間契約",
)
HARD_NEGATIVE_TERMS = (
    "不動産仲介", "賃貸管理", "内装工事", "設備工事", "機器販売", "機器メーカー", "卸売", "商材販売",
    "saas", "クラウドサービス", "posシステム", "予約システム", "教材販売", "研修サービス",
)
LINK_HINTS = (
    "サービス", "事業内容", "業務内容", "料金", "サポート", "運用", "マーケティング", "広告", "制作",
    "service", "business", "support", "marketing", "works", "company", "about",
)
HOSTED_FORM_DOMAINS = (
    "docs.google.com", "forms.gle", "form.run", "form.kintoneapp.com", "hubspot.com", "hsforms.com",
    "form-mailer.jp", "tayori.com", "select-type.com", "formzu.net", "mailform.mface.jp",
)
BLOCK_CLASSES = {"exclude_high_scale", "exclude_obvious_major", "exclude_confirmed", "review_enterprise_match"}


def norm(value: str) -> str:
    return re.sub(r"[\s\u3000]+", "", (value or "").lower())


def dom(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if "://" not in value:
        value = "https://" + value
    try:
        host = (urlparse(value).hostname or "").lower().strip(".")
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript|svg).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", "。", raw)
    text = html.unescape(raw)
    return re.sub(r"\s+", " ", text).strip()


def fetch(session: requests.Session, url: str) -> tuple[int, str, str]:
    if not url:
        return 0, "", ""
    try:
        r = session.get(url, timeout=(4, 8), allow_redirects=True, headers={"User-Agent": UA})
        ctype = r.headers.get("content-type", "").lower()
        body = r.text[:1_200_000] if "html" in ctype or not ctype else ""
        return r.status_code, r.url, body
    except requests.RequestException:
        return 0, url, ""


def useful_links(base: str, raw: str) -> list[str]:
    out: list[str] = []
    base_domain = dom(base)
    for href, anchor in re.findall(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', raw):
        url = urljoin(base, href)
        label = norm(strip_html(anchor) + " " + href)
        if dom(url) == base_domain and any(norm(x) in label for x in LINK_HINTS) and url not in out:
            out.append(url)
        if len(out) >= 2:
            break
    return out


def hits(content: str, terms: tuple[str, ...]) -> list[str]:
    n = norm(content)
    return [term for term in terms if norm(term) in n]


def evidence_sentence(content: str, terms: list[str]) -> str:
    if not content or not terms:
        return ""
    parts = [re.sub(r"\s+", " ", x).strip(" 。｜|\t") for x in re.split(r"[。！？!?｜|]", content)]
    for term in terms:
        nt = norm(term)
        for part in parts:
            if nt in norm(part) and 12 <= len(part) <= 220:
                return part[:180]
    return ""


def has_real_form(raw: str, final_url: str) -> bool:
    if any(dom(final_url).endswith(x) for x in HOSTED_FORM_DOMAINS):
        return True
    if not raw:
        return False
    forms = re.findall(r"(?is)<form\b.*?</form>", raw)
    for block in forms:
        n = norm(block)
        if any(x in n for x in ("textarea", "type=\"email\"", "type='email'", "name=\"email", "name='email", "お問い合わせ", "送信")):
            return True
    if re.search(r"(?is)(hubspot|hsforms|formrun|form-mailer|kintoneapp|formzu|mw_wp_form|contact-form-7)", raw):
        return True
    return False


def load_full_audit() -> dict[int, dict[str, str]]:
    with FULL_AUDIT.open("r", encoding="utf-8-sig", newline="") as fh:
        return {int(r["sheet_row"]): r for r in csv.DictReader(fh)}


def audit_one(item: dict[str, str], prior: dict[str, str]) -> dict[str, str]:
    session = requests.Session()
    pages: list[tuple[str, str]] = []
    status, final_url, raw = fetch(session, item["url"])
    if raw:
        pages.append((final_url, strip_html(raw)))
        for link in useful_links(final_url, raw):
            s, u, body = fetch(session, link)
            if 0 < s < 500 and body:
                pages.append((u, strip_html(body)))

    for evidence_url in (prior.get("evidence_urls", "") or "").split(" / "):
        evidence_url = evidence_url.strip()
        if evidence_url and all(evidence_url != u for u, _ in pages) and len(pages) < 4:
            s, u, body = fetch(session, evidence_url)
            if 0 < s < 500 and body:
                pages.append((u, strip_html(body)))

    contact_status, contact_final, contact_raw = fetch(session, item["contact_url"])
    form_ok = 0 < contact_status < 500 and has_real_form(contact_raw, contact_final)
    combined = "。".join(t for _, t in pages)
    client_hits = hits(combined, CLIENT_TERMS)
    service_hits = hits(combined, SERVICE_TERMS)
    recurring_hits = hits(combined, RECURRING_TERMS)
    negative_hits = hits(combined, HARD_NEGATIVE_TERMS)
    blocked = prior.get("classification", "") in BLOCK_CLASSES

    fail_reasons = []
    if blocked:
        fail_reasons.append("上場・大手・既知除外の監査区分")
    if not client_hits:
        fail_reasons.append("店舗型・地域型顧客の公式根拠なし")
    if not service_hits:
        fail_reasons.append("集客・販促等の受託サービス根拠なし")
    if not recurring_hits:
        fail_reasons.append("運用・保守・改善等の継続支援根拠なし")
    if not form_ok:
        fail_reasons.append("実在する問い合わせフォーム未確認")
    if negative_hits and not service_hits:
        fail_reasons.append("SaaS・設備・商材等が中心")

    adopted = not fail_reasons
    group = "B" if B_PATTERN.search(item["proposal_class"]) else "C"
    decision = f"採用候補｜{group}｜{item['proposal_class']}" if adopted else f"除外候補｜{group}｜{item['proposal_class']}"

    client_sentence = evidence_sentence(combined, client_hits)
    service_sentence = evidence_sentence(combined, service_hits)
    recurring_sentence = evidence_sentence(combined, recurring_hits)
    evidence_urls = [u for u, _ in pages]
    fact_parts = [
        "顧客=" + ("・".join(client_hits[:4]) + (f"（{client_sentence}）" if client_sentence else "") if client_hits else "確認できず"),
        "受託=" + ("・".join(service_hits[:5]) + (f"（{service_sentence}）" if service_sentence else "") if service_hits else "確認できず"),
        "継続=" + ("・".join(recurring_hits[:5]) + (f"（{recurring_sentence}）" if recurring_sentence else "") if recurring_hits else "確認できず"),
        "窓口=" + ("実フォーム確認" if form_ok else "実フォーム未確認"),
    ]
    if adopted:
        hypothesis = "【営業仮説・未確認】既存顧客向けの追加施策または実務外注としてGBP運用を提案できる可能性"
        comment = "【確認事実】" + "｜".join(fact_parts) + "｜" + hypothesis
    else:
        comment = "【除外根拠】" + "・".join(dict.fromkeys(fail_reasons)) + "｜【確認事実】" + "｜".join(fact_parts)
    if evidence_urls:
        comment += "｜根拠URL=" + " ; ".join(evidence_urls[:3])
    comment += f"｜監査日={TODAY}"
    comment = comment[:3500]

    return {
        **item,
        "group": group,
        "decision": decision,
        "comment": comment,
        "adopted": "yes" if adopted else "no",
        "client_hits": " / ".join(client_hits),
        "service_hits": " / ".join(service_hits),
        "recurring_hits": " / ".join(recurring_hits),
        "negative_hits": " / ".join(negative_hits),
        "form_ok": "yes" if form_ok else "no",
        "official_status": str(status),
        "contact_status": str(contact_status),
        "evidence_urls": " / ".join(evidence_urls),
        "prior_classification": prior.get("classification", ""),
    }


def read_targets() -> tuple[object, object, list[list[str]], list[dict[str, str]]]:
    client = get_client(str(CREDS))
    sh = client.open_by_key(SHEET_ID)
    ws = sh.worksheet(TAB)
    values = ws.get("A1:P2851", value_render_option="FORMATTED_VALUE")
    if len(values) != 2851:
        raise SystemExit(f"STOP: expected 2851 rows including header, got {len(values)}")
    targets = []
    for row_number, raw in enumerate(values[1:], start=2):
        row = raw + [""] * (16 - len(raw))
        proposal_class = row[14]
        if B_PATTERN.search(proposal_class) or C_PATTERN.search(proposal_class):
            targets.append({
                "sheet_row": str(row_number),
                "company_name": row[0],
                "url": row[1],
                "contact_url": row[5],
                "proposal_class": proposal_class,
                "previous_comment": row[15],
            })
    if len(targets) != 1144:
        raise SystemExit(f"STOP: expected 1144 B/C rows, got {len(targets)}")
    return sh, ws, values, targets


def prepare(workers: int) -> None:
    _, _, values, targets = read_targets()
    with BACKUP_OUT.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["sheet_row"] + values[0])
        for item in targets:
            row_number = int(item["sheet_row"])
            row = values[row_number - 1] + [""] * (16 - len(values[row_number - 1]))
            writer.writerow([row_number] + row[:16])

    prior = load_full_audit()
    results = []
    started = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(audit_one, item, prior[int(item["sheet_row"])]): item for item in targets}
        for idx, future in enumerate(as_completed(futures), start=1):
            results.append(future.result())
            if idx % 100 == 0:
                print(f"progress={idx}/1144 elapsed={time.time()-started:.1f}s", flush=True)
    results.sort(key=lambda r: int(r["sheet_row"]))
    with AUDIT_OUT.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    counts = {}
    for row in results:
        key = f"{row['group']}:{'adopt' if row['adopted']=='yes' else 'exclude'}"
        counts[key] = counts.get(key, 0) + 1
    print(json.dumps({"targets": len(results), "counts": counts, "backup": str(BACKUP_OUT), "audit": str(AUDIT_OUT)}, ensure_ascii=False, indent=2))


def apply_results() -> None:
    if not AUDIT_OUT.exists() or not BACKUP_OUT.exists():
        raise SystemExit("STOP: prepare artifacts missing")
    with AUDIT_OUT.open("r", encoding="utf-8-sig", newline="") as fh:
        results = list(csv.DictReader(fh))
    if len(results) != 1144:
        raise SystemExit(f"STOP: audit expected 1144 rows, got {len(results)}")
    sh, ws, values, targets = read_targets()
    current = {int(x["sheet_row"]): x for x in targets}
    data = []
    for row in results:
        rn = int(row["sheet_row"])
        live = current.get(rn)
        if not live or live["company_name"] != row["company_name"] or live["url"] != row["url"]:
            raise SystemExit(f"STOP: live row changed at {rn}")
        data.append({"range": f"'{TAB}'!O{rn}:P{rn}", "values": [[row["decision"], row["comment"]]]})
    sh.values_batch_update({"valueInputOption": "RAW", "data": data})

    reread = ws.get("O2:P2851", value_render_option="FORMATTED_VALUE")
    mismatches = []
    blanks = 0
    for row in results:
        rn = int(row["sheet_row"])
        vals = (reread[rn - 2] if rn - 2 < len(reread) else []) + ["", ""]
        if not vals[0] or not vals[1]:
            blanks += 1
        if vals[0] != row["decision"] or vals[1] != row["comment"]:
            mismatches.append(rn)
    if mismatches or blanks:
        raise SystemExit(f"STOP: verification failed mismatches={len(mismatches)} blanks={blanks} sample={mismatches[:10]}")
    print(json.dumps({"written": len(results), "verified": len(results), "blank_op": blanks, "mismatches": len(mismatches)}, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["prepare", "apply"])
    ap.add_argument("--workers", type=int, default=24)
    args = ap.parse_args()
    if args.mode == "prepare":
        prepare(args.workers)
    else:
        apply_results()


if __name__ == "__main__":
    main()
