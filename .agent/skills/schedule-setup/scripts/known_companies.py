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
def _rows_of_worksheet(ws) -> list[dict]:
    """1タブから {company_name,url} の配列を取り出す。日本語ヘッダは sheets_io の
    alias 解決に任せ、解決できないタブは A列=社名 / B列=URL とみなす保険を持つ。"""
    import sheets_io

    try:
        rows = sheets_io.read_rows(ws, want=["company_name", "url"])
        if any((r.get("company_name") or r.get("url")) for r in rows):
            return rows
    except Exception as e:  # noqa: BLE001  1タブの失敗で全体を止めない
        print(f"[known] タブ『{ws.title}』read_rows 失敗（位置指定で再試行）: {e}", file=sys.stderr)
    try:
        vals = ws.get_all_values()
    except Exception as e:  # noqa: BLE001
        print(f"[known] タブ『{ws.title}』読取スキップ: {e}", file=sys.stderr)
        return []
    out = []
    for row in vals[1:]:  # 1行目ヘッダ
        name = row[0] if len(row) > 0 else ""
        url = row[1] if len(row) > 1 else ""
        if (name or "").strip() or (url or "").strip():
            out.append({"company_name": name, "url": url})
    return out


def build_known_set(sh, *, tabs: list[str] | None = None, only_tabs: bool = False,
                    skip_tabs: list[str] | None = None,
                    verbose: bool = True) -> tuple["ef.ExcludeSet", list[dict]]:
    """スプレッドシート（gspread Spreadsheet）から既知社の ExcludeSet を作る。

    既定は **全タブ**（このシートに一度でも載った会社は「知っている会社」）。
    tabs を渡すと、その名前のタブ **だけ** に絞る（only_tabs=True のとき）。
    tabs + only_tabs=False は「全タブ ＋ 明示タブ」の意味だが、全タブに包含されるので実質同じ。
    skip_tabs は常に除く（呼び出し側で別セットとして数えたいタブ＝既存提携先など）。
    返り値: (ExcludeSet, [{"title":..,"rows":n}, ...])
    """
    es = ef.ExcludeSet(KEYS)
    detail: list[dict] = []
    try:
        worksheets = sh.worksheets()
    except Exception as e:  # noqa: BLE001
        print(f"[known] タブ一覧の取得に失敗: {e}", file=sys.stderr)
        return es, detail
    wanted = {t.strip() for t in (tabs or []) if t.strip()}
    skipped = {t.strip() for t in (skip_tabs or []) if t.strip()}
    for ws in worksheets:
        if only_tabs and wanted and ws.title not in wanted:
            continue
        if ws.title in skipped:
            continue
        rows = _rows_of_worksheet(ws)
        n = 0
        for r in rows:
            name = (r.get("company_name") or "").strip()
            url = (r.get("url") or "").strip()
            if not name and not url:
                continue
            es.add_record(company_name=name, url=url)
            n += 1
        detail.append({"title": ws.title, "rows": n})
        if verbose:
            print(f"[known] タブ『{ws.title}』: {n}行", file=sys.stderr)
    return es, detail


def dump_to_json(es: "ef.ExcludeSet", detail: list[dict]) -> dict:
    return {
        "version": 1,
        "domains": sorted(es.domains),
        "companies": sorted(es.companies),
        "tabs": detail,
        "size": len(es.domains) + len(es.companies),
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
    es, detail = build_known_set(sh, tabs=tabs, only_tabs=args.only_tabs)
    out = dump_to_json(es, detail)
    _write_json(args.out, out)
    print(f"[known] dump: ドメイン{len(out['domains'])} / 社名{len(out['companies'])}"
          f" / タブ{len(detail)} -> {args.out}", file=sys.stderr)
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

    print("=== known_companies selftest:", "PASS" if ok else "FAIL", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
