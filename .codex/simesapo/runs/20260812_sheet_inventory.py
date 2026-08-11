from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

import gspread
from google.oauth2.service_account import Credentials


ALIASES = {
    "company_name": ["company_name", "会社名", "企業名", "法人名", "事業者名"],
    "url": ["url", "URL", "公式URL", "公式サイト", "website", "ホームページ"],
    "contact_url": ["contact_url", "問い合わせURL", "問合せURL", "お問い合わせURL"],
    "status": ["status", "ステータス", "送信状況", "状態"],
    "classification": ["classification", "分類", "区分", "カテゴリ"],
    "message": ["message", "提案文", "本文", "送信文"],
    "phone": ["phone", "電話", "電話番号", "TEL"],
}


def norm_text(value: str) -> str:
    s = unicodedata.normalize("NFKC", value or "").strip().lower()
    s = re.sub(r"[\s\u3000]+", "", s)
    return s


def norm_company(value: str) -> str:
    s = norm_text(value)
    s = re.sub(r"^(株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人|医療法人|社会福祉法人|学校法人)", "", s)
    s = re.sub(r"(株式会社|有限会社|合同会社|合資会社|合名会社)$", "", s)
    return re.sub(r"[^0-9a-z\u3040-\u30ff\u3400-\u9fff]+", "", s)


