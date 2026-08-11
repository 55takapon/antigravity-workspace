from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
ROOT = SKILL.parent.parent.parent
sys.path.insert(0, str(ROOT / "shared"))
import sheets_io  # noqa: E402

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
WORKSHEET = "Web幹事"
FIELDS = ["company_name", "url", "contact_url", "message", "status", "error_reason"]


def main() -> int:
    start, end = map(int, sys.argv[1:3])
    if end - start + 1 != 50:
        raise SystemExit("50 physical rows are required")
    ws = sheets_io.open_worksheet(SHEET, WORKSHEET)
    rows = sheets_io.read_rows(ws, want=FIELDS, require=["company_name", "url", "contact_url", "message"])
    by_row = {int(r["_row"]): r for r in rows}
    selected = []
    for row_no in range(start, end + 1):
        r = by_row.get(row_no, {"_row": row_no})
        selected.append({"_row": row_no, **{k: (r.get(k) or "").strip() for k in FIELDS}})

    jpath = HERE / f"_snapshot_webkanji_rows{start}_{end}_current.json"
    cpath = HERE / f"_input_webkanji_rows{start}_{end}_current.csv"
    jpath.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")
    with cpath.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows([{k: r[k] for k in FIELDS} for r in selected])
    print(json.dumps({
        "range": [start, end], "physical_rows": len(selected),
        "company_nonblank": sum(bool(r["company_name"]) for r in selected),
        "url_nonblank": sum(bool(r["url"]) for r in selected),
        "contact_nonblank": sum(bool(r["contact_url"]) for r in selected),
        "message_nonblank_before": sum(bool(r["message"]) for r in selected),
        "snapshot": str(jpath), "csv": str(cpath),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
