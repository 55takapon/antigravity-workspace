#!/usr/bin/env python3
"""④式フィールド値ハンドオフ — prep（決定要求の取り出し）。

送信ランで「辞書に無い必須/select/radio」が残った社（assist_queue の
unknown_fields）を、ユーザーの Claude Code に値を決めてもらうための
クリーンな入力に整える。③の prep_openers と同じ「prep → Claude → apply」型。

使い方:
    # 1) prep: 直近の assist_queue から決定要求を取り出す
    python scripts/field_handoff.py prep            # logs/ の最新 assist_queue を自動選択
    python scripts/field_handoff.py prep logs/assist_queue_XXXX.jsonl
      → data/field_decisions_needed.json … 各社の欄＋options＋本文抜粋（Claude が読む）
      → data/field_decisions.json        … 値が空のスケルトン（Claude が埋める）

    # 2) decide: あなた（Claude Code）が data/field_decisions_needed.json を読み、
    #    各欄を options から選んで data/field_decisions.json の "" を埋める
    #    （会社名・本文・HP文脈から最適な選択肢を1つ。捏造せず options 内から選ぶ）

    # 3) apply: 決定を渡して未送信社だけ再送信
    python scripts/run_send.py <input.csv> --decisions data/field_decisions.json
    #  または Sheets 経由:
    python scripts/run_on_sheet.py "<シートURL>" --decisions data/field_decisions.json --force
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPTS_DIR.parent
LOGS_DIR = SKILL_DIR / "logs"
DATA_DIR = SKILL_DIR / "data"

NEEDED_PATH = DATA_DIR / "field_decisions_needed.json"
DECISIONS_PATH = DATA_DIR / "field_decisions.json"


def _latest_assist_queue() -> Path | None:
    files = sorted(LOGS_DIR.glob("assist_queue_*.jsonl"), reverse=True)
    return files[0] if files else None


def _load_queue(path: Path) -> list[dict]:
    entries: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def prep(queue_path: Path | None) -> int:
    qp = queue_path or _latest_assist_queue()
    if not qp or not qp.exists():
        print("[エラー] assist_queue が見つかりません（先に送信を1回実行してください）。",
              file=sys.stderr)
        return 1

    entries = _load_queue(qp)
    needed: list[dict] = []
    skeleton: dict[str, dict] = {}

    for e in entries:
        fd = e.get("field_detail") or {}
        unknown = fd.get("unknown_fields") or []
        # options を伴う未知欄だけが「値の決定」を要する（CAPTCHA だけの社は対象外）。
        decidable = [
            {"label": u.get("label") or "", "type": u.get("type") or "",
             "options": u.get("options") or []}
            for u in unknown
            if (u.get("label") and (u.get("options") or
                (u.get("type") or "").lower() in ("select", "select-one", "radio")))
        ]
        if not decidable:
            continue
        url = e.get("url") or ""
        company = e.get("company_name") or ""
        msg = (e.get("message") or "").strip().replace("\n", " ")
        needed.append({
            "url": url,
            "company_name": company,
            "message_excerpt": msg[:160],
            "fields": decidable,
        })
        key = url or company
        if key:
            skeleton[key] = {f["label"]: "" for f in decidable}

    if not needed:
        print(f"[情報] {qp.name}: 値決定が必要な未知欄はありませんでした。", file=sys.stderr)
        return 0

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    NEEDED_PATH.write_text(
        json.dumps(needed, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # 既存の決定があれば壊さない（追記マージ：未知キーだけ空で足す）。
    existing: dict = {}
    if DECISIONS_PATH.exists():
        try:
            existing = json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
        except BaseException:  # noqa: BLE001
            existing = {}
    for k, v in skeleton.items():
        slot = existing.setdefault(k, {})
        for label in v:
            slot.setdefault(label, "")
    DECISIONS_PATH.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[prep] {qp.name} → {len(needed)} 社・"
          f"{sum(len(n['fields']) for n in needed)} 欄の決定要求を書き出しました。", file=sys.stderr)
    print(f"  - 読む:   {NEEDED_PATH}", file=sys.stderr)
    print(f"  - 埋める: {DECISIONS_PATH}（各欄を options から1つ選んで \"\" を置換）", file=sys.stderr)
    print("  次: あなた(Claude)が値を決めて DECISIONS を埋め、"
          "run_send/run_on_sheet に --decisions で渡して再送信。", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="④式フィールド値ハンドオフ (prep)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_prep = sub.add_parser("prep", help="assist_queue から決定要求を取り出す")
    p_prep.add_argument("queue", nargs="?", default=None,
                        help="assist_queue JSONL（省略時は logs/ の最新）")
    args = parser.parse_args(argv)

    if args.cmd == "prep":
        qp = Path(args.queue).resolve() if args.queue else None
        return prep(qp)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
