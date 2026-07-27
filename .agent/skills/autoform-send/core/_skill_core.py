"""Sprint 4 — AutoformSend Skill 版 共通コア（純粋関数モジュール）。

1社のお問い合わせフォームへ営業メッセージを送信する純粋関数 `process_one_company`
を提供する。Skill 配布形態 (`skill/scripts/run_send.py`) からだけでなく、将来は
`python_worker/browser_use_worker.py` 側からも import 切替え可能な形にしてある。

設計方針 (Sprint 4 仕様書 §3-3, §5 Task 1):

- **副作用ゼロの純粋関数**: Supabase, requests (webhook), dotenv, telemetry 設定 を
  本モジュール内で一切行わない。すべて呼び出し側が責任を持つ。
- **Web アプリ版へのリグレッションゼロ**: 既存 `browser_use_worker.py` を 1 行も
  触らない。プロンプト文字列 (`FORM_GUIDELINE_STATIC`) は二重定義を採用し、
  同期検査は手動 (NOTE コメント)。これは仕様書 §5 Task 1 注意事項の (b) 案。
- **戻り値は dict のみ**: DB 行 / webhook payload に依存しない。Skill 側は
  この dict を CSV へ書き出す。
- **Fail Safe**: Browser Use 内部の例外は `BaseException` で握って
  `{"status": "failed", "error_reason": "<型>: <内容>"}` に落とす。

戻り値スキーマ:
    {
        "status": "completed" | "failed",
        "error_reason": str | None,
        "screenshot_path": str | None,
        "ended_at": str,  # ISO 8601 (例: "2026-05-31T12:34:56.789012")
    }
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# -----------------------------------------------------------------------------
# プロンプト本文 (FORM_GUIDELINE_STATIC)
#
# NOTE: Sync with python_worker/browser_use_worker.py:296-353
#   - 本文を編集するときは browser_use_worker.py 側の FORM_GUIDELINE_STATIC も
#     同じ内容に揃えること。差分が発生するとクラウド版と Skill 版で動作が
#     ズレる (主に Anthropic Prompt Caching のキャッシュキー)。
#   - 仕様書 §5 Task 1 注意事項 (b): 既存 worker への変更ゼロを優先するため
#     関数移動ではなくコピー二重定義を採用 (Risk Assessor 推奨)。
# -----------------------------------------------------------------------------
FORM_GUIDELINE_STATIC: str = """【共通フォーム入力ガイドライン (Static — Anthropic Prompt Caching 用の固定ブロック)】
このセクションは送信タスク全件で共通の知識であり、内容は会社・URL に依存しません。
動的な対象情報 (会社名 / 対象 URL / 送信者情報 / 本文) は task メッセージ側に記載されます。

1. 姓名分割フィールド (last_name / first_name) の扱い
   - "姓" "苗字" "セイ" "Last Name" のラベルや name 属性には "lastName" を入れる。
   - "名" "名前" "メイ" "First Name" には "firstName" を入れる。
   - フルネーム1欄しか無い場合は "姓 + 半角スペース + 名" で結合して入れる。
   - フリガナ欄が "姓カナ / 名カナ" で分離している場合は nameKana を半角スペースで分割する。
   - "氏名フリガナ" 1欄の場合は nameKana 全体を入れる。

2. フリガナのカタカナ / ひらがな自動判別
   - placeholder や label に "カナ" "ｶﾅ" "カタカナ" が含まれる → nameKana (カタカナ) を使う。
   - "ふりがな" "ひらがな" が含まれる → nameHiragana を使う。
   - 判別不能な場合はカタカナを優先する (国内 BtoB フォームの 7 割以上がカタカナを要求)。

3. 住所フィールド
   - "郵便番号" を入れた直後に 1〜2 秒待つ。多くのフォームが郵便番号 API で都道府県・市区町村を自動補完する。
   - 自動補完されなかった場合のみ手動で都道府県を select し、その後に番地等を text 入力する。
   - 郵便番号は "123-4567" 形式と "1234567" 形式の両方が存在する。フォーム側の pattern 属性に従う。
   - "番地" "建物名" が個別 input になっている場合は zip の後の address 文字列を最後の input にまとめて入れる。

4. 確認画面 (Confirmation Page) の扱い (最重要 — 二度押し事故防止)
   - "確認する" "確認画面へ" "Next" "次へ" のボタンを押した直後はまだ送信は完了していない。
   - 確認画面では入力内容が表示され、"送信する" "Submit" "この内容で送信" の真の送信ボタンがある。
   - 確認画面に到達したら絶対に "戻る" を押さない。入力を再度行うとセッションが切れる場合がある。
   - 確認画面のスクロールが必要な場合がある (送信ボタンがフッター付近にある)。

5. 同意 / Consent チェックボックス
   - "個人情報の取り扱いに同意" "プライバシーポリシーに同意" "利用規約に同意" の checkbox は必ず checked にする。
   - checkbox が hidden の場合、それを覆っている label をクリックする (button.click() ではなく label.click() が必要)。
   - reCAPTCHA v2 の "I'm not a robot" チェックボックスは Browser Use 内部の CapSolver 連携で処理されるため AI から手を出さない。

6. Shadow DOM / iframe 内のフィールド
   - フォームが見えているのに入力欄に何も入っていないように見える場合、Shadow DOM か iframe 内にある可能性が高い。
   - その場合でも一度入力済みであれば再入力しない (二重入力でフォームが壊れることがある)。
   - 再入力を要求されたら 1 回だけ retry し、それでも空に見える場合は "入力済みである" と仮定して次へ進む。

7. 送信ボタンの確実性
   - 送信ボタンは form.requestSubmit(button) でクリックするのが最も確実 (ネイティブバリデーションを正しくトリガーする)。
   - 通常の click() でうまくいかない場合、Enter キー押下や label クリックを順に試す。
   - 同じ送信ボタンを 3 回以上クリックしてはいけない (二重送信防止用にサーバ側で 5xx を返す実装が多い)。

