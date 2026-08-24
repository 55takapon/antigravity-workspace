#!/usr/bin/env python3
"""check_presets — 用意した営業文が、フォームの文字数上限に収まるかを確かめる（#57）。

問い合わせフォームには入力できる文字数に上限があるものがあり、超えた分は警告も出さずに
捨てられる。このツールでは**送る前に**、用意した各版が想定の上限に収まるかを表示する。

使い方:
    python scripts/check_presets.py
    python scripts/check_presets.py --company "とても長い名前の株式会社サンプル"

文字数は「会社名」と「冒頭文」を差し込んだ後の実際の長さで測る（社名の長さで変わるため）。
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _SKILL_DIR.parents[2]
sys.path.insert(0, str(_REPO_ROOT / "shared"))

import message_presets as MP  # noqa: E402

# よくある上限（実測: 27社中6社が上限あり。値は 100/100/100/300/2000/2000 だった）
COMMON_LIMITS = (2000, 1000, 500, 300, 100)
DEFAULT_OPENER_LEN = 300     # 冒頭文の長さの目安


def _load_sender() -> dict:
    import json
    p = _REPO_ROOT / "shared" / "sender_info.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except BaseException:  # noqa: BLE001
        return {}


def _estimate_full(company: str, opener: str, sender: dict) -> str:
    """フル版の実体を組み立てて返す（長さの試算に使う）。

    full.md があればそれ。無ければ現行どおり intro.md + 冒頭文 + common_body.md。
    ここをダミーにすると「上限2000のフォームでも1000字版が選ばれる」ように見えて、
    実際の挙動と食い違う表示になる。
    """
    text = MP.load("full")
    if text is not None:
        return MP.render(text, company, opener, sender)
    parts = []
    for name in ("intro.md", "common_body.md"):
        p = _REPO_ROOT / "shared" / name
        if not p.exists():
            continue
        body = MP._read_marker_text(p)
        if name == "intro.md":
            parts.append(MP.render(body, company, "", sender))
            parts.append(opener)
        else:
            parts.append(MP.render(body, company, "", sender))
    return "\n\n".join(p for p in parts if p)


def _opener_len_hint() -> int:
    """手元の実績から冒頭文の長さを見積もる（無ければ既定値）。"""
    try:
        sys.path.insert(0, str(_SKILL_DIR / "core"))
        import glob
        import json
        lens = []
        for f in glob.glob(str(_SKILL_DIR / "logs" / "trace_*.jsonl")):
            for line in open(f, encoding="utf-8"):
                try:
                    rec = json.loads(line)
                except BaseException:  # noqa: BLE001
                    continue
                n = rec.get("opener_length")
                if isinstance(n, int) and n > 0:
                    lens.append(n)
        if lens:
            return int(statistics.median(lens))
    except BaseException:  # noqa: BLE001
        pass
    return DEFAULT_OPENER_LEN


def main() -> int:
    ap = argparse.ArgumentParser(description="営業文の長さがフォームの上限に収まるか確認する")
    ap.add_argument("--company", default="株式会社サンプル",
                    help="長さの試算に使う会社名（長い社名で試すと安全側で確認できる）")
    ap.add_argument("--opener-len", type=int, default=None,
                    help="冒頭文の長さの目安（既定: 実績から推定、無ければ300）")
    args = ap.parse_args()

    sender = _load_sender()
    opener_len = args.opener_len if args.opener_len is not None else _opener_len_hint()
    opener = "あ" * opener_len

    print("■ 用意済みの営業文")
    lengths: dict[str, int] = {}
    for name in MP.PRESET_ORDER:
        text = MP.load(name)
        if text is None:
            note = ("未作成（現在の intro.md + common_body.md を使います）"
                    if name == "full" else
                    "未作成（既定では使わないので問題ありません）"
                    if name in MP.OPT_IN_PRESETS else
                    "未作成 → この長さのフォームには送りません（要見直しに入ります）")
            print(f"  {name + '.md':<10} … {note}")
            continue
        body = MP.render(text, args.company, opener if "{opener}" in text else "", sender)
        n = MP.ui_length(body)
        lengths[name] = n
        target = None if name == "full" else int(name)
        mark = ""
        if target is not None:
            mark = ("✅ " + f"{target}字のフォームに収まります") if n <= target else \
                   (f"🔴 {target}字に収まりません。あと{n - target}字ほど削ってください")
        print(f"  {name + '.md':<10} … {n}字{'（冒頭文' + str(opener_len) + '字込み）' if '{opener}' in text else ''}"
              f"{'  ' + mark if mark else ''}")

    full_text = _estimate_full(args.company, opener, sender)
    print(f"\n■ この設定で送れる見込み（会社名『{args.company}』で試算）")
    print(f"  ※フル版の長さ: {MP.ui_length(full_text)}字")
    print("  制限なしのフォーム … ✅ 送れます")
    ng = []
    for limit in COMMON_LIMITS:
        name, _ = MP.pick(limit, args.company, opener, sender, full_message=full_text)
        if name:
            print(f"  {limit}字までのフォーム … ✅ 送れます（{name} の版）")
        else:
            print(f"  {limit}字までのフォーム … 🔴 送れません（要見直しに入ります）")
            ng.append(limit)

    if ng:
        print(f"\n  → {', '.join(str(x) for x in ng)}字のフォームに送るには、"
              f"その長さに収まる版を用意してください（shared/message_presets/README.md）。")
        if any(x <= 300 for x in ng) and MP.load("100") is not None:
            print("    ※100字版は用意済みですが、既定では使いません（送るなら実行時に明示します）。")
    print("\n  ※実測では、問い合わせフォームの約2割に文字数の上限がありました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
