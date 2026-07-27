#!/usr/bin/env python3
"""form-send (Google Sheets 直結版) — シートを読んで送信し、結果5列を書き戻す薄いラッパ。

run_send.py 本体は無改変。本スクリプトは shared/sheets_io.py 経由でシートを読み、
送信対象を一時CSVに書き出して run_send.py に渡し、結果CSVの
sent_at/status/error_reason/screenshot_path/provider_used を同じ行に書き戻す。

使い方:
    python scripts/run_on_sheet.py <spreadsheet_url_or_key> [options]

options:
    --worksheet NAME   対象ワークシート名（既定: 先頭シート）
    --limit N          先頭N社のみ送信（0=全件、既定0）
    --force            既に status が入っている行も再送信する（既定はスキップ＝二重送信防止）
    --sender PATH      送信者情報JSON（既定: shared/sender_info.json）
    --env PATH         APIキー .env（既定: form-send/config/.env があればそれ）
    --creds PATH       サービスアカウントJSON（既定の探索順は sheets_io に準拠）
    (--model/--mode は run_send.py の既定に従う)

再実行ポリシー（設計 §9-c）: form-send は overwrite=False。既定では status 未記入の行だけ
送信し、送信済みの行は決して触らない（再送したい行は status セルを空にする / --force）。
★大量送信前の人間確認は run_send.py 側の運用ルールに従う。
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS_DIR.parent
REPO_ROOT = SCRIPTS_DIR.parents[3]   # .../<repo>/.claude/skills/005-form-send/scripts → parents[3]=<repo>

sys.path.insert(0, str(SCRIPTS_DIR))
import adapt_unified_input as adapt  # noqa: E402  (_is_real_url を再利用)
from _run_lock import SingleRunLock, LockBusyError  # noqa: E402  (多重起動ガード)

sys.path.insert(0, str(REPO_ROOT / "shared"))
import sheets_io  # noqa: E402

sys.path.insert(0, str(SKILL_DIR / "core"))
from _trace_logger import japanese_reason  # noqa: E402  (シートのエラーを日本語化)

RESULT_COLS = ["sent_at", "status", "error_reason", "screenshot_path", "provider_used"]


def _send_target(row: dict) -> str:
    """送信先URL: contact_url 優先、無ければ HP url。どちらも実URLでなければ ""。"""
    contact = (row.get("contact_url") or "").strip()
    hp = (row.get("url") or "").strip()
    if adapt._is_real_url(contact):
        return contact
    return hp if adapt._is_real_url(hp) else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Google Sheetsを読んで送信し結果5列を書き戻す")
    ap.add_argument("spreadsheet", help="スプレッドシートのURLまたはキー")
    ap.add_argument("--worksheet", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--row", type=int, default=0,
                    help="指定した物理行(1始まり)だけ送信する（0=全件、既定0）。単一行のピンポイント用")
    ap.add_argument("--force", action="store_true", help="status 記入済みの行も再送信する")
    ap.add_argument("--preview", action="store_true",
                    help="列マッピングと出力先だけ表示して終了（送信も書き込みもしない）")
    ap.add_argument("--message-col", default=None, help="本文ヘッダ名（既定: message / 自動検出）")
    ap.add_argument("--contact-col", default=None, help="送信先URLヘッダ名（既定: contact_url / 自動検出）")
    ap.add_argument("--sender", default=str(REPO_ROOT / "shared" / "sender_info.json"))
    ap.add_argument("--env", default=None)
    ap.add_argument("--creds", default=None)
    ap.add_argument("--decisions", default=None,
                    help="④式ハンドオフの決定JSON（run_send.py へ素通し）")
    ap.add_argument("--auto-default", action="store_true",
                    help="未解決 select/radio に汎用問い合わせの無難な選択肢を自動選択")
    args = ap.parse_args()

    # 多重起動ガード: 同じシートを対象にした送信が既に走っていれば即中止（二重送信/ブラウザ暴走防止）。
    # --preview は送信も書き込みもしないのでロック不要。
    if args.preview:
        return _run(args)
    lock = SingleRunLock("form-send-sheet", f"{args.spreadsheet}::{args.worksheet or '_first'}")
    try:
        lock.acquire()
    except LockBusyError as e:
        print(e.message, file=sys.stderr)
        return 3
    try:
        return _run(args)
    finally:
        lock.release()


def _run(args) -> int:
    aliases: dict[str, list[str]] = {}
    if args.message_col:
        aliases["message"] = [args.message_col]
    if args.contact_col:
        aliases["contact_url"] = [args.contact_col]

    try:
        ws = sheets_io.open_worksheet(args.spreadsheet, args.worksheet, creds_path=args.creds)
    except (FileNotFoundError, ImportError) as e:
        print(f"[エラー] {e}", file=sys.stderr)
        return 2

    want = ["company_name", "url", "contact_url", "message", "status"]
    if args.preview:
        print(sheets_io.preview_mapping(ws, want=want, outputs=RESULT_COLS, aliases=aliases))
        return 0

    rows = sheets_io.read_rows(ws, want=want, aliases=aliases)

    if args.row > 0:
        # 単一行のピンポイント: ユーザーが明示した物理行だけを対象にする（status 済みでも送る）。
        rows = [r for r in rows if int(r.get("_row", 0)) == args.row]
        if not rows:
            print(f"[エラー] 物理行 {args.row} が見つかりません（範囲外）。", file=sys.stderr)
            return 2

    # 自動送信してはいけない status は --force / --row でも決して送らない（送りたくなったら status を空に）。
    #   excluded   … #40 除外リスト該当（誤送信防止）
    #   手動送信要 … reCAPTCHA等で自動送信不可・手動対応必須（①収集時にサーバー抑止リストが付与）
    #   excluded/手動送信要 … 収集時抑止（#40）。要手動送信/送信不可/除外 … 5バケツ（#49）。
    #   いずれも --force/--row でも自動送信しない（送りたければ status を空にする）。
    NO_AUTO_SEND = {"excluded", "手動送信要", "要手動送信", "要手動送信（試行後）", "送信不可", "除外"}
    def _blocked(r):
        return str(r.get("status") or "").strip().lower() in {s.lower() for s in NO_AUTO_SEND}
    n_blocked = sum(1 for r in rows if _blocked(r))
    rows = [r for r in rows if not _blocked(r)]
    if n_blocked:
        print(f"[info] 自動送信対象外（excluded/手動送信要）{n_blocked}件はスキップ（送るなら status を空に）。",
              file=sys.stderr)

    # 送信対象: status 未記入 かつ 送信先URLと会社名がある行（--force / --row で status 済みも含む）
    candidates = [r for r in rows if (args.force or args.row > 0 or not r.get("status"))]
    targets, no_target, no_message = [], 0, 0
    for r in candidates:
        t = _send_target(r)
        if not (r.get("company_name") and t):
            no_target += 1
            continue
        # 本文(message)が空の行は絶対に送らない（③冒頭文が未生成の可能性）。
        # 空のまま送ると個別冒頭文でない誤送信になる。status は付けない＝生成し直せば次回拾える。
        if not (r.get("message") or "").strip():
            no_message += 1
            continue
        r["_send_url"] = t
        targets.append(r)
    if args.limit > 0:
        targets = targets[:args.limit]

    if no_message:
        print(f"[info] 本文(message)が空の {no_message}件は送信しません"
              "（③冒頭文が未生成の可能性。生成し直してから再実行してください）。", file=sys.stderr)

    if not targets:
        print(f"[done] 送信対象なし（送信済みスキップ/送信先なし {no_target}件・本文空 {no_message}件）。"
              "再送するなら status セルを空にするか --force。", file=sys.stderr)
        return 0

    # 一時入力CSV（run_send.py が要求する company_name,url,message）。順序を保持して突き合わせる
    with tempfile.TemporaryDirectory() as tmp:
        in_csv = Path(tmp) / "send_in.csv"
        out_csv = Path(tmp) / "send_out.csv"
        with open(in_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["company_name", "url", "message"])
            w.writeheader()
            for r in targets:
                w.writerow({"company_name": r["company_name"], "url": r["_send_url"],
                            "message": r.get("message", "")})

        cmd = [sys.executable, str(SCRIPTS_DIR / "run_send.py"),
               "--input", str(in_csv), "--sender", args.sender, "--output", str(out_csv)]
        default_env = SKILL_DIR / "config" / ".env"
        env_path = args.env or (str(default_env) if default_env.exists() else None)
        if env_path:
            cmd += ["--env", env_path]
        # ④式ハンドオフ／batch フォールバックを run_send.py へ素通し。
        if args.decisions:
            cmd += ["--decisions", args.decisions]
        if args.auto_default:
            cmd += ["--auto-default"]

        print(f"[send] {len(targets)}件を送信します -> run_send.py", file=sys.stderr)
        proc = subprocess.run(cmd, cwd=str(SKILL_DIR))
        if proc.returncode != 0:
            print(f"[エラー] run_send.py が異常終了しました (code={proc.returncode})。"
                  "シートへの書き戻しは行いません。", file=sys.stderr)
            return proc.returncode
        if not out_csv.exists():
            print("[エラー] 結果CSVが生成されませんでした。書き戻しを中止します。", file=sys.stderr)
            return 1

        # 結果を (company_name, url) で突き合わせ（順序が変わっても安全）
        result_by_key: dict[tuple, dict] = {}
        with open(out_csv, newline="", encoding="utf-8-sig") as f:
            for rec in csv.DictReader(f):
                key = ((rec.get("company_name") or "").strip(), (rec.get("url") or "").strip())
                result_by_key[key] = rec

    matched = 0
    for r in targets:
        rec = result_by_key.get((r["company_name"].strip(), r["_send_url"].strip()))
        if rec:
            for c in RESULT_COLS:
                r[c] = rec.get(c, "")
            # error_reason はシート向けに日本語化（技術コード→人が読める説明）。
            r["error_reason"] = japanese_reason(
                rec.get("error_reason", ""), rec.get("status", "")
            )
            matched += 1

    written = sheets_io.write_cells(ws, [r for r in targets if r.get("status")], RESULT_COLS,
                                    overwrite=False)
    print(f"[done] sent={matched}/{len(targets)} written_cells={written} -> sheet '{ws.title}'",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
