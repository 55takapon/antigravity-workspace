"""診断トレース集計レポート — logs/trace_<run_id>.jsonl を読み、次の一手を数字で示す。

`_trace_logger.TraceCollector` が書いた 1 社 1 行の JSONL を集計し、以下を表示する:

    1. 成功率 / provider 別内訳
    2. 失敗カテゴリ別 Pareto（どの失敗が多いか）
    3. Stage 別 到達・離脱（どこで止まっているか）
    4. 人間確認キュー（needs_human_review の会社一覧）
    5. ★辞書追加候補 — 未マッチだったフォーム欄ラベルを集計し
       「"<ラベル>" を labels.json に追加で N 社救済」を提示（ループの肝）

使い方:
    python scripts/trace_report.py logs/trace_20260613_153000.jsonl
    python scripts/trace_report.py logs/trace_*.jsonl     # 複数ランをまとめて

依存なし（標準ライブラリのみ）。送信処理には一切触れない読み取り専用ツール。
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def _load(paths: list[str]) -> list[dict]:
    records: list[dict] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            sys.stderr.write(f"[trace_report] not found: {path}\n")
            continue
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    sys.stderr.write(f"[trace_report] skip bad line: {e}\n")
    return records


def _section(title: str) -> None:
    print()
    print(f"── {title} " + "─" * max(0, 48 - len(title)))


def _success_rate(records: list[dict]) -> None:
    total = len(records)
    completed = sum(1 for r in records if r.get("final_status") == "completed")
    skipped = sum(1 for r in records if r.get("final_status") == "skipped")
    failed = total - completed - skipped
    rate = (completed / total * 100) if total else 0.0
    _section("成績サマリー")
    print(f"  対象 {total} 社 / 成功 {completed} ({rate:.1f}%) / "
          f"skip {skipped} / 失敗 {failed}")

    by_provider = Counter(
        (r.get("final_provider") or "none")
        for r in records if r.get("final_status") == "completed"
    )
    if by_provider:
        print("  成功の provider 内訳:")
        for prov, n in by_provider.most_common():
            cost = {"http_post": "¥0", "general_form": "¥0〜2",
                    "workflow_cache": "¥0", "browser_use": "約¥249"}.get(prov, "?")
            print(f"    {prov:14s}: {n:3d}  (コスト目安/社 {cost})")


def _failure_pareto(records: list[dict]) -> None:
    cats = Counter(
        r.get("failure_category") or "unknown"
        for r in records if r.get("final_status") != "completed"
    )
    _section("失敗カテゴリ Pareto（多い順）")
    if not cats:
        print("  失敗なし 🎉")
        return
    for cat, n in cats.most_common():
        print(f"  {n:3d}  {cat}")


def _stage_dropoff(records: list[dict]) -> None:
    # 各社が最後に触れた Stage と、その結果を集計
    last_stage = Counter()
    for r in records:
        stages = r.get("stages") or []
        if not stages:
            last_stage[("(no stage)", r.get("final_status") or "?")] += 1
            continue
        s = stages[-1]
        last_stage[(s.get("stage") or "?", s.get("result") or "?")] += 1
    _section("Stage 別 到達・離脱")
    for (stage, result), n in sorted(last_stage.items()):
        print(f"  {stage:18s} → {result:12s}: {n}")


def _human_review_queue(records: list[dict]) -> None:
    queue = [r for r in records if r.get("needs_human_review")]
    _section(f"人間確認キュー（{len(queue)} 社）")
    if not queue:
        print("  なし")
        return
    for r in queue:
        print(f"  ● {r.get('company_name') or '(no name)'}")
        print(f"      理由: {r.get('human_review_reason') or r.get('failure_category')}")
        print(f"      URL : {r.get('url') or ''}")


def _dictionary_candidates(records: list[dict]) -> None:
    """★ ループの肝: 未マッチ欄ラベルを集計し、辞書追加候補として提示する。"""
    label_counter: Counter = Counter()
    label_companies: dict[str, list[str]] = {}
    for r in records:
        for lbl in (r.get("unmapped_labels") or []):
            lbl = (lbl or "").strip()
            if not lbl:
                continue
            label_counter[lbl] += 1
            label_companies.setdefault(lbl, []).append(
                r.get("company_name") or "(no name)"
            )

    _section("★ 辞書追加候補（labels.json — 未マッチだった欄ラベル）")
    if not label_counter:
        print("  未マッチ欄なし（または Stage 1.5 未到達）")
    else:
        print("  ※ 出現の多い順。意味を当てて labels.json の aliases に追記すると、")
        print("     同じ言い回しのフォームが次回から自動でヒットします。")
        print()
        for lbl, n in label_counter.most_common(20):
            companies = label_companies[lbl]
            sample = "、".join(companies[:3]) + ("…" if len(companies) > 3 else "")
            print(f"  {n:3d}社  「{lbl}」")
            print(f"         例: {sample}")

    # 送信ボタン未検出 / 完了確認できず は別辞書の対象 — 件数だけ示す
    submit_miss = sum(
        1 for r in records if r.get("failure_category") == "submit_not_found"
    )
    conf_unclear = sum(
        1 for r in records if r.get("failure_category") == "confirmation_unclear"
    )
    if submit_miss or conf_unclear:
        print()
        print("  関連（別辞書の強化対象）:")
        if submit_miss:
            print(f"    送信ボタン未検出 {submit_miss} 社 → submit-buttons.json 要強化")
        if conf_unclear:
            print(f"    完了確認できず {conf_unclear} 社 → confirmation-signals.json 要強化"
                  "（人が成功確認後に語彙化）")


def main(argv: list[str]) -> int:
    if not argv:
        sys.stderr.write(
            "usage: python scripts/trace_report.py <trace_*.jsonl> [more.jsonl ...]\n"
        )
        return 1
    records = _load(argv)
    if not records:
        sys.stderr.write("[trace_report] レコードがありません。\n")
        return 1

    print("=" * 56)
    print(f" 診断トレース集計 — {len(records)} レコード")
    print("=" * 56)
    _success_rate(records)
    _failure_pareto(records)
    _stage_dropoff(records)
    _human_review_queue(records)
    _dictionary_candidates(records)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
