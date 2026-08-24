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
    --writeback-from CSV  送信せず、結果CSV（logs/sheet_send_*.csv）だけをシートへ書き戻す（復旧用）
    --chunk N          N件ごとに「送信→書き戻し」を繰り返す（既定50・0で分割なし）
    --sender PATH      送信者情報JSON（既定: shared/sender_info.json）
    --env PATH         APIキー .env（既定: form-send/config/.env があればそれ）
    --creds PATH       サービスアカウントJSON（既定の探索順は sheets_io に準拠）
    (--model/--mode は run_send.py の既定に従う)

再実行ポリシー（設計 §9-c）: form-send は overwrite=False。既定では status 未記入の行だけ
送信し、送信済みの行は決して触らない（再送したい行は status セルを空にする / --force）。
--row も同じ扱い＝status/sent_at が入っている行は送らずに中止する（#55 F3）。
★大量送信前の人間確認は run_send.py 側の運用ルールに従う。

終了コード: 0=正常 / 1=結果CSVなし等 / 2=引数・シートのエラー / 3=多重起動 /
4=--row の送信済みガードで中止 / それ以外=run_send.py の異常終了コード。
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import tempfile
from datetime import datetime
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
from _trace_logger import classify_failure, japanese_reason  # noqa: E402  (シートのエラーを日本語化/判定)

