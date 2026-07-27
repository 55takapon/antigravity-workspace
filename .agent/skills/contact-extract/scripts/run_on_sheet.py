#!/usr/bin/env python3
"""contact-extract (Google Sheets 直結版) — 検出ロジックを持たないシート⇄橋渡し。

②の問い合わせURL検出は秘匿コア(MCP contact_detect)が **あなた(Claude Code)経由** で行うため、
1本のPythonでは完結しない(③opener-generate と同型)。本スクリプトはシートの読み書きだけを担い、
検出キーワード等の秘匿ロジックはローカルに持たない(MCP側に閉じる)。

3ステップ（prep → AIが MCP contact_detect → write）:
  prep  : シートの url を読み、各社HPの <a> を素材化して batch(JSON) を出力。
          batch 各要素は {idx, _row, company_name, base_url, links}（_row=物理行番号）。
          --preview なら列マッピングと出力先だけ表示し、fetchも書き込みもしない（安全弁）。
  write : prep の batch(idx→_row) と MCP contact_detect の結果(JSON) を突き合わせ、
          method=probe の社はローカルで実在確認して contact_url を確定し、同じ行へ書き戻す。

使い方:
    python scripts/run_on_sheet.py prep  <URL> [--preview] [--limit N] [--force] [--out batch.json] [opts]
    # → AI: mcp__opener-core__contact_detect(batch.json) の結果を results.json に保存
    python scripts/run_on_sheet.py write <URL> <results.json> [--batch batch.json] [opts]

再利用（いずれも配布同梱・非秘匿）: <a>素材化=fetch_pages.extract_links、probe実在確認=write_contacts.probe。
再実行ポリシー（設計 §9-c）: 既定では contact_url 未記入の行だけ prep 対象（--force で全行）。
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

REPO_ROOT = SCRIPTS_DIR.parents[3]   # .../<repo>/.claude/skills/002-contact-extract/scripts → repo root
sys.path.insert(0, str(REPO_ROOT / "shared"))
import sheets_io  # noqa: E402

DATA_DIR = SCRIPTS_DIR.parent / "data"
DEFAULT_BATCH = DATA_DIR / "_contact_batch.json"


def _aliases(args) -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    if getattr(args, "url_col", None):
        aliases["url"] = [args.url_col]
    aliases.setdefault("contact_url", []).insert(0, args.contact_col)
    return aliases


def cmd_prep(args) -> int:
    aliases = _aliases(args)
    try:
        ws = sheets_io.open_worksheet(args.spreadsheet, args.worksheet, creds_path=args.creds)
    except (FileNotFoundError, ImportError) as e:
        print(f"[エラー] {e}", file=sys.stderr)
        return 2

    if args.preview:
        out_col = sheets_io.resolve_output_header(ws, "contact_url", args.contact_col, aliases=aliases)
        print(sheets_io.preview_mapping(ws, want=["company_name", "url", "contact_url"],
                                        outputs=[out_col], aliases=aliases))
        return 0

    rows = sheets_io.read_rows(ws, want=["company_name", "url", "contact_url", "status"], aliases=aliases)
    have_url = [r for r in rows if r.get("url")]
    if not have_url:
        print("[エラー] url 列を検出できませんでした。ヘッダに url（または『ホームページ』等）が必要です。",
              file=sys.stderr)
        return 2

    # #40 P2: status=excluded の行（除外リスト該当）は無駄なコストを避けるためスキップ（--force でも触らない）
    excluded = [r for r in have_url if str(r.get("status") or "").strip().lower() == "excluded"]
    have_url = [r for r in have_url if r not in excluded]
    targets = have_url if args.force else [r for r in have_url if not r.get("contact_url")]
    skipped_existing = len(have_url) - len(targets) + len(excluded)
    if args.limit > 0:
        targets = targets[:args.limit]
    if not targets:
        print(f"[done] 抽出対象なし（contact_url記入済み {skipped_existing}件をスキップ）。"
              "全行やり直すなら --force。", file=sys.stderr)
        return 0

    # <a> 素材化（判定はしない＝秘匿コア=MCP contact_detect の役割）。requests/bs4 は fetch_pages 側。
    import fetch_pages  # noqa: E402  (配布同梱・非秘匿。extract_links を再利用)

    print(f"対象 {len(targets)}件のHPを素材化します（workers={args.workers}）...", file=sys.stderr)
    batch: list[dict | None] = [None] * len(targets)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        fut = {ex.submit(fetch_pages.extract_links, r.get("url", "")): i for i, r in enumerate(targets)}
        done = 0
        for f in concurrent.futures.as_completed(fut):
            i = fut[f]
            try:
                d = f.result()
            except Exception:  # noqa: BLE001 — Fail-safe（取得失敗は links 空）
                d = {"base_url": targets[i].get("url", ""), "links": []}
            batch[i] = {"idx": i, "_row": targets[i].get("_row"),
                        "company_name": targets[i].get("company_name", ""), **d}
            done += 1
            if done % 10 == 0 or done == len(targets):
                print(f"進捗: {done}/{len(targets)}", file=sys.stderr)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(batch, ensure_ascii=False), encoding="utf-8")
    got = sum(1 for b in batch if b and b.get("links"))
    print(f"[done] {len(batch)}社を素材化（リンク取得 {got}社・記入済み {skipped_existing}件スキップ）-> {out}",
          file=sys.stderr)
    print("次: MCPツール mcp__opener-core__contact_detect にこの batch(JSON) を渡し、"
          "戻り(results)を JSON 保存 → "
          f"`run_on_sheet.py write \"{args.spreadsheet}\" <results.json>` で書き戻す。", file=sys.stderr)
    return 0


def cmd_write(args) -> int:
    aliases = _aliases(args)
    import write_contacts  # noqa: E402  (配布同梱・非秘匿。probe / load_results を再利用)

    # prep の batch から idx→_row 対応を作る（行ズレ防止：物理行で書き戻す）
    batch = json.loads(Path(args.batch).read_text(encoding="utf-8"))
    row_by_idx = {b.get("idx", i): b.get("_row") for i, b in enumerate(batch)}

    results = write_contacts.load_results(args.results)   # {idx: {method, contact_url, probe_candidates}}

    contact_by_idx: dict = {}
    probe_jobs: dict = {}
    for idx, r in results.items():
        if r.get("method") == "link" and r.get("contact_url"):
            contact_by_idx[idx] = r["contact_url"]
        elif r.get("method") == "probe":
            probe_jobs[idx] = r.get("probe_candidates", [])

    # probe 実在確認は並列（ローカルで HEAD/GET）。判定ロジックは write_contacts に一元化。
    if probe_jobs:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
            fut = {ex.submit(write_contacts.probe, c): idx for idx, c in probe_jobs.items()}
            for f in concurrent.futures.as_completed(fut):
                idx = fut[f]
                try:
                    contact_by_idx[idx] = f.result()
                except Exception:  # noqa: BLE001 — Fail-safe
                    contact_by_idx[idx] = ""

    try:
        ws = sheets_io.open_worksheet(args.spreadsheet, args.worksheet, creds_path=args.creds)
    except (FileNotFoundError, ImportError) as e:
        print(f"[エラー] {e}", file=sys.stderr)
        return 2

    # 書き戻し先: 既存ヘッダに contact_url 相当（例「お問い合わせページリンク」）があればその列へ。
    out_col = sheets_io.resolve_output_header(ws, "contact_url", args.contact_col, aliases=aliases)
    out_rows: list[dict] = []
    for idx, url in contact_by_idx.items():
        row_no = row_by_idx.get(idx)
        if not row_no or not url:
            continue
        out_rows.append({"_row": row_no, out_col: url})

    if not out_rows:
        found = sum(1 for u in contact_by_idx.values() if u)
        print(f"[done] 書き戻し対象なし（検出 {found}/{len(batch)}）。results/batch を確認。", file=sys.stderr)
        return 0

    written = sheets_io.write_cells(ws, out_rows, [out_col], overwrite=True)
    found = sum(1 for u in contact_by_idx.values() if u)
    print(f"[done] found={found}/{len(batch)} written={written} -> sheet '{ws.title}' col '{out_col}'",
          file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Google Sheets直結の②：検出はMCP contact_detect、本スクリプトはシート橋渡し")
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("spreadsheet", help="スプレッドシートのURLまたはキー")
    common.add_argument("--worksheet", default=None)
    common.add_argument("--workers", type=int, default=10)
    common.add_argument("--creds", default=None, help="サービスアカウントJSON（既定探索は sheets_io に準拠）")
    common.add_argument("--url-col", default=None, help="URLヘッダ名（既定: url / 自動検出）")
    common.add_argument("--contact-col", default="contact_url", help="contact_url の出力先ヘッダ名")

    p = sub.add_parser("prep", parents=[common],
                       help="シート→各社HPの<a>素材化(batch JSON)。--preview で確認のみ")
    p.add_argument("--preview", action="store_true",
                   help="列マッピングと出力先だけ表示して終了（fetchも書き込みもしない）")
    p.add_argument("--limit", type=int, default=0, help="先頭N社のみ（0=全件）。抽出対象に対しての先頭N社")
    p.add_argument("--force", action="store_true", help="contact_url 記入済みの行も対象にする")
    p.add_argument("--out", default=str(DEFAULT_BATCH), help="batch(JSON) の出力先")
    p.set_defaults(func=cmd_prep)

    w = sub.add_parser("write", parents=[common],
                       help="MCP contact_detect の結果をシートへ書き戻す（probeはローカル確認）")
    w.add_argument("results", help="MCP contact_detect の結果JSON")
    w.add_argument("--batch", default=str(DEFAULT_BATCH), help="prep が書いた batch(JSON: idx→_row)")
    w.set_defaults(func=cmd_write)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
