from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_DIR.parent.parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
DATA_DIR = SKILL_DIR / "data"

sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(REPO_ROOT / "shared"))

import opener_helpers as g  # noqa: E402
import sheets_io  # noqa: E402
from assemble_openers import _build_message  # noqa: E402


SHEET_URL = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
WORKSHEET = "シート1"
START_ROW = 970
END_ROW = 988


def _paragraph_count(text: str) -> int:
    normalized = text.replace("\r\n", "\n").strip()
    return len([p for p in normalized.split("\n\n") if p.strip()]) if normalized else 0


def main() -> int:
    tasks = json.loads((DATA_DIR / "_tasks_rows969_1018.json").read_text(encoding="utf-8"))
    results = json.loads((DATA_DIR / "_results_rows969_1018.json").read_text(encoding="utf-8"))
    blockers = json.loads((DATA_DIR / "_blockers_rows969_1018.json").read_text(encoding="utf-8"))
    blocker_by_row = {int(x["_row"]): x["reason"] for x in blockers}

    common_body = g.load_common_body()
    intro = g.load_intro()
    sender = g.load_sender_info()
    expected: dict[int, dict[str, str | int]] = {}
    for task in tasks:
        row_no = int(task.get("_row") or 0)
        if not START_ROW <= row_no <= END_ROW:
            continue
        idx = str(task["idx"])
        opener = (results.get(idx) or "").strip()
        expected[row_no] = {
            "company": (task.get("company_name") or "").strip(),
            "opener": opener,
            "opener_paragraphs": _paragraph_count(opener),
            "message": _build_message((task.get("company_name") or "").strip(), opener, common_body, intro, sender),
        }

    ws = sheets_io.open_worksheet(SHEET_URL, WORKSHEET)
    values = ws.get_all_values()
    header = values[0]
    aliases = {
        "message": ["message"],
        "status": ["status"],
        "error_reason": ["error_reason", "理由", "送信不可理由"],
        "contact_url": ["contact_url"],
        "company_name": ["company_name"],
    }
    wanted = ["company_name", "url", "contact_url", "message", "status", "error_reason"]
    colmap = sheets_io.find_columns(header, wanted, aliases=aliases)

    rows = []
    for row_no in range(START_ROW, END_ROW + 1):
        row = values[row_no - 1] if row_no - 1 < len(values) else []

        def value(key: str) -> str:
            idx = colmap.get(key)
            return row[idx].strip() if idx is not None and idx < len(row) else ""

        message = value("message")
        exp = expected.get(row_no)
        expected_message = str(exp["message"]) if exp else ""
        is_blocker = row_no in blocker_by_row
        rows.append(
            {
                "row": row_no,
                "company": value("company_name"),
                "url": value("url"),
                "contact_url": value("contact_url"),
                "message_present": bool(message),
                "message_expected_match": bool(exp) and message == expected_message,
                "message_sha256_12": hashlib.sha256(message.encode("utf-8")).hexdigest()[:12] if message else "",
                "expected_sha256_12": hashlib.sha256(expected_message.encode("utf-8")).hexdigest()[:12] if expected_message else "",
                "opener_paragraphs": int(exp["opener_paragraphs"]) if exp else None,
                "status": value("status"),
                "error_reason": value("error_reason"),
                "blocker_expected": is_blocker,
                "blocker_reason_match": is_blocker and value("error_reason") == blocker_by_row[row_no],
            }
        )

    summary = {
        "worksheet": ws.title,
        "range": [START_ROW, END_ROW],
        "physical_rows": len(rows),
        "eligible_expected": len(expected),
        "messages_present": sum(1 for r in rows if r["message_present"]),
        "messages_exact_match": sum(1 for r in rows if r["message_expected_match"]),
        "openers_three_paragraphs": sum(1 for r in rows if r["opener_paragraphs"] == 3),
        "blockers": sum(1 for r in rows if r["blocker_expected"]),
        "rows": rows,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