8. エラーメッセージの判定 (フォーム送信失敗のシグナル)
   - aria-invalid="true" の input が 1 つでもあれば、それが原因で送信が止まっている。
   - .wpcf7-not-valid-tip (Contact Form 7), .has-error, .error-message のクラスを持つ要素が見えればそれがエラー本文。
   - 修正可能なエラー (未入力 / 形式不一致) は再入力する。修正不能なエラー (CAPTCHA 失敗 / WAF ブロック) は即終了する。

9. ループ検出 (3 回繰り返さない)
   - 同じ selector に同じ値を 3 回連続入力した → ループしている。done で失敗報告して終了する。
   - 送信ボタンを押した後に同じ URL に留まり続けて 3 ステップ経過した → 失敗として終了する。

10. 完了の決定的シグナル
    - URL が /thanks /complete /done /success /confirm に遷移したら成功確定。
    - "送信完了" "ありがとうございます" "受け付けました" "Thank you" のいずれかが本文に出たら成功確定。
    - 上記いずれかに該当した瞬間、done アクションで "送信完了しました" を返して終了する。追加操作は不要。
"""
# --- end of FORM_GUIDELINE_STATIC --------------------------------------------


# 成功 / 失敗判定用キーワード (browser_use_worker.py:578-579 と同期)
# Sprint 5 Task 4 §3-8-4: confirmation-signals.json の contentKeywords を起動時に
# マージする。辞書ファイルが見つからない場合（Skill 単独配布など）はハードコード
# fallback のみで動作する（Fail Safe）。
#
# NOTE: Sync with python_worker/browser_use_worker.py:578
_FAILURE_KEYWORDS = (
    "確認できません",
    "失敗",
    "できませんでした",
    "エラー",
    "ブロック",
    "404",
    "not found",
)
# NOTE: Sync with python_worker/browser_use_worker.py:579
_SUCCESS_KEYWORDS_HARDCODED = (
    "送信完了",
    "送信しました",
    "ありがとう",
    "完了しました",
    "success",
)


def _load_merged_success_keywords() -> tuple[str, ...]:
    """Merge hardcoded success keywords with confirmation-signals.json contentKeywords.

    Sprint 5 Task 4 §3-8-4 (proposal 6). De-duplicates while preserving order.
    Failure to load the dictionary is non-fatal — returns hardcoded only.

    Imports are lazy and dual-path (`skill.core._pattern_loader` for
    repo-import contexts, `_pattern_loader` for skill/scripts/run_send.py
    which adds `skill/core/` directly to sys.path).
    """
    merged: list[str] = list(_SUCCESS_KEYWORDS_HARDCODED)
    try:
        try:
            from skill.core._pattern_loader import load_confirmation_signals  # noqa: WPS433
        except ImportError:
            from _pattern_loader import load_confirmation_signals  # type: ignore  # noqa: WPS433
        signals = load_confirmation_signals()
        # Use contentKeywords (page-body matching). titleKeywords / urlKeywords
        # are not applicable to AI agent's `final_result_text`.
        content = signals.get("contentKeywords") or {}
        for alias in content.get("aliases", []):
            if alias and alias not in merged:
                merged.append(alias)
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_skill_core] confirmation-signals.json merge failed (continuing): "
            f"{type(e).__name__}: {e}\n"
        )
    return tuple(merged)


# Build the keyword tuple once at module load. Tests that mutate the dictionary
# files should call `_reload_success_keywords()` to refresh.
_SUCCESS_KEYWORDS: tuple[str, ...] = _load_merged_success_keywords()


def _reload_success_keywords() -> None:
    """Test-only helper: refresh _SUCCESS_KEYWORDS after dictionary changes."""
    global _SUCCESS_KEYWORDS
    _SUCCESS_KEYWORDS = _load_merged_success_keywords()


def _check_success(result_text: str) -> bool:
    """Final result text から成功/失敗を判定する純粋関数。

    Sprint 5 Task 4: 成功キーワード集合は hardcoded + confirmation-signals.json の
    contentKeywords を merge した tuple を使う。判定ロジックは Sprint 4 と同じ。

    NOTE: Sync with python_worker/browser_use_worker.py:581-584 (check_success)
    """
    if not result_text:
        return False
    has_failure = any(kw in result_text for kw in _FAILURE_KEYWORDS)
    has_success = any(kw in result_text for kw in _SUCCESS_KEYWORDS)
    return has_success and not has_failure


def _build_task_prompt(
    company_name: str,
    url: str,
    message: str,
    sender_info: dict,
) -> str:
    """1 社送信用の task プロンプトを組み立てる純粋関数。

    NOTE: Sync with python_worker/browser_use_worker.py:475-525
        既存 worker の prompt 構造をそのまま再現。FORM_GUIDELINE_STATIC は
        Agent の extend_system_message に乗せるためここには含めない。
    """
    return f"""あなたはお問い合わせフォームの入力・送信を行うAIアシスタントです。

【対象URL】 {url}
【対象企業】 {company_name}

【送信者情報】
- 会社名: {sender_info.get('senderCompanyName', '')}
- 姓: {sender_info.get('lastName', '')}
- 名: {sender_info.get('firstName', '')}
- フルネーム（氏名1欄用・スペース無し）: {sender_info.get('name') or (sender_info.get('lastName', '') + sender_info.get('firstName', ''))}
- フリガナ（カタカナ）: {sender_info.get('nameKana', '')}
- フリガナ（ひらがな）: {sender_info.get('nameHiragana', '')}
- メールアドレス: {sender_info.get('email', '')}
- 電話番号: {sender_info.get('phone', '')}
- 郵便番号: {sender_info.get('zip', '')}
- 住所: {sender_info.get('address', '')}
- 部署: {sender_info.get('department', '')}
- 役職: {sender_info.get('position', '')}
- 件名: {sender_info.get('subject', '')}
- 自社サイトURL: {sender_info.get('companyUrl', '')}

