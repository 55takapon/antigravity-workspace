"""AutoformSend Skill エントリスクリプト (Sprint 4 Task 2)。

ユーザーが Claude Code 経由 / CLI 直叩きで実行する Python スクリプト。
入力 CSV を 1 行ずつ読み、`_skill_core.process_one_company()` を逐次呼び、
結果を出力 CSV へ追記する。

設計方針 (Sprint 4 仕様書 §5 Task 2):
- 並列実行しない (concurrency=1, KISS, IP ブロック確率低減)
- 1 社で例外が出ても次の社へ進む (Fail Safe)
- API キーが無ければ 1 社目処理前に exit 1 (Fail Fast)
- API キー値は stdout / 結果 CSV / ログのどこにも一切出さない

使い方:
    # 1. 設定ファイルを準備（送信者情報の雛形はリポジトリ直下 shared/ に一本化）
    cp config/.env.example .env
    cp shared/5_sender_info.example.json shared/sender_info.json  # リポジトリ直下で
    cp examples/input.example.csv input.csv
    # 2. .env と shared/sender_info.json を編集
    # 3. 実行（--sender 省略時は shared/sender_info.json を読む）
    uv run python scripts/run_send.py --input input.csv

入力 CSV: ヘッダ `company_name,url,message` 固定 (UTF-8 BOM 許容)
出力 CSV: 入力の列に `sent_at,status,error_reason,screenshot_path` を末尾追記
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Sprint 6 Task 0: Skill 版実装は skill/core/ に集約された。
# 2 通りの sys.path を入れる:
#   (a) skill/core/ — フラット import (`from _skill_core import ...`) 用
#       (Sprint 5 互換、テストやスクリプト内の遅延 import で広く使われている)
#   (b) repo root — package import (`from skill.core._skill_core import ...`)
#       用 (Sprint 6 で追加した dual-import 経路の一方)
# スキルディレクトリ名に依存しないパス解決（移植先で skill/ → form-send/ に改名済）。
# このファイルは <skill>/scripts/run_send.py。core は <skill>/core。
_SKILL_DIR = Path(__file__).resolve().parents[1]      # .../form-send
_SKILL_CORE_DIR = _SKILL_DIR / "core"                 # フラット import 用
_SCRIPTS_DIR = Path(__file__).resolve().parent        # .../form-send/scripts
_REPO_ROOT = _SKILL_DIR.parent                        # package import フォールバック用
# 送信者情報の正本はリポジトリ直下の shared/sender_info.json（run_on_sheet.py と統一）。
# .../<repo>/.claude/skills/005-form-send → parents[2] が <repo>。
_DEFAULT_SENDER_INFO = _SKILL_DIR.parents[2] / "shared" / "sender_info.json"
for _entry in (_SKILL_CORE_DIR, _SKILL_DIR, _SCRIPTS_DIR, _REPO_ROOT):
    if str(_entry) not in sys.path:
        sys.path.insert(0, str(_entry))

# 多重起動ガード（同一入力CSVへの二重送信防止）。scripts/ を sys.path に入れた後に import。
from _run_lock import SingleRunLock, LockBusyError  # noqa: E402

# --- 定数 --------------------------------------------------------------------
# 入力 CSV の必須列名 (UTF-8 BOM は csv.DictReader が自動 strip しないため
# 後処理で吸収する。下の _strip_bom_from_keys 参照)。
#
# 2026-06-03 仕様変更:
# - company_name, url は必須
# - message は CSV 推奨だが、sender_info.json に "message" (デフォルト営業文)
#   があれば CSV.message 列は空 or 省略可。各社別カスタム時のみ CSV.message に記載。
_REQUIRED_INPUT_COLUMNS = ("company_name", "url")
_OPTIONAL_INPUT_COLUMNS = ("message",)
# 統一スキーマでは送信先の正規列は contact_url（②が生成）。通常は adapt_unified_input.py が
# url←contact_url に詰め替えるが、統一CSVを直接 run_send.py に渡してアダプタを通し忘れても
# 正しい宛先（問い合わせページ）へ送れるよう、run_send 側でも contact_url を優先する。
# ただし実URL（http始まり）のときだけ採用し、非URL/空（"見つかりませんでした"等）は HP url に落とす。
_NON_URL_MARKERS = ("見つかりませんでした", "エラー", "")


def _is_real_url(value: str) -> bool:
    v = (value or "").strip()
    if not v or v.startswith("エラー") or v in _NON_URL_MARKERS:
        return False
    return v.startswith("http")


def _resolve_send_target(row: dict) -> str:
    """送信先URLを決める: 実URLの contact_url を優先、無ければ HP url（adapt と同じ解決順）。"""
    contact = (row.get("contact_url") or "").strip()
    if _is_real_url(contact):
        return contact
    return (row.get("url") or "").strip()
# 出力 CSV の追加列
# Sprint 5 Task 5: `provider_used` 列を追加 (http_post / browser_use / none)。
_OUTPUT_EXTRA_COLUMNS = (
    "sent_at", "status", "error_reason", "screenshot_path", "provider_used",
)
# 1 社処理後の遅延範囲 (秒)。IP ブロック確率低減と KISS の折衷。
# NOTE: TS 版の batch-scheduler.ts は 60-180 秒だが、Skill ユーザーの想定送信量
#       は数件〜十数件なので 2-5 秒で十分。実 API 連打を避ける目的。
# Sprint 5 §3-8 提案 5: 環境変数 AUTOFORM_DELAY_DISABLED=1 で OFF (CI/test 用、本番常用禁止)。
_INTER_REQUEST_DELAY_MIN_SEC = 2.0
_INTER_REQUEST_DELAY_MAX_SEC = 5.0


# --- ユーティリティ ----------------------------------------------------------
def _eprint(*args, **kwargs) -> None:
    """stderr への出力ヘルパー。stdout は Claude Code が拾うので分けておく。"""
    kwargs.setdefault("file", sys.stderr)
    kwargs.setdefault("flush", True)
    print(*args, **kwargs)


def _print_progress(*args, **kwargs) -> None:
    """進捗表示。stdout/flush で Claude Code から見える。"""
    kwargs.setdefault("flush", True)
    print(*args, **kwargs)


def _strip_bom_from_keys(row: dict) -> dict:
    """csv.DictReader が読んだ行から UTF-8 BOM を取り除く。"""
    return {(k.lstrip("﻿") if isinstance(k, str) else k): v for k, v in row.items()}


def _load_env_file(env_path: Path) -> None:
    """.env ファイルを読んで os.environ に反映する (python-dotenv 互換の最小実装)。

    依存最小化のため自前実装。`KEY=VALUE` 形式、コメント `#` 無視、空行無視のみ。
    値のクォート (`"value"` / `'value'`) は除去する。
    既存 env (Railway 等) を上書きしない (override=False 相当)。
    """
    if not env_path.exists():
        return
    try:
        text = env_path.read_text(encoding="utf-8")
    except BaseException as e:
        _eprint(f"[警告] .env の読み込みに失敗 (続行): {type(e).__name__}: {e}")
        return
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # 行末コメント除去 (value 内のダブルクォート外の # は無視)
        if value and value[0] not in ("'", '"'):
            # シンプルに # 以降を捨てる (値に # を含めたいユーザーはクォートを使う)
            hash_idx = value.find(" #")
            if hash_idx != -1:
                value = value[:hash_idx].strip()
        # クォート除去
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def _redact(value: str) -> str:
    """API キーをログ出力する際の伏字。先頭 4 文字のみ残す。"""
    if not value:
        return "(empty)"
    if len(value) <= 4:
        return "***"
    return f"{value[:4]}***({len(value)} chars)"


# --- メインロジック ----------------------------------------------------------
def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="run_send.py",
        description=(
            "AutoformSend Skill — ローカル CSV からお問い合わせフォームへ "
            "営業メッセージを自動送信する。"
        ),
    )
    parser.add_argument(
        "--input",
        required=True,
        help="送信対象 CSV (列: company_name,url,message)",
    )
    parser.add_argument(
        "--sender",
        default=str(_DEFAULT_SENDER_INFO),
        help="送信者情報 JSON (FillData 互換キー)。既定: リポジトリ直下の shared/sender_info.json",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="結果 CSV の出力先パス (省略時はカレントに output_YYYYMMDD_HHMMSS.csv)",
    )
    parser.add_argument(
        "--screenshots",
        default="screenshots",
        help="スクリーンショット保存先ディレクトリ (デフォルト: ./screenshots)",
    )
    parser.add_argument(
        "--env",
        default=".env",
        help="API キー定義の .env ファイルパス (デフォルト: ./.env)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        choices=["claude-sonnet-4-6"],
        help=(
            "使用するAIモデル (現状 claude-sonnet-4-6 のみサポート)。"
            "Haiku 4.5 は autonomous browser 検証で精度崩壊が確認されたため撤退済。"
        ),
    )
    parser.add_argument(
        "--mode",
        default="hybrid",
        choices=["hybrid", "ai_only", "legacy-no-stage15"],
        help=(
            "送信モード (Sprint 6 拡張):\n"
            "  hybrid: HTTP POST 先行 + 早期スキップ + Stage 1.5 (汎用フォーム) + Pareto noAI + AI fallback (推奨、デフォルト)\n"
            "  legacy-no-stage15: Stage 1.5 を完全バイパスし Sprint 5 互換動作 (デバッグ用)\n"
            "  ai_only: AI のみ (Phase 1 同等、ただし営業禁止/Bot 保護早期スキップ適用)"
        ),
    )
    parser.add_argument(
        "--decisions",
        default=None,
        help=(
            "④式ハンドオフの決定JSON。{\"<url or company>\": {\"<欄ラベル>\": \"<値>\"}}。"
            "未知の必須/select/radio をアシストに回す前に、この値で充填する"
            "（ユーザーの Claude Code が options から選んで書いたファイル）。"
        ),
    )
    parser.add_argument(
        "--auto-default",
        action="store_true",
        help=(
            "未解決の select/radio に汎用問い合わせの無難な選択肢"
            "（その他/お問い合わせ等）を AI なしで自動選択する（batch 用フォールバック）。"
        ),
    )
    return parser.parse_args(argv)


def _validate_inputs(args: argparse.Namespace) -> tuple[Path, Path, Path, Path]:
    """入力ファイルの存在を検証して Path を返す。問題があれば exit 1。"""
    input_path = Path(args.input).resolve()
    sender_path = Path(args.sender).resolve()
    env_path = Path(args.env).resolve()
    screenshots_dir = Path(args.screenshots).resolve()

    if not input_path.exists():
        _eprint(f"[エラー] 入力 CSV が見つかりません: {input_path}")
        sys.exit(1)
    if not sender_path.exists():
        _eprint(f"[エラー] 送信者情報 JSON が見つかりません: {sender_path}")
        sys.exit(1)
    # env_path は存在しなくても警告のみ (env var 直接設定もサポート)
    if not env_path.exists():
        _eprint(
            f"[情報] .env が見つかりません ({env_path}). "
            "環境変数から直接 ANTHROPIC_API_KEY を読み込みます。"
        )
    return input_path, sender_path, env_path, screenshots_dir


def _load_sender_info(sender_path: Path) -> dict:
    try:
        text = sender_path.read_text(encoding="utf-8")
        data = json.loads(text)
    except BaseException as e:
        _eprint(
            f"[エラー] 送信者情報 JSON のパースに失敗: {sender_path}\n"
            f"        {type(e).__name__}: {e}"
        )
        sys.exit(1)
    if not isinstance(data, dict):
        _eprint(
            f"[エラー] 送信者情報 JSON のトップレベルは object である必要があります。"
            f"        実際の型: {type(data).__name__}"
        )
        sys.exit(1)
    return data


def _load_input_csv(input_path: Path) -> tuple[list[dict], list[str]]:
    """入力 CSV を読み込んで (rows, original_columns) を返す。"""
    try:
        with input_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                _eprint(f"[エラー] 入力 CSV にヘッダ行がありません: {input_path}")
                sys.exit(1)
            original_columns = [c.lstrip("﻿") for c in reader.fieldnames]
            rows = [_strip_bom_from_keys(r) for r in reader]
    except BaseException as e:
        _eprint(f"[エラー] 入力 CSV の読み込みに失敗: {input_path}\n        {type(e).__name__}: {e}")
        sys.exit(1)

    missing = [c for c in _REQUIRED_INPUT_COLUMNS if c not in original_columns]
    if missing:
        _eprint(
            f"[エラー] 入力 CSV に必須列がありません: {missing}\n"
            f"        現在の列: {original_columns}\n"
            f"        必須列: {list(_REQUIRED_INPUT_COLUMNS)}"
        )
        sys.exit(1)

    if not rows:
        _eprint(f"[警告] 入力 CSV にデータ行がありません: {input_path}")
    return rows, original_columns


def _resolve_output_path(output_arg: Optional[str]) -> Path:
    if output_arg:
        return Path(output_arg).resolve()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path.cwd() / f"output_{ts}.csv"


def _resolve_api_key() -> str:
    """env から ANTHROPIC_API_KEY を取得。任意（v1 は辞書＋人間アシストで動くため）。

    未設定でも止めない。鍵が無い場合は AI フォールバック(Stage 3 browser_use)が使えない
    だけで、HTTP送信・Stage 1.5(辞書＋サーバーresolve_fields)は動作する。難フォームは
    人間アシストキューへ回る。鍵があれば従来どおり Stage 3 も使える。
    """
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        _eprint(
            "[情報] ANTHROPIC_API_KEY 未設定 — AIフォールバック(Stage 3)は無効。\n"
            "       HTTP送信＋辞書＋サーバー学習で動作し、難フォームは人間アシストへ回します。\n"
            "       Stage 3 も使う場合のみ .env に ANTHROPIC_API_KEY を設定してください。"
        )
    return key


def _summarize_progress(outcome: dict) -> str:
    """Sprint 6 Task 7: stdout 進捗の Stage 別サマリーを組み立てる。"""
    status = outcome.get("status", "failed")
    provider = outcome.get("provider_used", "none")
    reason = outcome.get("error_reason") or ""

    if status == "completed":
        if provider == "workflow_cache":
            return "workflow_cache_hit 成功 [Stage 1.5 学習済み]"
        if provider == "general_form":
            return "general_form 成功 [Stage 1.5]"
        return f"{provider} 成功"
    if status == "skipped" and reason == "prohibition_detected":
        return "営業禁止検知 → skipped [Stage 0]"
    if reason.startswith("bot_protection:"):
        kind = reason.split(":", 1)[1]
        return f"Bot 保護検知 ({kind}) → skipped [Stage 0]"
    if reason == "site_not_found":
        return "サイト到達不能 (HTTP 404) → skipped [Stage 1.5]"
    if reason == "domain_cooldown":
        return "domain_cooldown → skipped [Stage 1.5]"
    if reason == "robots_disallow":
        return "robots.txt で disallowed → skipped [Stage 1.5]"
    if reason.startswith("noai_filter:"):
        return f"noAI フィルタで skipped [Stage 2] ({reason[len('noai_filter:'):][:40]})"
    if provider == "browser_use":
        return f"browser_use {status} [Stage 3]"
    if provider == "general_form":
        return f"general_form {status} [Stage 1.5] ({reason[:40]})"
    if provider == "http_post":
        return f"http_post {status} [Stage 1] ({reason[:40]})"
    return f"{provider} {status}"


def _delay_disabled() -> bool:
    """Sprint 5 §3-8 提案 5: AUTOFORM_DELAY_DISABLED=1 で遅延 OFF (CI/test 用)。"""
    return os.environ.get("AUTOFORM_DELAY_DISABLED", "").strip() == "1"


async def _process_all_rows(
    rows: list[dict],
    sender_info: dict,
    api_key: str,
    model: str,
    mode: str,
    screenshots_dir: Path,
    field_decisions_by_key: dict | None = None,
    auto_default: bool = False,
) -> list[dict]:
    """全行を逐次処理し、結果を入力行に追記した dict のリストを返す。

    Sprint 5 Task 5: --mode 引数で Provider を切り替える。
        hybrid -> HybridProvider (HTTP POST 先行 + 早期スキップ + noAI + AI fallback)
        ai_only -> Provider 省略 (LocalBrowserUseProvider デフォルト経路)
    """
    # 遅延 import (Task 1 と同じ設計、起動時の副作用ゼロ)
    from _skill_core import (  # type: ignore
        HybridProvider,
        process_one_company,
    )
    # 診断トレース（純観測）: 失敗の解剖ログを logs/trace_<run_id>.jsonl に残す。
    # import 失敗時もループは続行（送信を止めない Fail Safe）。
    try:
        from _trace_logger import TraceCollector  # type: ignore
    except BaseException as _e:  # noqa: BLE001
        TraceCollector = None  # type: ignore
        sys.stderr.write(
            f"[run_send] trace logger unavailable (continuing without diagnostic log): "
            f"{type(_e).__name__}: {_e}\n"
        )

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logs_dir = _SKILL_DIR / "logs"
    # Human-in-the-loop の出口（🟡アシスト / 🔴手動ハンドオフ）に積む entry を貯める。
    handoff_entries: list[dict] = []

    # Provider の選択 (Sprint 6 Task 7):
    #   hybrid           -> HybridProvider with Stage 1.5 enabled
    #   legacy-no-stage15 -> HybridProvider with Stage 1.5 bypassed (Sprint 5 互換)
    #   ai_only          -> Provider 省略 (LocalBrowserUseProvider デフォルト経路)
    if mode == "hybrid":
        provider = HybridProvider(api_key=api_key, model=model, enable_stage15=True)
    elif mode == "legacy-no-stage15":
        provider = HybridProvider(api_key=api_key, model=model, enable_stage15=False)
    else:  # ai_only
        provider = None

    total = len(rows)
    results: list[dict] = []

    # sender_info の "message" をデフォルト営業文として扱う (Sprint 6 後追加)
    # 優先順位: input.csv の message 列 (各社カスタム) > sender_info.json の message (デフォルト)
    default_message = (
        (sender_info.get("message") or "").strip()
        if isinstance(sender_info, dict) else ""
    )
    # 両方空なら Fail Fast (1社目処理開始前に判明させる)
    has_any_csv_message = any((row.get("message") or "").strip() for row in rows)
    if not default_message and not has_any_csv_message:
        sys.stderr.write(
            "[エラー] 営業文 (message) が見つかりません。以下のいずれかを設定してください:\n"
            "  - sender_info.json に \"message\" フィールド (全社共通のデフォルト営業文)\n"
            "  - input.csv の message 列 (各社別カスタム)\n"
            "  - 両方の組み合わせ (CSV があれば優先、空なら sender_info の値を使う)\n"
        )
        return 1

    for idx, row in enumerate(rows, start=1):
        company = (row.get("company_name") or "").strip()
        url = _resolve_send_target(row)   # 実URLの contact_url を優先、無ければ HP url
        csv_message = (row.get("message") or "").strip()
        # csv.message が空なら sender_info.message を fallback として使う
        message = csv_message if csv_message else default_message

        _print_progress(f"[{idx}/{total}] {company or '(no name)'} → 処理開始")

        # ④式ハンドオフ: この社向けに Claude が決めた欄値があれば取り出す
        # （url キー優先、無ければ company_name）。
        _fd = None
        if field_decisions_by_key:
            _fd = field_decisions_by_key.get(url) or field_decisions_by_key.get(company)

        # 個別 try/except で 1 社例外が全体を止めないようにする (Fail Safe)
        try:
            outcome = await process_one_company(
                company_name=company,
                url=url,
                message=message,
                sender_info=sender_info,
                api_key=api_key,
                model=model,
                screenshot_dir=str(screenshots_dir),
                provider=provider,
                field_decisions=_fd,
                auto_default=auto_default,
            )
            status = outcome.get("status", "failed")
            error_reason = outcome.get("error_reason") or ""
            screenshot_path = outcome.get("screenshot_path") or ""
            ended_at = outcome.get("ended_at") or datetime.now().isoformat()
            provider_used = outcome.get("provider_used") or "none"
        except BaseException as e:  # noqa: BLE001 — Fail Safe per spec §5 Task 2
            # process_one_company 自体が握り損ねた例外。ここで最終防衛。
            status = "failed"
            error_reason = f"{type(e).__name__}: {e}"[:200]
            screenshot_path = ""
            ended_at = datetime.now().isoformat()
            provider_used = "none"
            outcome = {
                "status": status,
                "error_reason": error_reason,
                "provider_used": provider_used,
            }

        # 機密保護: ログに sender_info の値や API キーを出さない。
        # Sprint 5 Task 5: Stage 別サマリーを出す。
        _print_progress(
            f"[{idx}/{total}] {company or '(no name)'} → {_summarize_progress(outcome)}"
        )

        # 診断トレース（純観測）: outcome を 1 社 1 行の JSONL カルテに残す。
        # finalize 自体が Fail Safe（ログのバグで送信を止めない）。
        if TraceCollector is not None:
            try:
                rec = TraceCollector(
                    run_id=run_id,
                    company_name=company,
                    url=url,
                    logs_dir=str(logs_dir),
                ).finalize(outcome)
                # 失敗社は Human-in-the-loop の出口へ振り分ける材料を貯める。
                # message / url はここでしか取れない（trace レコードには無い）。
                if rec and rec.get("final_status") != "completed":
                    handoff_entries.append({
                        "company_name": company,
                        "url": url,
                        "message": message,
                        "failure_category": rec.get("failure_category"),
                        "error_reason": rec.get("error_reason"),
                        "field_detail": rec.get("field_detail"),
                    })
            except BaseException as e:  # noqa: BLE001 — Fail Safe
                sys.stderr.write(
                    f"[run_send] trace finalize failed (continuing): "
                    f"{type(e).__name__}: {e}\n"
                )

        out_row = dict(row)
        out_row["sent_at"] = ended_at
        out_row["status"] = status
        out_row["error_reason"] = error_reason
        out_row["screenshot_path"] = screenshot_path
        out_row["provider_used"] = provider_used
        results.append(out_row)

        # 次社処理前にランダム遅延 (最終ループでは省略、AUTOFORM_DELAY_DISABLED でも省略)
        if idx < total and not _delay_disabled():
            delay = random.uniform(
                _INTER_REQUEST_DELAY_MIN_SEC, _INTER_REQUEST_DELAY_MAX_SEC
            )
            await asyncio.sleep(delay)

    if TraceCollector is not None:
        trace_path = logs_dir / f"trace_{run_id}.jsonl"
        if trace_path.exists():
            _print_progress(f"[診断ログ] {trace_path}")
            _print_progress(
                f"[診断ログ] 集計: python scripts/trace_report.py {trace_path}"
            )

    # Human-in-the-loop の出口を書き出す（🟡アシスト / 🔴手動ハンドオフ）。
    if handoff_entries:
        try:
            from _handoff import (  # type: ignore
                route_failures,
                select_tier_b,
                write_assist_queue,
                write_manual_handoff,
                write_tier_b_queue,
            )
            assist, handoff = route_failures(handoff_entries)
            tier_b = select_tier_b(handoff_entries)
            n_assist = write_assist_queue(
                assist, logs_dir / f"assist_queue_{run_id}.jsonl"
            )
            n_handoff = write_manual_handoff(
                handoff,
                logs_dir / f"manual_handoff_{run_id}.md",
                logs_dir / f"manual_handoff_{run_id}.csv",
            )
            n_tier_b = write_tier_b_queue(
                tier_b, logs_dir / f"tier_b_queue_{run_id}.jsonl"
            )
            if n_assist:
                _print_progress(
                    f"[🟡アシスト] {n_assist} 社が CAPTCHA で“あと一歩”。"
                    f"仕上げ: python scripts/assist_mode.py "
                    f"{logs_dir / f'assist_queue_{run_id}.jsonl'}"
                )
            if n_handoff:
                _print_progress(
                    f"[🔴手動] {n_handoff} 社はサーバー側ブロック/reCAPTCHA v3 で自動化不可。"
                    f"通常ブラウザ用リスト: {logs_dir / f'manual_handoff_{run_id}.md'}"
                )
            if n_tier_b:
                _print_progress(
                    f"[🔵Tier B] {n_tier_b} 社は検出・操作が難しく Tier A 不可。"
                    f"対話セッションで Playwright MCP 運転（Step 8）: "
                    f"{logs_dir / f'tier_b_queue_{run_id}.jsonl'}"
                )
        except BaseException as e:  # noqa: BLE001 — Fail Safe
            sys.stderr.write(
                f"[run_send] handoff export failed (continuing): "
                f"{type(e).__name__}: {e}\n"
            )

    return results


def _write_output_csv(
    output_path: Path,
    results: list[dict],
    original_columns: list[str],
) -> None:
    """結果 CSV を書き出す。"""
    fieldnames = list(original_columns) + list(_OUTPUT_EXTRA_COLUMNS)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in results:
                writer.writerow(r)
    except BaseException as e:
        _eprint(
            f"[エラー] 結果 CSV の書き出しに失敗: {output_path}\n"
            f"        {type(e).__name__}: {e}"
        )
        sys.exit(2)


def _print_summary(results: list[dict], output_path: Path) -> None:
    total = len(results)
    completed = sum(1 for r in results if r.get("status") == "completed")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    failed = total - completed - skipped
    # Sprint 6 Task 7: 各 provider の成功内訳
    def _ok(p: str) -> int:
        return sum(
            1 for r in results
            if r.get("status") == "completed" and r.get("provider_used") == p
        )

    http_post_succ = _ok("http_post")
    general_form_succ = _ok("general_form")
    workflow_cache_succ = _ok("workflow_cache")
    ai_succ = _ok("browser_use")

    _print_progress("")
    _print_progress("=" * 60)
    _print_progress(
        f"完了: 成功 {completed} 件 / 失敗 {failed} 件 / スキップ {skipped} 件 / 全 {total} 件"
    )
    _print_progress(
        f"  内訳: http_post 成功 {http_post_succ} 件 / "
        f"general_form 成功 {general_form_succ} 件 / "
        f"workflow_cache 成功 {workflow_cache_succ} 件 / "
        f"browser_use 成功 {ai_succ} 件"
    )
    _print_progress(f"結果ファイル: {output_path}")
    _print_progress(
        "ローカルコスト集計: `python scripts/local_cost_report.py` で SQLite "
        "ai_usage_logs を集計できます。"
    )
    _print_progress("=" * 60)


def _preflight_server() -> None:
    """起動時のサーバー接続診断。未接続/認証エラーを可視化する（Fail-safe: 送信は止めない）。"""
    try:
        try:
            from skill.core import _server_client as _sc  # type: ignore
        except ImportError:
            import _server_client as _sc  # type: ignore
        pf = asyncio.run(_sc.probe())
    except BaseException as e:  # noqa: BLE001 — 診断は失敗しても止めない
        _eprint(f"[警告] 接続プリフライト実行に失敗（続行）: {type(e).__name__}: {e}")
        return
    st = pf.get("status")
    detail = pf.get("detail", "")
    if st == "ok":
        _print_progress("[接続] formsend-core: OK（氏名パターンの中央辞書を参照します）")
        return
    if st == "unconfigured":
        _eprint(
            f"[警告] formsend-core 未接続（{detail}）。\n"
            "        → .env に FORMSEND_CORE_URL / FORMSEND_CORE_TOKEN を設定してください。\n"
            "        未設定だと氏名欄の解決が弱まり AI 補完が増えます（送信は継続）。"
        )
    elif st == "unauthorized":
        _eprint(
            f"[警告] formsend-core 認証エラー（{detail}）。\n"
            "        → トークンが許可リストにありません。管理者に FORMSEND_CORE_TOKEN の確認を。\n"
            "        このままだと氏名欄の解決が弱まり AI 補完が増えます（送信は継続）。"
        )
    else:  # unreachable
        _eprint(
            f"[警告] formsend-core に接続できません（{detail}）。\n"
            "        → ネットワーク/URL を確認してください。氏名解決は一時的にローカルseed＋AIになります（送信は継続）。"
        )


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    input_path, sender_path, env_path, screenshots_dir = _validate_inputs(args)

    # 多重起動ガード: 同じ入力CSVを対象にした送信が既に走っていれば即中止（二重送信防止）。
    # 長時間ランを待ちきれず同じコマンドを再実行 → 2プロセス並走、を物理的にブロックする。
    lock = SingleRunLock("form-send", str(input_path))
    try:
        lock.acquire()
    except LockBusyError as e:
        _eprint(e.message)
        return 3
    try:
        return _main_locked(args, input_path, sender_path, env_path, screenshots_dir)
    finally:
        lock.release()


def _main_locked(
    args: argparse.Namespace,
    input_path: Path,
    sender_path: Path,
    env_path: Path,
    screenshots_dir: Path,
) -> int:
    # .env を読み込む (既存 env は上書きしない)
    _load_env_file(env_path)

    # API キー検証 (Fail Fast: 1 社目処理開始前に)
    api_key = _resolve_api_key()
    _print_progress(
        f"[起動] ANTHROPIC_API_KEY={_redact(api_key)} model={args.model} mode={args.mode}"
    )
    if _delay_disabled():
        _print_progress("[警告] AUTOFORM_DELAY_DISABLED=1 — IP 保護のための遅延が OFF です (本番常用禁止)")

    # 接続プリフライト: 氏名パターンの秘匿辞書はサーバー(formsend-core)にあり、未接続だと
    # 氏名解決が弱まり AI 補完が増える。起動時に状態を可視化する（Fail-safe: 送信は継続）。
    _preflight_server()

    # Sprint 6 Task 7: ローカル SQLite (label_dictionary / workflow_cache /
    # domain_cooldown / ai_usage_logs) を初回起動時に自動生成する。Stage 1.5
    # を有効化しないモードでも、(将来の Phase 統合等で) 副作用を起こさないよう
    # スキーマだけ揃えておく。
    if args.mode in ("hybrid", "legacy-no-stage15"):
        try:
            try:
                from skill.core._local_db import init_schema, resolve_db_path  # type: ignore
            except ImportError:
                from _local_db import init_schema, resolve_db_path  # type: ignore
            init_schema()
            _print_progress(f"[起動] SQLite: {resolve_db_path()} 準備完了")
        except BaseException as e:
            _eprint(
                f"[警告] SQLite 初期化に失敗 (続行、Stage 1.5 学習機能は無効): "
                f"{type(e).__name__}: {e}"
            )

    # 入力ファイル読み込み
    sender_info = _load_sender_info(sender_path)
    rows, original_columns = _load_input_csv(input_path)
    output_path = _resolve_output_path(args.output)

    _print_progress(
        f"[入力] {input_path.name} → {len(rows)} 件 / 送信者: {sender_path.name}"
    )
    _print_progress(f"[出力] {output_path}")
    _print_progress(f"[スクショ保存先] {screenshots_dir}")

    if not rows:
        # 空 CSV はヘッダだけ書いて完走 (Fail Safe + KISS)
        _write_output_csv(output_path, [], original_columns)
        _print_summary([], output_path)
        return 0

    # ④式ハンドオフの決定JSON（任意）。url/company をキーに {欄ラベル:値}。
    field_decisions_by_key: dict | None = None
    if args.decisions:
        try:
            with open(Path(args.decisions).resolve(), encoding="utf-8") as f:
                field_decisions_by_key = json.load(f)
            _print_progress(
                f"[ハンドオフ] 決定JSON {Path(args.decisions).name} → "
                f"{len(field_decisions_by_key or {})} 社分を適用"
            )
        except BaseException as e:  # noqa: BLE001 — Fail Safe
            _eprint(f"[警告] 決定JSONを読めません（無視して続行）: {type(e).__name__}: {e}")
            field_decisions_by_key = None

    # 全社処理
    try:
        results = asyncio.run(
            _process_all_rows(
                rows=rows,
                sender_info=sender_info,
                api_key=api_key,
                model=args.model,
                mode=args.mode,
                screenshots_dir=screenshots_dir,
                field_decisions_by_key=field_decisions_by_key,
                auto_default=args.auto_default,
            )
        )
    except KeyboardInterrupt:
        _eprint("[中断] Ctrl-C を受け取りました。中間結果は破棄されます。")
        return 130

    _write_output_csv(output_path, results, original_columns)
    _print_summary(results, output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
