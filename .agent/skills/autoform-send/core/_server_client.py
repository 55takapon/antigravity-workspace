"""formsend-core（秘匿頭脳サーバー）への薄い MCP クライアント。

役割（contract: docs/design/form_send_contract.md の 4 ツール）:
    A get_form_playbook  — 秘匿ノウハウ＋静的辞書＋noAI語彙（1ラン1回）
    B resolve_fields     — 欄ラベル→semantic 引き当て（学習辞書）。未知欄は unknown[]
    C check_domain       — 送信前ゲート（cooldown / レート）
    D report_outcome     — 結果を中央学習へ書き戻し

設計原則:
    - **Fail-safe**: サーバー未設定 / 不達 / エラー時は None を返し、呼び出し側は
      ローカル辞書・cooldown へフォールバックする（contract §5-3）。送信は止めない。
    - **薄く**: 判断ロジックは持たず、JSON-RPC で叩いて結果を返すだけ。
    - 設定は環境変数: FORMSEND_CORE_URL（例 https://formsend-core.<acct>.workers.dev/mcp）
      と FORMSEND_CORE_TOKEN（Bearer）。両方揃って初めて有効。
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional

try:
    import httpx
except ImportError:  # pragma: no cover — httpx は pyproject の依存
    httpx = None  # type: ignore


_PROTOCOL = "2025-06-18"
_TIMEOUT_S = 8.0
# 層5b: このクライアントのバージョン。サーバーの MIN_CLIENT_VERSION 以上なら通る。
# 配布物を更新するたびに日付を上げる（サーバー側 MIN を上げると旧配布を締め出せる）。
_CLIENT_VERSION = "2026-07-06"


def server_url() -> str:
    return os.environ.get("FORMSEND_CORE_URL", "").strip()


def server_token() -> str:
    return os.environ.get("FORMSEND_CORE_TOKEN", "").strip()


def is_configured() -> bool:
    """URL とトークンが揃い、httpx が使えるときだけ True。"""
    return bool(server_url() and server_token() and httpx is not None)


async def _call_tool(name: str, arguments: dict) -> Optional[dict]:
    """tools/call を 1 回叩いて content[].text の JSON をパースして返す。

    Fail-safe: 未設定 / HTTP エラー / RPC エラー / パース失敗はすべて None。
    """
    if not is_configured():
        return None
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    headers = {
        "authorization": f"Bearer {server_token()}",
        "content-type": "application/json",
        "accept": "application/json",
        "x-client-version": _CLIENT_VERSION,  # 層5b: バージョンゲート
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(server_url(), headers=headers, json=payload)
        if resp.status_code != 200:
            sys.stderr.write(
                f"[_server_client] {name} HTTP {resp.status_code} (falling back local)\n"
            )
            return None
        body = resp.json()
        if not isinstance(body, dict) or "result" not in body:
            return None
        content = (body["result"] or {}).get("content") or []
        if not content or not isinstance(content, list):
            return None
        text = content[0].get("text")
        if not text:
            return None
        return json.loads(text)
    except BaseException as e:  # noqa: BLE001 — Fail-safe
        sys.stderr.write(
            f"[_server_client] {name} error (falling back local): "
            f"{type(e).__name__}: {e}\n"
        )
        return None


# -----------------------------------------------------------------------------
# 4 ツールの薄いラッパー（戻り値の形は contract に準拠。失敗時 None）
# -----------------------------------------------------------------------------
async def get_form_playbook() -> Optional[dict]:
    """{version, guideline_text, static_labels:[{label,semantic}], no_ai_rules:[...]}"""
    return await _call_tool("get_form_playbook", {})


async def resolve_fields(
    form_fingerprint: Optional[str],
    fields: list[dict],
) -> Optional[dict]:
    """{resolved:[{label,semantic,value_source}], unknown:[label,...]}

    fields: [{label, type, options?}]
    """
    args: dict[str, Any] = {"fields": fields}
    if form_fingerprint:
        args["form_fingerprint"] = form_fingerprint
    return await _call_tool("resolve_fields", args)


async def check_domain(domain: str) -> Optional[dict]:
    """{send_ok:bool, cooldown_until?, reason?}"""
    if not domain:
        return None
    return await _call_tool("check_domain", {"domain": domain})


async def report_outcome(
    *,
    status: str,
    domain: str = "",
    form_fingerprint: str = "",
    error_reason: str = "",
    learned: Optional[list[dict]] = None,
    workflow: Optional[dict] = None,
) -> Optional[dict]:
    """{ack:true}。status in success|failed|skipped。"""
    args: dict[str, Any] = {"status": status}
    if domain:
        args["domain"] = domain
    if form_fingerprint:
        args["form_fingerprint"] = form_fingerprint
    if error_reason:
        args["error_reason"] = error_reason
    if learned:
        args["learned"] = learned
    if workflow:
        args["workflow"] = workflow
    return await _call_tool("report_outcome", args)


async def probe() -> dict:
    """接続プリフライト診断。氏名パターンの秘匿辞書はサーバー(formsend-core)にあり、
    未接続だと resolve_fields が使えず氏名解決が AI/assist に劣化する。起動時に状態を
    可視化するための軽量チェック（ping・認証のみ確認、副作用なし）。

    Returns: {"status": "ok"|"unconfigured"|"unauthorized"|"unreachable", "detail": str}
    """
    if httpx is None:
        return {"status": "unreachable", "detail": "httpx 未インストール（uv sync が必要）"}
    url, tok = server_url(), server_token()
    if not url or not tok:
        missing = [k for k, v in (("FORMSEND_CORE_URL", url), ("FORMSEND_CORE_TOKEN", tok)) if not v]
        return {"status": "unconfigured", "detail": "未設定: " + ", ".join(missing)}
    headers = {
        "authorization": f"Bearer {tok}",
        "content-type": "application/json",
        "accept": "application/json",
        "x-client-version": _CLIENT_VERSION,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
            resp = await client.post(url, headers=headers, json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
    except BaseException as e:  # noqa: BLE001 — 診断なので握って返す
        return {"status": "unreachable", "detail": f"{type(e).__name__}: {e}"}
    if resp.status_code == 200:
        return {"status": "ok", "detail": ""}
    if resp.status_code in (401, 403):
        return {"status": "unauthorized", "detail": f"HTTP {resp.status_code}（トークン不一致の可能性。ops台帳/AUTH_TOKENS 要確認）"}
    return {"status": "unreachable", "detail": f"HTTP {resp.status_code}"}


# -----------------------------------------------------------------------------
# Module self-check（手動疎通）: python core/_server_client.py
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import asyncio

    async def _main() -> None:
        print(f"[_server_client] configured={is_configured()} url={server_url() or '(none)'}")
        if not is_configured():
            print("  set FORMSEND_CORE_URL and FORMSEND_CORE_TOKEN to test.")
            return
        pb = await get_form_playbook()
        if pb:
            print(
                f"  playbook ok: version={pb.get('version')} "
                f"static_labels={len(pb.get('static_labels') or [])} "
                f"no_ai_rules={len(pb.get('no_ai_rules') or [])}"
            )
        else:
            print("  playbook: None (check URL/token/server)")

    asyncio.run(_main())
