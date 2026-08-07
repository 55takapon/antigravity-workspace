#!/usr/bin/env python3
"""Synchronize the progress dashboard after creating Sheet2."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
sys.path.insert(0, str(DIST / "shared"))
from sheets_io import get_client  # noqa: E402


def main() -> None:
    client = get_client(str(DIST / "shared" / "gcp_service_account.json"))
    sh = client.open_by_key("1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ")
    ws = sh.worksheet("収集進捗管理")
    ws.batch_update(
        [
            {"range": "B5", "values": [[2850]]},
            {"range": "E5", "values": [["57バッチ分。今回収集分をシート2へ完全一致コピー済み"]]},
            {"range": "B9", "values": [[38]]},
            {"range": "A17:C17", "values": [["参考：シート2", 2850, "今回収集分の完全一致コピー。シート1の元行は削除承認待ちのため合計に重複加算しない"]]},
            {"range": "A43:E43", "values": [["2026-08-07", "管理分離", "今回収集分2,850社をシート2へコピー", "コピー完了", "シート1の1874～4723行は削除承認待ち"]]},
        ],
        value_input_option="USER_ENTERED",
    )

    metadata = sh.fetch_sheet_metadata(params={"fields": "sheets(properties,charts)"})
    sheet_meta = next(x for x in metadata["sheets"] if x["properties"]["title"] == "収集進捗管理")
    charts = sheet_meta.get("charts", [])
    if charts:
        chart = charts[0]
        spec = chart["spec"]
        spec["title"] = "純増1万社への進捗（2,850 / 10,000）"
        sh.batch_update({"requests": [{"updateChartSpec": {"chartId": chart["chartId"], "spec": spec}}]})

    values = ws.get("A1:E43", value_render_option="FORMATTED_VALUE")
    result = {
        "accepted": values[4][1],
        "progress": values[4][3],
        "remaining": values[5][1],
        "active_total_without_sheet2_duplicate": values[15][1],
        "sheet2_reference": values[16][1],
        "management_note": values[42][2],
    }
    expected = {
        "accepted": "2,850",
        "progress": "28.5%",
        "remaining": "7,150",
        "active_total_without_sheet2_duplicate": "7,445",
        "sheet2_reference": "2850",
        "management_note": "今回収集分2,850社をシート2へコピー",
    }
    if result != expected:
        raise SystemExit("READBACK_MISMATCH\n" + json.dumps({"actual": result, "expected": expected}, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
