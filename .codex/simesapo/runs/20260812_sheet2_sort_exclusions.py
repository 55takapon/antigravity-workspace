#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
RUN = ROOT / ".codex" / "simesapo" / "runs" / "20260812_sheet2_sort_exclusions"
RUN.mkdir(parents=True, exist_ok=True)
CREDS = DIST / "shared" / "gcp_service_account.json"
SHEET_ID = "1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ"
TAB = "シート2"

sys.path.insert(0, str(DIST / ".codex_pydeps"))
sys.path.insert(0, str(DIST / "shared"))
from sheets_io import get_client  # noqa: E402


def pad(row: list[str], n: int) -> list[str]:
    return row + [""] * (n - len(row))


def domain(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url
    host = (urlparse(url).hostname or "").lower().strip(".")
    return host[4:] if host.startswith("www.") else host


def digest(row: list[str]) -> str:
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


client = get_client(str(CREDS))
sh = client.open_by_key(SHEET_ID)
ws = sh.worksheet(TAB)
values = ws.get("A1:P", value_render_option="FORMULA")
if len(values) != 2851:
    raise SystemExit(f"STOP: expected 2851 rows including header, got {len(values)}")
rows = [pad(r, 16) for r in values]
if ws.col_count != 16:
    raise SystemExit(f"STOP: expected 16 columns A:P, got {ws.col_count}")

data = [r[:16] for r in rows[1:]]
send_before = sum(r[14].startswith("送付対象｜") for r in data)
exclude_before = sum(r[14].startswith("除外｜") for r in data)
if (send_before, exclude_before) != (842, 302):
    raise SystemExit(f"STOP: expected send/exclude=842/302, got {send_before}/{exclude_before}")

backup = RUN / "sheet2_A_P_before_sort.csv"
with backup.open("w", encoding="utf-8-sig", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["original_row"] + rows[0][:16])
    for rn, row in enumerate(data, start=2):
        writer.writerow([rn] + row)

before_counter = Counter(digest(r) for r in data)
before_domains = [domain(r[1]) for r in data if domain(r[1])]
before_duplicate_domains = len(before_domains) - len(set(before_domains))

keys = [[0 if not row[14].startswith("除外｜") else 1, rn] for rn, row in enumerate(data, start=2)]
sh.batch_update({"requests": [{"appendDimension": {"sheetId": ws.id, "dimension": "COLUMNS", "length": 2}}]})
try:
    ws.update(range_name=f"Q2:R{len(rows)}", values=keys, value_input_option="RAW")
    sh.batch_update({"requests": [{
        "sortRange": {
            "range": {
                "sheetId": ws.id,
                "startRowIndex": 1,
                "endRowIndex": len(rows),
                "startColumnIndex": 0,
                "endColumnIndex": 18,
            },
            "sortSpecs": [
                {"dimensionIndex": 16, "sortOrder": "ASCENDING"},
                {"dimensionIndex": 17, "sortOrder": "ASCENDING"},
            ],
        }
    }]})
finally:
    sh.batch_update({"requests": [{"deleteDimension": {"range": {"sheetId": ws.id, "dimension": "COLUMNS", "startIndex": 16, "endIndex": 18}}}]})

after_raw = ws.get("A1:P", value_render_option="FORMULA")
after = [pad(r, 16) for r in after_raw]
if len(after) != 2851:
    raise SystemExit(f"STOP: post-sort expected 2851 rows, got {len(after)}")
after_data = [r[:16] for r in after[1:]]
after_counter = Counter(digest(r) for r in after_data)
send_after = sum(r[14].startswith("送付対象｜") for r in after_data)
exclude_after = sum(r[14].startswith("除外｜") for r in after_data)
first_exclude_idx = next((i for i, r in enumerate(after_data) if r[14].startswith("除外｜")), None)
tail_ok = first_exclude_idx is not None and all(r[14].startswith("除外｜") for r in after_data[first_exclude_idx:])
after_domains = [domain(r[1]) for r in after_data if domain(r[1])]
after_duplicate_domains = len(after_domains) - len(set(after_domains))
columns_restored = sh.worksheet(TAB).col_count == 16

report = {
    "rows_before": len(data),
    "rows_after": len(after_data),
    "send_before": send_before,
    "send_after": send_after,
    "exclude_before": exclude_before,
    "exclude_after": exclude_after,
    "first_exclude_sheet_row": first_exclude_idx + 2 if first_exclude_idx is not None else None,
    "last_exclude_sheet_row": len(after_data) + 1,
    "all_exclusions_contiguous_at_bottom": tail_ok,
    "row_multiset_equal": before_counter == after_counter,
    "duplicate_domains_before": before_duplicate_domains,
    "duplicate_domains_after": after_duplicate_domains,
    "columns_restored_to_A_P": columns_restored,
    "backup": str(backup),
}
(RUN / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
if not all((len(data) == len(after_data), send_before == send_after, exclude_before == exclude_after,
            tail_ok, before_counter == after_counter, before_duplicate_domains == after_duplicate_domains, columns_restored)):
    raise SystemExit("STOP: verification failed\n" + json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
