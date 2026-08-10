from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
REPO = SKILL.parents[2]
sys.path.insert(0, str(REPO / "shared"))
import sheets_io

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
WORKSHEET = "Web幹事"
FIELDS = ["company_name", "url", "contact_url", "message", "status", "error_reason"]


def main() -> int:
    start, end = map(int, sys.argv[1:3])
    if end - start + 1 != 50:
        raise SystemExit("50 physical rows are required")
    ws = sheets_io.open_worksheet(SHEET, WORKSHEET)
    rows = sheets_io.read_rows(ws, want=FIELDS, require=["company_name", "url"])
    by_row = {int(r["_row"]): r for r in rows}
    selected = []
    for row_no in range(start, end + 1):
        r = by_row.get(row_no, {"_row": row_no})
        selected.append({"_row": row_no, **{k: r.get(k, "") for k in FIELDS}})
    data = Path(__file__).resolve().parent
    stem = f"webkanji_rows{start}_{end}"
    (data / f"_snapshot_{stem}_current.json").write_text(
        json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (data / f"_input_{stem}_current.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows({k: r[k] for k in FIELDS} for r in selected)
    print(json.dumps({"start": start, "end": end, "rows": len(selected),
                      "message_nonblank": sum(bool(r["message"].strip()) for r in selected),
                      "contact_blank": sum(not r["contact_url"].strip() for r in selected)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