【本文（お問い合わせ内容）】
{message}

【手順】
1. URLにアクセスしてフォームを見つける
2. 必須項目を入力する（姓名分割、フリガナ、都道府県選択に注意）
3. 同意チェックボックスがあればチェック
4. 送信（または確認）ボタンをクリック
5. 確認画面が出たら最終送信ボタンをクリック

【完了判定 — 必ずこのルールに従うこと】
以下のいずれかに該当したら、即座に done アクションで結果を報告して終了すること。

● 送信成功:
  - 「ありがとうございます」「送信完了」「送信しました」「受け付けました」等のメッセージが表示された
  - URLが /thanks, /complete, /done 等に遷移した
  - 送信ボタンクリック後にフォームが消えて別の画面に切り替わった
  → done で「送信完了しました」と報告

● 送信失敗（即座に撤退）:
  - 404 / 403 / 500エラーページが表示された
  - CAPTCHAでブロックされた
  - フォームが見つからない
  - バリデーションエラーが出て、手持ちの情報では解決できない
  → done で失敗理由を報告

【禁止事項】
- 送信ボタンを押した後に、フォームの入力内容を再確認・やり直ししないこと。一度送信したら完了判定に進む。
- 同じフィールドに2回以上入力し直さないこと。Shadow DOMでフィールドが空に見えても、既に入力済みなら再入力しない。
- 同じ操作を3回以上繰り返さないこと。うまくいかなければ失敗として報告する。
"""


def _now_iso() -> str:
    """ISO 8601 形式の現在時刻文字列を返す純粋関数。"""
    return datetime.now().isoformat()


# 機密保護: error_reason に紛れ込みうる送信者個人情報 / API キー断片を伏字化する。
# AI が返答テキスト内で sender_info の値を引用した場合、それが CSV に出力されると
# コミュニティ配布時に個人情報漏洩リスクとなるため、書き出し直前に置換する。
_SENSITIVE_SENDER_KEYS = (
    "email",
    "phone",
    "address",
    "lastName",
    "firstName",
    "nameKana",
    "nameHiragana",
    "zip",
    "companyUrl",
)
# Anthropic API キーの prefix。万一テキストに紛れた場合に伏字化する。
_API_KEY_PATTERN = re.compile(r"sk-ant-[A-Za-z0-9_\-]+")
# 短すぎる値の誤置換を避けるための最小長 (例: zip="100" のような 3 桁を残すかどうか境界)。
_SANITIZE_MIN_VALUE_LEN = 3

# #38: Stage 1.5(汎用Playwright送信)1社あたりの掛け時計上限(秒)。真のハングだけを
# 捕るよう余裕を持たせる: goto(最大30s)+検出+35欄入力+success待ち(12s)を足しても
# 正当な送信はこの内に収まる。超過した社は失敗確定して次社へ(Fail Safe)。
_STAGE15_BUDGET_S = 180.0


def _sanitize_error_reason(text: str, sender_info: dict) -> str:
    """error_reason / 進捗ログに書き出す前にPII (個人識別情報) と API キー断片を伏字化する。

    Fail Safe: 例外が出ても元のテキストをそのまま返す (機密保護よりも処理続行を
    優先しない場合は将来 raise に切替えること)。
    """
    if not text:
        return text
    try:
        if isinstance(sender_info, dict):
            for key in _SENSITIVE_SENDER_KEYS:
                raw = sender_info.get(key)
                if raw is None:
                    continue
                value = str(raw)
                if len(value) >= _SANITIZE_MIN_VALUE_LEN and value in text:
                    text = text.replace(value, "<redacted>")
        text = _API_KEY_PATTERN.sub("<redacted-api-key>", text)
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_skill_core] _sanitize_error_reason failed (continuing with raw text): "
            f"{type(e).__name__}: {e}\n"
        )
    return text


def _save_screenshot(
    screenshot_bytes: Optional[bytes],
    screenshot_dir: Optional[str],
    company_name: str,
) -> Optional[str]:
    """スクリーンショット bytes をファイルへ保存する。

    Fail Safe: ディスク書き込みエラーは握って None を返す（呼出し側は status を
    優先して決めているため、screenshot 取得失敗だけで failed にしない）。
    """
    if not screenshot_bytes or not screenshot_dir:
        return None
    try:
        dir_path = Path(screenshot_dir)
        dir_path.mkdir(parents=True, exist_ok=True)
        # ファイル名: <timestamp>_<sanitized_company>.png
        # 機密情報は含まない。company_name は CSV 由来の公開情報。
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(
            c if c.isalnum() or c in ("-", "_") else "_" for c in company_name
        )[:40] or "company"
        path = dir_path / f"{ts}_{safe_name}.png"
        path.write_bytes(screenshot_bytes)
        return str(path.resolve())
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_skill_core] screenshot save failed (continuing): "
            f"{type(e).__name__}: {e}\n"
        )
        return None


async def _run_browser_use_send(
    company_name: str,
    url: str,
    message: str,
    sender_info: dict,
    *,
    api_key: str,
    model: str,
    screenshot_dir: Optional[str],
) -> dict:
    """Internal: run a single browser-use + Claude Sonnet send.

    Sprint 4 の `process_one_company` の本体ロジックを Sprint 5 で抽出。
    `LocalBrowserUseProvider` から呼ばれる。返り値スキーマは
    {status, error_reason, screenshot_path, ended_at, provider_used}.
    """
    # --- API キーを browser-use が読む環境変数へセット ----------------------
    # browser-use の ChatAnthropic は内部で os.environ["ANTHROPIC_API_KEY"] を
    # 読みに行く (browser_use.llm.ChatAnthropic は anthropic SDK の AsyncClient
    # を生成する際に api_key 引数が無ければ env 経由になる)。
    # 呼出し側で既に同じ値がセットされていれば no-op。
    # WARNING: このプロセスの ANTHROPIC_API_KEY を上書きします。
    # Web アプリ版 (python_worker/browser_use_worker.py) と同一プロセスから
    # skill.core._skill_core を import しないこと。
    os.environ["ANTHROPIC_API_KEY"] = api_key

    # browser-use のテレメトリ無効化 (CLAUDE.md 規則: ANONYMIZED_TELEMETRY=false)
    os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")

    # --- browser-use のログ静音化 (既定: 結果のみ) -------------------------
    # browser-use ライブラリは import 時に BROWSER_USE_LOGGING_LEVEL を読んで
    # ロガーを構成するため、必ず import より前に設定する。既定ではエージェントの
    # 逐次思考ログ (1 社で 200 行近く) をコンソールへ出さず、結果だけ残す。
    # 全文を見たいときは AUTOFORM_VERBOSE=1 で従来どおり info ログに戻せる。
    _verbose = os.environ.get("AUTOFORM_VERBOSE", "").strip() == "1"
    os.environ.setdefault(
        "BROWSER_USE_LOGGING_LEVEL", "info" if _verbose else "result"
    )
    if not _verbose:
        # 防御的に、既知の冗長ロガーを WARNING 以上へ引き上げる
        # (BROWSER_USE_LOGGING_LEVEL を尊重しないサブロガー対策)。
        import logging as _logging
        for _name in ("browser_use", "Agent", "bubus", "cdp_use", "root"):
            try:
                _logging.getLogger(_name).setLevel(_logging.WARNING)
            except BaseException:  # noqa: BLE001 — best effort
                pass

    # --- browser-use の遅延 import (副作用最小化) ---------------------------
    # モジュール読込時に browser-use を import すると重い (puppeteer-core 取得等
    # の副作用も発生しうる)。process_one_company が呼ばれて初めて import する。
    try:
        from browser_use import Agent, BrowserProfile  # type: ignore
        from browser_use.llm import ChatAnthropic  # type: ignore
    except ImportError as imp_err:
        return {
            "status": "failed",
            "error_reason": (
                f"browser-use library not installed: {imp_err}. "
                "Run `uv sync` (Skill) or `pip install browser-use` (manual)."
            ),
            "screenshot_path": None,
            "ended_at": _now_iso(),
            "provider_used": "browser_use",
        }

    # --- Agent 構築 & 実行 -------------------------------------------------
    prompt = _build_task_prompt(company_name, url, message, sender_info)
    screenshot_bytes: Optional[bytes] = None
    error_reason: Optional[str] = None
    is_success = False
    final_result_text = ""

    try:
        llm = ChatAnthropic(model=model, temperature=0.0)

        # Phase A1: Stage 1.5 と同じ AUTOFORM_HEADLESS=1 でヘッドレス統一制御
        # (既定は可視 = 現行動作を壊さない)
        _headless = os.environ.get("AUTOFORM_HEADLESS", "").strip() == "1"
        browser_profile = BrowserProfile(
            headless=_headless,
            viewport={"width": 1280, "height": 720},
            cross_origin_iframes=True,
            enable_default_extensions=True,
        )

        # NOTE: Sync with python_worker/browser_use_worker.py:555-576 (AGENT_COMMON)
        # Skill 版は 1 stage のみで KISS (Vision retry は YAGNI、初回失敗で次社へ)。
        agent: Any = Agent(
            task=prompt,
            llm=llm,
            browser_profile=browser_profile,
            max_failures=3,
            max_actions_per_step=5,
            max_steps=10,
            include_attributes=[
                "type",
                "placeholder",
                "aria-label",
                "aria-required",
                "value",
                "name",
            ],
            extend_system_message=FORM_GUIDELINE_STATIC,
            use_vision=False,
        )

        result = await agent.run()

        # スクショ撮影 (Fail Safe: 失敗しても処理は続行)
        try:
            page = await agent.browser_session.get_current_page()
            if page is not None:
                screenshot_bytes = await page.screenshot(format="png")
        except BaseException as shot_err:  # noqa: BLE001 — Fail Safe
            sys.stderr.write(
                f"[_skill_core] screenshot capture failed (continuing): "
                f"{type(shot_err).__name__}: {shot_err}\n"
            )

        final_result_text = (result.final_result() or "") if result is not None else ""
        is_success = _check_success(final_result_text)

        if not is_success:
            # 失敗理由: agent の final_result_text を 200 文字に切り詰める
            error_reason = (
                final_result_text[:200] if final_result_text
                else "AI agent did not report success"
            )
    except BaseException as e:  # noqa: BLE001 — Fail Safe per spec §5 Task 1
        # browser-use 内部の例外 (タイムアウト, ネットワーク, Anthropic API error 等)
        # を全部ここで握って failed として返す。Skill ユーザーは次社処理を続行する。
        is_success = False
        error_reason = f"{type(e).__name__}: {e}"[:200]

    # --- 結果 dict 組み立て --------------------------------------------------
    screenshot_path = _save_screenshot(
        screenshot_bytes, screenshot_dir, company_name
    )

    # 機密保護: error_reason に sender_info の値や API キー断片が紛れ込んでいないか
    # チェックし、見つかれば伏字化する。コミュニティ配布で output_*.csv を共有する
    # 際の個人情報漏洩リスクを抑える (MUST FIX #2)。
    sanitized_error_reason = (
        None if is_success else _sanitize_error_reason(error_reason or "", sender_info)
    )

    return {
        "status": "completed" if is_success else "failed",
        "error_reason": sanitized_error_reason,
        "screenshot_path": screenshot_path,
        "ended_at": _now_iso(),
        "provider_used": "browser_use",
    }


# =============================================================================
# Sprint 5 Task 4 — Provider abstraction
# =============================================================================
class FormSendProvider(ABC):
    """ABC for a form-send strategy.

    Implementations:
        LocalBrowserUseProvider — browser-use + Claude Sonnet AI fallback
        LocalHttpPostProvider   — CF7 HTTP POST direct send (cost ¥0)
        HybridProvider          — HTTP POST first + Pareto noAI + AI fallback
        AutoformSendAPIProvider — Phase 3 placeholder (not implemented in Sprint 5)

    Return-value schema (all providers must produce):
        {
            "status": "completed" | "failed" | "skipped",
            "error_reason": str | None,
            "screenshot_path": str | None,
            "ended_at": str,                    # ISO 8601
            "provider_used": str,               # "http_post" | "browser_use" | "none"
        }
    """

    @abstractmethod
    async def send(
        self,
        company_name: str,
        url: str,
        message: str,
        sender_info: dict,
        *,
        screenshot_dir: Optional[str] = None,
    ) -> dict:
        """Send a single message and return the canonical result dict."""
        raise NotImplementedError


class LocalBrowserUseProvider(FormSendProvider):
    """Phase 1 (Sprint 4) AI fallback: browser-use + Claude Sonnet.

    The `api_key` / `model` are bound at construction time so a single
    HybridProvider can share them across the 25-row CSV loop.
    """

    def __init__(self, *, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self._api_key = api_key
        self._model = model

    async def send(
        self,
        company_name: str,
        url: str,
        message: str,
        sender_info: dict,
        *,
        screenshot_dir: Optional[str] = None,
    ) -> dict:
        # _run_browser_use_send already returns the canonical schema incl.
        # provider_used="browser_use".
        return await _run_browser_use_send(
            company_name=company_name,
            url=url,
            message=message,
            sender_info=sender_info,
            api_key=self._api_key,
            model=self._model,
            screenshot_dir=screenshot_dir,
        )


class LocalHttpPostProvider(FormSendProvider):
    """CF7 HTTP POST direct send.

    Calls `_http_form_sender.try_http_post` and maps `Cf7SendResult.status`
    onto the canonical schema.

    Mapping (Sprint 5 spec §6 Task 4):
        completed              -> provider_used="http_post", status="completed"
        prohibition_detected   -> provider_used="none", status="skipped",
                                  error_reason="prohibition_detected"
        bot_protection         -> provider_used="none", status="failed",
                                  error_reason=f"bot_protection:{message}"
        recaptcha_detected     -> provider_used="http_post", status="failed"  (caller defers to AI)
        non_cf7                -> provider_used="http_post", status="failed"  (caller defers to AI)
        validation_failed      -> provider_used="http_post", status="failed"
        error                  -> provider_used="http_post", status="failed"  (caller may defer to AI via noAI filter)
    """

    async def send(
        self,
        company_name: str,
        url: str,
        message: str,
        sender_info: dict,
        *,
        screenshot_dir: Optional[str] = None,
    ) -> dict:
        # Build FillData from sender_info + per-row message
        # (sender_info uses the same key names as FillData)
        fill_data: dict[str, Any] = dict(sender_info)
        fill_data["message"] = message

        # Late import to avoid pulling httpx during simple unit tests of
        # process_one_company that don't exercise HTTP POST.
        # Dual import path: package context vs skill/scripts/run_send.py.
        try:
            from skill.core._http_form_sender import try_http_post  # noqa: WPS433
        except ImportError:
            from _http_form_sender import try_http_post  # type: ignore  # noqa: WPS433

        try:
            result = await try_http_post(url, fill_data)  # type: ignore[arg-type]
        except BaseException as e:  # noqa: BLE001 — Fail Safe
            return {
                "status": "failed",
                "error_reason": _sanitize_error_reason(
                    f"{type(e).__name__}: {e}"[:200], sender_info
                ),
                "screenshot_path": None,
                "ended_at": _now_iso(),
                "provider_used": "http_post",
            }

        # Map Cf7SendResult.status -> canonical
        if result.status == "completed":
            return {
                "status": "completed",
                "error_reason": None,
                "screenshot_path": None,
                "ended_at": _now_iso(),
                "provider_used": "http_post",
            }
        if result.status == "prohibition_detected":
            return {
                "status": "skipped",
                "error_reason": "prohibition_detected",
                "screenshot_path": None,
                "ended_at": _now_iso(),
                "provider_used": "none",
            }
        if result.status == "bot_protection":
            return {
                "status": "failed",
                "error_reason": f"bot_protection:{result.message or 'unknown'}",
                "screenshot_path": None,
                "ended_at": _now_iso(),
                "provider_used": "none",
            }
        # non_cf7 / recaptcha_detected / validation_failed / mail_failed / error
        # All of these leave the caller in charge of further routing.
        # We preserve the status string in error_reason so HybridProvider can
        # decide whether to defer to AI fallback.
        return {
            "status": "failed",
            "error_reason": _sanitize_error_reason(
                f"{result.status}:{result.message}" if result.message else result.status,
                sender_info,
            ),
            "screenshot_path": None,
            "ended_at": _now_iso(),
            "provider_used": "http_post",
        }


# -----------------------------------------------------------------------------
# reCAPTCHA 事前ゲート — ブラウザ(Stage 1.5)に入る前に v2/v3 を判定して振り分ける。
# 狙い①: 突破不能な社に時間・トークンを浪費させない（モニター報告の「CF7＋reCAPTCHA
#   v3 で送信失敗」＝フルコストを払って bot 判定で負けた無駄撃ちを消す）。
# 狙い②: v3 は「自動ツールが触った時点で減点確定＝アシスト(自動入力)でも弾かれる」ため、
#   自動ツールを一切触らせず 🔴手動ハンドオフ（人が自分のブラウザで丸ごと送る）へ回す。
#   v2 は最後のチェックだけ人が解けば送れるので 🟡アシストへ。
# -----------------------------------------------------------------------------
def _recaptcha_type(error_reason: str) -> str:
    """error_reason 'recaptcha_detected:<type>' から v2/v3/unknown を取り出す。"""
    if "recaptcha_detected:" not in error_reason:
        return "unknown"
    rest = error_reason.split("recaptcha_detected:", 1)[1].strip()
    token = rest.split()[0].strip(":|").lower() if rest else ""
    return token if token in ("v2", "v3") else "unknown"


def _recaptcha_v3_to_manual() -> bool:
    """v3(invisible) を自動で挑戦させず 🔴手動ハンドオフへ回すか。既定=ON(件数優先)。

    AUTOFORM_RECAPTCHA_V3_MANUAL=0/false/off で OFF（v3 は Stage 1.5 で 1 回だけ
    送信を試す＝従来挙動）。CapSolver やステルス化で v3 を突破できる環境では OFF を推奨。
    """
    val = os.environ.get("AUTOFORM_RECAPTCHA_V3_MANUAL", "1").strip().lower()
    return val not in ("0", "false", "no", "off", "")


def _recaptcha_gate_reason(rc_type: str) -> Optional[str]:
    """reCAPTCHA 種別ごとの「ブラウザに入れる前の終端 error_reason」を返す。

    None を返した場合は事前ゲートを素通り＝従来どおり Stage 1.5 で 1 回試す。
      - v2                → "bot_protection_recaptcha:v2"      → 🟡アシスト
      - v3 / unknown(既定) → "bot_protection_recaptcha_v3:manual" → 🔴手動ハンドオフ
      - v3 (スイッチOFF)   → None（Stage 1.5 で試す）
    unknown は判別不能なので、より確実に送れる v3 ポリシー(手動)に倒す（誤ってアシストに
    入れて弾かれるより、人の手で確実に送れる方を優先）。
    """
    if rc_type == "v2":
        return "bot_protection_recaptcha:v2"
    # v3 / unknown は v3 ポリシーに従う
    if _recaptcha_v3_to_manual():
        return "bot_protection_recaptcha_v3:manual"
    return None


class HybridProvider(FormSendProvider):
    """Hybrid: HTTP POST first -> [Stage 1.5 general form] -> noAI filter -> AI fallback.

    Implements the Stage 0/1/1.5/2/3 flow from system-workflow §2.4 + §3.2:
        Stage 0:   prohibition / bot_protection early-skip (no AI call)
        Stage 1:   CF7 HTTP POST direct send
        Stage 1.5: Generic Playwright form + pattern-mapping send (Sprint 6)
        Stage 2:   Pareto noAI filter (skip AI when WAF / DNS / etc.)
        Stage 3:   AI fallback (browser-use + Claude Sonnet)

    Sprint 6 args:
        enable_stage15: when False, behaves like Sprint 5 HybridProvider
            (Stage 1.5 bypassed entirely — no SQLite writes either).
            Used by `run_send.py --mode legacy-no-stage15` for debugging.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "claude-sonnet-4-6",
        enable_stage15: bool = True,
    ) -> None:
        self._http_post = LocalHttpPostProvider()
        self._enable_stage15 = enable_stage15
        # Build the Stage 1.5 provider lazily (importing _general_form_sender at
        # module load time would pull Playwright into every test run).
        self._general_form: Optional[Any] = None
        self._browser_use = LocalBrowserUseProvider(api_key=api_key, model=model)
        # v1: AIキー(ANTHROPIC)が無ければ Stage 3(browser_use) は使わない。
        # HTTP＋辞書＋サーバーで送れない難フォームは人間アシスト/手動へ回す。
        self._ai_enabled = bool((api_key or "").strip())

    def _get_general_form_provider(self) -> Optional[Any]:
        if not self._enable_stage15:
            return None
        if self._general_form is not None:
            return self._general_form
        try:
            try:
                from skill.core._general_form_sender import LocalGeneralFormProvider  # noqa: WPS433
            except ImportError:
                from _general_form_sender import LocalGeneralFormProvider  # type: ignore  # noqa: WPS433
            self._general_form = LocalGeneralFormProvider()
        except BaseException as e:  # noqa: BLE001 — Fail Safe
            sys.stderr.write(
                f"[HybridProvider] could not load Stage 1.5 LocalGeneralFormProvider "
                f"(continuing without it): {type(e).__name__}: {e}\n"
            )
            self._general_form = None
            self._enable_stage15 = False
        return self._general_form

    async def send(
        self,
        company_name: str,
        url: str,
        message: str,
        sender_info: dict,
        *,
        screenshot_dir: Optional[str] = None,
        field_decisions: Optional[dict] = None,
        auto_default: bool = False,
    ) -> dict:
        # Late import to keep dictionary-free callers happy.
        # Dual import path: package context vs skill/scripts/run_send.py.
        try:
            from skill.core._pattern_loader import should_send_to_ai  # noqa: WPS433
        except ImportError:
            from _pattern_loader import should_send_to_ai  # type: ignore  # noqa: WPS433

        # 診断トレース（純観測）: 各 Stage の通過を記録し、返却 dict に `_trace`
        # キーとして添える。consumer は `.get()` 参照、CSV は extrasaction="ignore"
        # なので送信ロジック・出力には一切影響しない。
        trace_stages: list[dict] = []

        def _ret(result: dict) -> dict:
            result["_trace"] = trace_stages
            return result

        http_result = await self._http_post.send(
            company_name=company_name,
            url=url,
            message=message,
            sender_info=sender_info,
            screenshot_dir=screenshot_dir,
        )

        # Stage 0 — early skip judgments (do NOT defer to AI)
        error_reason = http_result.get("error_reason") or ""
        if error_reason == "prohibition_detected":
            trace_stages.append({
                "stage": "0_early_skip", "result": "tripped",
                "reason": "prohibition_detected", "detail": None,
            })
            return _ret(http_result)
        if error_reason.startswith("bot_protection:"):
            trace_stages.append({
                "stage": "0_early_skip", "result": "tripped",
                "reason": error_reason, "detail": None,
            })
            return _ret(http_result)

        # Stage 1 — HTTP POST success
        if http_result.get("status") == "completed":
            trace_stages.append({
                "stage": "1_cf7_http", "result": "completed",
                "reason": None, "detail": None,
            })
            return _ret(http_result)

        # Stage 1 — failed (will route onward); record what HTTP POST reported.
        trace_stages.append({
            "stage": "1_cf7_http", "result": "failed",
            "reason": error_reason or None, "detail": None,
        })

        # Stage 1.5 (Sprint 6) — generic Playwright pattern-mapping
        # Skip Stage 1.5 if Stage 1 already detected a noAI signal (WAF/403/DNS等)
        # — Web 版 engine.ts と同等の優先順位、無駄なブラウザ起動を回避してコスト保護
        # ただし reCAPTCHA は CapSolver 経由で再挑戦可能なため Stage 1.5 へ送る
        # (仕様書 §3-7 の意図: CAPSOLVER_API_KEY 設定時のみ実際に CapSolver 呼び出し、
        #  未設定時は Stage 1.5 で reCAPTCHA detect → Stage 3 へ自然委譲)
        general_form = self._get_general_form_provider()
        is_recaptcha = error_reason.startswith("recaptcha_detected:")

        # 事前ゲート: reCAPTCHA はブラウザに入れる前に v2/v3 で振り分ける。ここで終端に
        # 落とせば Stage 1.5(自動ブラウザ)を一切起動しない＝v3 は自動ツールに触られず、
        # 監視されるべき挙動が発生しないまま 🔴手動ハンドオフへ回せる。
        if is_recaptcha:
            rc_type = _recaptcha_type(error_reason)
            gate_reason = _recaptcha_gate_reason(rc_type)
            if gate_reason is not None:
                route = "assist" if rc_type == "v2" else "manual"
                trace_stages.append({
                    "stage": "0.5_recaptcha_gate", "result": route,
                    "reason": f"recaptcha_{rc_type}", "detail": None,
                })
                return _ret({
                    "status": "failed",
                    "error_reason": gate_reason,
                    "screenshot_path": None,
                    "ended_at": _now_iso(),
                    "provider_used": "none",
                })

        if general_form is not None and (should_send_to_ai(error_reason) or is_recaptcha):
            try:
                # ★安全網(#38): Stage 1.5 全体を掛け時計で打ち切る。①のフレーム上限を
                # すり抜けた未知のハング(launch/screenshot/メインframe content 等)でも、
                # 1社が STAGE15_BUDGET_S を超えたら TimeoutError で失敗確定→次社へ。
                # 真のハングだけを捕るよう余裕を持たせる(正当に遅い正規送信は切らない)。
                general_result = await asyncio.wait_for(
                    general_form.send(
                        company_name=company_name,
                        url=url,
                        message=message,
                        sender_info=sender_info,
                        screenshot_dir=screenshot_dir,
                        field_decisions=field_decisions,
                        auto_default=auto_default,
                    ),
                    timeout=_STAGE15_BUDGET_S,
                )
            except BaseException as e:  # noqa: BLE001 — Fail Safe（TimeoutError含む）
                # If Stage 1.5 itself crashes, fall through to noAI/AI fallback.
                sys.stderr.write(
                    f"[HybridProvider] Stage 1.5 crashed (continuing): "
                    f"{type(e).__name__}: {e}\n"
                )
                trace_stages.append({
                    "stage": "1.5_general_form", "result": "crashed",
                    "reason": f"{type(e).__name__}: {e}"[:200], "detail": None,
                })
            else:
                # 欄検出 detail（fields_detected/mapped/unmapped）を trace に取り込む。
                trace_stages.append({
                    "stage": "1.5_general_form",
                    "result": general_result.get("status") or "failed",
                    "reason": general_result.get("error_reason") or None,
                    "detail": general_result.get("_trace_detail"),
                })
                if general_result.get("status") in ("completed", "skipped"):
                    return _ret(general_result)
                # Failure -> 元の Stage 1 error_reason に general_result の error_reason を
                # 追記してマージ。元の noAI シグナルを保持しつつ詳細情報も残す。
                new_reason = general_result.get("error_reason") or ""
                if new_reason:
                    error_reason = (
                        f"{error_reason} | {new_reason}" if error_reason else new_reason
                    )

        # Stage 2 — Pareto noAI filter
        # Use the most recent error message (which we packed into error_reason
        # in LocalHttpPostProvider / Stage 1.5) as the noAI heuristic input.
        # should_send_to_ai treats unknown messages as "send to AI" (conservative).
        if not should_send_to_ai(error_reason):
            # Mark as noAI-filter skip
            trace_stages.append({
                "stage": "2_noai_filter", "result": "tripped",
                "reason": error_reason or None, "detail": None,
            })
            return _ret({
                "status": "failed",
                "error_reason": f"noai_filter:{error_reason}",
                "screenshot_path": None,
                "ended_at": _now_iso(),
                "provider_used": "none",
            })

        # Stage 3 — AI fallback（v1: AIキーが無ければ試行せずスキップ）
        # browser_use を空キーで叩くと auth error になるだけなので、上流の
        # error_reason（unknown_fields:needs_assist 等）を保持したまま failed で返し、
        # run_send 側のハンドオフ振り分け（🟡アシスト/🔴手動）に委ねる。
        if not self._ai_enabled:
            trace_stages.append({
                "stage": "3_ai_fallback", "result": "skipped",
                "reason": "no_api_key", "detail": None,
            })
            return _ret({
                "status": "failed",
                "error_reason": error_reason or "stage15_failed_no_ai",
                "screenshot_path": None,
                "ended_at": _now_iso(),
                "provider_used": "none",
            })

        ai_result = await self._browser_use.send(
            company_name=company_name,
            url=url,
            message=message,
            sender_info=sender_info,
            screenshot_dir=screenshot_dir,
        )
        trace_stages.append({
            "stage": "3_ai_fallback",
            "result": ai_result.get("status") or "failed",
            "reason": ai_result.get("error_reason") or None,
            "detail": None,
        })
        return _ret(ai_result)


