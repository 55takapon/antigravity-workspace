from __future__ import annotations

import json
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = SKILL_DIR.parent.parent.parent
DATA_DIR = SKILL_DIR / "data"
sys.path.insert(0, str(SKILL_DIR / "scripts"))
sys.path.insert(0, str(DIST_DIR / "shared"))
import opener_helpers as helpers  # noqa: E402
import sheets_io  # noqa: E402


SHEET_URL = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
WORKSHEET = "Web幹事"
BLOCKED = {
    10: ("送信不可", "下記より制作パートナー様向けのLINE公式アカウントに登録した上でお問い合わせください。"),
    16: ("送信不可", "お問い合わせ E-mail　info@zaphc.shop"),
    32: ("送信不可", "株式会社マトリクスに関するお問合せは、下記までご連絡いただきますよう、よろしくお願いいたします。info@matrix-inc.jp"),
    39: ("送信不可", "メールでのお問い合わせはこちら"),
}
CONTACT_FIXES = {
    4: "https://gofw.jp/contact/",
    14: "https://www.fulltani.co.jp/homepage/contact_inquiry.html",
    15: "https://www.planuk.gr.jp/form/im/",
    20: "https://www.answer.co.jp/contact/",
    29: "https://www.flex-planning.com/contact/",
    46: "https://docs.google.com/forms/d/e/1FAIpQLSd95IebKlsrq19TGR_LJzWEDfgkBLX47u20cMuTaHF2u94sUA/viewform",
}
NAME_FIXES = {4: "株式会社ゴーフォワード", 41: "株式会社サイバーインジェクション"}
URL_FIXES = {38: "https://digi-studio.jp/"}


def main() -> int:
    tasks = json.loads((DATA_DIR / "_tasks_webkanji_rows2_50.json").read_text(encoding="utf-8"))
    results = json.loads((DATA_DIR / "_results_webkanji_rows2_50.json").read_text(encoding="utf-8"))
    intro_tmpl = helpers.load_intro()
    common_body = helpers.load_common_body()
    sender = helpers.load_sender_info()

    expected = {}
    for task in tasks:
        row_no = int(task["_row"])
        company = task["company_name"].strip()
        opener = results[str(task["idx"])].strip()
        intro = helpers.fill_placeholders(intro_tmpl, company, sender)
        body = helpers.fill_placeholders(common_body, company, sender)
        expected[row_no] = "\n\n".join((intro, opener, body))

    ws = sheets_io.open_worksheet(SHEET_URL, WORKSHEET)
    values = ws.get_all_values()
    header = values[0]
    fields = ["company_name", "url", "contact_url", "message", "status", "error_reason"]
    missing = [name for name in fields if name not in header]
    if missing:
        raise SystemExit(f"missing headers: {missing}")
    col = {name: header.index(name) for name in fields}
    rows = {}
    for row_no in range(2, 51):
        raw = values[row_no - 1] if row_no - 1 < len(values) else []
        rows[row_no] = {
            name: raw[idx].strip() if idx < len(raw) else ""
            for name, idx in col.items()
        }

    exact_mismatches = [row_no for row_no, message in expected.items() if rows[row_no]["message"] != message]
    blocked_message_nonblank = [row_no for row_no in BLOCKED if rows[row_no]["message"]]
    blocked_status_mismatches = [
        row_no for row_no, (status, reason) in BLOCKED.items()
        if rows[row_no]["status"] != status or rows[row_no]["error_reason"] != reason
    ]
    opener_bad = [
        int(task["_row"])
        for task in tasks
        if len([p for p in results[str(task["idx"])].replace("\r\n", "\n").split("\n\n") if p.strip()]) != 3
    ]
    contact_fix_mismatches = [row for row, value in CONTACT_FIXES.items() if rows[row]["contact_url"] != value]
    name_fix_mismatches = [row for row, value in NAME_FIXES.items() if rows[row]["company_name"] != value]
    url_fix_mismatches = [row for row, value in URL_FIXES.items() if rows[row]["url"] != value]
    messages = [rows[row]["message"] for row in expected]
    latest_body_missing = [row for row in expected if "ジェットプロデュース\n代表　田中 克章\nEmail　kansha@jet-produce.com" not in rows[row]["message"]]

    report = {
        "worksheet": ws.title,
        "range": [2, 50],
        "physical_rows": len(rows),
        "expected_messages": len(expected),
        "message_nonblank": sum(1 for row in rows.values() if row["message"]),
        "message_blank": sum(1 for row in rows.values() if not row["message"]),
        "unique_messages": len(set(messages)),
        "three_paragraph_openers": len(tasks) - len(opener_bad),
        "opener_bad_rows": opener_bad,
        "exact_message_mismatches": exact_mismatches,
        "blocked_rows": sorted(BLOCKED),
        "blocked_message_nonblank": blocked_message_nonblank,
        "blocked_status_mismatches": blocked_status_mismatches,
        "contact_fix_mismatches": contact_fix_mismatches,
        "name_fix_mismatches": name_fix_mismatches,
        "url_fix_mismatches": url_fix_mismatches,
        "latest_body_missing": latest_body_missing,
        "company_blank": sum(1 for row in rows.values() if not row["company_name"]),
        "url_blank": sum(1 for row in rows.values() if not row["url"]),
        "contact_url_blank": sum(1 for row in rows.values() if not row["contact_url"]),
    }
    report["ok"] = all([
        report["physical_rows"] == 49,
        report["expected_messages"] == 45,
        report["message_nonblank"] == 45,
        report["message_blank"] == 4,
        report["unique_messages"] == 45,
        report["three_paragraph_openers"] == 45,
        not exact_mismatches,
        not blocked_message_nonblank,
        not blocked_status_mismatches,
        not contact_fix_mismatches,
        not name_fix_mismatches,
        not url_fix_mismatches,
        not latest_body_missing,
        report["company_blank"] == 0,
        report["url_blank"] == 0,
        report["contact_url_blank"] == 0,
    ])
    out = DATA_DIR / "_audit_webkanji_rows2_50.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
