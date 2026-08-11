#!/usr/bin/env python3
"""Publish the full 2,850-company audit without deleting candidates."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
RUN = ROOT / ".codex" / "simesapo" / "runs" / "20260812_sheet2_full_audit"
INPUT = RUN / "partner_fit_audit_2850.csv"
sys.path.insert(0, str(DIST / "shared"))
from sheets_io import get_client  # noqa: E402

SPREADSHEET_ID = "1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ"
TAB = "シート2全件監査"
LABELS = {
    "exclude_confirmed": "除外確定：既知除外",
    "exclude_obvious_major": "除外確定：明確な大手",
    "exclude_high_scale": "要確認：規模シグナル強",
    "review_large_scale": "要確認：規模シグナル",
    "review_enterprise_match": "要確認：上場・大手一致",
    "keep_partner_fit": "維持：提携適合根拠あり",
    "likely_not_partner": "非適合濃厚",
    "review_membership_only": "要確認：団体掲載のみ",
    "review_weak_hub": "要確認：ハブ性弱い",
    "review_insufficient_evidence": "要確認：根拠不足",
}


def rgb(value: str) -> dict[str, float]:
    value = value.lstrip("#")
    return {"red": int(value[:2], 16) / 255, "green": int(value[2:4], 16) / 255, "blue": int(value[4:6], 16) / 255}


def grid(sid: int, r1: int, r2: int, c1: int, c2: int) -> dict:
    return {"sheetId": sid, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}


def main() -> None:
    with INPUT.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != 2850:
        raise SystemExit(f"STOP: expected 2850, got {len(rows)}")

    counts = {}
    for row in rows:
        label = LABELS[row["classification"]]
        counts[label] = counts.get(label, 0) + 1
    confirmed = counts.get("除外確定：既知除外", 0) + counts.get("除外確定：明確な大手", 0)
    scale_review = counts.get("要確認：規模シグナル強", 0) + counts.get("要確認：規模シグナル", 0) + counts.get("要確認：上場・大手一致", 0)

    client = get_client(str(DIST / "shared" / "gcp_service_account.json"))
    sh = client.open_by_key(SPREADSHEET_ID)
    titles = {ws.title for ws in sh.worksheets()}
    if TAB in titles:
        raise SystemExit(f"STOP: {TAB} already exists")
    ws = sh.add_worksheet(title=TAB, rows=2880, cols=20)

    summary = [
        ["シート2 全2,850社監査（規模・GBP提携適合性）"],
        ["監査日", "2026-08-12", "対象", "シート2全2,850社", "処理", "公式サイト・会社概要・事業ページ＋既存マスター"],
        ["区分", "件数", "割合", "判断"],
        ["除外確定", confirmed, f"=B4/2850", "帝国データバンク1社＋既存除外一致1社。まだ削除していない"],
        ["規模要確認", scale_review, f"=B5/2850", "ページ内数値の誤検出を含み得るため手動確定が必要"],
        ["維持：提携適合根拠あり", counts.get("維持：提携適合根拠あり", 0), f"=B6/2850", "公式サイトで受託支援と地域顧客接点を確認"],
        ["非適合濃厚", counts.get("非適合濃厚", 0), f"=B7/2850", "SaaS・設備・商材・管理等が中心。削除前に確定監査"],
        ["要確認：団体掲載のみ", counts.get("要確認：団体掲載のみ", 0), f"=B8/2850", "名簿掲載は提携根拠ではない"],
        ["要確認：ハブ性弱い", counts.get("要確認：ハブ性弱い", 0), f"=B9/2850", "受託支援はあるが複数案件への波及が不明"],
        ["要確認：根拠不足", counts.get("要確認：根拠不足", 0), f"=B10/2850", "取得不能・表現不足を含む。自動除外禁止"],
        ["重要", "確定除外は2社のみ。規模シグナル・団体掲載・根拠不足は削除しない"],
        [],
        ["シート2行", "会社名", "公式URL", "問い合わせURL", "既存区分", "既存根拠", "監査分類", "理由", "受託語", "顧客接点語", "非ハブ語", "団体掲載のみ", "従業員検出", "拠点検出", "資本金万円検出", "上場語", "全国規模語", "既存大手照合", "公式HTTP", "追加確認URL"],
    ]
    detail = []
    for row in rows:
        detail.append([
            int(row["sheet_row"]), row["company_name"], row["url"], row["contact_url"], row["proposal_class"], row["existing_evidence"],
            LABELS[row["classification"]], row["reason"], row["positive_hits"], row["hub_hits"], row["weak_hits"],
            "はい" if row["membership_only"] == "yes" else "いいえ", row["employees_detected"], row["offices_detected"],
            row["capital_man_detected"], "あり" if row["listed_signal"] == "yes" else "なし",
            "あり" if row["national_scale_signal"] == "yes" else "なし", row["existing_enterprise_class"],
            int(row["official_status"] or 0), row["evidence_urls"],
        ])
    ws.update(summary + detail, f"A1:T{len(summary) + len(detail)}", value_input_option="USER_ENTERED")

    sid = ws.id
    requests = [
        {"mergeCells": {"range": grid(sid, 0, 1, 0, 20), "mergeType": "MERGE_ALL"}},
        {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"frozenRowCount": 13, "hideGridlines": True}}, "fields": "gridProperties.frozenRowCount,gridProperties.hideGridlines"}},
        {"repeatCell": {"range": grid(sid, 0, 2863, 0, 20), "cell": {"userEnteredFormat": {"verticalAlignment": "MIDDLE", "textFormat": {"fontFamily": "Arial", "fontSize": 9}, "wrapStrategy": "WRAP"}}, "fields": "userEnteredFormat(verticalAlignment,textFormat,wrapStrategy)"}},
        {"repeatCell": {"range": grid(sid, 0, 1, 0, 20), "cell": {"userEnteredFormat": {"backgroundColor": rgb("1F4E78"), "textFormat": {"foregroundColor": rgb("FFFFFF"), "bold": True, "fontSize": 13}}}, "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
        {"repeatCell": {"range": grid(sid, 2, 3, 0, 4), "cell": {"userEnteredFormat": {"backgroundColor": rgb("D9EAF7"), "textFormat": {"bold": True}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": grid(sid, 12, 13, 0, 20), "cell": {"userEnteredFormat": {"backgroundColor": rgb("1F4E78"), "textFormat": {"foregroundColor": rgb("FFFFFF"), "bold": True}, "horizontalAlignment": "CENTER"}}, "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"}},
        {"repeatCell": {"range": grid(sid, 3, 10, 2, 3), "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}}, "fields": "userEnteredFormat.numberFormat"}},
        {"setBasicFilter": {"filter": {"range": grid(sid, 12, 2863, 0, 20)}}},
    ]
    widths = [70, 180, 220, 230, 190, 280, 170, 250, 160, 160, 150, 95, 90, 80, 100, 70, 80, 140, 80, 260]
    for i, width in enumerate(widths):
        requests.append({"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1}, "properties": {"pixelSize": width}, "fields": "pixelSize"}})
    colors = {
        "除外確定：既知除外": "F4CCCC", "除外確定：明確な大手": "F4CCCC", "要確認：規模シグナル強": "FCE5CD",
        "要確認：規模シグナル": "FFF2CC", "要確認：上場・大手一致": "FFF2CC", "維持：提携適合根拠あり": "D9EAD3",
        "非適合濃厚": "FCE5CD", "要確認：団体掲載のみ": "FFF2CC", "要確認：ハブ性弱い": "FFF2CC", "要確認：根拠不足": "EDEDED",
    }
    for index, (label, color) in enumerate(colors.items()):
        requests.append({"addConditionalFormatRule": {"index": index, "rule": {"ranges": [grid(sid, 13, 2863, 6, 7)], "booleanRule": {"condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": label}]}, "format": {"backgroundColor": rgb(color), "textFormat": {"bold": True}}}}}})
    sh.batch_update({"requests": requests})

    readback = ws.get("A1:T2863", value_render_option="FORMATTED_VALUE")
    result = {
        "detail_rows": len(readback) - 13,
        "confirmed_exclude": readback[3][1],
        "scale_review": readback[4][1],
        "keep": readback[5][1],
        "likely_not_partner": readback[6][1],
        "membership_only": readback[7][1],
        "weak_hub": readback[8][1],
        "insufficient": readback[9][1],
        "tdb_rows": sum(1 for row in readback[13:] if len(row) > 1 and "帝国データバンク" in row[1]),
    }
    expected = {
        "detail_rows": 2850, "confirmed_exclude": "2", "scale_review": "184", "keep": "461",
        "likely_not_partner": "168", "membership_only": "1205", "weak_hub": "156", "insufficient": "674", "tdb_rows": 1,
    }
    if result != expected:
        raise SystemExit("READBACK_MISMATCH\n" + json.dumps({"actual": result, "expected": expected}, ensure_ascii=False, indent=2))

    progress = sh.worksheet("収集進捗管理")
    progress.batch_update([
        {"range": "A58:E66", "values": [
            ["シート2全件監査（2026-08-12）", "", "", "", ""],
            ["区分", "件数", "割合", "判断", "次の処理"],
            ["除外確定", 2, "=B60/2850", "帝国データバンク＋既知除外一致", "除外反映は別承認"],
            ["規模要確認", 184, "=B61/2850", "自動除外禁止", "公式会社概要で確定"],
            ["維持根拠あり", 461, "=B62/2850", "現行基準適合", "維持"],
            ["非適合濃厚", 168, "=B63/2850", "現行方針と不整合", "確定監査"],
            ["団体掲載のみ", 1205, "=B64/2850", "名簿掲載は提携根拠ではない", "情報源・バッチ単位で再判定"],
            ["ハブ性弱い", 156, "=B65/2850", "複数案件波及が不明", "追加確認"],
            ["根拠不足", 674, "=B66/2850", "取得不能・表現不足を含む", "自動除外禁止"],
        ]},
    ], value_input_option="USER_ENTERED")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
