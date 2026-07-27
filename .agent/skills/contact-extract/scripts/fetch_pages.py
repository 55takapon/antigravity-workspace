#!/usr/bin/env python3
"""fetch_pages.py — ②contact-extract の薄いローカルfetch層（検出ロジックを持たない）。

統一CSV（url列）を読み、各社HPを取得して <a> リンクを {href,text,alt_title} に整形した
バッチJSONを出力する。**問い合わせページの判定はしない**（判定は秘匿コア＝MCP contact_detect の役割）。
ここは「取得して素材を整えるだけ」の汎用処理なので、見られても価値が無い＝ローカルに置いてよい。

出力JSON: [ {"idx":0, "base_url":"https://...", "links":[{"href","text","alt_title"}...]}, ... ]
  idx は入力CSVの行順（0始まり）。後段 write_contacts.py が同じ idx で書き戻す。

使い方:
    python scripts/fetch_pages.py <in_unified.csv> <out_pages.json> [--workers N] [--limit N]
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import sys
import warnings

import requests
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)
UA_FALLBACK = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)


def _headers(ua: str = UA) -> dict:
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def _fetch(url: str):
    res = requests.get(url, headers=_headers(), timeout=15, verify=False)
    if res.status_code in (403, 406, 429):
        res = requests.get(url, headers=_headers(UA_FALLBACK), timeout=15, verify=False)
    return res


def extract_links(url: str) -> dict:
    """HP url から全 <a> を素材化。判定はしない（誤爆云々は contact_detect 側の責務）。"""
    url = (url or "").strip()
    out = {"base_url": url, "links": []}
    if not url.startswith("http"):
        return out
    try:
        res = _fetch(url)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        for link in soup.find_all("a", href=True):
            alt_title = ""
            for tag in link.find_all(True):
                alt_title += (tag.get("alt") or "") + (tag.get("title") or "")
            out["links"].append({
                "href": link["href"],
                "text": link.get_text().strip(),
                "alt_title": alt_title,
            })
    except Exception:
        pass  # Fail-safe: 取得失敗は links 空で返す（後段が method=none 扱い）
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="統一CSVの url 列 → 各社HPの<a>素材バッチJSON")
    ap.add_argument("input", help="入力CSV（統一スキーマ: url 列を含む）")
    ap.add_argument("output", help="出力JSON（contact_detect に渡すバッチ）")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    with open(args.input, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "url" not in reader.fieldnames:
            print(f"エラー: 'url' 列がありません（{getattr(reader,'fieldnames',None)}）", file=sys.stderr)
            return 1
        rows = list(reader)
    if args.limit is not None:
        rows = rows[: args.limit]

    pages = [None] * len(rows)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut = {ex.submit(extract_links, r.get("url", "")): i for i, r in enumerate(rows)}
        for f in concurrent.futures.as_completed(fut):
            i = fut[f]
            try:
                d = f.result()
            except Exception:
                d = {"base_url": rows[i].get("url", ""), "links": []}
            pages[i] = {"idx": i, **d}

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False)
    print(f"[fetch_pages] {len(pages)} 社ぶんの素材を {args.output} に出力（MCP contact_detect へ渡す）",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
