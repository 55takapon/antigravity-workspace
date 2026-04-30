import csv
from pathlib import Path


INPUT = Path("web_kanji_missing_0429_duplicate_candidates.csv")
OUTPUT_CSV = Path("web_kanji_missing_0429_duplicate_review_only.csv")
OUTPUT_MD = Path("web_kanji_missing_0429_duplicate_review_preview.md")


def norm(value: str) -> str:
    return " ".join((value or "").strip().split())


def needs_review(row: dict) -> tuple[bool, str]:
    same_company = norm(row["kanji_company"]) == norm(row["format_company"])
    same_domain = norm(row["kanji_domain"]) == norm(row["format_domain"])
    if row["match_by"] == "company" and not same_domain:
        return True, "同一会社名・別ドメイン"
    if row["match_by"] == "domain" and not same_company:
        return True, "同一ドメイン・会社名違い"
    return False, ""


def main():
    with INPUT.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    review_rows = []
    for row in rows:
        review, reason = needs_review(row)
        if review:
            row["review_reason"] = reason
            review_rows.append(row)

    fieldnames = [
        "review_reason",
        "kanji_sheet_row",
        "kanji_number",
        "prefecture",
        "kanji_company",
        "kanji_representative",
        "kanji_domain",
        "kanji_url",
        "match_by",
        "format_sheet",
        "format_row",
        "format_company",
        "format_representative",
        "format_domain",
        "format_url",
    ]
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({name: row.get(name, "") for name in fieldnames} for row in review_rows)

    lines = [
        "# 4/29追加分 重複目視プレビュー",
        "",
        f"- 入力候補: {len(rows)}件",
        f"- 目視対象: {len(review_rows)}件",
        "- 除外: 同一会社名かつ同一ドメインの候補",
        "",
        "|理由|幹事行|追加側|追加URL|既存側|既存URL|",
        "|---|---:|---|---|---|---|",
    ]
    for row in review_rows:
        kanji = f"{row['prefecture']} / {row['kanji_company']} / {row['kanji_representative']} / {row['kanji_domain']}"
        existing = f"{row['format_sheet']}:{row['format_row']} / {row['format_company']} / {row['format_representative']} / {row['format_domain']}"
        lines.append(
            "|"
            + "|".join([
                row["review_reason"],
                row["kanji_sheet_row"],
                kanji.replace("|", " "),
                row["kanji_url"].replace("|", "%7C"),
                existing.replace("|", " "),
                row["format_url"].replace("|", "%7C"),
            ])
            + "|"
        )

    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    by_reason = {}
    for row in review_rows:
        by_reason[row["review_reason"]] = by_reason.get(row["review_reason"], 0) + 1

    print(f"input_candidates={len(rows)}")
    print(f"review_only={len(review_rows)}")
    print(f"by_reason={by_reason}")
    print(f"csv={OUTPUT_CSV}")
    print(f"md={OUTPUT_MD}")


if __name__ == "__main__":
    main()
