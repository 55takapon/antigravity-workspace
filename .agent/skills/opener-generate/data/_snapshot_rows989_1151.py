from __future__ import annotations

import csv
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
START_ROW = 989
END_ROW = 1151
FIELDS = ["company_name", "url", "contact_url", "message", "status", "error_reason"]


def main() -> int:
    ws = sheets_io.open_worksheet(SHEET_URL, WORKSHEET)
    values = ws.get_all_values()
    header = values[0]
    missing = [name for name in FIELDS if name not in header]
    if missing:
        raise SystemExit(f"missing headers: {missing}")
    col = {name: header.index(name) for name in FIELDS}
    rows = []
    for row_no in range(START_ROW, END_ROW + 1):
        source = values[row_no - 1]
        row = {"_row": row_no}
        for name in FIELDS:
            idx = col[name]
            row[name] = source[idx].strip() if idx < len(source) else ""
        rows.append(row)
    snapshot_path = DATA_DIR / "_snapshot_rows989_1151_current.json"
    csv_path = DATA_DIR / "_input_rows989_1151_current.csv"
    snapshot_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["_row", *FIELDS])
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "worksheet": ws.title,
        "range": [START_ROW, END_ROW],
        "physical_rows": len(rows),
        "message_nonblank": sum(1 for row in rows if row["message"]),
        "message_blank": sum(1 for row in rows if not row["message"]),
        "contact_url_blank": sum(1 for row in rows if not row["contact_url"]),
        "status_nonblank": sum(1 for row in rows if row["status"]),
        "snapshot": str(snapshot_path),
        "csv": str(csv_path),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
