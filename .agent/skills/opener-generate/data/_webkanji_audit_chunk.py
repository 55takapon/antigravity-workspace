from __future__ import annotations

import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent
SKILL = DATA.parent
REPO = SKILL.parents[2]
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(REPO / "shared"))
import opener_helpers as g
import sheets_io

SHEET = "https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing"
WORKSHEET = "Web幹事"


def build(company: str, opener: str) -> str:
    intro = g.fill_placeholders(g.load_intro(), company, g.load_sender_info())
    body = g.fill_placeholders(g.load_common_body(), company, g.load_sender_info())
    return "\n\n".join(x for x in (intro, opener, body) if x)


def main() -> int:
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    start, end = int(cfg["start"]), int(cfg["end"])
    blocked = {int(k): v for k, v in cfg.get("blocked", {}).items()}
    results = json.loads((DATA / f"_results_webkanji_rows{start}_{end}.json").read_text(encoding="utf-8"))
    tasks = json.loads((DATA / f"_tasks_webkanji_rows{start}_{end}.json").read_text(encoding="utf-8"))
    ws = sheets_io.open_worksheet(SHEET, WORKSHEET)
    rows = sheets_io.read_rows(ws, want=["company_name", "url", "contact_url", "message", "status", "error_reason"], require=["company_name", "url"])
    live = {int(r["_row"]): r for r in rows if start <= int(r["_row"]) <= end}
    para_issues, exact_mismatch = [], []
    for t in tasks:
        idx, row_no = str(t["idx"]), int(t["_row"])
        opener = (results.get(idx) or "").strip()
        if len([p for p in opener.split("\n\n") if p.strip()]) != 3:
            para_issues.append(row_no)
        if live[row_no].get("message", "") != build(t["company_name"], opener):
            exact_mismatch.append(row_no)
    blocked_nonblank, blocked_meta = [], []
    for row_no, meta in blocked.items():
        row = live[row_no]
        if row.get("message", "").strip():
            blocked_nonblank.append(row_no)
        if row.get("status", "") != meta["status"] or row.get("error_reason", "") != meta["reason"]:
            blocked_meta.append(row_no)
    fix_mismatch = {}
    for key, field in (("company_fixes", "company_name"), ("url_fixes", "url"), ("contact_fixes", "contact_url")):
        fix_mismatch[key] = [int(r) for r, v in cfg.get(key, {}).items() if live[int(r)].get(field, "") != v]
    messages = [live[int(t["_row"])].get("message", "") for t in tasks]
    report = {"worksheet": WORKSHEET, "range": [start, end], "physical_rows": end-start+1,
              "eligible_rows": len(tasks), "message_nonblank": sum(bool(x.strip()) for x in messages),
              "blocked_rows": sorted(blocked), "blocked_message_nonblank": blocked_nonblank,
              "blocked_metadata_mismatches": blocked_meta, "opener_paragraph_issues": para_issues,
              "exact_message_mismatches": exact_mismatch, "unique_messages": len(set(messages)),
              "company_fix_mismatches": fix_mismatch["company_fixes"],
              "url_fix_mismatches": fix_mismatch["url_fixes"],
              "contact_fix_mismatches": fix_mismatch["contact_fixes"]}
    report["ok"] = (report["message_nonblank"] == len(tasks) == report["unique_messages"]
                    and not any((blocked_nonblank, blocked_meta, para_issues, exact_mismatch,
                                 *fix_mismatch.values())))
    out = DATA / f"_audit_webkanji_rows{start}_{end}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
