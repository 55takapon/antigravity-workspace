#!/usr/bin/env python3
"""無人並列 Tier B 送信の担当リスト（worker{i}.json）を決定論で作る。

2つのモード:
  1) 既定（未送信モード）: status が空の送信可能行を先頭から cap 件取る。
  2) --from-queue <tier_b_queue.jsonl>: **Tier A が送れなかった残余だけ**を担当にする（2フェーズ運用）。
     Phase1 で run_on_sheet.py（Tier A＝HTTP POST＋パターンマッチ）を回すと、送れなかった社が
     tier_b_queue に出る。それをこのモードで読み、シート上の該当行（social名＋contact_url一致・status=failed）
     に対応づけて担当にする。＝AIブラウザ(Tier B)は「Tier Aで無理だった社」だけを処理する。

どちらのモードも **正規化 contact_url で重複排除**（同一送信先は1社だけ・二重送信防止）。

usage:
    python tierb_shards.py <sheet_key> <total_cap> <n_workers> <out_dir> [--from-queue <file>]

各 worker JSON: [{"row": int, "company": str, "contact_url": str, "message": str}, ...]
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parents[3]
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(REPO_ROOT / "shared"))
import sheets_io  # noqa: E402

JST = timezone(timedelta(hours=9))


def _norm_url(u: str) -> str:
    u = (u or "").strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def _mark_dups(ws, dup_rows: list[tuple[int, str, str]]) -> None:
    """重複行にシートで skipped/duplicate を記録（best-effort・送信対象からの除外は別途有効）。"""
    if not dup_rows:
        return
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
    ja = {"duplicate_already_processed": "重複（同一送信先が既に処理済み）",
          "duplicate_in_batch": "重複（同一送信先が同一バッチ内に複数）"}
    for (i, _c, reason) in dup_rows:
        try:
            ws.update(range_name=f"H{i}:L{i}", values=[[now, "skipped", ja.get(reason, reason), "", "dedupe"]])
        except TypeError:
            ws.update(f"H{i}:L{i}", [[now, "skipped", ja.get(reason, reason), "", "dedupe"]])
        except Exception as e:  # noqa: BLE001
            print(f"[warn] dup row{i} の記録に失敗（除外は有効）: {e}", file=sys.stderr)
    print(f"重複除外: {len(dup_rows)}件を skipped/duplicate に記録 rows={[d[0] for d in dup_rows]}")


def pick_unsent(ws, rows) -> list[dict]:
    """status 空の送信可能行を、既処理送信先・重複を除外して返す。"""
    processed = set()
    for r in rows:
        if str(r.get("status") or "").strip():
            k = _norm_url(r.get("contact_url") or r.get("url"))
            if k:
                processed.add(k)
    seen, out, dups = set(), [], []
    for i, r in enumerate(rows, start=2):
        if str(r.get("status") or "").strip():
            continue
        comp = str(r.get("company_name") or "").strip()
        tgt = str(r.get("contact_url") or r.get("url") or "").strip()
        msg = str(r.get("message") or "").strip()
        if not (comp and tgt and msg):
            continue
        k = _norm_url(tgt)
        if k in processed:
            dups.append((i, comp, "duplicate_already_processed")); continue
        if k in seen:
            dups.append((i, comp, "duplicate_in_batch")); continue
        seen.add(k)
        out.append({"row": i, "company": comp, "contact_url": tgt, "message": msg})
    _mark_dups(ws, dups)
    return out


def pick_from_queue(ws, rows, queue_path: Path) -> list[dict]:
    """Tier A の tier_b_queue（送れなかった残余）を、シート上の failed 行に対応づけて返す。"""
    entries = []
    for ln in queue_path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            try:
                entries.append(json.loads(ln))
            except Exception:
                pass
    # シート側の (社名, 正規化contact_url) → (row, status) 索引
    idx = {}
    for i, r in enumerate(rows, start=2):
        comp = str(r.get("company_name") or "").strip()
        k = _norm_url(r.get("contact_url") or r.get("url"))
        idx[(comp, k)] = (i, str(r.get("status") or "").strip().lower())
    seen, out, missing = set(), [], 0
    for e in entries:
        comp = str(e.get("company_name") or "").strip()
        tgt = str(e.get("contact_url") or e.get("url") or "").strip()
        msg = str(e.get("message") or "").strip()
        k = _norm_url(tgt)
        hit = idx.get((comp, k))
        if not (comp and tgt and msg and hit):
            missing += 1; continue
        row, st = hit
        if st not in ("failed", ""):  # Tier A が failed にした行だけ Tier B で再挑戦（completed等は触らない）
            continue
        if k in seen:
            continue
        seen.add(k)
        out.append({"row": row, "company": comp, "contact_url": tgt, "message": msg})
    if missing:
        print(f"[warn] queue {missing}件はシート行に対応づけできず除外", file=sys.stderr)
    return out


def main() -> int:
    args = [a for a in sys.argv[1:]]
    queue_path = None
    if "--from-queue" in args:
        qi = args.index("--from-queue")
        queue_path = Path(args[qi + 1])
        del args[qi:qi + 2]
    if len(args) < 4:
        print("usage: tierb_shards.py <sheet_key> <total_cap> <n_workers> <out_dir> [--from-queue <file>]",
              file=sys.stderr)
        return 1
    sheet_key, total_cap_s, n_s, out_dir_s = args[:4]
    total_cap, n = int(total_cap_s), max(1, int(n_s))
    out_dir = Path(out_dir_s)
    out_dir.mkdir(parents=True, exist_ok=True)

    ws = sheets_io.open_worksheet(sheet_key, None)
    rows = sheets_io.read_rows(ws, want=["company_name", "url", "contact_url", "message", "status"])

    if queue_path is not None:
        picked_all = pick_from_queue(ws, rows, queue_path)
        label = "Tier A残余(from-queue)"
    else:
        picked_all = pick_unsent(ws, rows)
        label = "未送信"

    picked = picked_all[: max(0, total_cap)] if total_cap > 0 else picked_all
    shards: list[list] = [[] for _ in range(n)]
    for idx2, item in enumerate(picked):
        shards[idx2 % n].append(item)

    for w in range(n):
        p = out_dir / f"worker{w + 1}.json"
        p.write_text(json.dumps(shards[w], ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"worker{w + 1}.json: {len(shards[w])}件 rows={[x['row'] for x in shards[w]]}")
    print(f"合計 {len(picked)}件 を {n} ワーカーへ分割（{label} {len(picked_all)}件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
