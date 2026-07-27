#!/usr/bin/env python3
"""fetch_sheet — 閲覧公開のGoogleスプレッドシートURLを読み、統一スキーマCSVに正規化する。

配布版 contact-extract の入口。ユーザーは「リンクを知っている全員が閲覧可」にした
シートのURLを渡すだけ。列の様式（ヘッダ名・列順）が違っても、会社名列とURL列を
自動検出して company_name, url の2列に正規化する。

curl/wget は環境のdenyで封印されているため、標準ライブラリ urllib で取得する。

使い方:
    python scripts/fetch_sheet.py "<シートURL>" <out_norm.csv>
    python scripts/fetch_sheet.py "<シートURL>" <out_norm.csv> --company-col 会社名 --url-col URL

出力: company_name, url の統一スキーマCSV（このあと extract_contact_pages.py が contact_url を足す）
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

# 列の自動検出に使う手掛かり（ヘッダ名に含まれていれば候補）
URL_HEADER_HINTS = ["url", " url", "リンク", "サイト", "ホームページ", "hp", "ＨＰ", "web", "ＵＲＬ"]
NAME_HEADER_HINTS = ["会社", "企業", "事業者", "店舗", "屋号", "名称", "社名", "company", "name", "会社名"]


def to_csv_export_url(sheet_url: str) -> str:
    """シートの編集URL/共有URLを CSVエクスポートURL に変換する。gid（タブ）も引き継ぐ。"""
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", sheet_url)
    if not m:
        # 既にエクスポートURL or 生のIDが渡された場合のフォールバック
        if sheet_url.startswith("http"):
            return sheet_url
        return f"https://docs.google.com/spreadsheets/d/{sheet_url}/export?format=csv"
    sheet_id = m.group(1)
    gm = re.search(r"[#&?]gid=([0-9]+)", sheet_url)
    base = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    return f"{base}&gid={gm.group(1)}" if gm else base


def download_csv_text(sheet_url: str) -> str:
    """エクスポートURLからCSV本文を取得。公開されていなければ分かりやすく失敗させる。"""
    export_url = to_csv_export_url(sheet_url)
    req = urllib.request.Request(export_url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            ctype = resp.headers.get("Content-Type", "")
            raw = resp.read()
    except Exception as e:  # noqa: BLE001
        print(f"[エラー] シートを取得できませんでした: {e}", file=sys.stderr)
        print("  → シートが『リンクを知っている全員が閲覧可』になっているか確認してください。", file=sys.stderr)
        raise SystemExit(2)
    # 非公開シートはログインHTMLが返る（CSVではない）
    if "text/html" in ctype:
        print("[エラ] シートが公開されていません（ログインページが返りました）。", file=sys.stderr)
        print("  → 共有設定を『リンクを知っている全員が閲覧可』にしてから再実行してください。", file=sys.stderr)
        raise SystemExit(2)
    return raw.decode("utf-8-sig", errors="replace")


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def detect_columns(headers: list[str], rows: list[list[str]],
                   company_col: str | None, url_col: str | None) -> tuple[int, int]:
    """会社名列とURL列のインデックスを返す。明示指定 > ヘッダ手掛かり > 値パターン の順。"""
    lower = [_norm(h) for h in headers]

    def find_by_name(name: str) -> int:
        target = _norm(name)
        for i, h in enumerate(lower):
            if h == target:
                return i
        for i, h in enumerate(lower):
            if target in h:
                return i
        print(f"[エラー] 指定された列 '{name}' が見つかりません。ヘッダ: {headers}", file=sys.stderr)
        raise SystemExit(2)

    # URL列: 明示 → ヘッダ手掛かり → 値が http で始まる割合が最大の列
    if url_col:
        url_idx = find_by_name(url_col)
    else:
        url_idx = next((i for i, h in enumerate(lower) if any(k in h for k in URL_HEADER_HINTS)), -1)
        if url_idx < 0:
            best, best_score = -1, 0.0
            ncols = len(headers)
            for i in range(ncols):
                vals = [r[i] for r in rows if i < len(r)]
                if not vals:
                    continue
                score = sum(1 for v in vals if v.strip().lower().startswith("http")) / len(vals)
                if score > best_score:
                    best, best_score = i, score
            if best_score >= 0.5:
                url_idx = best
        if url_idx < 0:
            print(f"[エラー] URL列を自動検出できませんでした。--url-col で指定してください。ヘッダ: {headers}",
                  file=sys.stderr)
            raise SystemExit(2)

    # 会社名列: 明示 → ヘッダ手掛かり → URL列以外の最初のテキスト列
    if company_col:
        name_idx = find_by_name(company_col)
    else:
        name_idx = next((i for i, h in enumerate(lower)
                         if i != url_idx and any(k in h for k in NAME_HEADER_HINTS)), -1)
        if name_idx < 0:
            name_idx = next((i for i in range(len(headers)) if i != url_idx), -1)
        if name_idx < 0:
            print(f"[エラー] 会社名列を特定できませんでした。--company-col で指定してください。ヘッダ: {headers}",
                  file=sys.stderr)
            raise SystemExit(2)

    return name_idx, url_idx


def main() -> None:
    ap = argparse.ArgumentParser(description="閲覧公開シートURL → 統一スキーマCSV(company_name,url)")
    ap.add_argument("sheet_url", help="GoogleスプレッドシートのURL（閲覧公開）")
    ap.add_argument("output", help="出力CSV（company_name, url）")
    ap.add_argument("--company-col", default=None, help="会社名のヘッダ名（既定: 自動検出）")
    ap.add_argument("--url-col", default=None, help="URLのヘッダ名（既定: 自動検出）")
    args = ap.parse_args()

    text = download_csv_text(args.sheet_url)
    table = list(csv.reader(io.StringIO(text)))
    if not table:
        print("[エラー] シートが空です。", file=sys.stderr)
        raise SystemExit(2)

    headers, data = table[0], table[1:]
    name_idx, url_idx = detect_columns(headers, data, args.company_col, args.url_col)
    print(f"列検出: 会社名='{headers[name_idx]}'(列{name_idx + 1}) / URL='{headers[url_idx]}'(列{url_idx + 1})")

    kept, skipped = 0, 0
    with open(args.output, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["company_name", "url"])
        for r in data:
            name = r[name_idx].strip() if name_idx < len(r) else ""
            url = r[url_idx].strip() if url_idx < len(r) else ""
            if not url.lower().startswith("http"):
                skipped += 1
                continue
            w.writerow([name, url])
            kept += 1

    print(f"正規化完了: {kept}件を {args.output} に書き出し（URL欠落でスキップ {skipped}件）。")


if __name__ == "__main__":
    main()
