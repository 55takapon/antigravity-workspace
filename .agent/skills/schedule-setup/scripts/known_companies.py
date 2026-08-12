#!/usr/bin/env python3
"""known_companies.py — 「もう知っている会社」を1つの照合セットに畳み、
①収集が **HPを開く前** に候補を機械的に間引くための土台（決定論・AIなし・0トークン）。

なぜ:
  これまで既知会社（シート既存行／既存提携先タブ／「要手動送信」タブへ移した行）は、
  子AIが 公式URL解決 → HP取得 → ②contact抽出 まで済ませた **後** に、
  親の prep_merge_append が捨てていた。取りに行く前に落とせば、その分の
  トークン・通信・時間がまるごと浮く（＝落とす社数は同じ・払う金だけ減る）。
  ★特に「要手動送信_リスト取り段階」へ移送した行はシート1から消えるため、
    従来の「シート1との突合」では既知と見なされず **毎回 再収集** されていた。
    ここで全タブを見るとその再収集も止まる。

モード:
  dump   <sheet_key> --out known.json [--tabs A,B] [--only-tabs] [--creds P]
         スプレッドシートの全タブ（既定）から照合キー（登録可能ドメイン／正規化社名）だけを抽出。
  screen --known known.json --in candidates.json --out kept.json [--stats-json S]
         候補レコード配列（company_name/url を持つ dict の配列）から既知社を落とす。
  --selftest   シート不要の純ロジックテスト。

入出力の形:
  known.json     {"version":1, "domains":[...], "companies":[...], "tabs":[{"title","rows"}], "size":N}
  candidates.json  [{"company_name":..., "url":..., ...}, ...]  （{"records":[...]} 形式も受ける）
  kept.json      入力と同じ形の配列（既知社を除いたもの・他の列はそのまま素通し）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]  # .../<repo>/.claude/skills/007-schedule-setup/scripts
sys.path.insert(0, str(REPO_ROOT / "shared"))
import exclude_filter as ef  # noqa: E402  社名(NFKC+法人格除去)/ドメイン正規化＝#40と同じ照合

# 照合キー。電話は収集候補の段階では持っていないことが多いので使わない。
KEYS = ("domain", "company")


# ---------------------------------------------------------------- 構築（dump）
def _col_ratio(data: list[list[str]], i: int, pred) -> float:
    """列 i の非空セルのうち pred を満たす割合。空列は 0.0。"""
    vals = [r[i].strip() for r in data if i < len(r) and r[i].strip()]
    return (sum(1 for v in vals if pred(v)) / len(vals)) if vals else 0.0


def _pick_col(data: list[list[str]], width: int, pred, threshold: float) -> int | None:
    """pred を満たす割合が threshold 以上の列のうち、最も割合が高いものを返す。"""
    best, best_r = None, 0.0
    for i in range(width):
        r = _col_ratio(data, i, pred)
        if r >= threshold and r > best_r:
            best, best_r = i, r
    return best


# 列の性格を「中身」から推定するときのしきい値。実シートでの実測は
# URL列=100% / 社名列=88〜100% だったので、いずれも十分な余裕がある。
URL_COL_RATIO = 0.5
NAME_COL_RATIO = 0.4


def classify_worksheet(header: list[str], data: list[list[str]]) -> tuple[int | None, int | None, str]:
    """このタブは会社リストか？ 会社リストなら (社名列, URL列, 判定理由) を返す。
    会社リストでなければ (None, None, "")。

    ★全タブを開いたうえで、**中身**を見て判断する（タブ名では判断しない）。
      ユーザーは各自のシートに自由なタブを作るので、名前や形を「守るべき決まり」にしない。
      判定は3段（#53）:
        (a) 1行目のヘッダに候補ワードがあるか
        (b) どこかの列の値が5割以上URLの形か（裸ドメインも可）
        (c) どこかの列の値が4割以上「社名の形」か
      どれも当たらなければ、そのタブは重複確認にも除外照合にも使わない。

    ★(a) が当たらないときに位置指定（A列=社名/B列=URL）へ無条件に落ちるのが 2026-08 の事故だった。
      設定タブのセルを URL とみなして照合セットの構築が全滅した。位置指定は廃止せず、
      **会社リストだと確定したタブの中でだけ**使う（社名列が特定できないときの最後の手段）。
    """
    import sheets_io

    width = max([len(header)] + [len(r) for r in data]) if (header or data) else 0
    cm = sheets_io.find_columns(header, ["company_name", "url"])
    ci, ui = cm.get("company_name"), cm.get("url")
    if ci is not None or ui is not None:
        why = "(a) ヘッダの候補ワード"
    else:
        ui = _pick_col(data, width, ef.looks_like_url, URL_COL_RATIO)
        if ui is not None:
            why = "(b) 値がURLの形"
        else:
            ci = _pick_col(data, width, ef.looks_like_company_name, NAME_COL_RATIO)
            if ci is None:
                return None, None, ""      # ← 会社リストではない＝このタブは使わない
            why = "(c) 値が社名の形"
    if ci is None:
        # 会社リストだと確定済み。社名列は「URL列以外で最も左の、中身のあるテキスト列」。
        ci = next((i for i in range(width)
                   if i != ui and any(i < len(r) and r[i].strip() for r in data)), None)
    return ci, ui, why


def _rows_of_worksheet(ws) -> tuple[list[dict], str, str]:
    """1タブから {company_name,url} の配列を取り出す。

    返り値: (rows, 取りこぼし理由, 判定の説明)
      取りこぼし理由 … 空文字なら健全。**本当に行が失われたときだけ**入れる（#53）。
        「会社リストでないので使わなかった」は取りこぼしではない（失うものが無い）。
        ここを混同すると、正常なシートで毎晩 degraded 判定になって収集が止まる。
    """
    import sheets_io

    try:
        rows = sheets_io.read_rows(ws, want=["company_name", "url"])
        if any((r.get("company_name") or r.get("url")) for r in rows):
            return rows, "", "(a) ヘッダの候補ワード"
    except Exception as e:  # noqa: BLE001  1タブの失敗で全体を止めない
        print(f"[known] タブ『{ws.title}』read_rows 失敗（中身から再判定）: {e}", file=sys.stderr)
    try:
        vals = ws.get_all_values()
    except Exception as e:  # noqa: BLE001
        print(f"[known] タブ『{ws.title}』読取スキップ: {e}", file=sys.stderr)
        return [], f"タブ『{ws.title}』が読めない: {e}", "🔴 読取失敗"
    header, data = (vals[0], vals[1:]) if vals else ([], [])
    ci, ui, why = classify_worksheet(header, data)
    if ci is None and ui is None:
        return [], "", "⏭ 対象外（会社データらしき列なし）"
    out = []
    for row in data:
        name = row[ci] if (ci is not None and ci < len(row)) else ""
        url = row[ui] if (ui is not None and ui < len(row)) else ""
        if (name or "").strip() or (url or "").strip():
            out.append({"company_name": name, "url": url})
    return out, "", why


def build_known_set(sh, *, tabs: list[str] | None = None, only_tabs: bool = False,
                    skip_tabs: list[str] | None = None,
                    verbose: bool = True) -> tuple["ef.ExcludeSet", list[dict], list[str]]:
    """スプレッドシート（gspread Spreadsheet）から既知社の ExcludeSet を作る。

    既定は **全タブ**（このシートに一度でも載った会社は「知っている会社」）。
    tabs を渡すと、その名前のタブ **だけ** に絞る（only_tabs=True のとき）。
    tabs + only_tabs=False は「全タブ ＋ 明示タブ」の意味だが、全タブに包含されるので実質同じ。
    skip_tabs は常に除く（呼び出し側で別セットとして数えたいタブ＝既存提携先など）。

    返り値: (ExcludeSet, [{"title":..,"rows":n,"skipped":m}, ...], degraded)
      degraded … **想定外に取りこぼした理由**の配列。空なら健全（#53）。
        ここが空でないまま追記すると、照合セットが痩せたまま「知らない会社」と誤判断して
        除外済みの会社を営業リストへ入れてしまう（2026-08 の事故がこれ）。
        ★空のタブ・空のシートは degraded ではない（失うものが無い）。
    """
    es = ef.ExcludeSet(KEYS)
    detail: list[dict] = []
    degraded: list[str] = []
    try:
        worksheets = sh.worksheets()
    except Exception as e:  # noqa: BLE001
        print(f"[known] タブ一覧の取得に失敗: {e}", file=sys.stderr)
        return es, detail, [f"タブ一覧が取得できない（全タブぶん取りこぼし）: {e}"]
    wanted = {t.strip() for t in (tabs or []) if t.strip()}
    skipped = {t.strip() for t in (skip_tabs or []) if t.strip()}
    for ws in worksheets:
        if only_tabs and wanted and ws.title not in wanted:
            continue
        if ws.title in skipped:
            continue
        rows, why_degraded, verdict = _rows_of_worksheet(ws)
        if why_degraded:
            degraded.append(why_degraded)
        n = dropped = 0   # ★dropped を skipped と名付けない（上の skip_tabs 集合を潰す）
        for r in rows:
            name = (r.get("company_name") or "").strip()
            url = (r.get("url") or "").strip()
            if not name and not url:
                continue
            try:
                es.add_record(company_name=name, url=url)
            except Exception as e:  # noqa: BLE001
                # ★1行の失敗でタブ全体・走査全体を巻き添えにしない（#53）。
                #   従来はここの例外が build_known_set の外まで抜け、**走査済みタブの蓄積ごと
                #   全部失われて**いた（照合セットが痩せたまま追記が進み、除外済み11社が混入）。
                if dropped == 0:  # 同じ理由で溢れないよう最初の1件だけ出す
                    print(f"[known] タブ『{ws.title}』の行を読み飛ばし: {e}", file=sys.stderr)
                dropped += 1
                continue
            n += 1
        if dropped:
            degraded.append(f"タブ『{ws.title}』で {dropped}行を読み飛ばし")
        detail.append({"title": ws.title, "rows": n, "skipped": dropped, "verdict": verdict})
        if verbose:
            # ★タブごとの判定を必ず出す。「読まれるはずのタブが対象外になっていないか」を
            #   人が1表で検算できる状態を保つ＝対象外にする仕様の安全装置。
            print(f"[known]   {ws.title[:24]:24} {n:5}行  {verdict}"
                  + (f"（読み飛ばし {dropped}行）" if dropped else ""), file=sys.stderr)
    if verbose:
        used = sum(1 for d in detail if not d["verdict"].startswith("⏭"))
        print(f"[known] 走査 {len(detail)}タブ（うち会社リスト {used}／対象外 {len(detail) - used}）"
              f" / 照合キー {len(es.domains)}ドメイン＋{len(es.companies)}社名"
              + (f" / 🔴 取りこぼし {len(degraded)}件" if degraded else " / 取りこぼしなし"),
              file=sys.stderr)
    return es, detail, degraded


def dump_to_json(es: "ef.ExcludeSet", detail: list[dict],
                 degraded: list[str] | None = None) -> dict:
    return {
        "version": 1,
        "domains": sorted(es.domains),
        "companies": sorted(es.companies),
        "tabs": detail,
        "size": len(es.domains) + len(es.companies),
        "degraded": list(degraded or []),
    }


def load_from_json(path: str) -> "ef.ExcludeSet":
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    es = ef.ExcludeSet(KEYS)
    es.domains.update(d for d in data.get("domains", []) if d)
    es.companies.update(c for c in data.get("companies", []) if c)
    return es


# ---------------------------------------------------------------- 選別（screen）
def screen_records(records: list[dict], known: "ef.ExcludeSet") -> tuple[list[dict], dict]:
    """候補配列から既知社を落とす（純ロジック）。同一run内の重複も同時に潰す。"""
    kept: list[dict] = []
    seen = ef.ExcludeSet(KEYS)
    stats = {"input": len(records), "kept": 0, "drop_known": 0, "drop_dup": 0, "drop_empty": 0}
    for r in records:
        name = (r.get("company_name") or "").strip()
        url = (r.get("url") or "").strip()
        if not name and not url:
            stats["drop_empty"] += 1
            continue
        if known.match(company_name=name, url=url):
            stats["drop_known"] += 1
            continue
        if seen.match(company_name=name, url=url):
            stats["drop_dup"] += 1
            continue
        seen.add_record(company_name=name, url=url)
        kept.append(r)
    stats["kept"] = len(kept)
    return kept, stats


def _write_json(path: str, obj) -> None:
    """JSONを書く。★親ディレクトリが無ければ作る（新規cloneには data/ が存在しないため）。"""
    p = Path(path)
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def _read_candidates(path: str) -> list[dict]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        for k in ("records", "kept", "candidates", "rows"):
            if isinstance(raw.get(k), list):
                return raw[k]
        raise ValueError("候補JSONに records/kept/candidates/rows の配列がありません")
    if not isinstance(raw, list):
        raise ValueError("候補JSONは配列（または records を持つオブジェクト）である必要があります")
    return raw


# ---------------------------------------------------------------- CLI
def cmd_dump(args) -> int:
    import sheets_io

    client = sheets_io.get_client(args.creds)
    sh = (client.open_by_url(args.spreadsheet) if args.spreadsheet.startswith("http")
          else client.open_by_key(args.spreadsheet))
    tabs = [t.strip() for t in (args.tabs or "").split(",") if t.strip()]
    es, detail, degraded = build_known_set(sh, tabs=tabs, only_tabs=args.only_tabs)
    out = dump_to_json(es, detail, degraded)
    _write_json(args.out, out)
    print(f"[known] dump: ドメイン{len(out['domains'])} / 社名{len(out['companies'])}"
          f" / タブ{len(detail)} -> {args.out}", file=sys.stderr)
    if degraded:
        # ★dump は事前間引き用（＝トークン節約）なので、痩せていても収集は止めない。
        #   ただし追記側（prep_merge_append）は同じ理由で必ず止まるため、先に予告しておく。
        print("[known] 🔴 既知会社の取りこぼしあり（このまま進むと追記側で中止されます）:",
              file=sys.stderr)
        for d in degraded:
            print(f"  - {d}", file=sys.stderr)
    return 0


def cmd_screen(args) -> int:
    known = load_from_json(args.known) if args.known and Path(args.known).exists() else ef.ExcludeSet(KEYS)
    if known.is_empty():
        print("[known] 既知セットが空（照合なしで素通し）", file=sys.stderr)
    records = _read_candidates(args.inp)
    kept, stats = screen_records(records, known)
    _write_json(args.out, kept)
    print(f"[known] screen: 入力{stats['input']} → 残り{stats['kept']}"
          f"（既知で除外{stats['drop_known']} / run内重複{stats['drop_dup']}"
          f" / 空{stats['drop_empty']}） -> {args.out}", file=sys.stderr)
    if args.stats_json:
        _write_json(args.stats_json, stats)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="既知会社の照合セット作成と、収集候補の事前間引き")
    sub = ap.add_subparsers(dest="cmd")

    d = sub.add_parser("dump", help="シート全タブ → 既知セット(JSON)")
    d.add_argument("spreadsheet", help="スプレッドシートのURLまたはキー")
    d.add_argument("--out", required=True)
    d.add_argument("--tabs", default="", help="対象タブ名（カンマ区切り）。--only-tabs と併用で限定")
    d.add_argument("--only-tabs", action="store_true", help="--tabs で挙げたタブだけを見る（既定は全タブ）")
    d.add_argument("--creds", default=None)

    s = sub.add_parser("screen", help="候補配列から既知社を落とす")
    s.add_argument("--known", required=True)
    s.add_argument("--in", dest="inp", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--stats-json", default=None)

    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if args.cmd == "dump":
        return cmd_dump(args)
    if args.cmd == "screen":
        return cmd_screen(args)
    ap.print_help()
    return 2


# ---------------------------------------------------------------- 自己テスト
def _selftest() -> int:
    ok = True

    def check(name, got, exp):
        nonlocal ok
        if got != exp:
            ok = False
        print(f"[{'OK ' if got == exp else 'NG '}] {name}: got={got} exp={exp}")

    known = ef.ExcludeSet(KEYS)
    known.add_record(company_name="株式会社デー", url="https://d.com")
    known.add_record(company_name="イー社", url="https://e-old.example.jp")

    cands = [
        {"company_name": "A社", "url": "https://a.com"},
        {"company_name": "デー", "url": "https://d.com/recruit"},      # 同一ドメイン別パス → 既知
        {"company_name": "イー社", "url": "https://e-new.example.com"},  # 社名一致・別URL → 既知
        {"company_name": "A社", "url": "http://www.a.com/"},            # run内重複
        {"company_name": "", "url": ""},                                # 空
        {"company_name": "B社", "url": "https://b.com", "note": "keep"},
    ]
    kept, st = screen_records(cands, known)
    check("kept社名", [r["company_name"] for r in kept], ["A社", "B社"])
    check("他列の素通し", kept[1].get("note"), "keep")
    check("input", st["input"], 6)
    check("drop_known", st["drop_known"], 2)
    check("drop_dup", st["drop_dup"], 1)
    check("drop_empty", st["drop_empty"], 1)
    check("kept数", st["kept"], 2)

    # 既知セットが空なら素通し（＝dump失敗時に収集を止めないフェイルソフト）
    kept2, st2 = screen_records([{"company_name": "A社", "url": "https://a.com"}], ef.ExcludeSet(KEYS))
    check("空セットは素通し", st2["kept"], 1)
    check("空セットで既知除外0", st2["drop_known"], 0)

    # JSON 往復（dump → load）で照合が壊れないこと
    es = ef.ExcludeSet(KEYS)
    es.add_record(company_name="株式会社エフ", url="https://f.co.jp")
    j = dump_to_json(es, [{"title": "シート1", "rows": 1}])
    tmp = Path(__file__).with_name("_known_selftest.json")
    tmp.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    try:
        back = load_from_json(str(tmp))
        check("JSON往復 domain一致", back.match(company_name="", url="https://www.f.co.jp/contact"), "domain")
        check("JSON往復 社名一致", back.match(company_name="エフ", url=""), "company")
    finally:
        tmp.unlink(missing_ok=True)

    # ---- #53 回帰: 会社リストでないタブのセル1つで走査が全滅しないこと ----
    class _FakeWS:
        def __init__(self, title, values):
            self.title, self._values = title, values

        def get_all_values(self):
            return self._values

    class _FakeSheet:
        def __init__(self, wss):
            self._wss = wss

        def worksheets(self):
            return self._wss

    # 事故そのものの再現: 「現在の設定」タブが走査の途中に挟まる並び。
    # 従来は2番目のタブで ValueError が抜け、**3番目の除外リストごと全部失われて**いた。
    accident = _FakeSheet([
        _FakeWS("シート1", [["会社名", "URL"],
                            ["株式会社アルファ", "https://alpha.example.com"]]),
        _FakeWS("現在の設定", [["設定項目", "現在の値"],
                             ["業種", "Web制作会社／Webマーケ会社／デザイン会社"],
                             ["件数", "200"]]),
        _FakeWS("除外リスト", [["会社名", "URL"],
                            ["株式会社ブラボー", "https://bravo.example.com"],
                            ["株式会社チャーリー", ""],
                            ["", "https://delta.example.com"]]),
    ])
    es_a, detail_a, deg_a = build_known_set(accident, verbose=False)
    check("事故タブの後ろのタブも走査される", [d["title"] for d in detail_a],
          ["シート1", "現在の設定", "除外リスト"])
    check("正常な走査は degraded にしない", deg_a, [])
    check("除外リストのドメインが残る", "bravo.example.com" in es_a.domains, True)
    check("URL無し行の社名も残る", "チャーリー" in es_a.companies, True)
    check("社名無し行のドメインも残る", "delta.example.com" in es_a.domains, True)
    check("事故セルはドメインキーを作らない",
          any("／" in d or "web制作会社" in d for d in es_a.domains), False)

    # 防御の確認: add_record が何かの理由で投げても、その行だけ飛ばして続行すること。
    orig_add = ef.ExcludeSet.add_record

    def _boom(self, *, company_name="", url="", phone=""):
        if company_name == "株式会社ボム":
            raise ValueError("injected failure")
        return orig_add(self, company_name=company_name, url=url, phone=phone)

    ef.ExcludeSet.add_record = _boom
    try:
        es_b, detail_b, deg_b = build_known_set(_FakeSheet([
            _FakeWS("シート1", [["会社名", "URL"],
                                ["株式会社エコー", "https://echo.example.com"],
                                ["株式会社ボム", "https://bomb.example.com"],
                                ["株式会社フォックス", "https://fox.example.com"]]),
        ]), verbose=False)
    finally:
        ef.ExcludeSet.add_record = orig_add
    check("例外行の前後が生き残る",
          sorted(es_b.domains), ["echo.example.com", "fox.example.com"])
    check("読み飛ばし件数を数える", detail_b[0]["skipped"], 1)
    check("読み飛ばしは行数に含めない", detail_b[0]["rows"], 2)
    check("行の取りこぼしは degraded になる", len(deg_b), 1)

    # ---- #53 degraded 判定: 「本当に行を失ったとき」だけ立てる ----
    class _DeadWS:
        title = "壊れタブ"

        def get_all_values(self):
            raise RuntimeError("APIError: 503")

    class _DeadSheet:
        def worksheets(self):
            raise RuntimeError("APIError: permission")

    _es, _d, deg_tab = build_known_set(_FakeSheet([
        _FakeWS("シート1", [["会社名", "URL"], ["株式会社ゴルフ", "https://golf.example.com"]]),
        _DeadWS(),
    ]), verbose=False)
    check("読めないタブは degraded", len(deg_tab), 1)
    check("読めるタブぶんは残る", "golf.example.com" in _es.domains, True)

    _es2, _d2, deg_all = build_known_set(_DeadSheet(), verbose=False)
    check("タブ一覧が取れないのも degraded", len(deg_all), 1)

    # ★誤検知させない側（ここを間違えると正常なシートで毎晩止まる）
    _es3, _d3, deg_ok = build_known_set(_FakeSheet([
        _FakeWS("シート1", [["会社名", "URL"], ["株式会社ホテル", "https://hotel.example.com"]]),
        _FakeWS("空タブ", [["会社名", "URL"]]),                  # 空＝失うものが無い
        _FakeWS("メモ", [["項目", "内容"], ["ひとこと", "後で見る"]]),  # 位置指定に落ちるのは設計どおり
    ]), verbose=False)
    check("空タブ・独自タブは degraded にしない", deg_ok, [])

    # JSON に degraded が載ること（追記側が読むための橋渡し）
    check("dump_to_json に degraded",
          dump_to_json(_es3, _d3, deg_tab).get("degraded"), deg_tab)

    # ---- #53 (a)(b)(c) 判定: 全タブ開いたうえで「中身」で会社リストか決める ----
    def verdict(header, data):
        ci, ui, why = classify_worksheet(header, data)
        return ("使わない" if (ci is None and ui is None) else why.split(")")[0] + ")")

    # 会社リスト側 = 必ず使う（取りこぼしたら除外漏れ＝事故）
    check("標準の営業リスト", verdict(["会社名", "URL"], [["株式会社ア", "https://a.jp"]]), "(a)")
    check("社名だけの除外リスト", verdict(["会社名"], [["株式会社イ"], ["有限会社ウ"]]), "(a)")
    check("見出しが語彙に無い除外リスト(裸ドメイン)",
          verdict(["法人名", "ドメイン"], [["株式会社エ", "e.co.jp"], ["有限会社オ", "o.jp"]]), "(b)")
    check("見出しも語彙に無く URL も無い(社名の形で救う)",
          verdict(["名前", "備考"], [["株式会社カ", "至急"], ["有限会社キ", "済"]]), "(c)")

    # 会社リストでない側 = 使わない（ここを使うと実在の会社が黙って収集対象外になる）
    check("★現在の設定タブ（事故タブ）",
          verdict(["設定項目", "現在の値"],
                  [["業種", "Web制作会社／Webマーケ会社／デザイン会社"], ["件数", "200"]]), "使わない")
    check("★整備中の営業部タブ",
          verdict(["担当", "メモ"], [["田中", "デザイン"], ["佐藤", "広告代理店"], ["鈴木", "来週"]]),
          "使わない")
    check("★営業文テンプレのタブ",
          verdict(["パターン名", "本文"],
                  [["制作会社向け", "株式会社{company_name} 様。突然のご連絡失礼します。"]]), "使わない")

    # 『デザイン』が除外条件に入らないこと＝実在の会社を黙って弾かない（本件の核心）
    _es4, _d4, _g4 = build_known_set(_FakeSheet([
        _FakeWS("営業部", [["担当", "メモ"], ["田中", "デザイン"], ["佐藤", "広告代理店"]]),
    ]), verbose=False)
    check("整備中タブの語は照合キーにならない", (sorted(_es4.companies), sorted(_es4.domains)), ([], []))

    # 会社リストと確定したタブでは、社名列が語彙で決まらなくても位置で拾う
    ci_p, ui_p, _w = classify_worksheet(["取引先", "HP"], [["株式会社ク", "https://k.jp"]])
    check("確定タブ内なら社名列を位置で補える", (ci_p, ui_p), (0, 1))

    print("=== known_companies selftest:", "PASS" if ok else "FAIL", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
