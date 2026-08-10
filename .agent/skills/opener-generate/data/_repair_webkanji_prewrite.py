from __future__ import annotations

import json
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = SKILL_DIR.parent.parent.parent
DATA_DIR = SKILL_DIR / "data"
sys.path.insert(0, str(DIST_DIR / "shared"))
import sheets_io  # noqa: E402


SHEET_URL = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
WORKSHEET = "Web幹事"
NAME_FIXES = {4: "株式会社ゴーフォワード", 41: "株式会社サイバーインジェクション"}
URL_FIXES = {38: "https://digi-studio.jp/"}
CONTACT_FIXES = {
    4: "https://gofw.jp/contact/",
    14: "https://www.fulltani.co.jp/homepage/contact_inquiry.html",
    15: "https://www.planuk.gr.jp/form/im/",
    20: "https://www.answer.co.jp/contact/",
    29: "https://www.flex-planning.com/contact/",
    46: "https://docs.google.com/forms/d/e/1FAIpQLSd95IebKlsrq19TGR_LJzWEDfgkBLX47u20cMuTaHF2u94sUA/viewform",
}
BLOCKED = {
    10: ("送信不可", "下記より制作パートナー様向けのLINE公式アカウントに登録した上でお問い合わせください。"),
    16: ("送信不可", "お問い合わせ E-mail　info@zaphc.shop"),
    32: ("送信不可", "株式会社マトリクスに関するお問合せは、下記までご連絡いただきますよう、よろしくお願いいたします。info@matrix-inc.jp"),
    39: ("送信不可", "メールでのお問い合わせはこちら"),
}


def main() -> int:
    tasks = json.loads((DATA_DIR / "_tasks_webkanji_rows2_50_repaired.json").read_text(encoding="utf-8"))
    contacts = json.loads((DATA_DIR / "_contact_scan_webkanji_rows2_50.json").read_text(encoding="utf-8"))
    contact_by_row = {int(item["row"]): item["contact_url"] for item in contacts}
    if len(tasks) != 49 or len(contact_by_row) != 49:
        raise SystemExit(f"recovery source incomplete: tasks={len(tasks)} contacts={len(contact_by_row)}")

    rows = []
    for task in tasks:
        row_no = int(task["idx"]) + 2
        rows.append({
            "_row": row_no,
            "company_name": NAME_FIXES.get(row_no, task["company_name"]),
            "url": URL_FIXES.get(row_no, task["url"]),
            "contact_url": CONTACT_FIXES.get(row_no, contact_by_row[row_no]),
        })

    ws = sheets_io.open_worksheet(SHEET_URL, WORKSHEET)
    restored = sheets_io.write_cells(
        ws, rows, ["company_name", "url", "contact_url"], overwrite=True
    )
    blockers = [
        {"_row": row_no, "status": status, "error_reason": reason}
        for row_no, (status, reason) in BLOCKED.items()
    ]
    blocked_written = sheets_io.write_cells(
        ws, blockers, ["status", "error_reason"], overwrite=True
    )
    print(json.dumps({"restored_cells": restored, "blocked_cells": blocked_written}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
