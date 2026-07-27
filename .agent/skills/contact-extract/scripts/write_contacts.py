#!/usr/bin/env python3
"""write_contacts.py — ②contact-extract の薄いローカル書き戻し層（判定ロジックを持たない）。

入力: 統一CSV ＋ MCP contact_detect の結果JSON。
処理:
  - method="link"   → contact_url をそのまま採用。
  - method="probe"  → サーバーが返した probe_candidates をローカルで HEAD/GET 実在確認し、
                      200 かつ最終URLが問い合わせ系トークンを含む先頭を採用（この確認は汎用・低IP）。
  - それ以外/未検出 → 空（Fail-safe）。
出力: 入力CSVに contact_url 列を足したCSV（既存列は保持）。

検出の勘所（キーワード群・ランキング・共通パス集合）は持たない＝秘匿コアは MCP 側に閉じている。

使い方:
    python scripts/write_contacts.py <in_unified.csv> <detect_results.json> <out.csv> [--workers N]

detect_results.json は MCP contact_detect の戻り（{"version","results":[...]}）そのもの、
または results 配列だけでも可。idx で入力CSV行に対応づける。
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import sys
import warnings

import requests

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)
# probe 実在確認の“問い合わせ系”判定に使う汎用トークン（候補URLに既に含まれる語＝低IP）。
PROBE_TOKENS = ("contact", "inquiry", "toiawase", "mailform")
# リダイレクト後の最終URLがこれらを含む＝送信完了/サンクスページ（フォームが無い）。採用しない。
# フォームページ→サンクスへのリダイレクトを拾い、送信不能な contact_url を確定する誤検出を防ぐ。
_THANKS_TOKENS = ("thanks", "thankyou", "thank-you", "thank_you", "complete", "finish",
                  "sent", "done", "kanryo")


def _headers() -> dict:
    return {"User-Agent": UA, "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"}


def probe(candidates: list[str]) -> str:
    """候補URL群を HEAD→GET で実在確認。200かつ最終URLが問い合わせ系なら採用。"""
    for url in candidates or []:
        for method in (requests.head, requests.get):
            try:
                r = method(url, headers=_headers(), timeout=6, verify=False, allow_redirects=True)
                final = r.url.lower()
                if (r.status_code == 200
                        and any(t in final for t in PROBE_TOKENS)
                        and not any(t in final for t in _THANKS_TOKENS)):
                    return r.url
                if r.status_code not in (405, 403, 406):
                    break
            except Exception:
                continue
    return ""


def load_results(path: str) -> dict:
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, list):
        return {r.get("idx", i): r for i, r in enumerate(data)}
    return {r.get("idx", i): r for i, r in enumerate(data.get("results", []))}


def main() -> int:
    ap = argparse.ArgumentParser(description="contact_detect 結果を統一CSVに書き戻す（probeはローカル確認）")
    ap.add_argument("input", help="入力CSV（統一スキーマ）")
    ap.add_argument("results", help="MCP contact_detect の結果JSON")
    ap.add_argument("output", help="出力CSV（contact_url 追加）")
    ap.add_argument("--workers", type=int, default=10)
    args = ap.parse_args()

    with open(args.input, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    if "contact_url" not in fieldnames:
        fieldnames.append("contact_url")

    by_idx = load_results(args.results)
    contact = [""] * len(rows)
    probe_jobs = {}  # idx -> candidates

    for i in range(len(rows)):
        r = by_idx.get(i)
        if not r:
            continue
        if r.get("method") == "link" and r.get("contact_url"):
            contact[i] = r["contact_url"]
        elif r.get("method") == "probe":
            probe_jobs[i] = r.get("probe_candidates", [])

    # probe 確認は並列（ネットワーク＝ローカルで実行）
    if probe_jobs:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
            fut = {ex.submit(probe, c): i for i, c in probe_jobs.items()}
            for f in concurrent.futures.as_completed(fut):
                i = fut[f]
                try:
                    contact[i] = f.result()
                except Exception:
                    contact[i] = ""

    found = 0
    with open(args.output, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for i, row in enumerate(rows):
            row["contact_url"] = contact[i]
            if contact[i]:
                found += 1
            w.writerow(row)

    print(f"[write_contacts] 成功 {found}/{len(rows)} 件 → {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
