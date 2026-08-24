"""Diagnostic trace logger — 1 社 1 行の JSONL「送信カルテ」を残す失敗解剖ログ。

`_usage_logger`（コスト）/ `_learning_dictionary`（成功学習）とは別系統で、
**失敗の解剖**を担う:
    - どの Stage で止まったか        (stages[])
    - どのフォーム/どの欄で失敗か    (field_detail.fields_unmapped ← 辞書追加候補)
    - reCAPTCHA か 欄判定ミスか      (failure_category 固定 enum)
    - 人間確認に回すべきか          (needs_human_review)
    - AI がどう動いたか              (ai_summary 要約のみ)

設計原則:
    - **純観測**。送信ロジックには一切干渉しない。
    - 全書き込みは Fail Safe（ログのバグで送信を絶対に止めない）。
    - 失敗理由は自由文ではなく**固定タクソノミ**に正規化し、後から集計可能にする。

入力は `process_one_company` が返す outcome dict（+ provider が埋めた
`_trace` / `_trace_detail` の追加キー）。出力は `logs/trace_<run_id>.jsonl`。

無効化: 環境変数 `TRACE_LOGGING_ENABLED=false`。
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# =============================================================================
# 失敗タクソノミ（固定 enum）
# =============================================================================
# 既存の自由文 error_reason をこの enum に正規化する。集計の核。
#
# 人間確認に回すべきカテゴリ（"送れたか不明" / CAPTCHA / 未分類）。
_HUMAN_REVIEW_REASONS = {
    "confirmation_unclear": "送信した可能性があるが完了確認できず — 最優先で目視",
    "unknown_fields": "辞書に無い必須/選択欄 — アシストモードで人が値を選んで送信",
    "bot_protection_recaptcha": "reCAPTCHA v2 — 自動不可、アシストで人が最後に解いて送信",
    "bot_protection_recaptcha_v3": "reCAPTCHA v3 — 挙動監視型で自動不可、手動ハンドオフ(自分のブラウザで送信)",
    "bot_protection_hcaptcha": "hCaptcha — 自動不可、アシストで人が最後に解いて送信",
    "bot_protection_turnstile": "Turnstile — 挙動監視型で自動不可、手動ハンドオフ(自分のブラウザで送信)",
    "bot_protection": "Bot 保護検出 — 手動送信候補",
    # 未送信だが、シートでは status=skipped が「除外」へ畳まれて自動送信対象から
    # 外れてしまう(=会社が静かに消える)。目視キューには残したままにする。
    "domain_cooldown": "待機のため未送信 — 送るならシートの status を空にして再実行",
    # 文字数上限（#57）。未送信が確定していて、原因も対処も分かっている＝人が文面を
    # 短くすれば次回そのまま送れる。目視キューに残して気づけるようにする。
    "message_too_long": "本文が長すぎて送っていない — 短い版を用意すれば次回送信できる",
    "field_too_long": "入力欄に収まらない項目があり送っていない — 値を短くすれば送信できる",
    "unknown": "未分類の失敗 — 念のため目視",
}


def classify_failure(error_reason: Optional[str], status: str) -> str:
    """自由文 error_reason を固定カテゴリへ正規化する。

    成功は "success"、skip は "skipped_other"（prohibition 等は個別カテゴリ）。
    判定は「より具体的なシグナルを先に」見る順序で書く。
    """
    if status == "completed":
        return "success"

    r = (error_reason or "").lower().strip()
    if not r:
        return "skipped_other" if status == "skipped" else "unknown"

    # --- Bot 保護（最優先で具体的に分類）---
    # v3(invisible/スコア式) は自動不可＝手動ハンドオフ専用カテゴリ。汎用 recaptcha より前に。
    if "recaptcha_v3" in r:
        return "bot_protection_recaptcha_v3"
    if "recaptcha" in r:
        return "bot_protection_recaptcha"
    if "hcaptcha" in r:
        return "bot_protection_hcaptcha"
    if "turnstile" in r:
        return "bot_protection_turnstile"
    if "bot_protection" in r:
        return "bot_protection"

    # --- 営業禁止 ---
    if "prohibition" in r:
        return "prohibition"

    # --- 到達性 / ネットワーク ---
    if "err_name_not_resolved" in r or "dns" in r or "name_not_resolved" in r:
        return "dns_error"
    if "403" in r or "forbidden" in r or "waf" in r:
        return "waf_403"
    if "site_not_found" in r or "404" in r:
        return "site_not_found"
    if "timeout" in r or "timed out" in r:
        return "timeout"
    if "transient_5xx" in r or "http 5" in r or "500" in r or "502" in r or "503" in r:
        return "http_5xx"

    # --- 文字数上限で入りきらない（#57）---
    # ★"field" 判定より前に置く: 本文以外の欄は "field_too_long:email" のような reason に
    #   なるため、下の `if "field" in r` に先に拾われると「入力欄をうまく特定できず」に化ける。
    #   切り詰めは**原因が分かっている**失敗なので、原因が読める形で残す。
    if "message_too_long" in r:
        return "message_too_long"
    if "too_long" in r:
        return "field_too_long"

    # --- フォームレベル（辞書強化の対象）---
    if "form_not_found" in r:
        return "form_not_found"
    if "confirmation" in r or "unclear" in r or "no_confirmation" in r:
        return "confirmation_unclear"
    if "submit" in r:
        return "submit_not_found"
    # 未知欄（辞書で解けず AI も使わない）→ 人間アシスト対象。"field" 判定より前に置く。
    if "unknown_field" in r:
        return "unknown_fields"
    if "field_mapping" in r or "field" in r:
        return "field_detection_miss"

    # --- noAI フィルタ（Stage 2 でスキップ）---
    if "noai_filter" in r:
        return "noai_filtered"

    # --- 意図的な待機（失敗ではない・未送信が確定）---
    # ★ここに置く理由: 今日 "domain_cooldown" は上のどの分岐にも当たらず "unknown" へ
    #   落ちている。最後尾に足せば、拾うのはその "unknown" だけ＝既存分類の巻き添えが
    #   構造的にゼロになる。上位に置くと "error:HTTP 404 ... | domain_cooldown" のような
    #   合成 reason（error_reason は Stage1 と Stage1.5 の連結）から site_not_found 等を
    #   横取りしてしまう。
    if "domain_cooldown" in r:
        return "domain_cooldown"

    return "unknown"


def triage(category: str) -> tuple[bool, str]:
    """失敗カテゴリ → (人間確認が必要か, 理由)。"""
    reason = _HUMAN_REVIEW_REASONS.get(category)
    if reason:
        return True, reason
    return False, ""


# 失敗カテゴリ → シート/ユーザー向けの日本語説明（技術コードを人が読める言葉に）。
_JP_CATEGORY: dict[str, str] = {
    "success": "送信完了",
    "prohibition": "営業お断りの明記あり → 送信せずスキップ",
    "bot_protection_recaptcha": "reCAPTCHA v2 で自動送信不可 → アシストで人が仕上げ",
    "bot_protection_recaptcha_v3": "reCAPTCHA v3(挙動監視型)で自動不可 → 手動ハンドオフ(通常ブラウザで送信)",
    "bot_protection_hcaptcha": "hCaptcha で自動送信不可 → アシストで人が仕上げ",
    "bot_protection_turnstile": "Turnstile(挙動監視型)で自動不可 → 手動ハンドオフ(通常ブラウザで送信)",
    "bot_protection": "Bot 保護検知 → アシスト/手動候補",
    "unknown_fields": "辞書に無い必須/選択欄 → 値を決めれば送信可（アシスト）",
    "confirmation_unclear": "送信した可能性あり・完了画面を確認できず → 要目視",
    # 文字数上限（#57）。★「上限」「文字数」を含める＝tierb_relabel が「要見直し」へ分類する
    #   合図になっている（文面を短くすれば次回そのまま送れる、という意味づけ）。
    #   本文と本文以外を分けるのは、「本文が長い」と表示しながら実はメール欄が切れていた、
    #   という表示の嘘を作らないため。
    "message_too_long": "本文が入力欄の文字数上限を超えています",
    "field_too_long": "入力欄の文字数上限に収まらない項目があります（連絡先が欠ける恐れ）",
    "form_not_found": "問い合わせフォームを検出できず",
    "submit_not_found": "送信ボタンを検出できず",
    "field_detection_miss": "入力欄をうまく特定できず",
    "noai_filtered": "WAF/画像認証など自動突破不能 → スキップ",
    "waf_403": "サーバー側ブロック(WAF/403) → 通常ブラウザで手動送信",
    "dns_error": "サイトに到達できず(ドメイン解決失敗/サイト消滅の可能性)",
    "site_not_found": "ページが見つからず(404)",
    "timeout": "ページ/送信がタイムアウト",
    "http_5xx": "相手サーバーがエラー応答(5xx)",
    "domain_cooldown": "同一サイトへ短時間に集中しないよう今回は見送り（未送信）→ 送るなら status セルを空にして再実行",
    "skipped_other": "対象外でスキップ",
    "unknown": "原因不明の失敗 → 念のため目視",
}


def japanese_reason(error_reason: str, status: str) -> str:
    """生の error_reason を、シート/ユーザー向けの日本語説明へ変換する。

    classify_failure で固定カテゴリへ正規化し、_JP_CATEGORY で日本語化する。
    マッピングが無い場合は元の文字列をそのまま返す（Fail-safe）。
    """
    if status == "completed":
        return "送信完了"
    cat = classify_failure(error_reason, status)
    return _JP_CATEGORY.get(cat) or (error_reason or "")


# =============================================================================
# TraceCollector — 1 社 1 インスタンス
# =============================================================================
class TraceCollector:
    """1 社分のトレースを組み立て、JSONL に 1 行追記する。

    使い方（run_send 側）:
        collector = TraceCollector(run_id=..., company_name=..., url=..., logs_dir=...)
        outcome = await process_one_company(...)   # provider が _trace を埋める
        collector.finalize(outcome)                 # 分類 + トリアージ + JSONL 追記
    """

    def __init__(
        self,
        *,
        run_id: str,
        company_name: str,
        url: str,
        logs_dir: str,
    ) -> None:
        self.run_id = run_id
        self.company_name = company_name
        self.url = url
        self.logs_dir = Path(logs_dir)

    # --- 内部ヘルパ ----------------------------------------------------------
    @staticmethod
    def _slim_stage(stage: dict) -> dict:
        """stage レコードを表示に必要な範囲へ整形（detail は保持）。"""
        return {
            "stage": stage.get("stage"),
            "result": stage.get("result"),
            "reason": stage.get("reason"),
            "detail": stage.get("detail"),
        }

    def _append(self, record: dict) -> None:
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        path = self.logs_dir / f"trace_{self.run_id}.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # --- 公開 API ------------------------------------------------------------
    def finalize(self, outcome: dict) -> Optional[dict]:
        """outcome から 1 社分のトレースレコードを構築し JSONL へ追記する。

        Fail Safe: いかなる例外も握り潰す（送信は既に終わっている）。
        戻り値は書き出したレコード（無効化時 / 失敗時は None）。
        """
        try:
            if os.environ.get("TRACE_LOGGING_ENABLED", "true").strip().lower() == "false":
                return None

            status = outcome.get("status", "failed")
            error_reason = outcome.get("error_reason") or ""
            provider = outcome.get("provider_used") or "none"
            stages: list[dict] = outcome.get("_trace") or []

            category = classify_failure(error_reason, status)
            needs_review, review_reason = (False, "")
            if status != "completed":
                needs_review, review_reason = triage(category)

            # Stage 1.5 の欄検出 detail（辞書追加候補の原材料）を抽出
            field_detail: Optional[dict] = None
            for s in stages:
                if s.get("stage") == "1.5_general_form" and s.get("detail"):
                    field_detail = s["detail"]

            # Stage 3 (browser_use) の AI 要約（要約のみ）
            ai_summary: Optional[dict] = None
            for s in stages:
                if s.get("stage") == "3_ai_fallback":
                    ai_summary = {
                        "agent_message": s.get("reason"),
                        "screenshot": outcome.get("screenshot_path") or None,
                    }

            unmapped = (field_detail or {}).get("fields_unmapped") or []

            record = {
                "run_id": self.run_id,
                "company_name": self.company_name,
                "url": self.url,
                "final_status": status,
                "final_provider": provider,
                "failure_category": category,
                "needs_human_review": needs_review,
                "human_review_reason": review_reason,
                "stages": [self._slim_stage(s) for s in stages],
                "unmapped_labels": unmapped,
                "field_detail": field_detail,
                "ai_summary": ai_summary,
                "error_reason": error_reason or None,
                "ended_at": outcome.get("ended_at") or datetime.now().isoformat(),
            }
            self._append(record)
            return record
        except BaseException as e:  # noqa: BLE001 — Fail Safe
            sys.stderr.write(
                f"[_trace_logger] finalize failed (continuing): "
                f"{type(e).__name__}: {e}\n"
            )
            return None
