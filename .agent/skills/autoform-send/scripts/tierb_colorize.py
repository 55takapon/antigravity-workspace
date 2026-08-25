#!/usr/bin/env python3
"""status 列（I列）に5バケツの色分け（条件付き書式）を設定する一度きりのセットアップ。

  送信済み → 緑 ／ 要目視 → 赤 ／ 要手動送信（試行後）→ オレンジ ／ 要見直し → 黄 ／ 送信不可・除外 → 灰

開いた瞬間に「緑=完了・黄=まだ取れる・灰=諦め」が一目で分かるようにする（#49 status区別）。
既存の条件付き書式を一旦消してから貼り直すので、何度実行しても重複しない。
usage: python tierb_colorize.py <sheet_key>
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parents[3]
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(REPO_ROOT / "shared"))
import sheets_io  # noqa: E402

# ★要手動送信（リスト段階・未試行）は「色なし」＝件数が多いので埋め尽くさない。
#   要手動送信（試行後）＝自動送信を試したが送れず要手動、はオレンジで目立たせる。
# ★赤（要目視）とオレンジ（要手動送信（試行後））は**意味が逆**なので、明度も変えて離す（#56）。
#   オレンジ＝手で送ってよい ／ 赤＝送る前に確認する（届いているかもしれない）。
#   理由列を1行ずつ読ませる設計は、件数が増えると必ず破れる＝色で手を止める。
COLORS = [
    ("送信済み", {"red": 0.72, "green": 0.88, "blue": 0.80}),          # 緑
    ("要目視", {"red": 0.90, "green": 0.42, "blue": 0.42}),            # 赤
    ("要手動送信（試行後）", {"red": 0.98, "green": 0.68, "blue": 0.36}),  # オレンジ
    ("要見直し", {"red": 1.0, "green": 0.90, "blue": 0.60}),           # 黄
    ("送信不可", {"red": 0.85, "green": 0.85, "blue": 0.85}),          # 灰
    ("除外", {"red": 0.92, "green": 0.92, "blue": 0.92}),              # 薄灰
]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: tierb_colorize.py <sheet_key>", file=sys.stderr)
        return 1
    ws = sheets_io.open_worksheet(sys.argv[1], None)
    sid = ws.id
    ss = ws.spreadsheet

    # 既存の条件付き書式を削除（重複防止）。多い順に index を落とす。
    meta = ss.fetch_sheet_metadata()
    n_existing = 0
    for sh in meta.get("sheets", []):
        if sh.get("properties", {}).get("sheetId") == sid:
            n_existing = len(sh.get("conditionalFormats", []) or [])
            break
    del_reqs = [{"deleteConditionalFormatRule": {"sheetId": sid, "index": 0}} for _ in range(n_existing)]

    rng = {"sheetId": sid, "startColumnIndex": 8, "endColumnIndex": 9, "startRowIndex": 1}
    add_reqs = []
    for i, (label, color) in enumerate(COLORS):
        add_reqs.append({"addConditionalFormatRule": {"index": i, "rule": {
            "ranges": [rng],
            "booleanRule": {
                "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": label}]},
                "format": {"backgroundColor": color},
            },
        }}})
    ss.batch_update({"requests": del_reqs + add_reqs})
    print(f"[colorize] 既存{n_existing}件を削除し、色分けを設定"
          f"（緑=送信済み / 赤=要目視(送る前に確認) / オレンジ=要手動送信（試行後）/ "
          f"黄=要見直し / 灰=送信不可・除外 / 要手動送信=色なし）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
