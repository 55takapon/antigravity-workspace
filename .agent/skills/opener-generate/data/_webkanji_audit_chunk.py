from __future__ import annotations

import json
import re
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


def paragraphs(text: str) -> list[str]:
    return [x.strip() for x in re.split(r"\n\s*\n", (text or "").strip()) if x.strip()]


def main() -> int:
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    start, end = int(cfg["start"]), int(cfg["end"])
    blocked = {int(k): v for k, v in cfg.get("blocked", {}).items()}
    company_fixes = {int(k): v for k, v in cfg.get("company_fixes", {}).items()}
    url_fixes = {int(k): v for k, v in cfg.get("url_fixes", {}).items()}
    contact_fixes = {int(k): v for k, v in cfg.get("contact_fixes", {}).items()}
    tasks = json.loads((HERE / f"_tasks_webkanji_rows{start}_{end}.json").read_text(encoding="utf-8"))
    results = json.loads((HERE / f"_results_webkanji_rows{start}_{end}.json").read_text(encoding="utf-8"))
    task_by_row = {int(t["_row"]): t for t in tasks}
    sender, intro, body = g.load_sender_info(), g.load_intro(), g.load_common_body()

    for attempt in range(1, 4):
        try:
            ws = sheets_io.open_worksheet(SHEET, WORKSHEET)
            rows = sheets_io.read_rows(ws, want=FIELDS, require=FIELDS[:4])
            break
        except Exception as e:
            if attempt == 3:
                raise
            print(f"[retry {attempt}/3] Google Sheets読込失敗: {type(e).__name__}: {e}", file=sys.stderr)
            time.sleep(5 * attempt)
    live = {int(r["_row"]): r for r in rows if start <= int(r["_row"]) <= end}
    para_issues, exact_issues, blocked_message = [], [], []
    blocked_meta, company_mis, url_mis, contact_mis = [], [], [], []
    eligible_meta, required_blanks = [], []
    messages = []
    for row_no in range(start, end + 1):
        r = live.get(row_no, {k: "" for k in FIELDS})
        if row_no in blocked:
            if (r.get("message") or "").strip():
                blocked_message.append(row_no)
            mark = blocked[row_no]
            if (r.get("status") or "").strip() != mark["status"] or (r.get("error_reason") or "").strip() != mark["reason"]:
                blocked_meta.append(row_no)
        else:
            t = task_by_row.get(row_no)
            opener = (results.get(str(row_no - start)) or "").strip()
            if len(paragraphs(opener)) != 3:
                para_issues.append(row_no)
            company = (t or {}).get("company_name", "")
            exact = "\n\n".join(x for x in (
                g.fill_placeholders(intro, company, sender), opener,
                g.fill_placeholders(body, company, sender)) if x)
            actual = (r.get("message") or "").strip()
            if actual != exact.strip():
                exact_issues.append(row_no)
            if actual:
                messages.append(actual)
            if (r.get("status") or "").strip() or (r.get("error_reason") or "").strip():
                eligible_meta.append(row_no)
            if not all((r.get(k) or "").strip() for k in ("company_name", "url", "contact_url")):
                required_blanks.append(row_no)
        if row_no in company_fixes and (r.get("company_name") or "").strip() != company_fixes[row_no]:
            company_mis.append(row_no)
        if row_no in url_fixes and (r.get("url") or "").strip() != url_fixes[row_no]:
            url_mis.append(row_no)
        if row_no in contact_fixes and (r.get("contact_url") or "").strip() != contact_fixes[row_no]:
            contact_mis.append(row_no)
    eligible = 50 - len(blocked)
    out = {
        "worksheet": WORKSHEET, "range": [start, end], "physical_rows": 50, "eligible_rows": eligible,
        "message_nonblank": len(messages), "blocked_rows": sorted(blocked),
        "blocked_message_nonblank": blocked_message, "blocked_metadata_mismatches": blocked_meta,
        "opener_paragraph_issues": para_issues, "exact_message_mismatches": exact_issues,
        "eligible_metadata_nonblank": eligible_meta, "eligible_required_field_blanks": required_blanks,
        "unique_messages": len(set(messages)), "company_fix_mismatches": company_mis,
        "url_fix_mismatches": url_mis, "contact_fix_mismatches": contact_mis,
    }
    out["ok"] = (
        len(live) == 50 and len(messages) == eligible and len(set(messages)) == eligible and
        not any((blocked_message, blocked_meta, para_issues, exact_issues, eligible_meta, required_blanks,
                 company_mis, url_mis, contact_mis))
    )
    dest = HERE / f"_audit_webkanji_rows{start}_{end}.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
