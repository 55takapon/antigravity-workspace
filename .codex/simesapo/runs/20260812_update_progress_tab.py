from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\hangy\.gemini\antigravity")
DIST = ROOT / ".agent" / "skills" / "simesapo-sales-skills-dist"
RUN = ROOT / ".codex" / "simesapo" / "runs" / "20260812_sheet2_sort_exclusions"
sys.path.insert(0, str(DIST / ".codex_pydeps"))
sys.path.insert(0, str(DIST / "shared"))
from sheets_io import get_client

book = get_client(str(DIST / "shared" / "gcp_service_account.json")).open_by_key("1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ")
ws = book.worksheet("収集進捗管理")
before = ws.get("A1:N120", value_render_option="FORMULA")
with (RUN / "progress_tab_before_update.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    csv.writer(fh).writerows(before)

updates = {
    "A2:D2": [["更新日", "2026-08-12", "管理基準", "現行基準の送付対象を純増1万社（過去収集量は進捗にしない）"]],
    "A4:E9": [
        ["指標", "現在値", "目標", "進捗率", "判定・注記"],
        ["現行基準の純増送付対象", "842", "10,000", "8.42%", "シート2 B/C救済分。既存・除外との会社名/ドメイン/電話一致0"],
        ["残り純増必要数", "9,158", "10,000", "91.58%", "旧2,850社は収集量であり進捗へ戻さない"],
        ["既存戦略適合基準", "8,241", "参考", "", "運用6タブを除外照合したユニークドメイン"],
        ["現在の有効基準母数", "9,083", "18,241", "49.8%", "既存8,241＋純増842"],
        ["シート2未救済在庫", "1,706", "", "", "新規収集へ混ぜず、今回の進捗にも算入しない"],
    ],
    "A11:C17": [
        ["ライブ在庫（2026-08-12読取）", "", ""],
        ["対象", "件数", "備考"],
        ["運用6タブ", "9,622行 / 9,492ドメイン", "シート1、Webマーケ、SNS運用、過去送信3タブ"],
        ["既存戦略適合基準", "8,241ドメイン", "除外照合・対象外区分・送信不可等を反映"],
        ["シート2送付対象", "842ドメイン", "既存・除外との一致0"],
        ["現在の有効基準母数", "9,083ドメイン", "追加1万社の確定進捗は842"],
        ["除外リスト", "3,119行 / 3,107ドメイン", "既知除外マスター"],
    ],
    "A18:L27": [
        ["収集戦略マトリクス（過去57バッチとの差分）", "", "", "", "", "", "", "", "", "", "", ""],
        ["波", "収集領域", "純増目標", "確定純増", "進捗率", "実施状況", "監査母数", "純増率", "送付対象率", "実フォーム", "判定", "次のアクション"],
        ["A", "広告プラットフォーム・広告会社公式名簿", "1,000", "0", "0.0%", "未着手", "", "", "", "", "試験", "大手除外を先行し公式取得元ごとに残存率測定"],
        ["B", "地域メディア・地域広告・クロスメディア", "2,500", "448", "17.9%", "印刷組合系は相当程度実施", "547", "", "81.9%", "送付対象は確認済み", "差分のみ", "JLAA等の未使用名簿。既探索印刷組合は停止"],
        ["C", "業界特化型集客支援", "3,500", "394", "11.3%", "主要12業種を一部実施", "597", "", "66.0%", "送付対象は確認済み", "差分のみ", "同じ一般検索をせず未使用公式ディレクトリ限定"],
        ["D", "店舗DX・SaaS・設備・商材", "0", "0", "-", "複数バッチ実施", "", "", "", "", "停止", "集客受託を別サービスで持つ会社だけ他波で扱う"],
        ["E", "広告制作・PR・コンテンツ", "3,000", "0", "0.0%", "専用公式名簿は未実施", "", "", "", "", "最優先", "OAC、PRSJの法人・PR会社を差分取得"],
        ["", "合計", "10,000", "842", "8.42%", "", "1,144", "", "73.6%", "", "進行中", "残り9,158"],
        ["", "対象外：不動産・内装・設備・厨房・清掃", "0", "0", "-", "過去に過剰取得", "", "", "", "", "恒久停止", "再探索しない"],
        ["", "一般Web制作ポータル・地方名検索", "0", "0", "-", "既に大半を刈取済み", "", "", "", "", "補完のみ", "主探索に戻さない"],
    ],
    "A29:C35": [
        ["公式取得元の継続・停止基準", "", ""],
        ["項目", "継続条件", "意味"],
        ["差分残存数", ">=20社", "全件機械照合後20社未満なら公式サイト監査へ進まない"],
        ["純増率", ">=30%", "既存9,083・除外照合後に十分な新規母集団がある"],
        ["送付対象率", ">=60%", "明確な除外以外を送付対象に残した実効率"],
        ["停止基準", "純増率<15% または送付対象率<40%", "同じ取得元を再試行しない"],
        ["処理単位", "母集団の残存実数", "50社を満たすため別検索を混ぜない"],
    ],
    "A82:F89": [
        ["次の差分取得元（2026-08-12確定）", "", "", "", "", ""],
        ["順位", "バッチID", "公式取得元", "公開母集団", "過去履歴との差分", "実行条件"],
        ["1", "NEXT-B-JLAA-001", "日本地域広告会社協会（JLAA）", "正会員53＋賛助10", "過去57バッチにJLAA利用記録なし", "63社全件を既存・大手・除外照合"],
        ["2", "NEXT-E-OAC-001", "日本広告制作協会（OAC）", "約120社・人", "広告制作会社専用名簿は未使用", "法人会員のみ。学校・個人・大手を先に除外"],
        ["3", "NEXT-E-PRSJ-001", "日本PR協会 PR会社検索", "公開検索結果", "PR会社専用検索は未使用", "PR受託会社だけ。事業会社・個人を除外"],
        ["4", "NEXT-A-JAAA-001", "日本広告業協会（JAAA）", "137社", "広告会社公式名簿として未使用", "大手率が高いため残存20社以上の場合だけ監査"],
        ["シート2", "行移動完了", "除外302社", "2550～2851行", "送付対象842社・全2,850行を維持", "行集合一致・重複ドメイン0"],
        ["進捗", "再計算完了", "純増842社", "8.42%", "有効基準9,083社", "残り9,158社"],
    ],
}
book.values_batch_update({
    "valueInputOption": "RAW",
    "data": [{"range": f"'収集進捗管理'!{rng}", "values": vals} for rng, vals in updates.items()],
})

# Format the new lower summary section without altering existing sheet-wide styling.
book.batch_update({"requests": [
    {"repeatCell": {"range": {"sheetId": ws.id, "startRowIndex": 81, "endRowIndex": 82, "startColumnIndex": 0, "endColumnIndex": 6},
                    "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.12, "green": 0.33, "blue": 0.55}, "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}}},
                    "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
    {"repeatCell": {"range": {"sheetId": ws.id, "startRowIndex": 82, "endRowIndex": 83, "startColumnIndex": 0, "endColumnIndex": 6},
                    "cell": {"userEnteredFormat": {"backgroundColor": {"red": 0.85, "green": 0.91, "blue": 0.96}, "textFormat": {"bold": True}}},
                    "fields": "userEnteredFormat(backgroundColor,textFormat)"}},
]})

checks = {}
read_ranges = list(updates)
read_values = ws.batch_get(read_ranges, value_render_option="FORMATTED_VALUE")
for (rng, expected), got in zip(updates.items(), read_values):
    # Pad API-trimmed rows for exact comparison.
    width = max(len(r) for r in expected)
    norm_got = [(r + [""] * width)[:width] for r in got]
    norm_exp = [(r + [""] * width)[:width] for r in expected]
    checks[rng] = norm_got == norm_exp
report = {"ranges_written": len(updates), "all_ranges_verified": all(checks.values()), "checks": checks}
(RUN / "progress_tab_update_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
if not report["all_ranges_verified"]:
    raise SystemExit("STOP: progress tab verification failed\n" + json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
