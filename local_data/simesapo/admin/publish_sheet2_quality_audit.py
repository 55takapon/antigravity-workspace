#!/usr/bin/env python3
"""Publish the 285-company Sheet2 quality sample to Google Sheets."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
INPUT = ROOT / "local_data" / "simesapo" / "admin" / "sheet2_quality_sample_285.csv"
sys.path.insert(0, str(DIST / "shared"))
from sheets_io import get_client  # noqa: E402

SPREADSHEET_ID = "1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ"
TAB = "シート2品質監査"
LABELS = {
    "strategic_valid": "確定有効",
    "likely_not_hub": "非ハブ濃厚",
    "review_weak_service": "要確認：受託根拠",
    "review_weak_hub": "要確認：ハブ性",
    "review_form": "要確認：フォーム",
    "review_unreachable": "要確認：サイト不達",
    "exclude_enterprise": "除外：上場・大手",
    "review_enterprise": "要確認：大手語一致",
}


def rgb(value: str) -> dict[str, float]:
    value = value.lstrip("#")
    return {"red": int(value[:2], 16) / 255, "green": int(value[2:4], 16) / 255, "blue": int(value[4:6], 16) / 255}


def grid(sid: int, r1: int, r2: int, c1: int, c2: int) -> dict:
    return {"sheetId": sid, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}


def main() -> None:
    with INPUT.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != 285:
        raise SystemExit(f"STOP: expected 285 rows, got {len(rows)}")

    client = get_client(str(DIST / "shared" / "gcp_service_account.json"))
    sh = client.open_by_key(SPREADSHEET_ID)
    titles = {ws.title for ws in sh.worksheets()}
    ws = sh.worksheet(TAB) if TAB in titles else sh.add_worksheet(title=TAB, rows=310, cols=16)

    summary = [
        ["シート2 品質監査（57バッチ×5社＝285社）"],
        ["監査日", "2026-08-07", "抽出方式", "各50社の1・11・21・31・41番目"],
        ["区分", "件数", "割合", "解釈"],
        ["確定有効", 51, "=B4/285", "受託サービス・地域顧客接点・実フォームを確認"],
        ["非ハブ濃厚", 69, "=B5/285", "SaaS・機器・商材・賃貸管理等の単体支援が中心"],
        ["要確認", 165, "=B6/285", "受託根拠・ハブ性・フォーム構造の追加確認が必要"],
        ["実フォーム確認", 246, "=B7/285", "問い合わせページ上のform要素と入力項目を確認"],
        ["公式サイト到達", 285, "=B8/285", "HTTP取得成功"],
        ["注意", "確定有効17.9%は下限値。要確認165社を不採用扱いしない"],
        [],
        ["バッチ", "標本位置", "シート2行", "会社名", "公式URL", "問い合わせURL", "既存区分", "既存根拠", "監査分類", "理由", "フォーム", "受託語", "顧客接点語", "非ハブ語", "公式HTTP", "問い合わせHTTP"],
    ]
    details = []
    for row in rows:
        details.append([
            int(row["batch_no"]), int(row["sample_position"]), int(row["sheet_row"]), row["company_name"],
            row["url"], row["contact_url"], row["proposal_class"], row["existing_evidence"],
            LABELS.get(row["classification"], row["classification"]), row["reason"],
            "あり" if row["form_exists"] == "yes" else "未確認", row["service_hits"], row["client_hits"],
            row["weak_only_hits"], int(row["official_status"] or 0), int(row["contact_status"] or 0),
        ])
    ws.update(summary + details, f"A1:P{len(summary) + len(details)}", value_input_option="USER_ENTERED")

    sid = ws.id
    requests = [
        {"mergeCells": {"range": grid(sid, 0, 1, 0, 16), "mergeType": "MERGE_ALL"}},
        {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": 11, "hideGridlines": True}}, "fields": "gridProperties.frozenRowCount,gridProperties.hideGridlines"}},
        {"repeatCell": {"range": grid(sid, 0, 296, 0, 16), "cell": {"userEnteredFormat": {"verticalAlignment": "MIDDLE", "textFormat": {"fontFamily": "Arial", "fontSize": 9}, "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(verticalAlignment,textFormat,wrapStrategy)"}},
        {"repeatCell": {"range": grid(sid, 0, 1, 0, 16), "cell": {"userEnteredFormat": {"backgroundColor": rgb("1F4E78"), "textFormat": {"foregroundColor": rgb("FFFFFF"), "bold": True, "fontSize": 13}}}, "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"repeatCell": {"range": grid(sid, 2, 3, 0, 4), "cell": {"userEnteredFormat": {"backgroundColor": rgb("D9EAF7"), "textFormat": {"bold": True}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": grid(sid, 10, 11, 0, 16), "cell": {"userEnteredFormat": {"backgroundColor": rgb("1F4E78"), "textFormat": {"foregroundColor": rgb("FFFFFF"), "bold": True}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": grid(sid, 3, 8, 2, 3), "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}}, "fields": "userEnteredFormat.numberFormat"}},
        {"setBasicFilter": {"filter": {"range": grid(sid, 10, 296, 0, 16)}}},
    ]
    widths = [60, 70, 75, 180, 230, 250, 180, 280, 130, 240, 75, 180, 180, 180, 80, 90]
    for i, width in enumerate(widths):
        requests.append({"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1}, "properties": {"pixelSize": width}, "fields": "pixelSize"}})
    colors = {"確定有効": "D9EAD3", "非ハブ濃厚": "F4CCCC", "要確認：受託根拠": "FFF2CC", "要確認：ハブ性": "FFF2CC", "要確認：フォーム": "FCE5CD"}
    for index, (label, color) in enumerate(colors.items()):
        requests.append({"addConditionalFormatRule": {"index": index, "rule": {"ranges": [grid(sid, 11, 296, 8, 9)], "booleanRule": {"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": label}]}, "format": {"backgroundColor": rgb(color), "textFormat": {"bold": True}}}}}})
    sh.batch_update({"requests": requests})

    check = ws.get("A1:P296", value_render_option="FORMATTED_VALUE")
    result = {
        "detail_rows": len(check) - 11,
        "valid": check[3][1],
        "valid_rate": check[3][2],
        "not_hub": check[4][1],
        "review": check[5][1],
        "forms": check[6][1],
        "last_company": check[-1][3],
    }
    expected = {"detail_rows": 285, "valid": "51", "valid_rate": "17.9%", "not_hub": "69", "review": "165", "forms": "246", "last_company": rows[-1]["company_name"]}
    if result != expected:
        raise SystemExit("READBACK_MISMATCH\n" + json.dumps({"actual": result, "expected": expected}, ensure_ascii=False, indent=2))

    progress = sh.worksheet("収集進捗管理")
    progress.batch_update([
        {"range": "A7:E7", "values": [["標本で確定有効", 51, 285, "=B7/C7", "57バッチ×5社。要確認165社は未判定のため除外しない"]]},
        {"range": "A50:E56", "values": [
            ["シート2品質監査", "", "", "", ""],
            ["区分", "件数", "割合", "判断", "次の処理"],
            ["確定有効", 51, "=B52/285", "下限値", "維持"],
            ["非ハブ濃厚", 69, "=B53/285", "現行方針と不整合", "バッチ・セグメント単位で再判定"],
            ["要確認", 165, "=B54/285", "即除外禁止", "追加確認で確定・非適合へ分離"],
            ["実フォーム確認", 246, "=B55/285", "良好", "005で最新状態を再確認"],
            ["公式サイト到達", 285, "=B56/285", "良好", "なし"],
        ]},
    ], value_input_option="USER_ENTERED")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
