#!/usr/bin/env python3
"""Tier B 無人並列送信用の --mcp-config を生成する。

内容: opener-core（既存登録を流用＝get_skill_flow でサーバー秘匿フローを取得）
     ＋ playwright1..N（各 --headless --isolated ＝独立ヘッドレスブラウザ N 台）。
--strict-mcp-config と併用して、送信ランのMCPをこのファイルの内容だけに固定する。

usage: python tierb_mcpconfig.py <N> <out_path>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HOME = Path.home()


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
    if len(sys.argv) < 3:
        print("usage: tierb_mcpconfig.py <N> <out_path>", file=sys.stderr)
        return 1
    n = max(1, int(sys.argv[1]))
    out = Path(sys.argv[2])

    servers: dict = {}
    oc = load_opener_core()
    if oc:
        servers["opener-core"] = oc
    for i in range(1, n + 1):
        servers[f"playwright{i}"] = {
            "command": "npx",
            "args": ["@playwright/mcp@latest", "--headless", "--isolated"],
        }
    out.write_text(json.dumps({"mcpServers": servers}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[mcp-config] {out}  servers={list(servers.keys())}")
    if not oc:
        print("[warn] opener-core が ~/.claude.json に見つからない＝get_skill_flow を呼べない恐れ。"
              "先に opener-core を登録すること。", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
