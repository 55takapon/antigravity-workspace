#!/usr/bin/env python3
"""Create and verify the Google Sheets collection progress dashboard."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
sys.path.insert(0, str(DIST / "shared"))

from sheets_io import get_client  # noqa: E402


SPREADSHEET_ID = "1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ"
SHEET_NAME = "収集進捗管理"


def rgb(hex_value: str) -> dict[str, float]:
    value = hex_value.lstrip("#")
    return {
        "red": int(value[0:2], 16) / 255,
        "green": int(value[2:4], 16) / 255,
        "blue": int(value[4:6], 16) / 255,
    }


def cell_range(sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int) -> dict:
    return {
        "sheetId": sheet_id,
        "startRowIndex": start_row,
        "endRowIndex": end_row,
        "startColumnIndex": start_col,
        "endColumnIndex": end_col,
    }


def main() -> None:
    client = get_client(str(DIST / "shared" / "gcp_service_account.json"))
    sh = client.open_by_key(SPREADSHEET_ID)

    existing = {ws.title: ws for ws in sh.worksheets()}
    ws = existing.get(SHEET_NAME)
    if ws is None:
        ws = sh.add_worksheet(title=SHEET_NAME, rows=120, cols=14)
    sid = ws.id

    values = [
        ["GBP提携先候補 収集進捗管理", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["更新日", "2026-08-07", "管理基準", "純増1万社（既存候補は含めない）", "", "", "", "", "", "", "", "", "", ""],
        ["全体KPI", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["指標", "現在値", "目標", "進捗率", "判定・注記", "", "", "", "", "", "", "", "", ""],
        ["運用上の純増採用", 2550, 10000, "=B5/C5", "51バッチ分。A:P読戻し済みの運用実績"],
        ["残数", "=C5-B5", 10000, "=B6/C6", "目標までの必要純増"],
        ["現行基準で戦略有効性確認済み", "未監査", 10000, "", "過去バッチの再標本監査後に入力"],
        ["進行中ラウンド", 150, 200, "=B8/C8", "第4セット38社は未反映・凍結中"],
        ["未反映・凍結候補", 38, "", "", "計画再構築が終わるまで候補シートへ追加しない"],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["現役候補タブ（2026-08-07読取）", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["タブ", "データ行数", "備考"],
        ["シート1", 4722, "物理行1のヘッダーを除く"],
        ["Webマーケ", 1984, "物理行1のヘッダーを除く"],
        ["SNS運用", 739, "物理行1のヘッダーを除く"],
        ["合計", "=SUM(B13:B15)", "10,000社計画の進捗には加算しない"],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["収集戦略マトリクス", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["優先度", "収集領域", "純増目標", "純増実績", "進捗率", "戦略有効確認", "原石数", "純増ドメイン率", "採用率", "実フォーム率", "判定", "次のアクション"],
        ["S", "業界特化型Web・マーケ支援", 2500, "要再集計", "", "未監査", "", "", "", "", "再集計", "過去バッチを現行ハブ基準で標本監査"],
        ["S", "地域広告・印刷・看板（デジタル支援あり）", 1800, "要再集計", "", "未監査", "", "", "", "", "再集計", "情報源単位500ドメインのパイロット"],
        ["A", "FC・多店舗・開業集客支援", 1400, "要再集計", "", "未監査", "", "", "", "", "再集計", "最終顧客・設備単体を分離"],
        ["A", "SNS・広告・動画・クリエイティブ", 1200, "要再集計", "", "未監査", "", "", "", "", "再集計", "店舗顧客の明示がある情報源を試験"],
        ["A", "業界専門コンサル・開業・出店支援", 1400, "要再集計", "", "未監査", "", "", "", "", "再集計", "受託・紹介・外注導線の有無を監査"],
        ["A", "小規模DX・SEO・MEO・販促支援", 1000, "要再集計", "", "未監査", "", "", "", "", "再集計", "SaaS・商材供給単体を除外"],
        ["B", "ポータル未掲載の地域Web制作補完", 700, "要再集計", "", "未監査", "", "", "", "", "停止中", "都道府県総当たりを止め、情報源を再設計"],
        ["", "合計", "=SUM(C20:C26)", "", "", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["パイロット昇格基準", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["項目", "継続条件", "意味"],
        ["純増ドメイン率", ">=60%", "開く前の全体重複除外後に十分な未出現母集団がある"],
        ["現行基準の採用率", ">=35%", "GBP提携ハブとして使える候補が確保できる"],
        ["採用候補の実フォーム率", ">=70%", "送信工程へ渡せる窓口がある"],
        ["試験単位", "情報源ごと500ドメイン", "都道府県別の穴埋めで50社を作らない"],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["課題・判断ログ", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["日付", "区分", "内容", "状態", "次の処理"],
        ["2026-08-07", "進捗", "運用上の純増は2,550社（25.5%）", "確定", "過去バッチの戦略有効性を別KPIで監査"],
        ["2026-08-07", "集計差異", "正本のフェーズ値は現行の純増総数と未照合", "要対応", "51バッチを単一台帳へ再集計"],
        ["2026-08-07", "探索停止", "地方別ディレクトリ残存候補は採用率24.8%で停止基準未達", "停止", "地域総当たりをやめ、情報源単位パイロットへ変更"],
        ["2026-08-07", "未反映", "第4セットの38社はシート未追加", "凍結", "再計画・品質確認後に採否決定"],
        ["2026-08-07", "次工程", "新規収集より先に進捗台帳の突合と過去バッチ標本監査を実施", "未着手", "完了後に1情報源500ドメインで再開"],
        ["", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["更新ルール", "", "", "", "", "", "", "", "", "", "", "", "", ""],
        ["タイミング", "更新内容"],
        ["50社反映ごと", "運用上純増、ラウンド進捗、該当領域の実績、フォーム標本結果を更新"],
        ["500ドメイン試験ごと", "原石数、純増ドメイン率、採用率、実フォーム率、継続・修正・停止を更新"],
        ["過去バッチ監査ごと", "戦略有効確認済み件数とセグメント別実績を更新"],
        ["005実行後", "営業禁止・フォーム不可の確定結果を除外リストへ還流し、傾向値を更新"],
    ]
    ws.update(values, "A1:N49", value_input_option="USER_ENTERED")

    requests = [
        {"mergeCells": {"range": cell_range(sid, 0, 1, 0, 14), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": cell_range(sid, 2, 3, 0, 14), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": cell_range(sid, 10, 11, 0, 14), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": cell_range(sid, 17, 18, 0, 14), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": cell_range(sid, 28, 29, 0, 14), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": cell_range(sid, 35, 36, 0, 14), "mergeType": "MERGE_ALL"}},
        {"mergeCells": {"range": cell_range(sid, 43, 44, 0, 14), "mergeType": "MERGE_ALL"}},
        {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": 4, "hideGridlines": True}}, "fields": "gridProperties.frozenRowCount,gridProperties.hideGridlines"}},
        {"repeatCell": {"range": cell_range(sid, 0, 49, 0, 14), "cell": {"userEnteredFormat": {"verticalAlignment": "MIDDLE", "textFormat": {"fontFamily": "Arial", "fontSize": 10}, "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(verticalAlignment,textFormat,wrapStrategy)"}},
    ]

    for row in (0, 2, 10, 17, 28, 35, 43):
        requests.append({"repeatCell": {"range": cell_range(sid, row, row + 1, 0, 14), "cell": {"userEnteredFormat": {"backgroundColor": rgb("1F4E78"), "horizontalAlignment": "LEFT", "textFormat": {"foregroundColor": rgb("FFFFFF"), "bold": True, "fontSize": 12}}}, "fields": "userEnteredFormat(backgroundColor,horizontalAlignment,textFormat)"}})

    for row, end_col in ((3, 5), (11, 3), (18, 12), (29, 3), (36, 5), (44, 2)):
        requests.append({"repeatCell": {"range": cell_range(sid, row, row + 1, 0, end_col), "cell": {"userEnteredFormat": {"backgroundColor": rgb("D9EAF7"), "textFormat": {"bold": True}, "horizontalAlignment": "CENTER", "borders": {"bottom": {"style": "SOLID_MEDIUM", "color": rgb("7F8C8D")}}}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,borders)"}})

    requests.extend([
        {"repeatCell": {"range": cell_range(sid, 4, 9, 1, 4), "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT", "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}}, "fields": "userEnteredFormat(horizontalAlignment,numberFormat)"}},
        {"repeatCell": {"range": cell_range(sid, 4, 9, 3, 4), "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}}, "fields": "userEnteredFormat.numberFormat"}},
        {"repeatCell": {"range": cell_range(sid, 4, 5, 0, 5), "cell": {"userEnteredFormat": {"backgroundColor": rgb("E2F0D9"), "textFormat": {"bold": True}}}, "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"repeatCell": {"range": cell_range(sid, 6, 9, 0, 5), "cell": {"userEnteredFormat": {"backgroundColor": rgb("FFF2CC")}}, "fields": "userEnteredFormat.backgroundColor"}},
        {"repeatCell": {"range": cell_range(sid, 12, 16, 1, 2), "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT", "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}}, "fields": "userEnteredFormat(horizontalAlignment,numberFormat)"}},
        {"repeatCell": {"range": cell_range(sid, 19, 27, 2, 10), "cell": {"userEnteredFormat": {"horizontalAlignment": "RIGHT"}}, "fields": "userEnteredFormat.horizontalAlignment"}},
        {"repeatCell": {"range": cell_range(sid, 19, 27, 4, 10), "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}}, "fields": "userEnteredFormat.numberFormat"}},
        {"repeatCell": {"range": cell_range(sid, 37, 42, 0, 5), "cell": {"userEnteredFormat": {"backgroundColor": rgb("FCE8E6")}}, "fields": "userEnteredFormat.backgroundColor"}},
        {"setDataValidation": {"range": cell_range(sid, 19, 27, 10, 11), "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": "継続"}, {"userEnteredValue": "要修正"}, {"userEnteredValue": "停止"}, {"userEnteredValue": "再集計"}, {"userEnteredValue": "停止中"}]}, "strict": True, "showCustomUi": True}}},
    ])

    widths = [90, 270, 105, 105, 250, 115, 90, 110, 90, 100, 90, 260, 90, 90]
    for idx, width in enumerate(widths):
        requests.append({"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": idx, "endIndex": idx + 1}, "properties": {"pixelSize": width}, "fields": "pixelSize"}})

    requests.append({"addConditionalFormatRule": {"index": 0, "rule": {"ranges": [cell_range(sid, 19, 27, 10, 11)], "booleanRule": {"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "停止"}]}, "format": {"backgroundColor": rgb("F4CCCC"), "textFormat": {"bold": True, "foregroundColor": rgb("9C0006")}}}}}})
    requests.append({"addConditionalFormatRule": {"index": 1, "rule": {"ranges": [cell_range(sid, 19, 27, 10, 11)], "booleanRule": {"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "再集計"}]}, "format": {"backgroundColor": rgb("FFF2CC"), "textFormat": {"bold": True}}}}}})

    requests.append({
        "addChart": {
            "chart": {
                "spec": {
                    "title": "純増1万社への進捗（2,550 / 10,000）",
                    "pieChart": {
                        "legendPosition": "RIGHT_LEGEND",
                        "domain": {"sourceRange": {"sources": [cell_range(sid, 4, 6, 0, 1)]}},
                        "series": {"sourceRange": {"sources": [cell_range(sid, 4, 6, 1, 2)]}},
                        "pieHole": 0.55,
                    },
                },
                "position": {"overlayPosition": {"anchorCell": {"sheetId": sid, "rowIndex": 2, "columnIndex": 6}, "widthPixels": 520, "heightPixels": 260}},
            }
        }
    })

    sh.batch_update({"requests": requests})

    readback = ws.get("A1:L49", value_render_option="FORMATTED_VALUE")
    formulas = ws.get("A1:L49", value_render_option="FORMULA")
    checks = {
        "sheet": ws.title,
        "title": readback[0][0],
        "operational_accepted": readback[4][1],
        "target": readback[4][2],
        "progress": readback[4][3],
        "remaining": readback[5][1],
        "active_total": readback[15][1],
        "matrix_target_total": readback[26][2],
        "formulas_present": formulas[4][3].startswith("=") and formulas[15][1].startswith("="),
        "rows_read": len(readback),
    }
    expected = {
        "sheet": SHEET_NAME,
        "title": "GBP提携先候補 収集進捗管理",
        "operational_accepted": "2,550",
        "target": "10,000",
        "progress": "25.5%",
        "remaining": "7,450",
        "active_total": "7,445",
        "matrix_target_total": "10000",
        "formulas_present": True,
        "rows_read": 49,
    }
    if checks != expected:
        raise SystemExit("READBACK_MISMATCH\n" + json.dumps({"actual": checks, "expected": expected}, ensure_ascii=False, indent=2))
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
