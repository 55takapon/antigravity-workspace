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
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]  # .../<repo>/.claude/skills/007-schedule-setup/scripts
sys.path.insert(0, str(REPO_ROOT / "shared"))
import exclude_filter as ef  # noqa: E402  社名(NFKC+法人格除去)/ドメイン正規化＝#40と同じ照合

# 既存シート／既存提携先との重複照合キー。domain=登録可能ドメイン(パス無視) と company=正規化社名。
# ※ 旧実装は URL パス込みで照合し「同一ドメイン別パス(例 /recruit)」と「社名一致別URL」を取りこぼした。
DEDUP_KEYS = ("domain", "company")
PARTNER_WORKSHEET = "既存提携先"
# 照合セットが不完全なまま追記を強行したときに全行へ付ける status。
# ④自動送信は status 非空をスキップするので、未照合の行が誤って送られない。
DEGRADED_STATUS = "要確認"
# 取りこぼしの多くは一時的（APIの5xx・瞬断）。ならし直してから中止を判断する。
RETRY_ATTEMPTS = 3
RETRY_WAIT_SEC = 5

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


def build_exclude_sets(ws, sh, *, all_tabs: bool = True
                       ) -> tuple["ef.ExcludeSet", "ef.ExcludeSet", list[str]]:
    """シート既存行と既存提携先タブから ExcludeSet を2つ作る（domain＋社名照合）。
    ws=対象ワークシート / sh=スプレッドシート（提携先タブ取得用）。

    all_tabs=True（既定）: 作業タブだけでなく **このシートの全タブ** を既存扱いにする。
      ★理由: prep_reap_manual が「手動送信要」の行を専用タブへ移送すると作業タブから消えるため、
        作業タブだけを見る旧実装ではその会社を「未知」と誤認し、毎回 再収集していた。
      all_tabs=False で旧挙動（作業タブのみ）。

    返り値: (existing, partner, degraded)
      degraded … **想定外に取りこぼした理由**の配列。空なら健全（#53）。
        接頭辞で出所を分ける: 「既存照合: …」/「提携先照合: …」。
        ★2026-08 の事故はここが痩せたまま黙って追記へ進んだこと自体が原因なので、
          呼び出し側は degraded が空でない限り**書き込まない**（--allow-degraded-append 時を除く）。
        ★正常な状態を degraded にしない: 提携先タブが**存在しない**シートは普通にある／
          空タブ・空シートは失うものが無い／列が解決できず位置指定に落ちるのは設計どおりの保険。
    """
    import sheets_io  # 遅延import（--selftest はシート非依存）
    existing = ef.ExcludeSet(DEDUP_KEYS)
    degraded: list[str] = []
    if all_tabs:
        try:
            import known_companies as kc  # 同ディレクトリ（全タブ走査の実装はこちらが正本）
            existing, _detail, kc_degraded = kc.build_known_set(sh, skip_tabs=[PARTNER_WORKSHEET])
            degraded += [f"既存照合: {d}" for d in kc_degraded]
        except Exception as e:  # noqa: BLE001  作業タブのみで続行するが degraded として記録する
            print(f"[merge] 全タブ走査に失敗（作業タブのみで続行）: {e}", file=sys.stderr)
            existing = ef.ExcludeSet(DEDUP_KEYS)
            degraded.append(f"既存照合: 全タブ走査に失敗: {e}")
    if existing.is_empty():
        try:
            for r in sheets_io.read_rows(ws, want=["company_name", "url"]):
                existing.add_record(company_name=r.get("company_name", ""), url=r.get("url", ""))
        except Exception as e:  # noqa: BLE001
            print(f"[merge] 作業タブ『{ws.title}』の読取にも失敗: {e}", file=sys.stderr)
            degraded.append(f"既存照合: 作業タブが読めない: {e}")
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
        # ★「タブが無い」は正常（提携先を管理していないシートは普通にある）＝degraded にしない。
        #   「タブは在るのに読めない」だけが取りこぼし。gspread への依存を増やさず型名で見分ける。
        if type(e).__name__ != "WorksheetNotFound":
            degraded.append(f"提携先照合: タブ『{PARTNER_WORKSHEET}』が読めない: {e}")
    return existing, partner, degraded


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
    ap.add_argument("--allow-degraded-append", action="store_true",
                    help="既知会社の照合セットが不完全でも追記する（既定は中止＝除外済みの会社を"
                         f"入れないため）。指定時は全行に status='{DEGRADED_STATUS}' を付けて"
                         "④自動送信の対象外にする。")
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
    # ★取りこぼしは一時的なこと（APIの 5xx・瞬断）が多い。1回の失敗で丸ごと捨てると、
    #   収集に使ったトークンが全損する。数回ならし直してから判断する（#53）。
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        existing_set, partner_set, degraded = build_exclude_sets(ws, sh, all_tabs=not args.no_all_tabs)
        if args.no_dedup_existing:
            existing_set = ef.ExcludeSet(DEDUP_KEYS)  # 空＝既存照合オフ（提携先照合は常時ON）
            # ユーザーが明示的に既存照合を切っている＝その取りこぼしは想定内。提携先側だけ残す。
            degraded = [d for d in degraded if not d.startswith("既存照合:")]
        if not degraded or attempt == RETRY_ATTEMPTS:
            break
        wait = RETRY_WAIT_SEC * attempt
        print(f"[merge] 照合セットに取りこぼし {len(degraded)}件。{wait}秒待って再取得します"
              f"（{attempt}/{RETRY_ATTEMPTS - 1}回目）", file=sys.stderr)
        time.sleep(wait)
    if degraded:
        print(f"[merge] {RETRY_ATTEMPTS}回試しても取りこぼしが解消しませんでした", file=sys.stderr)
    def _cnt(s):
        return len(getattr(s, "domains", ())) + len(getattr(s, "companies", ()))
    print(f"[merge] 照合セット: 既存 dom/社名={_cnt(existing_set)} / 提携先={_cnt(partner_set)}", file=sys.stderr)

    degraded_status = ""   # --allow-degraded-append 時に全行へ付ける status

    # ★照合セットが想定外に痩せているなら、書かない（#53）。
    #   2026-08 の事故の本体は例外そのものではなく、**痩せたまま黙って追記まで進んだこと**。
    #   照合できないまま足すより、足さない方を選ぶ。worker CSV は残るので、原因を直して
    #   同じコマンドを再実行すれば拾える＝データは失われない。
    #   --preview は1セルも書かないので止めない（人が確認するための経路）。
    if degraded and not args.preview:
        print(f"[merge] 🔴 既知会社の照合セットが不完全です（{len(degraded)}件の取りこぼし）",
              file=sys.stderr)
        for d in degraded:
            print(f"  - {d}", file=sys.stderr)
        if not args.allow_degraded_append:
            ws_opt = f' --worksheet "{args.worksheet}"' if args.worksheet else ""
            csvs = " ".join(f'"{p}"' for p in paths)
            print("[merge] 🔴 追記を中止しました。除外済みの会社を営業リストへ入れてしまうため、"
                  "照合できないまま書き込みません。\n"
                  "  ★収集した結果は消していません。原因（シートの共有設定・ネットワーク・"
                  "タブの権限など）を直したあと、下記を実行すれば**収集をやり直さずに**追記できます:\n"
                  f"    {sys.executable} {Path(__file__).resolve()} "
                  f'"{args.spreadsheet}" {csvs}{ws_opt}\n'
                  "  どうしても今すぐ追記したい場合のみ --allow-degraded-append を付けてください"
                  "（全行に status を付けて④自動送信の対象外にします）。", file=sys.stderr)
            return 3
        # ★サーバー照合が成功していても付ける。痩せているのは「既知会社の照合セット」であって
        #   サーバー照合とは別物なので、そちらの成否では免除しない。
        degraded_status = args.unverified_status or DEGRADED_STATUS
        print(f"[merge] --allow-degraded-append 指定のため続行します"
              f"（全行に status='{degraded_status}' を付けます）", file=sys.stderr)

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

    # 照合セットが痩せたまま追記を強行する場合は、サーバー照合の成否に関係なく全行へ印を付ける。
    if degraded_status:
        kept = [dict(r, status=(r.get("status") or degraded_status)) for r in kept]
        print(f"[merge] 照合セット不完全のため status='{degraded_status}' を付与"
              "（④自動送信の対象外）", file=sys.stderr)

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

    # ---- #53 degraded: 照合セットが痩せたら「1セルも書かない」ことを end-to-end で固定 ----
    # ★ここが本丸。build_exclude_sets が理由を返しても main が書いてしまえば意味がないので、
    #   実際に append_rows が呼ばれないこと・終了コードが 0 でないことまで確認する。
    import types

    class _FakeWS:
        title = "シート1"

        def get_all_values(self):
            return [["会社名", "URL"]]

    class _FakeSheet:
        def worksheets(self):
            raise RuntimeError("APIError: permission")   # ← 想定外の取りこぼし

        def worksheet(self, name):
            raise RuntimeError("WorksheetNotFound stub")

        sheet1 = _FakeWS()

    global RETRY_WAIT_SEC
    RETRY_WAIT_SEC = 0        # テストで待たない（リトライ回数の検証は別途）
    calls = {"append": 0}
    fake_io = types.ModuleType("sheets_io")
    fake_io.get_client = lambda creds: types.SimpleNamespace(
        open_by_key=lambda k: _FakeSheet(), open_by_url=lambda u: _FakeSheet())
    fake_io.read_rows = lambda ws, **kw: []
    fake_io.append_rows = lambda ws, rows, cols: calls.__setitem__("append", calls["append"] + 1)
    sys.modules["sheets_io"] = fake_io

    csv_path = Path(__file__).with_name("_merge_selftest.csv")
    csv_path.write_text("company_name,url\n株式会社インディア,https://india.example.com\n",
                        encoding="utf-8")
    argv_backup = sys.argv
    try:
        sys.argv = ["prep_merge_append.py", "DUMMYKEY", str(csv_path)]
        rc = main()
        check("degraded なら終了コードが 0 でない", rc != 0, True)
        check("degraded なら1行も追記しない", calls["append"], 0)

        sys.argv = ["prep_merge_append.py", "DUMMYKEY", str(csv_path), "--allow-degraded-append"]
        rc2 = main()
        check("--allow-degraded-append なら追記する", (rc2, calls["append"]), (0, 1))

        # --preview は1セルも書かないので、degraded でも人の確認経路として通す
        sys.argv = ["prep_merge_append.py", "DUMMYKEY", str(csv_path), "--preview"]
        rc3 = main()
        check("--preview は degraded でも通る・書かない", (rc3, calls["append"]), (0, 1))
    finally:
        sys.argv = argv_backup
        sys.modules.pop("sheets_io", None)
        csv_path.unlink(missing_ok=True)

    print("=== prep_merge_append selftest:", "PASS" if ok else "FAIL", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
