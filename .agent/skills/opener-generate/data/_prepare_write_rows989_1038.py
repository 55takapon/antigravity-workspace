from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = SKILL_DIR.parent.parent.parent
DATA_DIR = SKILL_DIR / "data"
sys.path.insert(0, str(DIST_DIR / "shared"))

import sheets_io  # noqa: E402


SHEET_URL = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
WORKSHEET = "シート1"

BLOCKERS = {
    999: ("送信不可", "以下のメールアドレスもしくは、お電話にてお願いいたします。"),
    1001: ("skip営業NG", "※営業代行・マーケティングツール・M&Aのお誘いはお断りいたします。"),
    1018: ("skip営業NG", "※お客様専用のご相談フォームです。営業・勧誘のメールは送らないでください。"),
    1029: ("skip営業NG", "メールアドレスを利用しての商品・サービスの売り込みなどはご遠慮ください。"),
    1035: ("skip営業NG", "※当フォームを利用した当社への営業・売り込みはご遠慮いただいております。"),
    1037: ("送信不可", "下記のEメールアドレスをご利用いただくか、お電話、FAXでお問い合せください。"),
}

URL_FIXES = {
    1016: "https://www.architect.co.jp/contact/inquiry/",
    1034: "https://form.run/@rab-s-contact",
}

NAME_FIXES = {
    1012: "株式会社ケーアンドリサーチデータ",
    1013: "株式会社マーケッティング・サービス",
    1014: "株式会社ショッパーファースト",
    1015: "株式会社市場開発研究所",
    1016: "株式会社アーキテクト",
    1017: "株式会社コンシュマーズ・リサーチ",
    1033: "株式会社アズクリエイション",
    1036: "株式会社サキガケアドバ",
}


def main() -> int:
    input_path = DATA_DIR / "_input_rows989_1038_current.csv"
    raw_tasks_path = DATA_DIR / "_tasks_rows989_1038_current_raw.json"
    results_path = DATA_DIR / "_results_rows989_1038_current.json"
    tasks_path = DATA_DIR / "_tasks_rows989_1038_current.json"

    with input_path.open(encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    row_by_idx = {idx: int(row["_row"]) for idx, row in enumerate(source_rows)}
    raw_tasks = json.loads(raw_tasks_path.read_text(encoding="utf-8"))
    results = json.loads(results_path.read_text(encoding="utf-8"))

    expected = {
        str(task["idx"])
        for task in raw_tasks
        if row_by_idx[int(task["idx"])] not in BLOCKERS
    }
    actual = set(results)
    if expected != actual:
        raise SystemExit(f"result key mismatch missing={sorted(expected-actual)} extra={sorted(actual-expected)}")

    openers = list(results.values())
    if len(openers) != len(set(openers)):
        raise SystemExit("duplicate openers detected")
    quality = []
    for idx, opener in results.items():
        paragraphs = [p for p in opener.strip().split("\n\n") if p.strip()]
        max_line = max(len(line) for line in opener.splitlines())
        banned = [mark for mark in ("—", "…", "“", "”") if mark in opener]
        if len(paragraphs) != 3 or banned:
            raise SystemExit(f"quality failure idx={idx} paragraphs={len(paragraphs)} banned={banned}")
        quality.append({"idx": int(idx), "paragraphs": len(paragraphs), "max_line": max_line})

    tasks = []
    for task in raw_tasks:
        idx = int(task["idx"])
        row_no = row_by_idx[idx]
        if row_no in BLOCKERS:
            continue
        normalized = dict(task)
        normalized["_row"] = row_no
        if row_no in NAME_FIXES:
            normalized["company_name"] = NAME_FIXES[row_no]
        tasks.append(normalized)
    tasks_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")

    ws = sheets_io.open_worksheet(SHEET_URL, WORKSHEET)
    blocker_rows = [
        {"_row": row_no, "status": status, "error_reason": reason}
        for row_no, (status, reason) in BLOCKERS.items()
    ]
    name_rows = [{"_row": row_no, "company_name": value} for row_no, value in NAME_FIXES.items()]
    url_rows = [{"_row": row_no, "contact_url": value} for row_no, value in URL_FIXES.items()]
    written = {
        "blockers": sheets_io.write_cells(ws, blocker_rows, ["status", "error_reason"], overwrite=True),
        "names": sheets_io.write_cells(ws, name_rows, ["company_name"], overwrite=True),
        "urls": sheets_io.write_cells(ws, url_rows, ["contact_url"], overwrite=True),
    }
    report = {
        "tasks": len(tasks),
        "results": len(results),
        "blockers": len(BLOCKERS),
        "all_three_paragraphs": all(x["paragraphs"] == 3 for x in quality),
        "max_line": max(x["max_line"] for x in quality),
        "sheet_cells_written": written,
        "tasks_path": str(tasks_path),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
