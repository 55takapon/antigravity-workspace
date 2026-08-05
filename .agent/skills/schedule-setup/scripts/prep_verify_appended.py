#!/usr/bin/env python3
"""prep_verify_appended.py — リスト取りで「今回 追記された行」だけを後から検証する門番。

なぜ:
  1本で順に処理する経路（＝並列を使わない既定の経路）では、送ってはいけない先の除外を
  収集AI自身が行っている。ところが安いモデルはこの手順を黙って飛ばすことがあり、実際に
  2026-08-04、営業をお断りしている会社が3社シートへ混入した（並列側は親が最後にまとめて
  照合するため防げた）。
  そこで1本経路でも「収集が終わったあとに、増えた行だけをまとめて1回照合する」門番を置く。
  照合そのものは呼び出し側（kick 殻）が短い会話で1回だけ行い、本スクリプトは
  その前後（増えた行の切り出し／結果の反映）を決定論で担当する。

  ★増えた行だけを見るので、シートが何千行あっても検証コストは一定。

モード:
  snapshot <sheet_key> --out state.json          収集前の行数を記録
  export   <sheet_key> --state state.json --out cands.json
                                                 収集後、増えた行を候補として書き出す
  apply    <sheet_key> --state state.json [--filter-result f.json]
                       [--unverified-status 要確認]
                                                 照合結果を反映（営業不可を削除・statusを付与）。
                                                 照合結果が無い/壊れている場合は増えた行へ
                                                 --unverified-status を付ける（④自動送信の対象外）。
  --selftest                                     シート不要の純ロジックテスト
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[3]
sys.path.insert(0, str(REPO_ROOT / "shared"))
sys.path.insert(0, str(SCRIPT_DIR))
import exclude_filter as ef  # noqa: E402
import prep_merge_append as pm  # noqa: E402  照合結果のほぐし方は1箇所に集約する

STATUS_ALIASES = {"status": ["status", "ステータス", "状態", "ステータス（送信結果）"]}


def _open(sheet: str, worksheet: str | None, creds: str | None):
    import sheets_io
    client = sheets_io.get_client(creds)
    sh = client.open_by_url(sheet) if sheet.startswith("http") else client.open_by_key(sheet)
    ws = sh.worksheet(worksheet) if worksheet else sh.sheet1
    return sheets_io, sh, ws


def _read(sheets_io, ws) -> list[dict]:
    return sheets_io.read_rows(ws, want=["company_name", "url", "phone", "status"],
                               aliases=STATUS_ALIASES)


def pick_new_rows(rows: list[dict], before: int) -> list[dict]:
    """収集前の行数 before を基準に「増えた行」を返す（追記は末尾に積まれる前提）。
    行が減っていた場合（人が消した等）は安全側に倒して空を返す＝誤って既存行を消さない。"""
    if before < 0 or len(rows) <= before:
        return []
    return rows[before:]


# ---------------------------------------------------------------- モード
def cmd_snapshot(args) -> int:
    sheets_io, _sh, ws = _open(args.spreadsheet, args.worksheet, args.creds)
    n = len(_read(sheets_io, ws))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({"rows": n, "worksheet": ws.title}, ensure_ascii=False),
                              encoding="utf-8")
    print(f"[verify] 収集前スナップショット: {ws.title} = {n}行 -> {args.out}", file=sys.stderr)
    return 0


def cmd_export(args) -> int:
    state = json.loads(Path(args.state).read_text(encoding="utf-8"))
    sheets_io, _sh, ws = _open(args.spreadsheet, args.worksheet or state.get("worksheet"), args.creds)
    rows = _read(sheets_io, ws)
    new = pick_new_rows(rows, int(state.get("rows", -1)))
    cands = [{"company_name": r.get("company_name", ""), "url": r.get("url", ""),
              "phone": r.get("phone", "")} for r in new if (r.get("url") or "").strip()]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(cands, ensure_ascii=False), encoding="utf-8")
    print(f"[verify] 今回増えた行: {len(new)}（うちURL有り {len(cands)}）-> {args.out}", file=sys.stderr)
    return 0 if cands else 3   # 3 = 検証対象なし（呼び出し側は照合をスキップしてよい）


def cmd_apply(args) -> int:
    state = json.loads(Path(args.state).read_text(encoding="utf-8"))
    sheets_io, _sh, ws = _open(args.spreadsheet, args.worksheet or state.get("worksheet"), args.creds)
    rows = _read(sheets_io, ws)
    new = pick_new_rows(rows, int(state.get("rows", -1)))
    if not new:
        print("[verify] 今回増えた行なし。何もしない。", file=sys.stderr)
        return 0

    dropped, status_by_dom = set(), {}
    ok = False
    if args.filter_result and Path(args.filter_result).exists():
        try:
            dropped, status_by_dom, fstats = pm.load_filter_result(args.filter_result)
            ok = True
            print(f"[verify] 照合結果を読込: server_stats={fstats}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"[verify] 🔴 照合結果が読めない: {e}", file=sys.stderr)

    del_rows, set_status = [], []
    for r in new:
        d = ef.norm_domain(r.get("url", "") or "")
        cur = (r.get("status") or "").strip()
        if ok and d and d in dropped:
            del_rows.append(r["_row"])
            continue
        if ok and d in status_by_dom and not cur:
            set_status.append({"_row": r["_row"], "status": status_by_dom[d]})
        elif not ok and args.unverified_status and not cur:
            set_status.append({"_row": r["_row"], "status": args.unverified_status})

    if args.preview:
        print(f"[verify] プレビュー: 削除 {len(del_rows)}行 / status付与 {len(set_status)}行"
              f"（照合={'あり' if ok else 'なし'}）。1セルも書いていません。")
        return 0

    if set_status:
        sheets_io.write_cells(ws, set_status, ["status"], overwrite=True)
    if del_rows:
        sheets_io.delete_row_numbers(ws, del_rows)
    label = "営業不可を削除" if ok else f"未照合のため status='{args.unverified_status}' を付与"
    print(f"[verify] {label}: 削除 {len(del_rows)}行 / status付与 {len(set_status)}行"
          f"（対象 {len(new)}行）", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="今回追記された行だけを後から照合して掃除する")
    sub = ap.add_subparsers(dest="cmd")
    for name, extra in (("snapshot", ("out",)), ("export", ("state", "out")),
                        ("apply", ("state",))):
        sp = sub.add_parser(name)
        sp.add_argument("spreadsheet")
        sp.add_argument("--worksheet", default=None)
        sp.add_argument("--creds", default=None)
        if "out" in extra:
            sp.add_argument("--out", required=True)
        if "state" in extra:
            sp.add_argument("--state", required=True)
        if name == "apply":
            sp.add_argument("--filter-result", default=None)
            sp.add_argument("--unverified-status", default="要確認")
            sp.add_argument("--preview", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    return {"snapshot": cmd_snapshot, "export": cmd_export, "apply": cmd_apply}.get(
        args.cmd, lambda a: (ap.print_help() or 2))(args)


# ---------------------------------------------------------------- 自己テスト
def _selftest() -> int:
    ok = True

    def check(name, got, exp):
        nonlocal ok
        if got != exp:
            ok = False
        print(f"[{'OK ' if got == exp else 'NG '}] {name}: got={got} exp={exp}")

    rows = [{"_row": 2, "company_name": "旧A", "url": "https://old-a.jp"},
            {"_row": 3, "company_name": "旧B", "url": "https://old-b.jp"},
            {"_row": 4, "company_name": "新C", "url": "https://new-c.jp"},
            {"_row": 5, "company_name": "新D", "url": "https://www.new-d.jp"}]
    check("増えた行（前2行）", [r["company_name"] for r in pick_new_rows(rows, 2)], ["新C", "新D"])
    check("増分なし", pick_new_rows(rows, 4), [])
    check("行が減っていたら安全側で空", pick_new_rows(rows, 9), [])
    check("スナップショット0＝全行が対象", len(pick_new_rows(rows, 0)), 4)

    # 照合結果のほぐし（www 付きURLでも登録可能ドメインで一致すること）
    import tempfile
    fr = {"kept": [{"url": "https://new-c.jp", "status": "手動送信要"}],
          "dropped": [{"url": "https://www.new-d.jp", "reason": "no_contact"}], "stats": {}}
    p = Path(tempfile.mkdtemp()) / "f.json"
    p.write_text(json.dumps(fr, ensure_ascii=False), encoding="utf-8")
    dropped, st, _ = pm.load_filter_result(str(p))
    check("落とすドメイン", dropped, {"new-d.jp"})
    check("status付与", st, {"new-c.jp": "手動送信要"})
    check("www付きでも一致", ef.norm_domain("https://www.new-d.jp/") in dropped, True)

    print("=== prep_verify_appended selftest:", "PASS" if ok else "FAIL", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
