#!/usr/bin/env python3
"""Tier B 無人並列送信用の --mcp-config を生成する。

内容: opener-core（既存登録を流用＝get_skill_flow でサーバー秘匿フローを取得）
     ＋ playwright1..N（各 --headless --isolated ＝独立ヘッドレスブラウザ N 台）。
--strict-mcp-config と併用して、送信ランのMCPをこのファイルの内容だけに固定する。

usage: python tierb_mcpconfig.py <N> <out_path>
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

HOME = Path.home()

# ★Node系バイナリの置き場所候補。kick_sales.sh の _add_path ループ／setup_schedule.py の
#   NODE_BIN_CANDIDATES と**同一に保つこと**（tests/test_scheduler_node_path.py が3者の一致を検証）。
#   2026-08-19: Apple Silicon の Homebrew（/opt/homebrew/bin）が launchd のPATHから漏れており、
#   npx が見つからず Tier B のブラウザが1台も起動しないまま「完了」になっていた。
NODE_BIN_CANDIDATES = [
    HOME / ".nodebrew/current/bin",
    HOME / ".npm-global/bin",
    HOME / ".volta/bin",
    Path("/opt/homebrew/bin"),
    Path("/usr/local/bin"),
    HOME / ".local/bin",
]


def _nvm_bin() -> Path | None:
    """nvm は版ごとにディレクトリが分かれる。default エイリアス優先、無ければ最新版。"""
    root = HOME / ".nvm/versions/node"
    if not root.is_dir():
        return None
    alias = HOME / ".nvm/alias/default"
    if alias.is_file():
        v = alias.read_text(encoding="utf-8", errors="ignore").strip().lstrip("v")
        cand = root / f"v{v}" / "bin"
        if cand.is_dir():
            return cand
    vers = sorted((p for p in root.iterdir() if (p / "bin").is_dir()), key=lambda p: p.name)
    return (vers[-1] / "bin") if vers else None


def resolve_bin(name: str) -> Path | None:
    """PATH → 候補ディレクトリの順に実行可能ファイルを探す。

    ★launchd 起動では PATH が最小限なので、PATH だけに頼ってはいけない（それが今回の事故）。
    """
    p = shutil.which(name)
    if p:
        return Path(p)
    cands = list(NODE_BIN_CANDIDATES)
    nv = _nvm_bin()
    if nv:
        cands.append(nv)
    for d in cands:
        c = d / name
        if c.is_file() and os.access(c, os.X_OK):
            return c
    return None


def load_opener_core() -> dict | None:
    """~/.claude.json（top-level または project スコープ）から opener-core 登録を探す。"""
    p = HOME / ".claude.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    top = d.get("mcpServers", {})
    if "opener-core" in top:
        return top["opener-core"]
    for proj in d.get("projects", {}).values():
        m = proj.get("mcpServers", {})
        if "opener-core" in m:
            return m["opener-core"]
    return None


def main() -> int:
    # preflight（007 setup_schedule.py）から「実行時とまったく同じ解決規則」で問い合わせるための口。
    # ★点検と本番で別の探し方をしていたのが 2026-08-19 の事故の一因（点検はGOと出るのに本番で通れない）。
    if len(sys.argv) >= 2 and sys.argv[1] == "--print-npx":
        p = resolve_bin("npx")
        if not p:
            print("npx を解決できない", file=sys.stderr)
            return 4
        print(str(p))
        return 0

    if len(sys.argv) < 3:
        print("usage: tierb_mcpconfig.py <N> <out_path> | --print-npx", file=sys.stderr)
        return 1
    n = max(1, int(sys.argv[1]))
    out = Path(sys.argv[2])

    # ★"npx" という名前ではなく解決済みの絶対パスを書く＝PATHに依存しない。
    npx = resolve_bin("npx")
    if not npx:
        print("[NG] npx が見つからない＝@playwright/mcp を起動できない（Tier B は1社も送れない）。\n"
              "     探した場所: PATH と " + ", ".join(str(d) for d in NODE_BIN_CANDIDATES) + "\n"
              "     Node.js を入れるか、既に入っているなら置き場所を教えてください。", file=sys.stderr)
        return 4
    # npx 本体は node を PATH から探す（shebang が env node）。npx と同じ場所を先頭に足して渡す。
    child_path = os.pathsep.join([str(npx.parent), os.environ.get("PATH", "")]).rstrip(os.pathsep)

    servers: dict = {}
    oc = load_opener_core()
    if oc:
        servers["opener-core"] = oc
    for i in range(1, n + 1):
        servers[f"playwright{i}"] = {
            "command": str(npx),
            "args": ["@playwright/mcp@latest", "--headless", "--isolated"],
            "env": {"PATH": child_path},
        }
    out.write_text(json.dumps({"mcpServers": servers}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[mcp-config] {out}  servers={list(servers.keys())}  npx={npx}")
    if not oc:
        print("[warn] opener-core が ~/.claude.json に見つからない＝get_skill_flow を呼べない恐れ。"
              "先に opener-core を登録すること。", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
