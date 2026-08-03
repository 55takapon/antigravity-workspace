from __future__ import annotations

import json
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_DIR.parent.parent.parent
DATA_DIR = SKILL_DIR / "data"
sys.path.insert(0, str(REPO_ROOT / "shared"))

import sheets_io  # noqa: E402


SHEET_URL = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
WORKSHEET = "シート1"
EXPECTED_COMPANIES = {
    970: "株式会社NEOプロモーション",
    971: "株式会社RegionLine",
    972: "合資会社ビーウェイブ",
    973: "有限会社アイディー・ブランド",
    974: "有限会社メディアファクトリー",
    975: "株式会社総協エージェンシー",
    976: "nps株式会社",
    977: "株式会社クルーズ",
    978: "有限会社Panthers",
    979: "株式会社みなつ",
    980: "株式会社スマートカンパニー",
    981: "株式会社H&Company",
    982: "株式会社アソオ",
    983: "株式会社ジェイ.ワン",
    984: "グリニッジ株式会社",
    985: "株式会社サン・アド",
    986: "株式会社ピースカンパニー",
    987: "株式会社協同プレス",
    988: "株式会社デルタアイエムシー",
}
BLOCKERS = {
    970: "準備中",
    971: "このデモは「外部リンク禁止」ルールに合わせて、LINEの外部URLを設置していません。",
    972: "治療院オーナー様限定／LINEで無料診断を申し込む",
    980: "[contact-form-7 id=\"442\" title=\"コンタクトフォーム デスクトップとタブレット\"]",
}
CONTACT_FIXES = {
    983: "https://jei-one.co.jp/contact/",
    985: "https://www.san-ad.co.jp/form/contact/",
}


def main() -> int:
    ws = sheets_io.open_worksheet(SHEET_URL, WORKSHEET)
    values = ws.get_all_values()
    header = values[0]
    required = ["company_name", "contact_url", "message", "status", "error_reason"]
    missing = [name for name in required if name not in header]
    if missing:
        raise SystemExit(f"missing exact headers: {missing}")
    col = {name: header.index(name) for name in required}

    snapshot = {
        "worksheet": ws.title,
        "header": header,
        "rows": {str(r): values[r - 1] for r in range(970, 989)},
    }
    (DATA_DIR / "_snapshot_rows970_988_current_before_write.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for row_no, expected_company in EXPECTED_COMPANIES.items():
        row = values[row_no - 1]
        actual_company = row[col["company_name"]].strip() if col["company_name"] < len(row) else ""
        message = row[col["message"]].strip() if col["message"] < len(row) else ""
        if actual_company != expected_company:
            raise SystemExit(f"row {row_no} company changed: {actual_company!r} != {expected_company!r}")
        if message:
            raise SystemExit(f"row {row_no} message is no longer blank; refusing to overwrite")

    blocker_rows = [
        {"_row": row_no, "status": "送信不可", "error_reason": reason}
        for row_no, reason in BLOCKERS.items()
    ]
    contact_rows = [
        {"_row": row_no, "contact_url": url}
        for row_no, url in CONTACT_FIXES.items()
    ]
    blocker_cells = sheets_io.write_cells(ws, blocker_rows, ["status", "error_reason"], overwrite=True)
    contact_cells = sheets_io.write_cells(ws, contact_rows, ["contact_url"], overwrite=True)
    print(f"blocker_cells={blocker_cells} contact_cells={contact_cells}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
