#!/usr/bin/env python3
"""統一CSVスキーマ → form-send 入力CSV への薄いアダプタ。

form-send 本体 (run_send.py) は送信先を `url` 列で受け取る。
本パイプラインの統一スキーマでは送信先は `contact_url` 列なので、
ここで `url ← contact_url` に詰め替えた一時CSVを生成する（本体は無改変）。

使い方:
    python scripts/adapt_unified_input.py <unified.csv> <out_for_send.csv>

挙動:
- 出力列は run_send.py が必須とする company_name, url, message。
- `contact_url` があればそれを送信先 `url` にする。無ければ元の `url`（HP）を使う。
- `contact_url` が空 / 値なし（"見つかりませんでした" 等）の行はスキップし、stderr に件数を出す。
- message 列は素通し（空でも可。空なら run_send.py 側が sender_info.json の message を使う）。
"""
import csv
import sys

# contact_url が「実URLでない」とみなす値（ListGetAuto 由来の非URL文字列）
_NON_URL_MARKERS = ("見つかりませんでした", "エラー", "")


def _is_real_url(value: str) -> bool:
    v = (value or "").strip()
    if not v or v.startswith("エラー") or v in _NON_URL_MARKERS:
        return False
    return v.startswith("http")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: adapt_unified_input.py <unified.csv> <out_for_send.csv>", file=sys.stderr)
        return 2

    src, dst = sys.argv[1], sys.argv[2]
    kept, skipped = 0, 0

    with open(src, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    out_rows = []
    for row in rows:
        company = (row.get("company_name") or "").strip()
        contact = (row.get("contact_url") or "").strip()
        hp = (row.get("url") or "").strip()
        message = (row.get("message") or "").strip()

        # 送信先の決定: contact_url 優先、無ければ HP url
        target = contact if _is_real_url(contact) else (hp if _is_real_url(hp) else "")
        if not company or not target:
            skipped += 1
            continue

        out_rows.append({"company_name": company, "url": target, "message": message})
        kept += 1

    with open(dst, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["company_name", "url", "message"])
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"[adapt] kept={kept} skipped={skipped} -> {dst}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
