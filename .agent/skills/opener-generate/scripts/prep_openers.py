#!/usr/bin/env python3
"""prep_openers — プロンプト駆動版③の前処理。各社HPを取得して worklist(JSON) に落とす。

プロンプト駆動版の流れ（CSV入力・シート入力の両対応）:
    1) [このスクリプト] 入力（CSV or シート）の各社HPを取得 → data/_opener_tasks.json
    2) [Claude本体]     MCPツール get_opener_prompt で生成テンプレを取得し、各社の冒頭文を生成
                        → data/_opener_results.json（{"idx": "冒頭文", ...}）
    3) [assemble_openers.py] 冒頭文＋固定パートを連結して出力（CSV or シート書き戻し）

HP取得は opener_helpers.py の実装（requests→Playwrightフォールバック）を再利用するので、
API版と**同じHP本文**で生成でき、A/B比較が公平になる（opener_helpers は配布同梱・非秘匿）。

入力2モード:
    CSV    : python scripts/prep_openers.py <in_unified.csv> [--limit N]
    シート : python scripts/prep_openers.py --sheet <URL> [--limit N] [--force]

シートモードは shared/sheets_io.py で読み、各タスクに物理行番号 `_row` を持たせる
（assemble がこの `_row` を使って同じ行の message 列へ書き戻す＝行ズレ防止）。
既定では message 未記入の行だけを対象にする（再生成コストの二重発生を防ぐ。全行は --force）。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opener_helpers as g  # noqa: E402  (HP取得・shared/ロード等の非秘匿ヘルパ。配布同梱)

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"


def _rows_from_csv(path: str, limit: int) -> list[dict]:
    """CSV入力 → [{idx, company_name, url}] （_row は持たない）。"""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if limit > 0:
        rows = rows[:limit]
    out = []
    for idx, row in enumerate(rows):
        out.append({
            "idx": idx,
            "_row": None,
            "company_name": (row.get("company_name") or "").strip(),
            "url": (row.get("url") or "").strip(),
        })
    return out


def _rows_from_sheet(args) -> list[dict]:
    """シート入力 → [{idx, _row, company_name, url}]。message 未記入の行だけ（--force で全行）。"""
    sys.path.insert(0, str(g.REPO_ROOT / "shared"))
    import sheets_io  # noqa: E402

    aliases: dict[str, list[str]] = {}
    if args.company_col:
        aliases["company_name"] = [args.company_col]
    if args.url_col:
        aliases["url"] = [args.url_col]
    aliases.setdefault("message", []).insert(0, args.message_col)

    ws = sheets_io.open_worksheet(args.sheet, args.worksheet, creds_path=args.creds)
    # require=company_name,url: ヘッダ破損（会話文の誤ペースト等）で列を見失ったまま
    # 黙って空の会社名で生成してしまうのを防ぐ。未解決なら read_rows が明確に中断する。
    rows = sheets_io.read_rows(ws, want=["company_name", "url", "message", "status"], aliases=aliases,
                               require=["company_name", "url"])
    have_input = [r for r in rows if r.get("company_name") or r.get("url")]
    if not have_input:
        raise SystemExit("[エラー] company_name / url の列を検出できませんでした。"
                         "--company-col / --url-col で指定してください。")
    # #40 P2: status=excluded の行（除外リスト該当）は冒頭文AI生成の無駄コストを避けるためスキップ（--force でも触らない）
    excluded = [r for r in have_input if str(r.get("status") or "").strip().lower() == "excluded"]
    have_input = [r for r in have_input if r not in excluded]
    targets = have_input if args.force else [r for r in have_input if not r.get("message")]
    skipped = len(have_input) - len(targets)
    if args.limit > 0:
        targets = targets[:args.limit]
    if skipped or excluded:
        print(f"[info] message記入済み {skipped}件・除外(excluded) {len(excluded)}件はスキップ"
              "（全行やり直すなら --force）", file=sys.stderr)
    out = []
    for idx, r in enumerate(targets):
        out.append({
            "idx": idx,
            "_row": r.get("_row"),
            "company_name": (r.get("company_name") or "").strip(),
            "url": (r.get("url") or "").strip(),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="各社HPを取得して冒頭文生成のworklistを作る")
    ap.add_argument("input", nargs="?", help="統一CSV（company_name, url, ...）。--sheet と排他")
    ap.add_argument("--sheet", default=None, help="スプレッドシートのURL/キー（CSV入力の代わり）")
    ap.add_argument("--worksheet", default=None, help="対象ワークシート名（シート時・既定先頭）")
    ap.add_argument("--creds", default=None, help="サービスアカウントJSON（シート時）")
    ap.add_argument("--force", action="store_true", help="シート時: message記入済みの行も対象にする")
    ap.add_argument("--company-col", default=None, help="会社名ヘッダ名（シート時・既定 company_name）")
    ap.add_argument("--url-col", default=None, help="URLヘッダ名（シート時・既定 url）")
    ap.add_argument("--message-col", default="message", help="出力先ヘッダ名（シート時・スキップ判定に使用）")
    ap.add_argument("--limit", type=int, default=0, help="先頭N社のみ（0=全件）")
    ap.add_argument("--out", default=str(DATA_DIR / "_opener_tasks.json"))
    args = ap.parse_args()

    if bool(args.input) == bool(args.sheet):
        ap.error("入力は CSV（位置引数）か --sheet のどちらか一方を指定してください。")

    base = _rows_from_sheet(args) if args.sheet else _rows_from_csv(args.input, args.limit)

    tasks = []
    for t in base:
        url = t["url"]
        hp_text = g.fetch_hp_text(url) if url else ""
        tasks.append({**t, "hp_text": hp_text})
        print(f"[{t['idx']+1}/{len(base)}] {'取得' if hp_text else '本文なし'}  {t['company_name']}",
              file=sys.stderr)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    got = sum(1 for t in tasks if t["hp_text"])
    src = f"シート '{args.sheet}'" if args.sheet else f"CSV '{args.input}'"
    print(f"[done] {src} / {len(tasks)}社 / HP本文取得 {got}社 -> {out}", file=sys.stderr)
    print(f"次: MCPツール get_opener_prompt（サーバー opener-core）で生成テンプレを取得し、"
          f"各社ぶん {{company}}/{{hp_text}} を埋めて冒頭文を生成 → "
          f"data/_opener_results.json に書く（キーは idx）", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
