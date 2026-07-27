#!/usr/bin/env python3
"""aggregate_csv — ⑥result-review の配布側スクリプト（非秘匿・stdライブラリのみ・0トークン）。

役割は2つだけ:
  1) ④結果CSVの status / error_reason / provider_used を「集計」する（生の行はローカルから出さない）。
  2) ユーザー入力の指標(metrics)と合わせて JSON を1つ標準出力に吐く。

診断そのもの（しきい値・判定規則・改善アドバイス）はこのスクリプトには無い。
出力JSONを opener-core の MCP ツール `review_diagnose` に渡して findings を得る（SKILL.md 参照）。

使い方:
    python3 scripts/aggregate_csv.py [result.csv] \
        --sent 350 --views 38 --view-page achievement --replies 3 --meetings 1 --contracts 0
    # CSVは任意（口頭モードは省略可）。1指標だけ即判定したいとき:
    python3 scripts/aggregate_csv.py --classify reply --sent 350 --value 3
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

# ④が status に入れる値（core/_general_form_sender.py 由来）
SUCCESS_STATUSES = {"completed", "ok"}
SKIP_STATUSES = {"skipped"}


def aggregate_csv(csv_path: Path) -> dict:
    """結果CSVを集計。status / error_reason / provider_used の内訳を返す（生の行は出さない）。"""
    rows = 0
    status_counts: dict[str, int] = {}
    error_counts: dict[str, int] = {}
    provider_counts: dict[str, int] = {}
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = {c.strip().lstrip("﻿"): c for c in (reader.fieldnames or [])}
        c_status = cols.get("status")
        c_error = cols.get("error_reason")
        c_prov = cols.get("provider_used")
        for r in reader:
            rows += 1
            if c_status:
                st = (r.get(c_status) or "").strip() or "(空)"
                status_counts[st] = status_counts.get(st, 0) + 1
            if c_error:
                er = (r.get(c_error) or "").strip()
                if er:
                    key = er.split(":", 1)[0]  # ":詳細" は畳んで代表理由でまとめる
                    error_counts[key] = error_counts.get(key, 0) + 1
            if c_prov:
                pv = (r.get(c_prov) or "").strip() or "(空)"
                provider_counts[pv] = provider_counts.get(pv, 0) + 1
    attempted = sum(v for k, v in status_counts.items() if k not in SKIP_STATUSES and k != "(空)")
    success = sum(v for k, v in status_counts.items() if k in SUCCESS_STATUSES)
    return {
        "rows": rows,
        "status": status_counts,
        "errors": error_counts,
        "providers": provider_counts,
        "attempted": attempted,
        "success": success,
        "has_status": c_status is not None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="④結果CSVを集計し、指標と合わせて review_diagnose 用のJSONを吐く")
    ap.add_argument("csv", nargs="?", default=None, help="④form-send の結果CSV（任意・口頭モードは省略可）")
    ap.add_argument("--classify", choices=["reply", "link"], default=None, help="1指標だけ即判定するとき")
    ap.add_argument("--value", type=float, default=None, help="--classify の対象値（reply=返信数 / link=閲覧数）")
    ap.add_argument("--sent", type=int, default=None)
    ap.add_argument("--views", type=int, default=None, help="資料閲覧数")
    ap.add_argument("--view-rate", type=float, default=None, help="資料閲覧率（10 や 0.10 のどちらでも可）")
    ap.add_argument("--view-page", choices=["achievement", "own_site"], default=None,
                    help="閲覧先ページ種別。achievement=実績直載せ / own_site=自社サイト（既定 achievement）")
    ap.add_argument("--replies", type=int, default=None)
    ap.add_argument("--meetings", type=int, default=None)
    ap.add_argument("--contracts", type=int, default=None)
    ap.add_argument("--metrics", default=None, help="指標をまとめたJSON（個別フラグが優先）")
    args = ap.parse_args()

    metrics: dict = {}
    if args.metrics:
        metrics.update(json.loads(Path(args.metrics).read_text(encoding="utf-8")))
    for k in ("sent", "views", "replies", "meetings", "contracts"):
        v = getattr(args, k)
        if v is not None:
            metrics[k] = v
    if args.value is not None:
        metrics["value"] = args.value
    if args.view_rate is not None:
        metrics["view_rate"] = args.view_rate  # 正規化(>1→百分率)はサーバー側で行う
    if args.view_page is not None:
        metrics["view_page"] = args.view_page

    agg = None
    if args.csv:
        csv_path = Path(args.csv)
        if not csv_path.exists():
            print(f"[エラー] CSVが無い: {csv_path}", file=sys.stderr)
            return 2
        agg = aggregate_csv(csv_path)

    out = {"agg": agg, "metrics": metrics, "classify": args.classify}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