def norm_domain(value: str) -> str:
    s = unicodedata.normalize("NFKC", value or "").strip()
    if not s:
        return ""
    if not re.match(r"^[a-z][a-z0-9+.-]*://", s, re.I):
        s = "https://" + s
    try:
        host = (urlparse(s).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def norm_phone(value: str) -> str:
    digits = re.sub(r"\D", "", unicodedata.normalize("NFKC", value or ""))
    if digits.startswith("81") and len(digits) >= 10:
        digits = "0" + digits[2:]
    return digits if len(digits) >= 9 else ""


def find_col(headers: list[str], key: str) -> int | None:
    norm_headers = [norm_text(x) for x in headers]
    for alias in ALIASES[key]:
        n = norm_text(alias)
        if n in norm_headers:
            return norm_headers.index(n)
    return None


def cell(row: list[str], idx: int | None) -> str:
    return row[idx].strip() if idx is not None and idx < len(row) else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("spreadsheet")
    ap.add_argument("--creds", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly", "https://www.googleapis.com/auth/drive.readonly"]
    creds = Credentials.from_service_account_file(args.creds, scopes=scopes)
    book = gspread.authorize(creds).open_by_key(args.spreadsheet)

    inventory = []
    records_by_tab: dict[str, list[dict[str, str]]] = {}
    status_by_tab: dict[str, dict[str, int]] = {}

    for ws in book.worksheets():
        values = ws.get_all_values()
        headers = values[0] if values else []
        rows = values[1:] if len(values) > 1 else []
        rows = [r for r in rows if any((v or "").strip() for v in r)]
        cols = {k: find_col(headers, k) for k in ALIASES}
        records = []
        statuses = Counter()
        for physical, row in enumerate(values[1:], start=2):
            if not any((v or "").strip() for v in row):
                continue
            rec = {k: cell(row, idx) for k, idx in cols.items()}
            rec["row"] = str(physical)
            rec["domain"] = norm_domain(rec["url"])
            rec["company_norm"] = norm_company(rec["company_name"])
            rec["phone_norm"] = norm_phone(rec["phone"])
            records.append(rec)
            statuses[rec["status"] or "(空欄)"] += 1
        records_by_tab[ws.title] = records
        status_by_tab[ws.title] = dict(statuses.most_common())
        inventory.append({
            "tab": ws.title,
            "data_rows": len(rows),
            "grid_rows": ws.row_count,
            "grid_cols": ws.col_count,
            "headers": headers,
            "mapped_columns": {k: (v + 1 if v is not None else None) for k, v in cols.items()},
            "company_nonblank": sum(bool(r["company_name"]) for r in records),
            "url_nonblank": sum(bool(r["url"]) for r in records),
            "domain_nonblank": sum(bool(r["domain"]) for r in records),
            "contact_nonblank": sum(bool(r["contact_url"]) for r in records),
            "status_nonblank": sum(bool(r["status"]) for r in records),
            "message_nonblank": sum(bool(r["message"]) for r in records),
            "classification_nonblank": sum(bool(r["classification"]) for r in records),
            "classification_counts": dict(Counter(r["classification"] or "(空欄)" for r in records).most_common(30)),
            "status_counts": dict(statuses.most_common(30)),
        })

    operational = ["シート1", "Webマーケ", "SNS運用", "251127作成", "251222作成", "Web幹事"]
    exclusion = "除外リスト"
    sheet2 = "シート2"

    def summarize_tabs(tabs: list[str]) -> dict:
        rows = [dict(r, tab=t) for t in tabs for r in records_by_tab.get(t, [])]
        domains = [r["domain"] for r in rows if r["domain"]]
        companies = [r["company_norm"] for r in rows if r["company_norm"]]
        entity_keys = [("d:" + r["domain"]) if r["domain"] else ("c:" + r["company_norm"] if r["company_norm"] else "") for r in rows]
        entity_keys = [x for x in entity_keys if x]
        return {
            "tabs": tabs,
            "rows": len(rows),
            "unique_domains": len(set(domains)),
            "domain_duplicate_rows": len(domains) - len(set(domains)),
            "unique_companies": len(set(companies)),
            "company_duplicate_rows": len(companies) - len(set(companies)),
            "unique_entities": len(set(entity_keys)),
            "contact_nonblank": sum(bool(r["contact_url"]) for r in rows),
            "status_nonblank": sum(bool(r["status"]) for r in rows),
        }

    operational_summary = summarize_tabs(operational)
    sheet2_summary = summarize_tabs([sheet2])
    all_collected_summary = summarize_tabs(operational + [sheet2])
    exclude_summary = summarize_tabs([exclusion])

    op_rows = [dict(r, tab=t) for t in operational for r in records_by_tab.get(t, [])]
    s2_rows = records_by_tab.get(sheet2, [])
    ex_rows = records_by_tab.get(exclusion, [])
    op_domains = {r["domain"] for r in op_rows if r["domain"]}
    s2_domains = {r["domain"] for r in s2_rows if r["domain"]}
    ex_domains = {r["domain"] for r in ex_rows if r["domain"]}
    op_companies = {r["company_norm"] for r in op_rows if r["company_norm"]}
    s2_companies = {r["company_norm"] for r in s2_rows if r["company_norm"]}
    ex_companies = {r["company_norm"] for r in ex_rows if r["company_norm"]}
    ex_phones = {r["phone_norm"] for r in ex_rows if r["phone_norm"]}

    op_survivors = [
        r for r in op_rows
        if not (
            (r["domain"] and r["domain"] in ex_domains)
            or (r["company_norm"] and r["company_norm"] in ex_companies)
            or (r["phone_norm"] and r["phone_norm"] in ex_phones)
        )
    ]
    survivor_domains = {r["domain"] for r in op_survivors if r["domain"]}
    survivor_companies = {r["company_norm"] for r in op_survivors if r["company_norm"]}

    fit_classes = {
        "シート1": {"Web制作会社", "周辺業種_Web付随", "Webマーケ・SNS運用"},
        "Webマーケ": {"Webマーケ・広告運用", "Web制作会社", "周辺業種_Web付随"},
        "SNS運用": {"SNS運用・SNS広告"},
    }
    historical_web_tabs = {"251127作成", "251222作成", "Web幹事"}
    hard_block_status = {"送信不可", "skip営業NG", "営業NG業種違い", "営業不可", "excluded"}
    strategic_rows = []
    for r in op_survivors:
        tab = r["tab"]
        is_fit = (tab in fit_classes and r["classification"] in fit_classes[tab]) or tab in historical_web_tabs
        if is_fit and r["status"] not in hard_block_status:
            strategic_rows.append(r)
    strategic_domains = {r["domain"] for r in strategic_rows if r["domain"]}
    strategic_companies = {r["company_norm"] for r in strategic_rows if r["company_norm"]}
    strategic_status = Counter(r["status"] or "(空欄)" for r in strategic_rows)

    cross = {
        "operational_vs_sheet2_domain_overlap": len(op_domains & s2_domains),
        "operational_vs_sheet2_company_overlap": len(op_companies & s2_companies),
        "operational_vs_exclusion_domain_overlap": len(op_domains & ex_domains),
        "operational_vs_exclusion_company_overlap": len(op_companies & ex_companies),
        "sheet2_vs_exclusion_domain_overlap": len(s2_domains & ex_domains),
        "sheet2_vs_exclusion_company_overlap": len(s2_companies & ex_companies),
        "operational_rows_after_exclusion_or_match": len(op_survivors),
        "operational_unique_domains_after_exclusion_or_match": len(survivor_domains),
        "operational_unique_companies_after_exclusion_or_match": len(survivor_companies),
        "strategic_fit_rows_after_exclusion": len(strategic_rows),
        "strategic_fit_unique_domains_after_exclusion": len(strategic_domains),
        "strategic_fit_unique_companies_after_exclusion": len(strategic_companies),
        "strategic_fit_status_counts": dict(strategic_status.most_common()),
    }

    # Across operational tabs, count domains appearing in more than one tab.
    domain_tabs = defaultdict(set)
    company_tabs = defaultdict(set)
    for r in op_rows:
        if r["domain"]:
            domain_tabs[r["domain"]].add(r["tab"])
        if r["company_norm"]:
            company_tabs[r["company_norm"]].add(r["tab"])
    cross["operational_domains_in_multiple_tabs"] = sum(len(v) > 1 for v in domain_tabs.values())
    cross["operational_companies_in_multiple_tabs"] = sum(len(v) > 1 for v in company_tabs.values())

    pairwise = []
    for i, left in enumerate(operational):
        left_rows = records_by_tab.get(left, [])
        left_domains = {r["domain"] for r in left_rows if r["domain"]}
        left_companies = {r["company_norm"] for r in left_rows if r["company_norm"]}
        for right in operational[i + 1:]:
            right_rows = records_by_tab.get(right, [])
            right_domains = {r["domain"] for r in right_rows if r["domain"]}
            right_companies = {r["company_norm"] for r in right_rows if r["company_norm"]}
            pairwise.append({
                "left": left,
                "right": right,
                "domain_overlap": len(left_domains & right_domains),
                "company_overlap": len(left_companies & right_companies),
            })

    status_total = Counter()
    for t in operational:
        status_total.update(status_by_tab.get(t, {}))

    result = {
        "spreadsheet_title": book.title,
        "spreadsheet_id": book.id,
        "tabs": inventory,
        "operational": operational_summary,
        "sheet2": sheet2_summary,
        "all_collected_including_sheet2": all_collected_summary,
        "exclusion": exclude_summary,
        "cross_checks": cross,
        "pairwise_operational_overlap": pairwise,
        "operational_status_total": dict(status_total.most_common()),
        "status_by_tab": status_by_tab,
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
