#!/usr/bin/env python3
"""assemble_openers — プロンプト駆動版③の後処理。

Claude本体が生成した冒頭文（data/_opener_results.json: {"idx": "冒頭文", ...}）を、
固定パート（intro→冒頭文→common_body のサンドイッチ）と連結して message を作る。
連結ロジック・テンプレ・プレースホルダ差し込みは opener_helpers.py（配布同梱・非秘匿）を
共有するので、出力はAPI版と同じ形式になり、opener 列同士でA/B比較できる。

出力2モード:
    CSV    : python scripts/assemble_openers.py <in_unified.csv> <out.csv>
    シート : python scripts/assemble_openers.py --sheet <URL>

シートモードは data/_opener_tasks.json（prep が書いた idx→_row 対応）を使い、
Claude生成の冒頭文を同じ物理行の message 列へ書き戻す（overwrite=False＝既存温存。--force で上書き）。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opener_helpers as g  # noqa: E402  (連結・プレースホルダ差し込み等の非秘匿ヘルパ。配布同梱)
import verify_openers as vo  # noqa: E402  (完全性の門番＝共通部品。部分成功を静かに成功にしない)

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"


def _build_message(company: str, opener: str, common_body: str, intro_tmpl: str, sender: dict) -> str:
    """intro→冒頭文→common_body のサンドイッチを連結（API版と同一ロジック）。"""
    intro = g.fill_placeholders(intro_tmpl, company, sender)
    body = g.fill_placeholders(common_body, company, sender)
    return "\n\n".join(p for p in (intro, opener, body) if p)


def _run_csv(args, by_idx, common_body, intro_tmpl, sender) -> int:
    with open(args.input, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = [c.lstrip("﻿") for c in (reader.fieldnames or [])]
        rows = list(reader)
    for col in ("message", "opener"):
        if col not in fieldnames:
            fieldnames.append(col)

    ok = miss = 0
    for idx, row in enumerate(rows):
        company = (row.get("company_name") or "").strip()
        opener = (by_idx.get(str(idx)) or "").strip()
        if not opener:
            row["message"] = (row.get("message") or "").strip()
            row["opener"] = ""
            miss += 1
            print(f"[{idx}] 冒頭文なし（results未記入）: {company}", file=sys.stderr)
            continue
        row["message"] = _build_message(company, opener, common_body, intro_tmpl, sender)
        row["opener"] = opener
        ok += 1

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"[done] 連結 {ok}社 / 未生成 {miss}社 -> {args.output}", file=sys.stderr)
    return 0


def _run_sheet(args, by_idx, common_body, intro_tmpl, sender) -> int:
    sys.path.insert(0, str(g.REPO_ROOT / "shared"))
    import sheets_io  # noqa: E402

    tasks = json.loads(Path(args.tasks).read_text(encoding="utf-8"))
    out_rows: list[dict] = []
    ok = miss = 0
    for t in tasks:
        row_no = t.get("_row")
        if not row_no:
            continue  # シート由来でない（CSV用 tasks）はスキップ
        company = (t.get("company_name") or "").strip()
        opener = (by_idx.get(str(t.get("idx"))) or "").strip()
        if not opener:
            miss += 1
            print(f"[row {row_no}] 冒頭文なし（results未記入）: {company}", file=sys.stderr)
            continue
        message = _build_message(company, opener, common_body, intro_tmpl, sender)
        out_rows.append({"_row": row_no, args.message_col: message})
        ok += 1

    if not out_rows:
        print(f"[done] 書き戻し対象なし（連結 {ok} / 未生成 {miss}）。tasks/results を確認。",
              file=sys.stderr)
        return 0

    ws = sheets_io.open_worksheet(args.sheet, args.worksheet, creds_path=args.creds)
    # 書き戻し先: 既存ヘッダに message 相当（例「営業文」）があればその列へ。無ければ新設。
    aliases = {"message": [args.message_col]}
    out_col = sheets_io.resolve_output_header(ws, "message", args.message_col, aliases=aliases)
    if out_col != args.message_col:
        out_rows = [{"_row": r["_row"], out_col: r[args.message_col]} for r in out_rows]
    written = sheets_io.write_cells(ws, out_rows, [out_col], overwrite=args.force)
    print(f"[done] 連結 {ok}社 / 未生成 {miss}社 / 書込 {written}セル "
          f"-> sheet '{ws.title}' col '{out_col}'", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Claude生成の冒頭文を固定パートと連結して message を作る")
    ap.add_argument("input", nargs="?", help="統一CSV（CSVモード）。--sheet と排他")
    ap.add_argument("output", nargs="?", help="出力CSV（CSVモード）")
    ap.add_argument("--sheet", default=None, help="スプレッドシートのURL/キー（CSV入出力の代わりに書き戻す）")
    ap.add_argument("--worksheet", default=None, help="対象ワークシート名（シート時・既定先頭）")
    ap.add_argument("--creds", default=None, help="サービスアカウントJSON（シート時）")
    ap.add_argument("--message-col", default="message", help="書き戻し先ヘッダ名（シート時・既定 message）")
    ap.add_argument("--force", action="store_true", help="シート時: 既存の message を上書きする")
    ap.add_argument("--tasks", default=str(DATA_DIR / "_opener_tasks.json"),
                    help="prep が書いた worklist（idx→_row 対応。シート時に使用）")
    ap.add_argument("--results", default=str(DATA_DIR / "_opener_results.json"),
                    help="Claudeが書いた冒頭文 {idx: 冒頭文} のJSON")
    ap.add_argument("--allow-partial", action="store_true",
                    help="完全性ゲートを無効化し未生成があっても続行（非推奨・手動デバッグ専用）")
    ap.add_argument("--log", default=str(DATA_DIR / "_opener_verify.log"),
                    help="完全性ゲート未達の永続ログ出力先")
    args = ap.parse_args()

    if bool(args.sheet) == bool(args.input):
        ap.error("出力は CSV（位置引数 input output）か --sheet のどちらか一方を指定してください。")
    if args.input and not args.output:
        ap.error("CSVモードでは output（出力CSV）も指定してください。")

    results = json.loads(Path(args.results).read_text(encoding="utf-8"))
    by_idx = {str(k): v for k, v in results.items()}

    # ── 完全性ゲート（施策2）─────────────────────────────────────────────
    # 生成タスク(_opener_tasks.json)と結果が「N件==N件・idx一致・空文字なし・余分なし」で
    # 揃っていない限り、シートも出力CSVも一切書かずに非ゼロ終了する。
    # ②生成（ホストAIの手動ループ）が一部を書き漏らしても、後段で静かに成功扱いにしない。
    tasks_path = Path(args.tasks)
    if not tasks_path.exists():
        if not args.allow_partial:
            sys.stderr.write(f"[STOP] _opener_tasks.json が見つかりません: {tasks_path}\n"
                             "  prep からやり直してください（強制続行は --allow-partial）。\n")
            return 2
    else:
        chk = vo.check(vo.load_tasks(tasks_path), results)
        if not chk["ok"]:
            sys.stderr.write(vo.format_report(
                chk, header="[STOP] 冒頭文の生成結果が不足しています"
                            "（未生成があるため連結・書き戻し・送信を中止）"))
            vo.append_log(Path(args.log), chk)
            if not args.allow_partial:
                sys.stderr.write("  → 未生成 idx だけ再生成して _opener_results.json に追記し、"
                                 "再実行してください（無視して続行は --allow-partial）。\n")
                return 2

    common_body = g.load_common_body()
    intro_tmpl = g.load_intro()
    sender = g.load_sender_info()

    if args.sheet:
        return _run_sheet(args, by_idx, common_body, intro_tmpl, sender)
    return _run_csv(args, by_idx, common_body, intro_tmpl, sender)


if __name__ == "__main__":
    raise SystemExit(main())