class AutoformSendAPIProvider(FormSendProvider):
    """Phase 3 placeholder — calls the future AutoformSend SaaS API.

    Sprint 5 spec §13: 本 Sprint で **実装本体は書かない**。インターフェースだけ。

    将来 Phase 3 で実装するとき:
        - `__init__(self, *, api_key: str, base_url: str)` を追加
        - `send()` の中で `httpx.AsyncClient` で POST /api/skill-send を呼ぶ
        - provider_used="autoformsend_api" を返す
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Constructor body intentionally empty — kept so the class can be
        # subclassed and instantiated during Provider-shape tests.
        pass

    async def send(
        self,
        company_name: str,
        url: str,
        message: str,
        sender_info: dict,
        *,
        screenshot_dir: Optional[str] = None,
    ) -> dict:
        raise NotImplementedError(
            "AutoformSendAPIProvider is a Phase 3 placeholder. "
            "Implement in a follow-up sprint after the SaaS API ships."
        )


# =============================================================================
# Backward-compatible process_one_company (Sprint 4 signature)
# =============================================================================
async def process_one_company(
    company_name: str,
    url: str,
    message: str,
    sender_info: dict,
    *,
    api_key: str,
    model: str = "claude-sonnet-4-6",
    screenshot_dir: Optional[str] = None,
    provider: Optional[FormSendProvider] = None,
    field_decisions: Optional[dict] = None,
    auto_default: bool = False,
) -> dict:
    """1 社のお問い合わせフォームへ営業メッセージを送信する。

    Sprint 4 後方互換: `provider=None` のとき `LocalBrowserUseProvider` を
    内部で生成して呼ぶ。返り値は Sprint 4 と同じキー + 新規 `provider_used`。

    Sprint 5 拡張: `provider=HybridProvider(api_key=..., model=...)` を渡すと
    HTTP POST 先行 + 早期スキップ + Pareto noAI + AI fallback のハイブリッド動作。

    Args:
        company_name: 対象企業名 (プロンプト・スクショファイル名に使用)。
        url: お問い合わせフォーム URL。
        message: 送信本文。
        sender_info: 送信者情報 dict (FillData 互換キー)。
        api_key: ANTHROPIC_API_KEY。`provider` が None のときのみ参照される。
        model: Claude モデル名。`provider` が None のときのみ参照される。
        screenshot_dir: スクリーンショット保存先ディレクトリ。None なら保存しない。
        provider: Sprint 5 拡張 — 明示的に Provider を渡す場合に使う。
                  None なら LocalBrowserUseProvider (Sprint 4 同等動作)。

    Returns:
        dict: {"status", "error_reason", "screenshot_path", "ended_at", "provider_used"}

    Raises:
        通常の例外は内部で握って failed として返す (Skill ユーザーは次社へ進む)。
    """
    # --- 入力バリデーション (Fail Fast for programming errors) ---------------
    if not isinstance(sender_info, dict):
        return {
            "status": "failed",
            "error_reason": f"sender_info must be dict, got {type(sender_info).__name__}",
            "screenshot_path": None,
            "ended_at": _now_iso(),
            "provider_used": "none",
        }
    if not url:
        return {
            "status": "failed",
            "error_reason": "url is empty",
            "screenshot_path": None,
            "ended_at": _now_iso(),
            "provider_used": "none",
        }
    # api_key validation only matters for the default provider path
    if provider is None and not api_key:
        return {
            "status": "failed",
            "error_reason": "api_key is empty",
            "screenshot_path": None,
            "ended_at": _now_iso(),
            "provider_used": "none",
        }

    if provider is None:
        provider = LocalBrowserUseProvider(api_key=api_key, model=model)

    # field_decisions/auto_default は Stage 1.5 を持つ HybridProvider だけが解する。
    # 他 Provider のシグネチャを壊さないよう、対応 Provider のときだけ渡す。
    extra: dict = {}
    if isinstance(provider, HybridProvider):
        extra = {"field_decisions": field_decisions, "auto_default": auto_default}

    try:
        return await provider.send(
            company_name=company_name,
            url=url,
            message=message,
            sender_info=sender_info,
            screenshot_dir=screenshot_dir,
            **extra,
        )
    except BaseException as e:  # noqa: BLE001 — Fail Safe top-level
        return {
            "status": "failed",
            "error_reason": _sanitize_error_reason(
                f"{type(e).__name__}: {e}"[:200], sender_info
            ),
            "screenshot_path": None,
            "ended_at": _now_iso(),
            "provider_used": "none",
        }


# -----------------------------------------------------------------------------
# 単体動作確認用 (CLI 直叩きは想定しない、import グラフ確認のため)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # `python -c "from python_worker._skill_core import process_one_company; print('ok')"`
    # と同等の検証。実際の Browser Use 起動は行わない。
    print("[_skill_core] module loaded successfully")
    print(f"  - process_one_company: {process_one_company}")
    print(f"  - providers: FormSendProvider, LocalBrowserUseProvider, LocalHttpPostProvider, HybridProvider")
    print(f"  - FORM_GUIDELINE_STATIC length: {len(FORM_GUIDELINE_STATIC)} chars")
    print(f"  - _SUCCESS_KEYWORDS: {len(_SUCCESS_KEYWORDS)} entries (incl. confirmation-signals merge)")
