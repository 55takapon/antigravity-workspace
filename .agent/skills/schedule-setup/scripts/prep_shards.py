#!/usr/bin/env python3
"""prep_shards.py — 並列prep（リスト収集）の「都市」シャード割当（決定論・AIなし）。

親オーケストレータ kick_prep_parallel.sh が最初に1回だけ呼ぶ。全国の主要都市プールから
その日に担当する N 都市を決めて worker 仕様を吐く。各 worker（子）は**1都市だけ**を
担当し、自分専用CSVに集める（シートには触らない）。

★狙い（供給の枯渇対策）:
  同じ criteria を N 本で並列に回すと、同じ枯れたクエリ空間を取り合って重複が増えるだけ。
  そこで **6並列＝6つの別都市**に散らし、探索面（地理）そのものを割る。さらに **日替わり
  ローテーション**で毎日ちがう都市群を当てる（15都市を N=6 で回すと約5日で全国一巡）。
  除外リスト/既存シート/提携先との重複で目減りしても、都市を分散させれば新規の純増を稼げる。

決定論: 乱数を使わず、基準日（既定=本日）から回転オフセットを決める。テストは --today で固定。

使い方:
  python3 prep_shards.py --count 200 --shards 6 --workdir /tmp/prep_run \
      --criteria "求人媒体から今 求人を出しているWeb制作・Webマーケ会社を自社採用ページ経由で収集" \
      --out /tmp/prep_run/shards.json
  python3 prep_shards.py --selftest

出力（--out。省略時は stdout）: worker 仕様の JSON
  {"date": "2026-07-21", "city_pool": 15, "shards": 6, "count": 200,
   "workers": [{"i": 1, "city": "札幌", "count": 34,
                "out_csv": "<workdir>/worker_1.csv",
                "criteria": "<base>", "scope": "札幌"}], ...}
列や追記は一切しない（純粋に割当の計算だけ）。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

# 都市プール（拡張＝供給拡大＆ローテ周期↑。--cities で上書き可）。
# 全国の地方ブロックに散らし、都市間の重複（同一商圏）を最小化する。15都市。
DEFAULT_CITIES = [
    "札幌", "仙台", "東京", "横浜", "名古屋", "金沢", "京都", "大阪",
    "神戸", "岡山", "広島", "高松", "福岡", "熊本", "那覇",
]


def rotation_offset(d: date, n: int, total: int) -> int:
    """基準日から、その日に使う都市群の開始オフセットを決める（決定論の日替わり回転）。
    1日ごとに n だけ進めるので、都市を日替わりで入れ替えつつ全体を巡回する。"""
    if total <= 0:
        return 0
    return (d.timetuple().tm_yday * n) % total


def pick_items(items: list[str], n: int, offset: int) -> list[str]:
    """offset から n 個を、末尾で先頭へ回り込みつつ選ぶ（重複なしで最大 total 個）。"""
    total = len(items)
    if total == 0 or n <= 0:
        return []
    n = min(n, total)
    return [items[(offset + k) % total] for k in range(n)]


def split_count(total_count: int, n: int) -> list[int]:
    """総件数を n シャードへ按分する。余りは先頭のシャードから1件ずつ配る。"""
    if n <= 0:
        return []
    base, rem = divmod(max(0, total_count), n)
    return [base + (1 if k < rem else 0) for k in range(n)]


def build_workers(*, count: int, shards: int, workdir: str, criteria: str,
                  today: date, cities: list[str], slot: int = 0, slots_per_day: int = 3) -> dict:
    total = len(cities)
    # 日付で基準窓を決め、その日の実行スロット(0=朝/1=昼/2=夕)ごとに都市窓をずらす。
    # ずらし幅は total/slots_per_day（例 15都市/3回=5）＝3回の窓を全周へ均等分散し、
    # 1回目と3回目がほぼ同じ都市になる（N ずらしの弊害）のを避ける。
    slot_shift = slot * max(1, total // max(1, slots_per_day))
    off = (rotation_offset(today, shards, total) + slot_shift) % total if total else 0
    chosen = pick_items(cities, shards, off)
    counts = split_count(count, len(chosen))
    wd = Path(workdir)
    workers = []
    for i, (city, cnt) in enumerate(zip(chosen, counts), start=1):
        workers.append({
            "i": i,
            "city": city,
            "count": cnt,
            "out_csv": str(wd / f"worker_{i}.csv"),
            "criteria": criteria,
            "scope": city,
        })
    return {
        "date": today.isoformat(),
        "slot": slot,
        "city_pool": total,
        "rotation_offset": off,
        "shards": len(chosen),
        "count": count,
        "workers": workers,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="並列prepの都市シャード割当（決定論・6並列=6都市）")
    ap.add_argument("--count", type=int, default=200, help="総収集目標件数（全シャード合計）")
    ap.add_argument("--shards", type=int, default=6, help="並列シャード数N（=その日に使う都市数）")
    ap.add_argument("--workdir", default=".", help="worker CSV の出力ディレクトリ")
    ap.add_argument("--criteria", default="", help="ベース収集条件（各子に渡す共通文）")
    ap.add_argument("--cities", default=None, help="都市一覧（カンマ区切り。既定=全国15都市）")
    ap.add_argument("--today", default=None, help="基準日 YYYY-MM-DD（省略時は本日・回転の固定用）")
    ap.add_argument("--slot", type=int, default=None,
                    help="実行スロット(0=朝/1=昼/2=夕。省略時は現在時刻から判定＝1日3回で別都市)")
    ap.add_argument("--out", default=None, help="出力JSONパス（省略時 stdout）")
    ap.add_argument("--selftest", action="store_true", help="決定論ロジックの自己テスト")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    cities = [c.strip() for c in args.cities.split(",") if c.strip()] if args.cities else DEFAULT_CITIES
    today = date.fromisoformat(args.today) if args.today else date.today()
    # スロット: 明示 --slot 優先。無ければ現在時刻から 0(〜12時)/1(〜16時)/2(それ以降) を判定。
    if args.slot is not None:
        slot = args.slot
    else:
        hr = datetime.now().hour
        slot = 0 if hr < 12 else (1 if hr < 16 else 2)

    result = build_workers(count=args.count, shards=args.shards, workdir=args.workdir,
                           criteria=args.criteria, today=today, cities=cities, slot=slot)

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        picks = " / ".join(f"{w['city']}({w['count']})" for w in result["workers"])
        print(f"[prep_shards] {result['date']} slot{result['slot']} 割当 {result['shards']}都市: {picks}", file=sys.stderr)
        print(f"[prep_shards] out={args.out}", file=sys.stderr)
    else:
        print(text)
    return 0


# ---------------------------------------------------------------- 自己テスト
def _selftest() -> int:
    ok = True

    def check(name, got, exp):
        nonlocal ok
        st = "OK " if got == exp else "NG "
        if got != exp:
            ok = False
        print(f"[{st}] {name}: got={got} exp={exp}")

    # 按分: 余りは先頭から
    check("split_count(200,6)", split_count(200, 6), [34, 34, 33, 33, 33, 33])
    check("split_count(20,6)", split_count(20, 6), [4, 4, 3, 3, 3, 3])
    check("split_count(6,3)", split_count(6, 3), [2, 2, 2])

    check("都市プール数", len(DEFAULT_CITIES), 15)
    check("都市の重複なし", len(set(DEFAULT_CITIES)), 15)

    # 回り込み選択: offset=13, n=6 → 13,14,0,1,2,3
    picked = pick_items(DEFAULT_CITIES, 6, 13)
    check("pick 回り込み先頭", picked[0], DEFAULT_CITIES[13])
    check("pick 回り込み折返し", picked[2], DEFAULT_CITIES[0])
    check("pick 個数", len(picked), 6)
    check("pick 重複なし（同日内は全都市バラバラ）", len(set(picked)), 6)

    # 日替わりローテ: 15都市/N=6 は5日で全都市を網羅（start offsets: 0,6,12,3,9 の周期5）
    seen = set()
    for dd in range(5):
        d = date(2026, 1, 1 + dd)  # tm_yday = 1..5
        off = rotation_offset(d, 6, 15)
        for c in pick_items(DEFAULT_CITIES, 6, off):
            seen.add(c)
    check("5日で全15都市を網羅", len(seen), 15)

    # rotation は決定論
    check("rotation決定論", rotation_offset(date(2026, 7, 21), 6, 15),
          rotation_offset(date(2026, 7, 21), 6, 15))

    # build_workers の形と不変条件
    r = build_workers(count=200, shards=6, workdir="/tmp/x", criteria="C",
                      today=date(2026, 7, 21), cities=DEFAULT_CITIES)
    check("workers数", len(r["workers"]), 6)
    check("count合計=200", sum(w["count"] for w in r["workers"]), 200)
    check("out_csv一意", len({w["out_csv"] for w in r["workers"]}), 6)
    check("6ワーカーは6つの別都市", len({w["city"] for w in r["workers"]}), 6)
    check("scope=city", r["workers"][0]["scope"], r["workers"][0]["city"])

    # slot: 同日の3回(0/1/2)は別の都市窓（N=8都市ずつずらす）＝日中の重複取りを避ける
    d0 = date(2026, 7, 21)
    sets = []
    for sl in (0, 1, 2):
        w = build_workers(count=300, shards=8, workdir="/tmp/x", criteria="C",
                          today=d0, cities=DEFAULT_CITIES, slot=sl)
        sets.append(frozenset(x["city"] for x in w["workers"]))
        check(f"slot{sl}は8都市", len(w["workers"]), 8)
    check("slot0とslot1で都市窓が異なる", sets[0] != sets[1], True)
    check("slot1とslot2で都市窓が異なる", sets[1] != sets[2], True)
    check("3スロットの和集合が全15都市を網羅", len(sets[0] | sets[1] | sets[2]), 15)
    check("slot決定論", build_workers(count=300, shards=8, workdir="/tmp/x", criteria="C",
                                    today=d0, cities=DEFAULT_CITIES, slot=1)["rotation_offset"],
          build_workers(count=300, shards=8, workdir="/tmp/x", criteria="C",
                        today=d0, cities=DEFAULT_CITIES, slot=1)["rotation_offset"])

    # shards が都市数を超えても total で頭打ち（重複ゼロ）
    r2 = build_workers(count=100, shards=99, workdir="/tmp/x", criteria="C",
                       today=date(2026, 7, 21), cities=DEFAULT_CITIES)
    check("shards>都市数 は頭打ち", r2["shards"], 15)
    check("上限時も件数合計保存", sum(w["count"] for w in r2["workers"]), 100)

    print("=== prep_shards selftest:", "PASS" if ok else "FAIL", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
