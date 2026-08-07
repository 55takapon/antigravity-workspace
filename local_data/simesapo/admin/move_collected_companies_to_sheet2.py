#!/usr/bin/env python3
"""Copy the verified Aug 2-7 collection block from Sheet1 to Sheet2 safely."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
BACKUP = ROOT / "local_data" / "simesapo" / "admin" / "sheet2_migration_backup_20260807.csv"
sys.path.insert(0, str(DIST / "shared"))
from sheets_io import get_client  # noqa: E402


SPREADSHEET_ID = "1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ"
SOURCE = "シート1"
DEST = "シート2"
START_ROW = 1874
END_ROW = 4723
EXPECTED_ROWS = 2850


def normalized_domain(value: str) -> str:
    value = (value or "").strip()
    if "://" not in value:
        value = "https://" + value
    host = (urlparse(value).hostname or "").lower().strip(".")
    return host[4:] if host.startswith("www.") else host


def digest(rows: list[list[str]]) -> str:
    normalized = "\n".join("\t".join(row + [""] * (16 - len(row))) for row in rows)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def main() -> None:
    client = get_client(str(DIST / "shared" / "gcp_service_account.json"))
    sh = client.open_by_key(SPREADSHEET_ID)
    source = sh.worksheet(SOURCE)

    titles = {ws.title for ws in sh.worksheets()}
    if DEST in titles:
        raise SystemExit(f"STOP: {DEST} already exists; migration was not retried")

    header = source.get("A1:P1", value_render_option="FORMATTED_VALUE")[0]
    rows = source.get(f"A{START_ROW}:P{END_ROW}", value_render_option="FORMATTED_VALUE")
    rows = [row + [""] * (16 - len(row)) for row in rows]
    header = header + [""] * (16 - len(header))

    if len(rows) != EXPECTED_ROWS:
        raise SystemExit(f"STOP: expected {EXPECTED_ROWS} rows, got {len(rows)}")
    required_blanks = {
        "company_name": sum(not row[0].strip() for row in rows),
        "url": sum(not row[1].strip() for row in rows),
        "contact_url": sum(not row[5].strip() for row in rows),
        "classification_O": sum(not row[14].strip() for row in rows),
        "evidence_P": sum(not row[15].strip() for row in rows),
    }
    if any(required_blanks.values()):
        raise SystemExit("STOP: required blanks: " + json.dumps(required_blanks, ensure_ascii=False))
    domains = [normalized_domain(row[1]) for row in rows]
    if len(set(domains)) != EXPECTED_ROWS:
        raise SystemExit("STOP: duplicate domains exist in migration scope")

    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    with BACKUP.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)

    original_hash = digest(rows)
    dest = sh.add_worksheet(title=DEST, rows=3000, cols=16)
    dest.update([header] + rows, f"A1:P{EXPECTED_ROWS + 1}", value_input_option="RAW")

    sh.batch_update({
        "requests": [
            {
                "copyPaste": {
                    "source": {"sheetId": source.id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 16},
                    "destination": {"sheetId": dest.id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 16},
                    "pasteType": "PASTE_FORMAT",
                    "pasteOrientation": "NORMAL",
                }
            },
            {
                "updateSheetProperties": {
                    "properties": {"sheetId": dest.id, "gridProperties": {"frozenRowCount": 1}},
                    "fields": "gridProperties.frozenRowCount",
                }
            },
            {
                "setBasicFilter": {
                    "filter": {"range": {"sheetId": dest.id, "startRowIndex": 0, "endRowIndex": EXPECTED_ROWS + 1, "startColumnIndex": 0, "endColumnIndex": 16}}
                }
            },
        ]
    })

    copied = dest.get(f"A2:P{EXPECTED_ROWS + 1}", value_render_option="FORMATTED_VALUE")
    copied = [row + [""] * (16 - len(row)) for row in copied]
    if len(copied) != EXPECTED_ROWS or copied != rows or digest(copied) != original_hash:
        raise SystemExit("STOP: Sheet2 readback mismatch; source rows were not deleted")

    source_values = source.get_all_values()
    dest_values = dest.get_all_values()
    source_domains = {normalized_domain(row[1]) for row in source_values[1:] if len(row) > 1 and row[1].strip()}
    dest_domains = {normalized_domain(row[1]) for row in dest_values[1:] if len(row) > 1 and row[1].strip()}
    checks = {
        "copied_rows": len(dest_values) - 1,
        "sheet1_data_rows": len(source_values) - 1,
        "sheet2_data_rows": len(dest_values) - 1,
        "sheet2_unique_domains": len(dest_domains),
        "source_rows_retained": len(source_values) - 1 == END_ROW - 1,
        "sheet2_hash": digest([r + [""] * (16 - len(r)) for r in dest_values[1:]]),
        "expected_hash": original_hash,
        "backup": str(BACKUP),
    }
    expected = {
        "copied_rows": EXPECTED_ROWS,
        "sheet1_data_rows": END_ROW - 1,
        "sheet2_data_rows": EXPECTED_ROWS,
        "sheet2_unique_domains": EXPECTED_ROWS,
        "source_rows_retained": True,
    }
    for key, value in expected.items():
        if checks[key] != value:
            raise SystemExit("POST_MIGRATION_MISMATCH\n" + json.dumps(checks, ensure_ascii=False, indent=2))
    if checks["sheet2_hash"] != checks["expected_hash"]:
        raise SystemExit("POST_MIGRATION_HASH_MISMATCH\n" + json.dumps(checks, ensure_ascii=False, indent=2))
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
