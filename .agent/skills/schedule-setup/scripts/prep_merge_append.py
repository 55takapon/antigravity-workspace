#!/usr/bin/env python3
"""prep_merge_append.py — 並列prepの「直列集約」パート（決定論・AIなし・壊れる所）。

各子（worker）が自分専用CSVに吐いた収集結果（①②まで＝company_name..contact_url）を、
親が **1回だけ** マージしてシート末尾へ追記する。並列で壊れるのは「同一シートへの
同時書き込み」なので、書き込みは必ずこの1プロセスに直列化する（子は絶対にシートへ書かない）。

処理:
  1) N個の worker CSV を読む（--manifest の out_csv、または positional 指定）
  2) シャード間の重複を registrable_domain で除去（同じ会社が別シャードに出た場合）
  3) シート既存の url と突合して既出をスキップ（再実行・既存行との二重追記防止）
  4) 残りを sheets_io.append_rows で **日本語操作列に alias 解決して** 追記（列ズレ地雷回避）
  ※ message(営業文) はここでは埋めない。追記後に 004 merge_on_sheet.py が1回で差し込む。

使い方:
  python3 prep_merge_append.py <sheet_key> --manifest shards.json [--worksheet NAME] [--preview]
  python3 prep_merge_append.py <sheet_key> worker_1.csv worker_2.csv ... [--preview]
  python3 prep_merge_append.py --selftest        # シート不要（マージ/重複除去の純ロジック）
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]  # .../<repo>/.claude/skills/007-schedule-setup/scripts
sys.path.insert(0, str(REPO_ROOT / "shared"))
import exclude_filter as ef  # noqa: E402  社名(NFKC+法人格除去)/ドメイン正規化＝#40と同じ照合

# 既存シート／既存提携先との重複照合キー。domain=登録可能ドメイン(パス無視) と company=正規化社名。
# ※ 旧実装は URL パス込みで照合し「同一ドメイン別パス(例 /recruit)」と「社名一致別URL」を取りこぼした。
DEDUP_KEYS = ("domain", "company")
PARTNER_WORKSHEET = "既存提携先"

# 子CSVから拾ってシートへ運ぶ列（統一スキーマ順・message は 004 が後段で埋める）。
# status は抑止リスト由来の「手動送信要」フラグを運ぶための任意列（在れば追記に含める）。
CARRY_COLS = ["company_name", "url", "address", "phone", "maps_url", "contact_url", "status"]


def norm_url_key(u: str) -> str:
    """重複照合用のURL正規化。scheme/www/末尾スラ・大小の揺れを吸収する
    （001 run_on_sheet._norm_url と同じ規則＝シート既存URLとの突合をぶらさない）。"""
    u = (u or "").strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def read_worker_csv(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def merge_and_dedup(row_lists: list[list[dict]],
                    existing_set: "ef.ExcludeSet", partner_set: "ef.ExcludeSet") -> tuple[list[dict], dict]:
    """複数workerの行を1本に畳む（純ロジック・シート非依存）。
    - company_name / url 欠落行は捨てる
    - シャード間の重複は domain OR 社名 で除去（先勝ち）＝同一ドメイン別パス・社名一致も捕捉
    - existing_set（シート既存の domain/社名）に在るものはスキップ
    - partner_set（既存提携先タブの domain/社名）に在るものはスキップ（★指示なしでも提携先を弾く）
    返り値: (kept_rows, stats)
    """
    kept: list[dict] = []
    seen = ef.ExcludeSet(DEDUP_KEYS)
    stats = {"input": 0, "kept": 0, "drop_no_required": 0, "drop_cross_dup": 0,
             "drop_existing": 0, "drop_partner": 0}
    for rows in row_lists:
        for r in rows:
            stats["input"] += 1
            name = (r.get("company_name") or "").strip()
            url = (r.get("url") or "").strip()
            phone = (r.get("phone") or "").strip()
            if not name or not url:
                stats["drop_no_required"] += 1
                continue
            if seen.match(company_name=name, url=url):
                stats["drop_cross_dup"] += 1
                continue
            if existing_set.match(company_name=name, url=url):
                stats["drop_existing"] += 1
                continue
            if partner_set.match(company_name=name, url=url):
                stats["drop_partner"] += 1
                continue
            seen.add_record(company_name=name, url=url, phone=phone)
            kept.append(r)
    stats["kept"] = len(kept)
    return kept, stats


def build_exclude_sets(ws, sh, *, all_tabs: bool = True) -> tuple["ef.ExcludeSet", "ef.ExcludeSet"]:
    """シート既存行と既存提携先タブから ExcludeSet を2つ作る（domain＋社名照合）。
    ws=対象ワークシート / sh=スプレッドシート（提携先タブ取得用）。

    all_tabs=True（既定）: 作業タブだけでなく **このシートの全タブ** を既存扱いにする。
      ★理由: prep_reap_manual が「手動送信要」の行を専用タブへ移送すると作業タブから消えるため、
        作業タブだけを見る旧実装ではその会社を「未知」と誤認し、毎回 再収集していた。
      all_tabs=False で旧挙動（作業タブのみ）。
    """
    import sheets_io  # 遅延import（--selftest はシート非依存）
    existing = ef.ExcludeSet(DEDUP_KEYS)
    if all_tabs:
        try:
            import known_companies as kc  # 同ディレクトリ（全タブ走査の実装はこちらが正本）
            existing, _detail = kc.build_known_set(sh, skip_tabs=[PARTNER_WORKSHEET])
        except Exception as e:  # noqa: BLE001  失敗しても作業タブのみで続行（フェイルソフト）
            print(f"[merge] 全タブ走査に失敗（作業タブのみで続行）: {e}", file=sys.stderr)
            existing = ef.ExcludeSet(DEDUP_KEYS)
    if existing.is_empty():
        for r in sheets_io.read_rows(ws, want=["company_name", "url"]):
            existing.add_record(company_name=r.get("company_name", ""), url=r.get("url", ""))
    partner = ef.ExcludeSet(DEDUP_KEYS)
    try:
        pv = sh.worksheet(PARTNER_WORKSHEET).get_all_values()
        for row in pv[1:]:  # 1行目ヘッダ（会社名/URL）
            name = row[0] if len(row) > 0 else ""
            url = row[1] if len(row) > 1 else ""
            if (name or "").strip() or (url or "").strip():
                partner.add_record(company_name=name, url=url)
    except Exception as e:  # noqa: BLE001  タブが無い等でも既存照合は続行
        print(f"[merge] 既存提携先タブ『{PARTNER_WORKSHEET}』読取スキップ: {e}", file=sys.stderr)
    return existing, partner


# ---------------------------------------------------------- サーバー照合の橋渡し
def _dom(u: str) -> str:
    return ef.norm_domain(u or "")


def load_filter_result(path: str) -> tuple[set, dict, dict]:
    """サーバー照合(list_filter_exclude)の戻りJSONを読み、
    (落とすドメイン集合, ドメイン→status, stats) にほぐす。

    ★なぜ親でやるか: 子(収集AI)に「必ず照合を通せ」と指示しても、モデルによっては黙って
      飛ばす。実際 2026-08-04 のToBバッチ3で営業不可3社がシートに入り、手動送信要2社の
      status が欠けた。判定は1回まとめて親が通すのが確実で、しかも安い。
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, str):          # 文字列で包まれて来た場合
        data = json.loads(data)
    dropped = {_dom(d.get("url", "")) for d in data.get("dropped", []) if d.get("url")}
    dropped.discard("")
    status_by_dom = {}
    for k in data.get("kept", []):
        st = (k.get("status") or "").strip()
        d = _dom(k.get("url", ""))
        if d and st:
            status_by_dom[d] = st
    return dropped, status_by_dom, data.get("stats", {})


