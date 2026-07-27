#!/usr/bin/env python3
"""template-fill (Google Sheets 直結版) — シートの company_name 列を読み、
テンプレ営業文の {company_name} をその社名に差し替えて message 列（既定）へ書き戻す。

AIなし・HP不要の決定論的な文字置換。共有アダプタ shared/sheets_io.py 経由でシートを
読み書きする。テンプレは shared/message_template.md（`---本文ここから/ここまで---` の間）。

使い方:
    python scripts/merge_on_sheet.py <spreadsheet_url_or_key> [options]

options:
    --worksheet NAME   対象ワークシート名（既定: 先頭シート）
    --template PATH    テンプレ営業文ファイル（既定: shared/message_template.md）
    --out-col NAME     差し込んだ営業文の出力先ヘッダ名（既定: message）
    --company-col NAME 会社名の入力列ヘッダ名（既定: company_name / 自動検出）
    --limit N          先頭N社のみ処理（0=全件、既定0）。※差し込み対象に対しての先頭N社
    --force            既に出力列が埋まっている行も再生成する（既定はスキップ）
    --preview          列マッピングと出力先だけ表示して終了（1セルも書かない）
    --creds PATH       サービスアカウントJSON（既定の探索順は sheets_io に準拠）

再実行ポリシー: 既定では出力列が未記入の行だけ差し込む（二重生成を避ける）。
全行やり直すなら --force。書き戻しは write_cells(overwrite=True)。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]   # .../<repo>/.claude/skills/004-template-fill/scripts
sys.path.insert(0, str(REPO_ROOT / "shared"))
import sheets_io  # noqa: E402

DEFAULT_TEMPLATE = REPO_ROOT / "shared" / "message_template.md"


def load_template(path: Path) -> str:
    """テンプレ営業文の本文を返す。`---本文ここから---`〜`---本文ここまで---` の間だけを
    採用し、無ければ全文。行頭 `<!--` のコメント行は落とす（common_body と同じ流儀）。"""
    raw = path.read_text(encoding="utf-8")
    m = re.search(r"---本文ここから---\n(.*?)\n---本文ここまで---", raw, flags=re.S)
    body = m.group(1) if m else raw
    lines = [ln for ln in body.splitlines() if not ln.lstrip().startswith("<!--")]
    return "\n".join(lines).strip()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Google Sheetsの company_name をテンプレに差し込んで message を作る（AIなし）")
    ap.add_argument("spreadsheet", help="スプレッドシートのURLまたはキー")
    ap.add_argument("--worksheet", default=None)
    ap.add_argument("--template", default=str(DEFAULT_TEMPLATE),
                    help=f"テンプレ営業文ファイル（既定: {DEFAULT_TEMPLATE}）")
    ap.add_argument("--out-col", default="message", help="出力先ヘッダ名（既定: message）")
    ap.add_argument("--company-col", default=None, help="会社名ヘッダ名（既定: company_name / 自動検出）")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true", help="出力列が記入済みの行も再生成")
    ap.add_argument("--preview", action="store_true",
                    help="列マッピングと出力先だけ表示して終了（1セルも書かない）")
    ap.add_argument("--creds", default=None)
    args = ap.parse_args()

    tmpl_path = Path(args.template)
    if not tmpl_path.is_absolute():
        tmpl_path = (REPO_ROOT / tmpl_path).resolve()
    if not tmpl_path.exists():
        print(f"[エラー] テンプレが見つかりません: {tmpl_path}\n"
              f"  → cp shared/3_message_template.example.md shared/message_template.md して用意してください。",
              file=sys.stderr)
        return 2
    template = load_template(tmpl_path)
    if "{company_name}" not in template:
        print(f"[warn] テンプレに {{company_name}} が見当たりません。社名が差し込まれず全社同一文になります。",
              file=sys.stderr)

    aliases: dict[str, list[str]] = {}
    if args.company_col:
        aliases["company_name"] = [args.company_col]

    try:
        ws = sheets_io.open_worksheet(args.spreadsheet, args.worksheet, creds_path=args.creds)
    except (FileNotFoundError, ImportError) as e:
        print(f"[エラー] {e}", file=sys.stderr)
        return 2

    # 出力先の列を決める:
    #  - 既定(message)は既存の message 相当列（『営業文』等）へ寄せる（③/パイプライン互換）。
    #  - --out-col を明示したら、その名前の列をそのまま使う（無ければ write_cells が末尾に新設）。
    if args.out_col == "message":
        out_col = sheets_io.resolve_output_header(ws, "message", "message", aliases=aliases)
    else:
        out_col = args.out_col

    if args.preview:
        print(sheets_io.preview_mapping(ws, want=["company_name"],
                                        outputs=[out_col], aliases=aliases))
        return 0

    rows = sheets_io.read_rows(ws, want=["company_name"], aliases=aliases, require=["company_name"])
    have_company = [r for r in rows if r.get("company_name")]
    if not have_company:
        print("[エラー] company_name 列に会社名がありません。ヘッダに company_name（または『会社名』等）が必要です。",
              file=sys.stderr)
        return 2

    # 出力列の既存値で skip 判定（明示した新規列なら空＝全行が対象）。
    filled: set[int] = set()
    header = ws.row_values(1)
    if out_col in header:
        colvals = ws.col_values(header.index(out_col) + 1)  # index0=ヘッダ
        for r in have_company:
            phys = int(r["_row"])
            cur = colvals[phys - 1] if (phys - 1) < len(colvals) else ""
            if cur.strip():
                filled.add(phys)

    targets = have_company if args.force else [r for r in have_company if int(r["_row"]) not in filled]
    skipped_existing = len(have_company) - len(targets)
    if args.limit > 0:
        targets = targets[:args.limit]

    if not targets:
        print(f"[done] 差し込み対象なし（出力列『{out_col}』記入済み {skipped_existing}件をスキップ）。"
              "全行やり直すなら --force。", file=sys.stderr)
        return 0

    for r in targets:
        r[out_col] = template.replace("{company_name}", r["company_name"])
    written = sheets_io.write_cells(ws, targets, [out_col], overwrite=True)
    print(f"[done] merged={len(targets)} written={written} "
          f"skipped_existing={skipped_existing} -> sheet '{ws.title}' 列『{out_col}』", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
