#!/usr/bin/env python3
"""Tier B（AIブラウザ運転）送信結果の決定論・ガード付きシート書き戻し。

無人並列 Tier B 送信では、各サブエージェントが1社送信するたびに本CLIを呼び、
Tier A と同じ5列（H:sent_at I:status J:error_reason K:screenshot_path L:provider_used）へ
結果を記録する。error_reason は必ず日本語で記録する（英語コードは REASON_JA で和訳）。

usage:
    python tierb_writeback.py <sheet_key> <row> <expected_company> <status> <provider> [reason] [--overwrite-failed]

ガード:
  - A{row} が expected_company を含む（or 逆包含）＝行取り違え防止。
  - 既定: I{row}(status) が空でないなら書かない＝二重書き防止。
  - --overwrite-failed 指定時のみ: 現在の status が「failed」の行に限り上書き可
    （Tier A が送れず failed にした行を Tier B が送り直して completed 等へ更新する用途）。
    completed / skipped / 手動送信要 / excluded は --overwrite-failed でも決して触らない。
戻り値: 0=書込成功 / 1=引数不足 / 2=行照合失敗 / 3=書込対象外（既存statusを尊重）。
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS_DIR.parent
REPO_ROOT = SCRIPTS_DIR.parents[3]
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(SKILL_DIR / "core"))
sys.path.insert(0, str(REPO_ROOT / "shared"))
import sheets_io  # noqa: E402

JST = timezone(timedelta(hours=9))

# Tier B 固有の理由コード → 日本語（Tier A の japanese_reason が持たない語彙をここで補う）。
REASON_JA = {
    "": "",
    "no_solicitation": "営業お断りの明示があります",
    "captcha": "CAPTCHAのため人手が必要です",
    "silent_reject": "送信が拒否されました（reCAPTCHA等のサイレント拒否）",
    "http_403_blocked": "アクセスがブロックされました（403）",
    "waf_403": "アクセスがブロックされました（403/WAF）",
    "form_not_found": "問い合わせフォームが見つかりません",
    "field_detection_miss": "入力欄をうまく特定できませんでした",
    "message_too_long": "本文が入力欄の文字数上限を超えています",
    "recruit_entry_form_not_contact": "問い合わせでなく採用応募フォームでした",
    "duplicate_registration": "重複登録の可能性があります",
    "duplicate_already_processed": "重複（同一送信先が既に処理済み）",
    "duplicate_in_batch": "重複（同一送信先が同一バッチ内に複数）",
    "duplicate_assigned_to_other_worker": "重複（同一送信先が別ワーカー担当）",
    "uncertain": "送信可否が不明のため見送りました",
    "dns_error": "サイトに到達できません（DNSエラー）",
    "site_not_found": "サイトが見つかりません",
}


def to_japanese(reason: str, status: str) -> str:
    """理由を日本語へ。既知の Tier B コードは REASON_JA、それ以外は Tier A の
    japanese_reason（あれば）へ委譲。どちらにも無ければ原文のまま返す。"""
    r = (reason or "").strip()
    if r in REASON_JA:
        return REASON_JA[r]
    try:
        from _trace_logger import japanese_reason  # type: ignore
        ja = japanese_reason(r, status)
        if ja:
            return ja
    except Exception:
        pass
    return r


def main() -> int:
    argv = [a for a in sys.argv[1:] if a != "--overwrite-failed"]
    overwrite_failed = "--overwrite-failed" in sys.argv[1:]
    if len(argv) < 5:
        print("usage: tierb_writeback.py <sheet_key> <row> <expected_company> <status> "
              "<provider> [reason] [--overwrite-failed]", file=sys.stderr)
        return 1
    sheet_key, row_s, expected, status, provider = argv[:5]
    row = int(row_s)
    expected = expected.strip()
    status = status.strip()
    provider = provider.strip()
    reason_code = argv[5] if len(argv) > 5 else ""

    ws = sheets_io.open_worksheet(sheet_key, None)
    a = (ws.acell(f"A{row}").value or "").strip()
    if not (expected and (expected in a or a in expected)):
        print(f"[GUARD-FAIL] A{row}={a!r} != expected {expected!r}; 書き込み中止", file=sys.stderr)
        return 2
    cur = (ws.acell(f"I{row}").value or "").strip()
    if cur:
        # 上書き可なのは「failed の行を --overwrite-failed で送り直す」場合だけ。
        if not (overwrite_failed and cur.lower() == "failed"):
            print(f"[GUARD-SKIP] I{row} は既に status={cur!r}; 上書きしない", file=sys.stderr)
            return 3

    sent_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    reason_ja = to_japanese(reason_code, status)
    values = [[sent_at, status, reason_ja, "", provider]]
    try:
        ws.update(range_name=f"H{row}:L{row}", values=values)
    except TypeError:  # 古い gspread 互換
        ws.update(f"H{row}:L{row}", values)
    print(f"[OK] row{row} ({a}) <- status={status} reason={reason_ja!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
