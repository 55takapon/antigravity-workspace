import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse


LEGAL = re.compile(r"株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人")
BASE_HEADER = [
    "company_name", "url", "address", "phone", "maps_url", "contact_url", "message", "sent_at",
    "status", "error_reason", "screenshot_path", "provider_used", "提案区分", "", "区分", "検出ワード",
]


def read_rows(path: str) -> tuple[list[str], list[list[str]]]:
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return next(reader), list(reader)


def norm_name(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").lower()
    value = LEGAL.sub("", value)
    return re.sub(r"[^0-9a-z一-龠々ぁ-んァ-ヶ]", "", value)


def norm_phone(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def domain(value: str) -> str:
    try:
        parsed = urlparse(value if "://" in value else "https://" + value)
        return parsed.netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def keys(row: list[str], offset: int = 1) -> tuple[str, str, str]:
    return norm_name(row[offset]), domain(row[offset + 1]), norm_phone(row[offset + 3])


def add_keys(target: tuple[set, set, set], row: list[str], offset: int = 1) -> None:
    name, dom, phone = keys(row, offset)
    if name:
        target[0].add(name)
    if dom:
        target[1].add(dom)
    if phone:
        target[2].add(phone)


def match_reason(target: tuple[set, set, set], row: list[str], offset: int = 1) -> str:
    name, dom, phone = keys(row, offset)
    hits = []
    if name and name in target[0]:
        hits.append("company_name")
    if dom and dom in target[1]:
        hits.append("domain")
    if phone and phone in target[2]:
        hits.append("phone")
    return "+".join(hits)


def destination_values(path: str) -> tuple[list[list[str]], tuple[set, set, set]]:
    _, rows = read_rows(path)
    values, target = [], (set(), set(), set())
    for row in rows:
        base = (row[1:16] + [""])[:16]
        values.append(base)
        add_keys(target, row)
    return values, target


def write(path: str, rows: list[list[str]]) -> None:
    with Path(path).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(BASE_HEADER)
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("audit_csv")
    parser.add_argument("--sheet1", required=True)
    parser.add_argument("--webmarketing", required=True)
    parser.add_argument("--references", nargs="+", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    _, audited = read_rows(args.audit_csv)
    reference_keys = (set(), set(), set())
    for path in args.references:
        _, rows = read_rows(path)
        for row in rows:
            add_keys(reference_keys, row)

    sheet1_rows, sheet1_keys = destination_values(args.sheet1)
    marketing_rows, marketing_keys = destination_values(args.webmarketing)
    sns_rows, audit_rows = [], []
    counts = {
        "sns_kept": 0, "sns_reference_excluded": 0, "web_appended": 0, "web_existing": 0,
        "web_reference_excluded": 0, "marketing_appended": 0, "marketing_existing": 0,
        "marketing_reference_excluded": 0, "service_excluded": 0, "review_excluded": 0,
    }

    for row in audited:
        physical = row[0]
        base = (row[1:17] + [""] * 16)[:16]
        state, reason, category, evidence, urls = row[17:22]
        base[14], base[15] = category, evidence
        ref_match = match_reason(reference_keys, row)
        action = ""

        if state == "sns":
            if ref_match:
                counts["sns_reference_excluded"] += 1
                action = "excluded_reference:" + ref_match
            else:
                sns_rows.append(base)
                counts["sns_kept"] += 1
                action = "kept_sns"
        elif state == "web":
            if ref_match:
                counts["web_reference_excluded"] += 1
                action = "excluded_reference:" + ref_match
            else:
                existing = match_reason(sheet1_keys, row)
                if existing:
                    counts["web_existing"] += 1
                    action = "already_in_sheet1:" + existing
                else:
                    sheet1_rows.append(base)
                    add_keys(sheet1_keys, ["", *base])
                    counts["web_appended"] += 1
                    action = "appended_sheet1"
        elif state == "marketing":
            if ref_match:
                counts["marketing_reference_excluded"] += 1
                action = "excluded_reference:" + ref_match
            else:
                existing = match_reason(marketing_keys, row)
                if existing:
                    counts["marketing_existing"] += 1
                    action = "already_in_webmarketing:" + existing
                else:
                    marketing_rows.append(base)
                    add_keys(marketing_keys, ["", *base])
                    counts["marketing_appended"] += 1
                    action = "appended_webmarketing"
        elif state == "review":
            counts["review_excluded"] += 1
            action = "excluded_unverified:" + reason
        else:
            counts["service_excluded"] += 1
            action = "excluded_service:" + reason

        audit_rows.append([physical, row[1], row[2], state, category, evidence, urls, action])

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    write(out / "sns_final.csv", sns_rows)
    write(out / "sheet1_final.csv", sheet1_rows)
    write(out / "webmarketing_final.csv", marketing_rows)
    with (out / "reclassification_audit.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["_row", "company_name", "url", "fit_state", "fit_category", "fit_evidence", "evidence_urls", "action"])
        writer.writerows(audit_rows)
    (out / "summary.json").write_text(json.dumps(counts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({**counts, "sns_final": len(sns_rows), "sheet1_final": len(sheet1_rows), "webmarketing_final": len(marketing_rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
