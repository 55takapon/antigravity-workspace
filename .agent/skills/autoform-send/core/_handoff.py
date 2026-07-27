"""Human-in-the-loop の出口 — 失敗を「人が仕上げる箱」に振り分けて書き出す。

送信ラン後、自動で送りきれなかった社を 2 種類に仕分ける（純観測・送信不変）:

    🟡 アシストキュー  (assist_queue_<run_id>.jsonl)
        CAPTCHA 系（reCAPTCHA / hCaptcha / Turnstile）。対話型の関門なので
        人がその場で解けば送れる。`scripts/assist_mode.py` が 1 件ずつ
        目視ブラウザで再オープン＋自動入力し、最後の操作だけ人に委ねる。

    🔴 手動ハンドオフ  (manual_handoff_<run_id>.md / .csv)
        サーバー側ブロック（WAF / 403）や reCAPTCHA v3（挙動監視型）。自動化
        ブラウザでは入力挙動そのものが bot 判定されて弾かれるため、人の「普段
        使いブラウザ」で丸ごと送るしかない。URL＋本文をコピペしやすい形で
        書き出すだけ（無理に自動化しない）。

入力は run_send が組み立てた entry のリスト:
    {company_name, url, message, failure_category, error_reason, field_detail}
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Optional


# 対話型 CAPTCHA（人が最後に解けば送れる）/ 辞書に無い必須・選択欄 → アシストモード行き。
#  - reCAPTCHA v2 / hCaptcha は「人が解く前提の対話チャレンジ」で自動入力を許容する。
#  ※ Turnstile と reCAPTCHA v3 は挙動採点型でアシストでも弾かれる → _HANDOFF_CATEGORIES へ。
_ASSIST_CATEGORIES = {
    "bot_protection_recaptcha",
    "bot_protection_hcaptcha",
    "bot_protection",
    # 未知欄（辞書で解けず AI 不使用）。assist_mode が自動入力し、人が欄を選んで送信。
    "unknown_fields",
}

# 自動化セッションでは突破不能 → 人の通常ブラウザへ手渡し。
#  - waf_403: サーバー側ブロック。
#  - bot_protection_recaptcha_v3 / bot_protection_turnstile: いずれも「セッションの挙動」を
#    採点する監視型。アシスト(自動入力＋人の最終操作)でも入力時点で bot 判定が確定して
#    弾かれる（2026-07-10 アド・エータイプ=Turnstile 実証：人が解いても送信ブロック）。
#    自動ツールを一切触らせず、人が自分の通常ブラウザで丸ごと送るしかない。
_HANDOFF_CATEGORIES = {
    "waf_403",
    "bot_protection_recaptcha_v3",
    "bot_protection_turnstile",
}

# 検出・操作そのものが難しく Tier A(Python)で送れなかった社 — ホストの Claude が
# Playwright MCP でブラウザ運転して救う（Step 8 / Tier B。別料金API不要・対話時のみ）。
# ※ confirmation_unclear は「既に送信済みの可能性」があり再運転=二重送信リスクのため除外
#   （要目視のまま）。unknown_fields はより安い Step 6（ブラウザ不要）で処理するため除外。
_TIER_B_CATEGORIES = {
    "form_not_found",
    "submit_not_found",
    "field_detection_miss",
}


def route_failures(entries: list[dict]) -> tuple[list[dict], list[dict]]:
    """entry リストを (assist, handoff) に振り分ける。

    どちらにも該当しない失敗（dns_error / site_not_found / 死にサイト等）は
    人手でも救えないので、どちらの箱にも入れない。
    """
    assist = [e for e in entries if e.get("failure_category") in _ASSIST_CATEGORIES]
    handoff = [e for e in entries if e.get("failure_category") in _HANDOFF_CATEGORIES]
    return assist, handoff


def select_tier_b(entries: list[dict]) -> list[dict]:
    """entry リストから Tier B（Step 8）行きの社だけ抜き出す。

    assist / handoff とは disjoint（1社=1 failure_category）。従来どちらの箱にも
    入らず素通りしていた検出・操作失敗を、ホスト運転の救済キューに載せる。
    """
    return [e for e in entries if e.get("failure_category") in _TIER_B_CATEGORIES]


def write_tier_b_queue(entries: list[dict], path: Path) -> int:
    """🔵 Tier B キューを JSONL で書き出す。書けた件数を返す（Fail Safe）。

    ホストの Claude が Step 8（references/step8_tier_b_browser_mcp.md）に従い、
    `contact_url` に直行 → snapshot → 入力 → ★人間確認 → 送信、で 1 社ずつ運転する。
    実行は対話セッション内（無人バッチ不可）。送信結果・計測（snapshot 回数 /
    フォールバック探索の有無 / 解決した本物URL）は Step 8 で書き戻す。
    """
    if not entries:
        return 0
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for e in entries:
                # 送信先 url は adapt 後＝②の contact_url。step8 はこれに直行する
                # （HPトップから探索しない＝トークン最小化）。
                target = e.get("url") or ""
                row = {
                    "company_name": e.get("company_name") or "",
                    "contact_url": target,
                    "url": target,
                    "message": e.get("message") or "",
                    # なぜ Tier B に来たか（form/submit/field のどれで詰まったか）
                    "escalated_from": e.get("failure_category") or "",
                    "error_reason": e.get("error_reason") or "",
                    # Tier A が掴んでいた欄ヒント（あれば運転の参考に）
                    "field_detail": e.get("field_detail"),
                    "status": "pending",
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return len(entries)
    except BaseException as ex:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_handoff] write_tier_b_queue failed (continuing): "
            f"{type(ex).__name__}: {ex}\n"
        )
        return 0


def write_assist_queue(entries: list[dict], path: Path) -> int:
    """🟡 アシストキューを JSONL で書き出す。書けた件数を返す（Fail Safe）。"""
    if not entries:
        return 0
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for e in entries:
                row = {
                    "company_name": e.get("company_name") or "",
                    "url": e.get("url") or "",
                    "message": e.get("message") or "",
                    "captcha_type": e.get("failure_category") or "",
                    "error_reason": e.get("error_reason") or "",
                    # 再入力のヒント（あれば）。assist_mode はライブ再検出するが、
                    # どの欄が埋まる想定だったかの参考として残す。
                    "field_detail": e.get("field_detail"),
                    "status": "pending",
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return len(entries)
    except BaseException as ex:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_handoff] write_assist_queue failed (continuing): "
            f"{type(ex).__name__}: {ex}\n"
        )
        return 0


def write_manual_handoff(
    entries: list[dict],
    md_path: Path,
    csv_path: Optional[Path] = None,
) -> int:
    """🔴 手動ハンドオフ（人の通常ブラウザ用）を Markdown + CSV で書き出す。"""
    if not entries:
        return 0
    try:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        lines.append(f"# 手動送信リスト（{len(entries)} 社）— ご自分のブラウザで開いてください")
        lines.append("")
        lines.append("> サーバー側ブロック（WAF/403）のため自動・アシスト不可。")
        lines.append("> お使いの通常ブラウザ（Chrome 等）で URL を開き、本文を貼って送信してください。")
        lines.append("")
        for i, e in enumerate(entries, start=1):
            name = e.get("company_name") or "(no name)"
            url = e.get("url") or ""
            message = e.get("message") or ""
            lines.append(f"## {i}. {name}")
            lines.append(f"- フォーム: {url}")
            lines.append("- 本文（下のブロックをコピペ）:")
            lines.append("")
            lines.append("```")
            lines.append(message)
            lines.append("```")
            lines.append("- [ ] 送信済み")
            lines.append("")
        md_path.write_text("\n".join(lines), encoding="utf-8")

        if csv_path is not None:
            with csv_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["company_name", "url", "message", "error_reason"]
                )
                writer.writeheader()
                for e in entries:
                    writer.writerow({
                        "company_name": e.get("company_name") or "",
                        "url": e.get("url") or "",
                        "message": e.get("message") or "",
                        "error_reason": e.get("error_reason") or "",
                    })
        return len(entries)
    except BaseException as ex:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_handoff] write_manual_handoff failed (continuing): "
            f"{type(ex).__name__}: {ex}\n"
        )
        return 0
