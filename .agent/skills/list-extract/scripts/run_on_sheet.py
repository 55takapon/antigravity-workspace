#!/usr/bin/env python3
"""list-extract (Google Sheets 直結版) — 正規化済みリストCSVをユーザーのシートに追記する。

パイプラインの起点。normalize_dedup.py が出力した統一CSV
（company_name, url[, address, phone, maps_url]）を読み、ユーザーが用意した
スプレッドシートの末尾に追記する。以降 ②③④ が同じシートに列を足していく。

使い方:
    python scripts/run_on_sheet.py <spreadsheet_url_or_key> <normalized.csv> [options]

options:
    --worksheet NAME   対象ワークシート名（既定: 先頭シート）
    --no-dedup         シート既存の url との重複除去をしない（既定は重複行をスキップ）
    --creds PATH       サービスアカウントJSON（既定の探索順は sheets_io に準拠）

設計 §9-a/b: ユーザーが用意した1枚の空シートに、統一列を横並びで追記する。
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]   # .../<repo>/.claude/skills/001-list-extract/scripts
sys.path.insert(0, str(REPO_ROOT / "shared"))
import sheets_io  # noqa: E402

# 統一スキーマのうち list-extract が書く列（CSVに在るものだけを採用、この順序で）
# status は抑止リスト由来の「手動送信要」を運ぶための任意列（CSVに在れば追記対象に含める）。
LIST_COLS = ["company_name", "url", "address", "phone", "maps_url", "status"]


def _norm_url(u: str) -> str:
    """重複照合用のURL正規化。scheme/www/末尾スラッシュ・大小の揺れを吸収する。
    （既存シートには末尾スラッシュ付きURLが混在するため、exact照合だと同一URLでも
    すり抜けて二重追記になる。照合キーだけ正規化し、書き込む値は元のまま。）"""
    u = (u or "").strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def main() -> int:
    ap = argparse.ArgumentParser(description="正規化済みリストCSVをスプレッドシートに追記する")
    ap.add_argument("spreadsheet", help="スプレッドシートのURLまたはキー")
    ap.add_argument("input_csv", help="normalize_dedup.py が出力した統一CSV")
    ap.add_argument("--worksheet", default=None)
    ap.add_argument("--no-dedup", action="store_true", help="シート既存urlとの重複除去をしない")
    ap.add_argument("--preview", action="store_true",
                    help="追記する列と件数だけ表示して終了（1セルも書かない）")
    ap.add_argument("--creds", default=None)
    args = ap.parse_args()

    src = Path(args.input_csv)
    if not src.exists():
        print(f"[エラー] 入力CSVが見つかりません: {src}", file=sys.stderr)
        return 2
    with open(src, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = [h.lstrip("﻿") for h in (reader.fieldnames or [])]
        csv_rows = list(reader)
    if "url" not in headers:
        print(f"[エラー] 入力CSVに url 列がありません（{headers}）。", file=sys.stderr)
        return 2

    cols = [c for c in LIST_COLS if c in headers]

    try:
        ws = sheets_io.open_worksheet(args.spreadsheet, args.worksheet, creds_path=args.creds)
    except (FileNotFoundError, ImportError) as e:
        print(f"[エラー] {e}", file=sys.stderr)
        return 2

    # 重複除去: シートに既にある url はスキップ（再実行で二重追記しない）
    existing_urls: set[str] = set()
    if not args.no_dedup:
        for r in sheets_io.read_rows(ws, want=["url"]):
            u = (r.get("url") or "").strip()
            if u:
                existing_urls.add(_norm_url(u))

    new_rows, dup, blank = [], 0, 0
    seen_in_batch: set[str] = set()
    for rec in csv_rows:
        url = (rec.get("url") or "").strip()
        if not url:
            blank += 1
            continue
        key = _norm_url(url)
        if (not args.no_dedup and key in existing_urls) or key in seen_in_batch:
            dup += 1
            continue
        seen_in_batch.add(key)
        new_rows.append({c: (rec.get(c) or "").strip() for c in cols})

    if args.preview:
        print(f"シート『{ws.title}』へ追記プレビュー")
        print(f"  追記する列 : {cols}")
        print(f"  追記行数   : {len(new_rows)}（重複skip {dup}件 / url空 {blank}件）")
        for r in new_rows[:3]:
            print("  - " + " / ".join(f"{c}={r.get(c) or '∅'}" for c in cols))
        print("※ プレビューのみ。シートには1セルも書き込んでいません。")
        return 0

    if not new_rows:
        print(f"[done] 追記対象なし（重複 {dup}件 / url空 {blank}件）。", file=sys.stderr)
        return 0

    appended = sheets_io.append_rows(ws, new_rows, cols)
    print(f"[done] appended={appended} dup_skip={dup} blank_skip={blank} "
          f"cols={cols} -> sheet '{ws.title}'", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
