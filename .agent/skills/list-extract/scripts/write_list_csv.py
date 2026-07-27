#!/usr/bin/env python3
"""write_list_csv.py — ①list-extract の薄いローカル書き出し層（除外/重複ロジックを持たない）。

MCP `list_filter_exclude` が返した kept 配列を、統一スキーマの列順で CSV に書くだけ。
除外ドメイン辞書・URL正規化・重複除去は**秘匿コア（MCP側）**が済ませている前提。

入力: list_filter_exclude の戻りJSON（{"version","kept":[...],"dropped":[...],"stats":{...}}）
      または kept 配列だけでも可。
出力: 統一CSV（company_name, url, address, phone, maps_url）。

使い方:
    python scripts/write_list_csv.py <filter_result.json> <out.csv>
"""
from __future__ import annotations

import argparse
import csv
import json
import sys

COLUMNS = ["company_name", "url", "address", "phone", "maps_url"]


def main() -> int:
    ap = argparse.ArgumentParser(description="list_filter_exclude の kept を統一CSVに書く")
    ap.add_argument("result", help="MCP list_filter_exclude の戻りJSON")
    ap.add_argument("output", help="出力CSVパス")
    args = ap.parse_args()

    data = json.load(open(args.result, encoding="utf-8"))
    kept = data if isinstance(data, list) else data.get("kept", [])
    stats = {} if isinstance(data, list) else data.get("stats", {})

    # 抑止リスト適用で status（例: 手動送信要）が付いた kept 行があれば status 列も出力する。
    # → 後続の run_on_sheet がこの status をシートへ運び、④form-send が自動送信対象から外す。
    cols = list(COLUMNS)
    if any((r.get("status") or "").strip() for r in kept):
        cols.append("status")

    with open(args.output, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in kept:
            w.writerow({c: (r.get(c) or "") for c in cols})

    if stats:
        manual = stats.get("manual", 0)
        print(
            f"[list-extract] 入力 {stats.get('total','?')} 件 → 出力 {stats.get('kept',len(kept))} 件\n"
            f"  除外内訳: 必須欠落 {stats.get('no_required','?')} / 除外ドメイン {stats.get('excluded','?')} / 重複 {stats.get('dup','?')}"
            f" / 除外タブ {stats.get('partner',0)} / 営業不可 {stats.get('no_contact',0)}\n"
            f"  手動送信要（自動送信対象外）: {manual} 件\n"
            f"  出力先: {args.output}",
            file=sys.stderr,
        )
    else:
        print(f"[list-extract] 出力 {len(kept)} 件 → {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
