#!/usr/bin/env python3
"""`claude -p --output-format json` の結果を、ログに読める形で吐き出し、異常を可視化する。

★なぜ要るか（2026-08-19 モニター報告）:
  claude -p は **ツールを1つも実行できなくても終了コード0（subtype=success）を返す**。
  そのため kick_*.sh の `[[ $rc -eq 0 ]]` は素通りし、Tier B が1社も送れていないのに
  ログには「done (rc=0)」と書かれていた。異常が異常として表に出ない状態だった。

  拒否された事実は JSON の permission_denials にだけ残る。ここでそれを必ずログへ出す。
  （モデル本人には拒否の理由が渡らないので、モデルの説明文はあてにならない。一次資料はこれ）

usage:
  claude_result.py <json_path> [--label LABEL] [--metrics]

出力: 人が読む本文（result）＋ 拒否の一覧（あれば）＋ --metrics 時は usage/コスト
終了コード:
  0 = 正常（拒否なし）
  5 = 拒否あり（呼び出し側が警告/中止を判断する。ここでは判断しない）
  6 = JSON を読めない / 想定の形でない（＝claude 側が異常終了した疑い）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("json_path")
    ap.add_argument("--label", default="claude")
    ap.add_argument("--metrics", action="store_true")
    a = ap.parse_args()

    raw = Path(a.json_path)
    if not raw.is_file() or raw.stat().st_size == 0:
        print(f"[{a.label}] 🔴 claude の出力が空（異常終了の疑い）", file=sys.stderr)
        return 6
    try:
        d = json.loads(raw.read_text(encoding="utf-8"))
    except Exception as e:
        # 壊れたJSONでも中身は捨てない（切り分けの手がかりを残す）
        print(f"[{a.label}] 🔴 claude の出力をJSONとして読めない: {e}", file=sys.stderr)
        print(raw.read_text(encoding="utf-8", errors="replace")[:2000])
        return 6

    # 本文。ここを出さないとログが読めなくなる（従来はテキスト出力がそのまま入っていた）
    text = d.get("result")
    if text:
        print(text)

    if a.metrics:
        u = d.get("usage") or {}
        cost = d.get("total_cost_usd")
        print(f"[{a.label}] usage={json.dumps(u, ensure_ascii=False)} cost_usd={cost}")

    if d.get("is_error"):
        print(f"[{a.label}] 🔴 claude が is_error=true を返した (subtype={d.get('subtype')})", file=sys.stderr)

    denials = d.get("permission_denials") or []
    if not denials:
        return 0

    # ★拒否は必ず全部出す。「何が許可リストから漏れているか」はここにしか残らない。
    print(f"[{a.label}] 🔴 許可されず実行できなかったツールが {len(denials)} 件あります"
          f"（許可リストの漏れ、またはパスに空白がある可能性）", file=sys.stderr)
    seen: dict[str, int] = {}
    for x in denials:
        tool = x.get("tool_name", "?")
        inp = x.get("tool_input") or {}
        detail = inp.get("command") or inp.get("file_path") or inp.get("pattern") or ""
        key = f"{tool}: {detail}"
        seen[key] = seen.get(key, 0) + 1
    for key, n in sorted(seen.items(), key=lambda kv: -kv[1]):
        print(f"    ×{n}  {key[:300]}", file=sys.stderr)
    return 5


if __name__ == "__main__":
    raise SystemExit(main())
