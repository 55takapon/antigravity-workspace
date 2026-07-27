#!/usr/bin/env python3
"""verify_openers — ③冒頭文生成の「完全性の門番」（決定論・共通部品）。

生成すべき全件の SSOT である data/_opener_tasks.json（prep が書く worklist）と、
ホストAI が書いた data/_opener_results.json（{"idx": 冒頭文, ...}）を突き合わせ、
「N タスクに対し N 件の非空結果が揃っているか」だけを判定する。

なぜ必要か:
    ②生成はホストAIの手動ループで、N 件中一部を書き漏らしても後段は気づかない。
    この門番を assemble（書き戻し前）が通すことで「部分成功を静かに成功にしない」を強制する。
    単体 CLI としても使える（生成→verify→未達だけ再生成、の自己修復ループの検証部品）。

判定（すべて満たせば ok）:
    - task の idx 集合 == 非空 result の idx 集合（欠落なし）
    - result に余分な idx がない
    - 空文字の result がない（空は「未生成」と同じ扱い）

CLI:
    python scripts/verify_openers.py [--tasks PATH] [--results PATH] [--log PATH]
    未達なら欠落 idx/物理行/会社名を表示し、--log へ追記して exit 1。揃っていれば exit 0。
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPTS_DIR.parent / "data"


def _valid(v) -> bool:
    """有効な生成結果 = 空でない文字列。"""
    return isinstance(v, str) and bool(v.strip())


def check(tasks: list[dict], results: dict) -> dict:
    """tasks と results を突き合わせ、完全性の判定結果を返す（副作用なし）。"""
    task_idx = {int(t["idx"]) for t in tasks if "idx" in t}
    meta = {int(t["idx"]): t for t in tasks if "idx" in t}  # idx -> task（行/社名の逆引き用）
    valid_idx = {int(k) for k, v in results.items() if _valid(v)}
    empty_idx = {int(k) for k, v in results.items() if not _valid(v)}
    missing_idx = sorted(task_idx - valid_idx)
    extra_idx = sorted(valid_idx - task_idx)

    def _row(i: int):
        t = meta.get(i, {})
        return {"idx": i, "_row": t.get("_row"), "company_name": t.get("company_name", "")}

    return {
        "ok": not missing_idx and not extra_idx,
        "task_count": len(task_idx),
        "valid_count": len(valid_idx),
        "missing": [_row(i) for i in missing_idx],   # 生成されるべきなのに無い
        "empty_keys": sorted(empty_idx),              # キーはあるが空文字（未達の内訳）
        "extra": extra_idx,                           # tasks に無い余分な idx
    }


def format_report(res: dict, header: str | None = None) -> str:
    """人間が読める要約（stderr 向け）。末尾に改行付き。"""
    lines: list[str] = []
    if header:
        lines.append(header)
    lines.append(f"  tasks={res['task_count']} / valid_results={res['valid_count']} "
                 f"/ missing={len(res['missing'])} / extra={len(res['extra'])}")
    for m in res["missing"]:
        lines.append(f"  - 未生成 idx={m['idx']} 行={m['_row']} {m['company_name']}")
    if res["extra"]:
        lines.append(f"  - 余分な結果 idx={res['extra']}（tasks に無い。tasks/results の対応を確認）")
    if res["empty_keys"]:
        lines.append(f"  - 空文字の結果 idx={res['empty_keys']}（未生成扱い）")
    return "\n".join(lines) + "\n"


def append_log(log_path: Path, res: dict) -> None:
    """未達の痕跡を永続ログへ追記（無人実行で stderr が消えても事後調査できるように）。"""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat(timespec="seconds")
    miss = [{"idx": m["idx"], "row": m["_row"], "company": m["company_name"]} for m in res["missing"]]
    rec = {
        "ts": ts,
        "verdict": "STOP" if not res["ok"] else "OK",
        "task_count": res["task_count"],
        "valid_count": res["valid_count"],
        "missing": miss,
        "extra": res["extra"],
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load_tasks(path: Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_results(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="③冒頭文生成の完全性（tasks==results）を検証する")
    ap.add_argument("--tasks", default=str(DATA_DIR / "_opener_tasks.json"))
    ap.add_argument("--results", default=str(DATA_DIR / "_opener_results.json"))
    ap.add_argument("--log", default=str(DATA_DIR / "_opener_verify.log"))
    args = ap.parse_args()

    import sys
    tasks_p, results_p = Path(args.tasks), Path(args.results)
    if not tasks_p.exists():
        sys.stderr.write(f"[STOP] tasks が見つかりません: {tasks_p}（prep からやり直してください）\n")
        return 2
    if not results_p.exists():
        sys.stderr.write(f"[STOP] results が見つかりません: {results_p}（②生成が未実行です）\n")
        return 2

    res = check(load_tasks(tasks_p), load_results(results_p))
    if res["ok"]:
        sys.stderr.write(format_report(res, header="[OK] 生成結果は完全（全 task に非空の冒頭文あり）"))
        return 0
    sys.stderr.write(format_report(res, header="[STOP] 冒頭文の生成結果が不足しています"))
    append_log(Path(args.log), res)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
