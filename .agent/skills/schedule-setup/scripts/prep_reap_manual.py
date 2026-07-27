#!/usr/bin/env python3
"""prep_reap_manual.py — prep（リスト取り）で「手動送信要」に振り分けられた行を、
メインの「シート1」から専用タブ「要手動送信_リスト取り段階」へ **移送** する（決定論・AIなし）。

なぜ:
  収集時抑止フィルタが「手動送信要」と判定した会社は、これまでシート1に他の送信候補と
  一緒に追記されていた。すると送信後もシート1に「送信前の要手動送信」が混在し続け、
  ①見かけ上の送信済み件数が薄く見える ②後で手動送信するためのリストを抜き出しにくい。
  そこで prep の最後に本スクリプトを1回だけ回し、該当行を別タブへ **移す**（=シート1から消す）。

移送のタイミング:
  prep本体（①②→message差し込み）が終わった後に呼ぶ。この時点で message は埋まっているので、
  会社名・URL・コンタクトURL・営業文(message)・ステータス の5項目を揃えて転記できる。

安全設計（既存の「壊れる所は直列」に合わせる）:
  - 転記は append（末尾追加）、移送元の削除は下(大きい行番号)からまとめて（行ズレ無し）。
  - 転記先URLで重複除去（再実行しても二重登録しない）。既に転記先に在る行も、移送元からは消す
    （＝シート1をきれいに保つのが目的なので、重複でも移送元からは必ず除去する）。
  - --preview は1セルも書かない（対象の可視化だけ）。--dry-run 同義。

使い方:
  python3 prep_reap_manual.py <sheet_key> [--source-worksheet NAME] \
      [--dest-worksheet 要手動送信_リスト取り段階] [--status-values 手動送信要,要手動送信] \
      [--preview] [--creds PATH]
  python3 prep_reap_manual.py --selftest     # シート不要（仕分けロジックの純テスト）
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]  # .../<repo>/.claude/skills/007-schedule-setup/scripts
sys.path.insert(0, str(REPO_ROOT / "shared"))

DEST_WORKSHEET = "要手動送信_リスト取り段階"
# prep が付ける値は「手動送信要」。送信段の relabel 表記「要手動送信」も念のため拾う。
DEFAULT_STATUS_VALUES = ["手動送信要", "要手動送信"]
# 転記する統一スキーマ列（この順で別タブへ並べる）。
CARRY_COLS = ["company_name", "url", "contact_url", "message", "status"]
# 転記先タブに書くステータス表記（ユーザー仕様＝「要手動送信」に正規化）。
DEST_STATUS_LABEL = "要手動送信"
# status/message は sheets_io の既定 aliases に無いので、ここで日本語ヘッダ候補を補う。
READ_ALIASES = {
    "status": ["status", "ステータス", "状態", "ステータス（送信結果）"],
}


def norm_url_key(u: str) -> str:
    """重複照合用のURL正規化（001/prep_merge_append と同じ規則）。"""
    u = (u or "").strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def is_manual(status: str, status_values: list[str]) -> bool:
    """status が手動送信要マーカーに一致するか（前後空白・全半角の揺れを軽く吸収）。"""
    s = (status or "").strip()
    return s in status_values


def select_manual_rows(rows: list[dict], status_values: list[str]) -> list[dict]:
    """read_rows 由来の行（_row 付き）から、status が手動送信要の行だけを抜く（純ロジック）。"""
    return [r for r in rows if is_manual(r.get("status", ""), status_values)]


def partition_for_move(manual_rows: list[dict], dest_existing_norm: set[str]) -> tuple[list[dict], list[dict]]:
    """手動送信要の行を「転記先へ新規追記する分」と「既に転記先に在る分(=追記不要)」に分ける。
    どちらも移送元(シート1)からは削除する（返り値の2つ目も削除対象に含める呼び出し側の想定）。
    返り値: (to_append, already_in_dest)
    """
    to_append: list[dict] = []
    already: list[dict] = []
    seen: set[str] = set()  # 同一バッチ内の重複URLも1件に畳む
    for r in manual_rows:
        key = norm_url_key(r.get("url", ""))
        if key and (key in dest_existing_norm or key in seen):
            already.append(r)
            continue
        if key:
            seen.add(key)
        to_append.append(r)
    return to_append, already


def _resolve_dest_header(source_header: list[str]) -> list[str]:
    """転記先タブの1行目ヘッダを決める。シート1の実ヘッダ名に極力合わせ（見た目の一貫性）、
    見つからない列は日本語の既定名でフォールバックする。"""
    import sheets_io
    # source_header から CARRY_COLS 各 canonical の実ヘッダ名を引く
    colmap = sheets_io.find_columns(source_header, CARRY_COLS, aliases=READ_ALIASES)
    defaults = {
        "company_name": "会社名", "url": "URL", "contact_url": "コンタクトURL",
        "message": "営業文", "status": "ステータス",
    }
    header: list[str] = []
    for c in CARRY_COLS:
        idx = colmap.get(c)
        if idx is not None and 0 <= idx < len(source_header) and (source_header[idx] or "").strip():
            header.append(source_header[idx])
        else:
            header.append(defaults[c])
    return header


def main() -> int:
    ap = argparse.ArgumentParser(
        description="prep の『手動送信要』行をシート1から専用タブへ移送する（転記+削除）")
    ap.add_argument("spreadsheet", nargs="?", help="スプレッドシートのURLまたはキー")
    ap.add_argument("--source-worksheet", default=None, help="移送元タブ名（既定: 先頭シート=シート1）")
    ap.add_argument("--dest-worksheet", default=DEST_WORKSHEET, help=f"移送先タブ名（既定: {DEST_WORKSHEET}）")
    ap.add_argument("--status-values", default=",".join(DEFAULT_STATUS_VALUES),
                    help="手動送信要とみなす status 値（カンマ区切り）")
    ap.add_argument("--preview", action="store_true", help="対象の件数だけ表示・1セルも書かない")
    ap.add_argument("--dry-run", action="store_true", help="--preview と同義")
    ap.add_argument("--creds", default=None)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    if not args.spreadsheet:
        print("[エラー] spreadsheet（シートURL/キー）が必要です。", file=sys.stderr)
        return 2

    status_values = [s.strip() for s in args.status_values.split(",") if s.strip()]
    preview = args.preview or args.dry_run

    import sheets_io  # 遅延import（--selftest はシート非依存で通す）
    try:
        client = sheets_io.get_client(args.creds)
        src = sheets_io.open_worksheet(args.spreadsheet, args.source_worksheet, client=client)
    except (FileNotFoundError, ImportError) as e:
        print(f"[エラー] {e}", file=sys.stderr)
        return 2

    # 移送元を読む（_row 付き）。status は aliases で日本語ヘッダも拾う。
    rows = sheets_io.read_rows(src, want=CARRY_COLS, aliases=READ_ALIASES)
    manual_rows = select_manual_rows(rows, status_values)

    if not manual_rows:
        print(f"[done] 移送対象なし（{src.title}）。手動送信要の行は見つかりませんでした。", file=sys.stderr)
        return 0

    source_header = src.row_values(1)
    dest_header = _resolve_dest_header(source_header)

    if preview:
        print(f"シート『{src.title}』→『{args.dest_worksheet}』へ移送プレビュー")
        print(f"  手動送信要の行 : {len(manual_rows)} 件")
        print(f"  転記先ヘッダ   : {dest_header}")
        for r in manual_rows[:5]:
            print(f"  - row{r['_row']}: {r.get('company_name') or '∅'} / {r.get('url') or '∅'}"
                  f" / contact={r.get('contact_url') or '∅'} / msg={'有' if r.get('message') else '空'}")
        if len(manual_rows) > 5:
            print(f"  … ほか {len(manual_rows) - 5} 件")
        print("※ プレビューのみ。シートには1セルも書き込んでいません（削除もしません）。")
        return 0

    # 転記先タブを開く/作る（新規時はシート1準拠のヘッダを1行目に置く）。
    dest, created = sheets_io.open_or_create_worksheet(
        args.spreadsheet, args.dest_worksheet, client=client, template_header=dest_header)

    # 転記先の既存URLで重複除去（再実行の二重登録防止）。
    dest_existing_norm: set[str] = set()
    dvals = dest.get_all_values()
    if dvals:
        dcolmap = sheets_io.find_columns(dvals[0], ["url"], aliases=READ_ALIASES)
        uidx = dcolmap.get("url")
        if uidx is not None:
            for drow in dvals[1:]:
                if uidx < len(drow) and drow[uidx].strip():
                    dest_existing_norm.add(norm_url_key(drow[uidx]))

    to_append, already = partition_for_move(manual_rows, dest_existing_norm)

    # 転記先ヘッダの列順で値リストを組む（append_rows の alias 解決に依存せず決定論的に並べる）。
    values = []
    for r in to_append:
        line = [
            r.get("company_name", ""),
            r.get("url", ""),
            r.get("contact_url", ""),
            r.get("message", ""),
            DEST_STATUS_LABEL,  # ステータスは「要手動送信」に統一
        ]
        values.append(line)
    appended = 0
    if values:
        dest.append_rows(values, value_input_option="RAW")
        appended = len(values)

    # 移送元(シート1)から該当行を削除（新規転記分＋既に転記先に在った分の両方＝シート1をきれいに）。
    del_rows = [int(r["_row"]) for r in manual_rows]
    deleted = sheets_io.delete_row_numbers(src, del_rows)

    tab_note = "（新規作成）" if created else ""
    print(f"[done] 移送 {len(manual_rows)}件: 転記 append={appended}"
          f"（既存重複スキップ {len(already)}） / シート1から削除 {deleted}行"
          f" -> '{args.dest_worksheet}'{tab_note}", file=sys.stderr)
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

    # URL正規化
    check("norm scheme/www/slash", norm_url_key("HTTPS://WWW.A.com/"), "a.com")

    # is_manual: 一致/前後空白/不一致
    check("is_manual(手動送信要)", is_manual("手動送信要", DEFAULT_STATUS_VALUES), True)
    check("is_manual( 要手動送信 )", is_manual("  要手動送信  ", DEFAULT_STATUS_VALUES), True)
    check("is_manual(送信済み→False)", is_manual("送信済み", DEFAULT_STATUS_VALUES), False)
    check("is_manual(空→False)", is_manual("", DEFAULT_STATUS_VALUES), False)

    # select_manual_rows: status で抽出
    rows = [
        {"_row": 2, "company_name": "A", "url": "https://a.com", "status": "手動送信要"},
        {"_row": 3, "company_name": "B", "url": "https://b.com", "status": ""},
        {"_row": 4, "company_name": "C", "url": "https://c.com", "status": "送信済み"},
        {"_row": 5, "company_name": "D", "url": "https://d.com", "status": "要手動送信"},
    ]
    picked = select_manual_rows(rows, DEFAULT_STATUS_VALUES)
    check("select 抽出行", [r["_row"] for r in picked], [2, 5])

    # partition_for_move: 既存重複は already、バッチ内重複も1件へ
    manual = [
        {"_row": 2, "url": "https://a.com"},   # 新規
        {"_row": 5, "url": "https://d.com"},   # 転記先に既存
        {"_row": 7, "url": "http://www.a.com/"},  # バッチ内でAと重複
    ]
    dest_norm = {norm_url_key("https://d.com")}
    to_append, already = partition_for_move(manual, dest_norm)
    check("to_append(新規Aのみ)", [r["_row"] for r in to_append], [2])
    check("already(D既存+A重複)", sorted(r["_row"] for r in already), [5, 7])

    # 全行が移送元の削除対象（新規+重複ともシート1から消す）
    del_rows = [int(r["_row"]) for r in manual]
    check("削除対象=全手動行", sorted(del_rows), [2, 5, 7])

    print("=== prep_reap_manual selftest:", "PASS" if ok else "FAIL", "===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
