#!/usr/bin/env python3
"""Finalize the authorized Sheet1 -> Sheet2 migration."""

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
START_ROW = 1874
END_ROW = 4723
EXPECTED = 2850


def pad(rows: list[list[str]]) -> list[list[str]]:
    return [row + [""] * (16 - len(row)) for row in rows]


def digest(rows: list[list[str]]) -> str:
    body = "\n".join("\t".join(row[:16]) for row in pad(rows))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def domain(value: str) -> str:
    value = (value or "").strip()
    if "://" not in value:
        value = "https://" + value
    host = (urlparse(value).hostname or "").lower().strip(".")
    return host[4:] if host.startswith("www.") else host


def main() -> None:
    if not BACKUP.exists():
        raise SystemExit(f"STOP: backup not found: {BACKUP}")
    with BACKUP.open("r", encoding="utf-8-sig", newline="") as fh:
        backup_rows = list(csv.reader(fh))[1:]

    client = get_client(str(DIST / "shared" / "gcp_service_account.json"))
    sh = client.open_by_key(SPREADSHEET_ID)
    source = sh.worksheet("シート1")
    dest = sh.worksheet("シート2")

    source_block = pad(source.get(f"A{START_ROW}:P{END_ROW}", value_render_option="FORMATTED_VALUE"))
    dest_block = pad(dest.get(f"A2:P{EXPECTED + 1}", value_render_option="FORMATTED_VALUE"))
    backup_block = pad(backup_rows)
    hashes = {"source": digest(source_block), "sheet2": digest(dest_block), "backup": digest(backup_block)}
    if len(source_block) != EXPECTED or len(dest_block) != EXPECTED or len(backup_block) != EXPECTED:
        raise SystemExit("STOP: row count mismatch before deletion\n" + json.dumps(hashes, ensure_ascii=False, indent=2))
    if len(set(hashes.values())) != 1:
        raise SystemExit("STOP: source, Sheet2, and backup are not identical\n" + json.dumps(hashes, ensure_ascii=False, indent=2))

    boundary_before = source.get(f"A{START_ROW - 1}:P{START_ROW - 1}", value_render_option="FORMATTED_VALUE")
    sh.batch_update({"requests": [{"deleteDimension": {"range": {"sheetId": source.id, "dimension": "ROWS", "startIndex": START_ROW - 1, "endIndex": END_ROW}}}]})

    source_values = source.get_all_values()
    dest_values = dest.get_all_values()
    source_domains = {domain(row[1]) for row in source_values[1:] if len(row) > 1 and row[1].strip()}
    dest_domains = {domain(row[1]) for row in dest_values[1:] if len(row) > 1 and row[1].strip()}
    boundary_after = source.get(f"A{START_ROW - 1}:P{START_ROW - 1}", value_render_option="FORMATTED_VALUE")
    result = {
        "deleted_from_sheet1": EXPECTED,
        "sheet1_data_rows": len(source_values) - 1,
        "sheet2_data_rows": len(dest_values) - 1,
        "sheet2_unique_domains": len(dest_domains),
        "cross_tab_duplicate_domains": len(source_domains & dest_domains),
        "boundary_preserved": boundary_before == boundary_after,
        "sheet2_backup_hash_match": digest(dest_values[1:]) == digest(backup_block),
        "backup": str(BACKUP),
    }
    expected = {
        "deleted_from_sheet1": 2850,
        "sheet1_data_rows": 1872,
        "sheet2_data_rows": 2850,
        "sheet2_unique_domains": 2850,
        "cross_tab_duplicate_domains": 0,
        "boundary_preserved": True,
        "sheet2_backup_hash_match": True,
    }
    for key, value in expected.items():
        if result[key] != value:
            raise SystemExit("POST_DELETE_MISMATCH\n" + json.dumps(result, ensure_ascii=False, indent=2))

    progress = sh.worksheet("収集進捗管理")
    progress.batch_update(
        [
            {"range": "A13:C17", "values": [
                ["シート1", 1872, "従来候補。今回収集分2,850社をシート2へ移動済み"],
                ["シート2", 2850, "今回収集分。A:P完全一致・正規化ドメイン重複0"],
                ["Webマーケ", 1984, "10,000社計画の純増実績には加算しない"],
                ["SNS運用", 739, "10,000社計画の純増実績には加算しない"],
                ["合計", "=SUM(B13:B16)", "タブ間移動のため総数は変更なし"],
            ]},
            {"range": "D43:E43", "values": [["移動完了", "シート1の1874～4723行を削除し、シート2へ正式分離"]]},
        ],
        value_input_option="USER_ENTERED",
    )
    progress_check = progress.get("A13:E17", value_render_option="FORMATTED_VALUE")
    result["progress_total"] = progress_check[4][1]
    result["progress_sheet2"] = progress_check[1][1]
    if result["progress_total"] != "7,445" or result["progress_sheet2"] != "2,850":
        raise SystemExit("PROGRESS_READBACK_MISMATCH\n" + json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