RESULT_COLS = ["sent_at", "status", "error_reason", "screenshot_path", "provider_used",
               # どの長さの版で送ったか（#57）。message 列はフル版のままなので、
               # ここが空欄だと「この文面が届いた」と読み違える＝表示の嘘になる。
               "message_variant"]


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
                    help="指定した物理行(1始まり)だけ送信する（0=全件、既定0）。単一行のピンポイント用。"
                         "status/sent_at が入っている行は送らず中止する（送り直すなら status を空に）")
    ap.add_argument("--force", action="store_true", help="status 記入済みの行も再送信する")
    ap.add_argument("--writeback-from", default=None, metavar="CSV",
                    help="送信はせず、指定した結果CSV（logs/sheet_send_*.csv）だけをシートへ書き戻す。"
                         "ファイル／ディレクトリ／ワイルドカード可。送信が途中で強制終了したときの復旧用")
    ap.add_argument("--chunk", type=int, default=50, metavar="N",
                    help="N件ごとに送信→シートへ書き戻すのを繰り返す（既定50・0で分割なし）。"
                         "分割しないと、途中で強制終了されたとき全件がシート未反映のまま残る")
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
    ap.add_argument("--allow-tiny", action="store_true",
                    help="100字版など極端に短い営業文も使う（#57）。既定では使わない")
    ap.add_argument("--allow-resend", action="store_true",
                    help="送信済み台帳の照合を外して、既に送った会社にも送る。"
                         "★二重送信の最後の砦を自分で外す操作（--force とは別に必要）")
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

    # opener＝③が作った会社ごとの冒頭文。短い版を組み立て直すのに使う（#57）。
    want = ["company_name", "url", "contact_url", "message", "opener", "status"]
    if args.preview:
        print(sheets_io.preview_mapping(ws, want=want, outputs=RESULT_COLS, aliases=aliases))
        return 0

    # sent_at も読む: --row の送信済みガード（#55 F3）で「送信を試みた痕跡」を見るため。
    rows = sheets_io.read_rows(ws, want=want + ["sent_at"], aliases=aliases)

    if args.row > 0:
        # 単一行のピンポイント: ユーザーが明示した物理行だけを対象にする。
        rows = [r for r in rows if int(r.get("_row", 0)) == args.row]
        if not rows:
            print(f"[エラー] 物理行 {args.row} が見つかりません（範囲外）。", file=sys.stderr)
            return 2
        # ★送信済みガード（#55 F3）: --row は中断からの復旧作業でこそ使われる。そこに再送防止が
        #   無いと、送信済みの行を名指しした瞬間に取り消せない二重送信になる（実害80社の再発経路）。
        #   status か sent_at のどちらかが入っている＝一度は送信を試みた行で、**届いている可能性がある**
        #   （失敗記録でも「送信ボタンは押せていた」ケースがある＝#56）。よってどちらでも止める。
        #   本当に送り直すなら status セルを空にする＝人が確認した印を残してから。
        prev_status = str(rows[0].get("status") or "").strip()
        prev_sent_at = str(rows[0].get("sent_at") or "").strip()
        if prev_status or prev_sent_at:
            detail = "・".join(filter(None, [
                f"status='{prev_status}'" if prev_status else "",
                f"sent_at='{prev_sent_at}'" if prev_sent_at else "",
            ]))
            print(f"[中止] 行 {args.row} は既に送信を試みた行です（{detail}）。"
                  "届いている可能性があるため送信しません。\n"
                  "  → 本当に送り直すなら、シートのその行の status セル（と sent_at セル）を"
                  "空にしてから再実行してください。", file=sys.stderr)
            return 4

    # 自動送信してはいけない status は --force / --row でも決して送らない（送りたくなったら status を空に）。
    #   excluded   … #40 除外リスト該当（誤送信防止）
    #   手動送信要 … reCAPTCHA等で自動送信不可・手動対応必須（①収集時にサーバー抑止リストが付与）
    #   excluded/手動送信要 … 収集時抑止（#40）。要手動送信/送信不可/除外 … 5バケツ（#49）。
    #   いずれも --force でも自動送信しない（送りたければ status を空にする）。
    #   ※--row は上の送信済みガードで status 記入行を既に弾いている。
    NO_AUTO_SEND = {"excluded", "手動送信要", "要手動送信", "要手動送信（試行後）", "送信不可", "除外"}
    def _blocked(r):
        return str(r.get("status") or "").strip().lower() in {s.lower() for s in NO_AUTO_SEND}
    n_blocked = sum(1 for r in rows if _blocked(r))
    rows = [r for r in rows if not _blocked(r)]
    if n_blocked:
        print(f"[info] 自動送信対象外（excluded/手動送信要）{n_blocked}件はスキップ（送るなら status を空に）。",
              file=sys.stderr)

    # 送信対象: status 未記入 かつ 送信先URLと会社名がある行（--force のときだけ status 済みも含む）
    candidates = [r for r in rows if (args.force or not r.get("status"))]
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
    # 復旧モードでは --limit で候補を削らない（記録済みの社を全部拾えるように）
    if args.limit > 0 and not args.writeback_from:
        targets = targets[:args.limit]

    if no_message:
        print(f"[info] 本文(message)が空の {no_message}件は送信しません"
              "（③冒頭文が未生成の可能性。生成し直してから再実行してください）。", file=sys.stderr)

    if not targets:
        print(f"[done] 送信対象なし（送信済みスキップ/送信先なし {no_target}件・本文空 {no_message}件）。"
              "再送するなら status セルを空にするか --force。", file=sys.stderr)
        return 0

    # 復旧モード: 送信はせず、既にある結果CSVをシートへ書き戻すだけ（#55 F1）。
    # 送信が強制終了して書き戻しだけ残っている場合に、二重送信せず記録を復旧するための道。
    if args.writeback_from:
        srcs = _resolve_result_files(args.writeback_from)
        if not srcs:
            print(f"[エラー] 結果CSVが見つかりません: {args.writeback_from}", file=sys.stderr)
            return 2
        print(f"[復旧] 送信せずに書き戻します: {'、'.join(p.name for p in srcs)}", file=sys.stderr)
        merged: dict[tuple, dict] = {}
        for p in srcs:                      # 分割送信では1ランが複数ファイルに分かれる
            merged.update(_read_results(p))
        _writeback(ws, targets, merged)
        return 0

    # 結果CSVは**消えない場所**に置く（#55 F1）。tempdir に置くと、実行ごと強制終了された
    # ときに「送信は飛んだのに結果が残らない」＝再開時の二重送信になる。logs/ は .gitignore 済み。
    logs_dir = SKILL_DIR / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ★チャンク分割（#55 F4）: 全件を1本のプロセスに渡すと、シートへの反映は最後まで来ない。
    #   そこを実行ごと落とされると、送信は飛んでいるのにシートは空欄のまま残る。
    #   N件ずつ「送る→書き戻す」を繰り返せば、空欄で残るのは最大N件に抑えられる。
    size = args.chunk if args.chunk > 0 else len(targets)
    batches = [targets[i:i + size] for i in range(0, len(targets), size)]

    print(f"[send] {len(targets)}件を送信します"
          f"（{len(batches)}回に分割・1回あたり最大{size}件）-> run_send.py", file=sys.stderr)
    print(f"[記録] 送信結果は1社ごとに追記されます: {logs_dir}/sheet_send_{stamp}_c*.csv\n"
          f"       途中で強制終了した場合は、この記録から書き戻せます:\n"
          f"       python scripts/run_on_sheet.py \"{args.spreadsheet}\" "
          f"--writeback-from \"logs/sheet_send_{stamp}_c*.csv\"", file=sys.stderr)

    rc = 0
    for i, batch in enumerate(batches, start=1):
        out_csv = logs_dir / f"sheet_send_{stamp}_c{i:02d}.csv"
        if len(batches) > 1:
            print(f"[send] {i}/{len(batches)} 回目（{len(batch)}件）", file=sys.stderr)
        rc = _send_batch(args, batch, out_csv)

        # ★異常終了でも、書けている分は必ず書き戻す（#55 F1）。ここで捨てると
        #   「送信は飛んでいるのにシートは空欄」になり、次のランで二重送信になる。
        if rc != 0:
            print(f"[警告] run_send.py が異常終了しました (code={rc})。"
                  "ここまでに記録された分だけシートへ書き戻します。", file=sys.stderr)
        if out_csv.exists():
            _writeback(ws, batch, _read_results(out_csv))
        else:
            print("[エラー] 結果CSVが生成されませんでした。書き戻す内容がありません。", file=sys.stderr)
            rc = rc or 1

        if rc != 0:
            # 壊れた状態で次のチャンクへ進まない。ここまでの分は書き戻し済み。
            print(f"[中断] {i}/{len(batches)} 回目で停止しました"
                  f"（{i - 1}回分はシートへ反映済み）。原因を確認してから再実行してください。",
                  file=sys.stderr)
            break

    # シグナルで殺されると rc は負値。シェルに正しく伝わるよう Unix 慣例(128+N)へ直す。
    return rc if rc >= 0 else 128 - rc