def apply_filter(rows: list[dict], dropped: set, status_by_dom: dict) -> tuple[list[dict], dict]:
    """照合結果を行に反映。落とす行を除き、手動送信要などの status を書き込む。"""
    kept, st = [], {"in": len(rows), "dropped": 0, "status_set": 0}
    for r in rows:
        d = _dom(r.get("url", ""))
        if d and d in dropped:
            st["dropped"] += 1
            continue
        if d in status_by_dom and not (r.get("status") or "").strip():
            r = dict(r, status=status_by_dom[d])
            st["status_set"] += 1
        kept.append(r)
    return kept, st


def _resolve_worker_paths(args) -> list[str]:
    if args.manifest:
        data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        return [w["out_csv"] for w in data.get("workers", [])]
    return list(args.csvs)


def main() -> int:
    ap = argparse.ArgumentParser(description="並列prepの直列集約：N worker CSV をマージしてシートへ1回追記")
    ap.add_argument("spreadsheet", nargs="?", help="スプレッドシートのURLまたはキー")
    ap.add_argument("csvs", nargs="*", help="worker CSV パス（--manifest 未指定時）")
    ap.add_argument("--manifest", help="prep_shards.py が出した shards.json（out_csv を読む）")
    ap.add_argument("--worksheet", default=None)
    ap.add_argument("--creds", default=None)
    ap.add_argument("--no-dedup-existing", action="store_true",
                    help="シート既存URLとの突合をしない（既定は既出をスキップ）")
    ap.add_argument("--no-all-tabs", action="store_true",
                    help="既存照合を作業タブだけに限る（既定は全タブ＝移送済みの手動送信タブ等も既知扱い）")
    ap.add_argument("--export-candidates", metavar="PATH",
                    help="マージ+重複除去した候補を JSON 配列で書き出して終了（追記しない）。"
                         "親がサーバー照合(list_filter_exclude)に渡すための出口。")
    ap.add_argument("--apply-filter", metavar="PATH",
                    help="サーバー照合の戻りJSONを読み、営業不可を落とし status を付けてから追記する。")
    ap.add_argument("--unverified-status", default=None,
                    help="照合ができなかったときに全行へ付ける status（例『要確認』）。"
                         "④自動送信は status 非空をスキップするので、未照合のまま送るのを防げる。")
    ap.add_argument("--preview", action="store_true", help="件数と列だけ表示・1セルも書かない")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    if not args.spreadsheet:
        print("[エラー] spreadsheet（シートURL/キー）が必要です。", file=sys.stderr)
        return 2

    paths = _resolve_worker_paths(args)
    if not paths:
        print("[エラー] worker CSV が指定されていません（--manifest か positional）。", file=sys.stderr)
        return 2
    row_lists = [read_worker_csv(p) for p in paths]
    found = sum(1 for rl in row_lists if rl)
    print(f"[merge] worker {len(paths)}本中 {found}本にデータ / "
          f"総行 {sum(len(rl) for rl in row_lists)}", file=sys.stderr)

    import sheets_io  # 遅延import（--selftest はシート非依存で通す）
    try:
        client = sheets_io.get_client(args.creds)
        sh = client.open_by_url(args.spreadsheet) if args.spreadsheet.startswith("http") \
            else client.open_by_key(args.spreadsheet)
        ws = sh.worksheet(args.worksheet) if args.worksheet else sh.sheet1
    except (FileNotFoundError, ImportError) as e:
        print(f"[エラー] {e}", file=sys.stderr)
        return 2

    # 既存シート＋既存提携先タブの ExcludeSet（domain＋社名照合）。--no-dedup-existing で既存側だけ無効化。
    existing_set, partner_set = build_exclude_sets(ws, sh, all_tabs=not args.no_all_tabs)
    if args.no_dedup_existing:
        existing_set = ef.ExcludeSet(DEDUP_KEYS)  # 空＝既存照合オフ（提携先照合は常時ON）
    def _cnt(s):
        return len(getattr(s, "domains", ())) + len(getattr(s, "companies", ()))
    print(f"[merge] 照合セット: 既存 dom/社名={_cnt(existing_set)} / 提携先={_cnt(partner_set)}", file=sys.stderr)

    kept, stats = merge_and_dedup(row_lists, existing_set, partner_set)

    # --- サーバー照合の出口: 候補だけ書き出して終了（追記しない）---
    if args.export_candidates:
        cands = [{"company_name": r.get("company_name", ""), "url": r.get("url", ""),
                  "phone": r.get("phone", "")} for r in kept]
        Path(args.export_candidates).write_text(json.dumps(cands, ensure_ascii=False), encoding="utf-8")
        print(f"[merge] 候補 {len(cands)}件 を書き出し -> {args.export_candidates}", file=sys.stderr)
        return 0

    # --- サーバー照合の入口: 営業不可を落とし status を付ける ---
    if args.apply_filter:
        try:
            dropped_doms, status_by_dom, fstats = load_filter_result(args.apply_filter)
            kept, ast = apply_filter(kept, dropped_doms, status_by_dom)
            print(f"[merge] サーバー照合を適用: 入力{ast['in']} → 残り{len(kept)}"
                  f"（営業不可等で除外 {ast['dropped']} / status付与 {ast['status_set']}）"
                  f" server_stats={fstats}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"[merge] 🔴 照合結果の適用に失敗: {e}", file=sys.stderr)
            if args.unverified_status:
                kept = [dict(r, status=(r.get("status") or args.unverified_status)) for r in kept]
                print(f"[merge] 未照合のため status='{args.unverified_status}' を付与"
                      "（④自動送信の対象外にする）", file=sys.stderr)
    elif args.unverified_status:
        kept = [dict(r, status=(r.get("status") or args.unverified_status)) for r in kept]
        print(f"[merge] 照合なしのため status='{args.unverified_status}' を付与", file=sys.stderr)

    # 実際に書ける列（子CSVに在る CARRY_COLS のみ）。列順は CARRY_COLS 固定。
    present = set().union(*[set(rl[0].keys()) for rl in row_lists if rl]) if found else set()
    if any((r.get("status") or "").strip() for r in kept):
        present.add("status")   # 照合で付けた status を子CSVに列が無くても書けるようにする
    cols = [c for c in CARRY_COLS if c in present]
    rows_out = [{c: (r.get(c) or "").strip() for c in cols} for r in kept]

    if args.preview:
        print(f"シート『{ws.title}』へ追記プレビュー")
        print(f"  追記する列 : {cols}")
        print(f"  追記行数   : {len(rows_out)}")
        print(f"  内訳: 入力 {stats['input']} / 必須欠落 {stats['drop_no_required']}"
              f" / シャード間重複 {stats['drop_cross_dup']} / 既存重複 {stats['drop_existing']}"
              f" / 提携先重複 {stats['drop_partner']}")
        for r in rows_out[:3]:
            print("  - " + " / ".join(f"{c}={r.get(c) or '∅'}" for c in cols))
        print("※ プレビューのみ。シートには1セルも書き込んでいません。")
        return 0

    if not rows_out:
        print(f"[done] 追記対象なし（入力 {stats['input']} / 既存重複 {stats['drop_existing']}"
              f" / シャード間重複 {stats['drop_cross_dup']}）。", file=sys.stderr)
        return 0

    appended = sheets_io.append_rows(ws, rows_out, cols)
    print(f"[done] appended={appended} cols={cols} "
          f"(cross_dup={stats['drop_cross_dup']} existing_dup={stats['drop_existing']} "
          f"partner_dup={stats['drop_partner']} no_req={stats['drop_no_required']}) "
          f"-> sheet '{ws.title}'", file=sys.stderr)
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

    def es(records):
        s = ef.ExcludeSet(DEDUP_KEYS)
        for company_name, url in records:
            s.add_record(company_name=company_name, url=url)
        return s

    # 既存＝D社(ドメイン)・E社(社名一致・別URL)。提携先＝P社。
    existing = es([("D社", "https://d.com"), ("E社", "https://e-old.example.jp")])
    partner = es([("P社", "https://p.com")])

    w1 = [
        {"company_name": "A社", "url": "https://a.com", "contact_url": "https://a.com/c"},
        {"company_name": "B社", "url": "https://b.com", "contact_url": ""},
        {"company_name": "", "url": "https://x.com"},               # 必須欠落（社名なし）
        {"company_name": "D社", "url": "https://d.com/recruit"},    # ★同一ドメイン別パス→既存重複(旧実装は取りこぼし)
    ]
    w2 = [
        {"company_name": "A社", "url": "http://www.a.com/"},        # 子1と重複（www/slash吸収）
        {"company_name": "C社", "url": "https://c.com"},
        {"company_name": "E社", "url": "https://e-new.example.com"},  # ★社名一致別URL→既存重複
        {"company_name": "P社", "url": "https://p.com/contact"},    # ★提携先重複
    ]
    kept, stats = merge_and_dedup([w1, w2], existing, partner)
    names = [r["company_name"] for r in kept]
    check("kept順(先勝ち・各種重複を除く)", names, ["A社", "B社", "C社"])
    check("stat input", stats["input"], 8)
    check("stat cross_dup(A社2つ目)", stats["drop_cross_dup"], 1)
    check("stat existing(D社別パス+E社社名一致)", stats["drop_existing"], 2)
    check("stat partner(P社)", stats["drop_partner"], 1)
    check("stat no_required", stats["drop_no_required"], 1)
    check("stat kept", stats["kept"], 3)

    # 空入力
    kept2, stats2 = merge_and_dedup([[], []], ef.ExcludeSet(DEDUP_KEYS), ef.ExcludeSet(DEDUP_KEYS))
    check("空入力 kept", kept2, [])
    check("空入力 input", stats2["input"], 0)

    print("=== prep_merge_append selftest:", "PASS" if ok else "FAIL", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
