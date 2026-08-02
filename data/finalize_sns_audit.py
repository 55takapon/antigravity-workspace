import argparse
import csv
import html
import re
from pathlib import Path
from urllib.parse import urlparse


OVERRIDES = {
    155: "カンパーニュ株式会社",
    167: "株式会社FLCクリエイティブスタジオ",
    370: "株式会社FaceIntelligence&co.",
    552: "スライムワークデザイン株式会社",
    803: "INPグループ合同会社",
    868: "株式会社角川アスキー総合研究所",
    1079: "アライドアーキテクツ株式会社",
    1109: "Plow株式会社",
    1660: "株式会社Fan Circle",
    1712: "エクシム株式会社",
    1718: "株式会社デザインスタジオパステル",
    1851: "ノーバジェット株式会社",
    2057: "アイビスティ有限会社",
    2132: "MOST8株式会社",
    2245: "株式会社ソアラサービス",
    2297: "株式会社アールデザイン",
    2360: "シン・フィールド合同会社",
    2554: "インダステクノロジーズ株式会社",
    2809: "アパッショナート合同会社",
}
SOURCE_RANK = {"company_label": 0, "company_jsonld": 1, "root_jsonld": 2, "existing": 3, "existing_english": 4}
BAD_MARKER = re.compile(
    r"(?:著作権|帰属|事務局|運営会社|主催[：:]|法人[：:]|\[会社名\]|［公式］|【公式】|公式サイト|"
    r"オフィシャル|自社HP|登録商標|〒|\bTEL\b|\bFAX\b|本気で行う会社|なら株式会社|会社概要はこちら|"
    r"All Rights|Copyright)",
    re.I,
)
GENERIC = re.compile(
    r"(?:株式会社|有限会社|合同会社|合資会社|合名会社)\s*(?:代表|代表取締役社長|創立|英語表記|本社|拠点|所在地|設立|について|co|内)?$",
    re.I,
)


def norm_name(value: str) -> str:
    return re.sub(r"[^0-9a-z一-龠ぁ-んァ-ヶ]", "", re.sub(r"株式会社|有限会社|合同会社|合資会社|合名会社|一般社団法人|一般財団法人", "", value.lower()))


def norm_phone(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def domain(value: str) -> str:
    try:
        return urlparse(value).netloc.lower().removeprefix("www.")
    except ValueError:
        return ""


def write(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("output_dir")
    args = parser.parse_args()
    with Path(args.input_csv).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    base_fields = [field for field in rows[0].keys() if field not in {"_row", "official_name", "name_source", "audit_state", "audit_reason", "category", "evidence", "resolved_url"}]
    audit_fields = ["_row", *base_fields, "official_name", "name_source", "audit_state", "audit_reason", "category", "evidence", "resolved_url"]

    for row in rows:
        physical = int(row["_row"])
        row["official_name"] = OVERRIDES.get(physical, html.unescape(row.get("official_name", ""))).strip()
        if row["audit_state"] == "valid":
            name = row["official_name"]
            if not name or BAD_MARKER.search(name) or GENERIC.fullmatch(name) or len(norm_name(name)) < 2:
                row["audit_state"] = "review"
                row["audit_reason"] = "company_name_lint_failed"

    for row in rows:
        if row["audit_state"] == "review":
            row["audit_state"] = "exclude"
            row["audit_reason"] = "unverified_" + (row.get("audit_reason") or "unknown")

    valid = [row for row in rows if row["audit_state"] == "valid"]
    valid.sort(key=lambda row: (SOURCE_RANK.get(row.get("name_source", ""), 9), int(row["_row"])))
    seen_domains, seen_names, seen_phones = set(), set(), set()
    deduped = []
    for row in valid:
        d = domain(row.get("resolved_url") or row.get("url", ""))
        n = norm_name(row["official_name"])
        p = norm_phone(row.get("phone", ""))
        reasons = []
        if d and d in seen_domains:
            reasons.append("domain")
        if n and n in seen_names:
            reasons.append("company_name")
        if p and p in seen_phones:
            reasons.append("phone")
        if reasons:
            row["audit_state"] = "exclude"
            row["audit_reason"] = "duplicate_" + "_".join(reasons)
            continue
        if d:
            seen_domains.add(d)
        if n:
            seen_names.add(n)
        if p:
            seen_phones.add(p)
        deduped.append(row)

    deduped.sort(key=lambda row: int(row["_row"]))
    main_rows = []
    for row in deduped:
        item = {field: row.get(field, "") for field in base_fields}
        item["company_name"] = row["official_name"]
        item["url"] = row.get("resolved_url") or row.get("url", "")
        item["区分"] = row["category"]
        item["検出ワード"] = row["evidence"]
        main_rows.append(item)

    excluded = sorted((row for row in rows if row["audit_state"] == "exclude"), key=lambda row: int(row["_row"]))
    review = sorted((row for row in rows if row["audit_state"] == "review"), key=lambda row: int(row["_row"]))
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    write(out / "sns_audit_main.csv", main_rows, base_fields)
    write(out / "sns_audit_excluded.csv", excluded, audit_fields)
    write(out / "sns_audit_review.csv", review, audit_fields)
    print(f"main={len(main_rows)} excluded={len(excluded)} review={len(review)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
