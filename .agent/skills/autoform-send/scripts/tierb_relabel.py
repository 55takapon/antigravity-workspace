#!/usr/bin/env python3
"""シートの status を「ユーザーが何をすればいいか」の5バケツへ畳む（#49 status区別）。

内部status（completed/skipped/failed/手動送信要）＋日本語 error_reason を読み、
アクション別の5バケツへ書き換える。error_reason 列（日本語詳細）はそのまま残す。

  送信済み   … 送信成功。何もしなくてよい。
  要手動送信 … 自動では送れなかったがフォームは生きている（CAPTCHA/サイレント拒否/判定不明）。人が送れば取れる。
  要見直し   … 設定を直せば次回自動で送れる（本文が長すぎ/②URLが採用・別窓口）。
  送信不可   … フォーム無・死にサイト・WAF(403)・営業お断り。諦める。
  除外       … 除外リスト該当・重複行（意図的スキップ）。

冪等（既にバケツ済みの行は触らない）。ラン末尾で毎回呼んでよい（既存行も順次移行される）。
usage: python tierb_relabel.py <sheet_key>
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parents[3]
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(REPO_ROOT / "shared"))
import sheets_io  # noqa: E402

BUCKETS = {"送信済み", "要手動送信", "要手動送信（試行後）", "要見直し", "送信不可", "除外"}
INTERNAL = {"completed", "skipped", "failed", "手動送信要"}  # excluded は issue40 の判定に使うので触らない
# 「要手動送信」も再評価対象に含める＝既存行を sent_at の有無で「試行後」へ分離するため。
REEVAL = INTERNAL | {"要手動送信"}


def _has(reason: str, *keys: str) -> bool:
    return any(k in reason for k in keys)


def classify(status: str, reason: str, has_attempt: bool) -> str:
    """status/理由/送信試行の有無 → 6バケツ。
    has_attempt=送信を試した（sent_at か provider がある）かどうか。
    要手動送信を「リスト段階（未試行・色なし）」と「試行後（オレンジ）」に分ける。"""
    st = (status or "").strip().lower()
    r = reason or ""
    if st == "completed":
        return "送信済み"
    # 送信不可＝諦めてよい（送れない/送るべきでない）＝営業お断り・WAF(403)・死にサイトのみ。
    if _has(r, "営業お断り", "営業目的", "勧誘"):
        return "送信不可"
    if _has(r, "403", "ブロック", "ＷＡＦ", "WAF"):
        return "送信不可"
    if _has(r, "到達できません", "到達不能", "404", "DNS", "死にサイト", "サイトが見つかり"):
        return "送信不可"
    # 要見直し＝設定を直せば次回自動で送れる（本文長超過・②URLが採用/別窓口）。
    if _has(r, "上限", "文字数"):
        return "要見直し"
    if _has(r, "採用"):
        return "要見直し"
    if st == "skipped":
        return "除外"  # skipped の既定＝意図的スキップ（除外リスト・重複等）
    # 要手動送信系（手動送信要=リスト段階の抑止／failed=検出困難やCAPTCHA等／既存の要手動送信）。
    #   送信を試したか（has_attempt）で色分け用に2つへ分ける。
    return "要手動送信（試行後）" if has_attempt else "要手動送信"


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--dry"]
    dry = "--dry" in sys.argv[1:]
    if not args:
        print("usage: tierb_relabel.py <sheet_key> [--dry]", file=sys.stderr)
        return 1
    ws = sheets_io.open_worksheet(args[0], None)
    grid = ws.get("A1:L")
    updates = []  # (row, old_status, reason, bucket)
    for i, r in enumerate(grid, start=1):
        if i == 1:
            continue  # ヘッダ
        g = lambda x: r[x] if x < len(r) else ""  # noqa: E731
        status = (g(8) or "").strip()
        if status not in REEVAL:
            continue  # 既にバケツ（試行後含む）/ excluded / 空 は触らない
        has_attempt = bool((g(7) or "").strip() or (g(11) or "").strip())  # H:sent_at / L:provider
        bucket = classify(status, g(9) or "", has_attempt)
        if bucket and bucket != status:
            updates.append((i, status, g(9) or "", bucket))

    from collections import Counter
    dist = Counter(u[3] for u in updates)
    print(f"[relabel] 変換対象 {len(updates)}行 → {dict(dist)}")
    if dry:
        for (row, st, rs, bk) in updates[:15]:
            print(f"  row{row}: {st}/{rs[:20]} -> {bk}")
        print("（--dry のため書き込みなし）")
        return 0
    if updates:
        ws.batch_update([{"range": f"I{row}", "values": [[bucket]]} for (row, _s, _r, bucket) in updates])
    print(f"[relabel] {len(updates)}行を5バケツへ書き換え完了")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
