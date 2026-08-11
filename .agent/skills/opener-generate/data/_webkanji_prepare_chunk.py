from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
ROOT = SKILL.parent.parent.parent
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(SKILL / "scripts"))
import sheets_io  # noqa: E402
import opener_helpers as g  # noqa: E402

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
WORKSHEET = "Web幹事"
FIELDS = ["company_name", "url", "contact_url", "message", "status", "error_reason"]


def main() -> int:
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    start, end = int(cfg["start"]), int(cfg["end"])
    snapshot = json.loads((HERE / f"_snapshot_webkanji_rows{start}_{end}_current.json").read_text(encoding="utf-8"))
    raw_tasks = json.loads((HERE / f"_tasks_webkanji_rows{start}_{end}_raw.json").read_text(encoding="utf-8"))
    raw_by_row = {start + int(t["idx"]): t for t in raw_tasks}
    company_fixes = {int(k): v for k, v in cfg.get("company_fixes", {}).items()}
    url_fixes = {int(k): v for k, v in cfg.get("url_fixes", {}).items()}
    contact_fixes = {int(k): v for k, v in cfg.get("contact_fixes", {}).items()}
    blocked = {int(k): v for k, v in cfg.get("blocked", {}).items()}

    updates = []
    tasks = []
    for original in snapshot:
        row_no = int(original["_row"])
        company = company_fixes.get(row_no, original.get("company_name", "")).strip()
        url = url_fixes.get(row_no, original.get("url", "")).strip()
        contact = contact_fixes.get(row_no, original.get("contact_url", "")).strip()
        mark = blocked.get(row_no)
        updates.append({
            "_row": row_no, "company_name": company, "url": url, "contact_url": contact,
            "message": "", "status": (mark or {}).get("status", ""),
            "error_reason": (mark or {}).get("reason", ""),
        })
        if mark:
            continue
        raw = dict(raw_by_row[row_no])
        raw.update({"idx": row_no - start, "_row": row_no, "company_name": company, "url": url})
        if url != (original.get("url") or "").strip():
            raw["hp_text"] = g.fetch_hp_text(url) if url else ""
        tasks.append(raw)

    out = HERE / f"_tasks_webkanji_rows{start}_{end}.json"
    out.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    last_error = None
    for attempt in range(1, 4):
        try:
            ws = sheets_io.open_worksheet(SHEET, WORKSHEET)
            written = sheets_io.write_cells(ws, updates, FIELDS, overwrite=True)
            break
        except Exception as e:
            last_error = e
            if attempt == 3:
                raise
            print(f"[retry {attempt}/3] Google Sheets接続失敗: {type(e).__name__}: {e}", file=sys.stderr)
            time.sleep(5 * attempt)
    print(json.dumps({"range": [start, end], "eligible": len(tasks), "blocked": len(blocked),
                      "written_cells": written, "tasks": str(out)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
