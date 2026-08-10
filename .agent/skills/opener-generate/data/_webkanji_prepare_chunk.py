from __future__ import annotations

import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent
SKILL = DATA.parent
REPO = SKILL.parents[2]
sys.path.insert(0, str(REPO / "shared"))
import sheets_io

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
WORKSHEET = "Web幹事"


def main() -> int:
    cfg_path = Path(sys.argv[1])
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    start, end = int(cfg["start"]), int(cfg["end"])
    snap = json.loads((DATA / f"_snapshot_webkanji_rows{start}_{end}_current.json").read_text(encoding="utf-8"))
    tasks = json.loads((DATA / f"_tasks_webkanji_rows{start}_{end}_raw.json").read_text(encoding="utf-8"))
    by_row = {int(r["_row"]): r for r in snap}
    fixes = {k: {int(r): v for r, v in cfg.get(k, {}).items()} for k in ("company_fixes", "url_fixes", "contact_fixes")}
    blocked = {int(r): v for r, v in cfg.get("blocked", {}).items()}

    # Build a complete six-field desired row for every physical row.  Passing sparse
    # rows to write_cells would blank unspecified columns because it writes a shared
    # column set for every row.
    updates = []
    for row_no in range(start, end + 1):
        src = by_row[row_no]
        u = {"_row": row_no,
             "company_name": src.get("company_name", ""),
             "url": src.get("url", ""),
             "contact_url": src.get("contact_url", ""),
             "message": "",
             "status": "",
             "error_reason": ""}
        if row_no in fixes["company_fixes"]:
            u["company_name"] = fixes["company_fixes"][row_no]
        if row_no in fixes["url_fixes"]:
            u["url"] = fixes["url_fixes"][row_no]
        if row_no in fixes["contact_fixes"]:
            u["contact_url"] = fixes["contact_fixes"][row_no]
        if row_no in blocked:
            u["message"] = ""
            u["status"] = blocked[row_no]["status"]
            u["error_reason"] = blocked[row_no]["reason"]
        updates.append(u)

    ws = sheets_io.open_worksheet(SHEET, WORKSHEET)
    header = ws.row_values(1)
    colmap = sheets_io.find_columns(header, ["company_name", "url", "contact_url", "message", "status", "error_reason"])
    actual = {}
    for canonical, idx in colmap.items():
        actual[canonical] = header[idx] if idx is not None else canonical
    rendered = []
    for u in updates:
        rendered.append({"_row": u["_row"], **{actual[k]: v for k, v in u.items() if k != "_row"}})
    columns = sorted({k for u in rendered for k in u if k != "_row"})
    written = sheets_io.write_cells(ws, rendered, columns, overwrite=True) if columns else 0

    eligible = []
    for t in tasks:
        row_no = start + int(t["idx"])
        if row_no in blocked:
            continue
        t = dict(t)
        t["_row"] = row_no
        t["company_name"] = fixes["company_fixes"].get(row_no, t.get("company_name", ""))
        t["url"] = fixes["url_fixes"].get(row_no, t.get("url", ""))
        eligible.append(t)
    out = DATA / f"_tasks_webkanji_rows{start}_{end}.json"
    out.write_text(json.dumps(eligible, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"eligible": len(eligible), "blocked": len(blocked), "written_cells": written}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