def _send_batch(args, batch: list[dict], out_csv: Path) -> int:
    """1チャンク分を run_send.py に渡して送信する。戻り値は run_send.py の終了コード。"""
    # 入力CSV（営業本文を含む）は一時ディレクトリ＝実行後に自動で消す
    with tempfile.TemporaryDirectory() as tmp:
        in_csv = Path(tmp) / "send_in.csv"
        with open(in_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["company_name", "url", "message", "opener"])
            w.writeheader()
            for r in batch:
                w.writerow({"company_name": r["company_name"], "url": r["_send_url"],
                            "message": r.get("message", ""),
                            "opener": r.get("opener", "")})

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
        # ★台帳照合を外すのは --force とは別の明示操作（--force だけでは外れない）。
        if getattr(args, "allow_resend", False):
            cmd += ["--allow-resend"]
        if getattr(args, "allow_tiny", False):
            cmd += ["--allow-tiny"]
        return subprocess.run(cmd, cwd=str(SKILL_DIR)).returncode


def _resolve_result_files(spec: str) -> list[Path]:
    """--writeback-from の指定を実ファイルの並びに解く。

    分割送信では1回のランが sheet_send_<日時>_c01.csv, _c02.csv … に分かれるので、
    ファイル1本だけでなく、ディレクトリ／ワイルドカードでもまとめて拾えるようにする。
    """
    p = Path(spec).expanduser()
    if p.is_dir():
        return sorted(p.glob("sheet_send_*.csv"))
    if any(ch in p.name for ch in "*?["):
        return sorted(p.parent.glob(p.name))
    return [p] if p.exists() else []


def _read_results(out_csv: Path) -> dict[tuple, dict]:
    """結果CSVを (company_name, url) で引ける形に読む（順序が変わっても安全）。

    途中で落ちた場合は最終行が壊れていることがあるので、行単位で読み飛ばす。
    """
    result_by_key: dict[tuple, dict] = {}
    with open(out_csv, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        while True:
            try:
                rec = next(reader)
            except StopIteration:
                break
            except csv.Error as e:  # 途中で切れた行。ここまでの分は活かす
                print(f"[warn] 結果CSVの末尾が壊れています（読み飛ばし）: {e}", file=sys.stderr)
                break
            key = ((rec.get("company_name") or "").strip(), (rec.get("url") or "").strip())
            result_by_key[key] = rec
    return result_by_key


def _writeback(ws, targets: list[dict], result_by_key: dict[tuple, dict]) -> int:
    """結果をシートの同じ行へ書き戻す。書き込んだ社数を返す。"""
    matched = 0
    cooldown_kept: list[str] = []
    for r in targets:
        rec = result_by_key.get((r["company_name"].strip(), r["_send_url"].strip()))
        if not rec:
            continue
        raw_status = rec.get("status", "")
        raw_reason = rec.get("error_reason", "")
        # ★待機(domain_cooldown)で見送った行は status を書かない＝空のまま残す。
        #   書くと status=skipped になり、tierb_relabel が「除外」へ畳む（:57-58）。
        #   結果、**一度も送っていない会社が二度と送られなくなる**（本番シートで17行が
        #   実際にこれで失われた＝#52 の発端）。空のままなら relabel は REEVAL 外で触らず、
        #   次のランで通常どおり候補に戻る＝「次回ランで再試行」が初めて真になる。
        if classify_failure(raw_reason, raw_status) == "domain_cooldown":
            cooldown_kept.append(r.get("company_name") or "")
            continue
        for c in RESULT_COLS:
            r[c] = rec.get(c, "")
        # error_reason はシート向けに日本語化（技術コード→人が読める説明）。
        r["error_reason"] = japanese_reason(raw_reason, raw_status)
        matched += 1

    written = sheets_io.write_cells(ws, [r for r in targets if r.get("status")], RESULT_COLS,
                                    overwrite=False)
    if cooldown_kept:
        print(f"[info] 待機のため未送信 {len(cooldown_kept)}件は status を書かずに残しました"
              f"（次のランで再挑戦されます）: {'、'.join(cooldown_kept[:5])}"
              f"{' ほか' if len(cooldown_kept) > 5 else ''}", file=sys.stderr)
    print(f"[done] sent={matched}/{len(targets)} written_cells={written} -> sheet '{ws.title}'",
          file=sys.stderr)
    return matched


if __name__ == "__main__":
    raise SystemExit(main())
