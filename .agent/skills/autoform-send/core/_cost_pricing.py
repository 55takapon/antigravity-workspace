"""Sprint 3-C Task A-1 / Sprint 6 Task 1: AI 単価定数モジュール（Python 側）。

NOTE: Sync with python_worker/_cost_pricing.py (Web 版用)。Sprint 6 Task 1 で
Skill 単独配布対応のため `skill/core/` 配下にコピーした。価格改定時は両方を更新。
Phase 2-C で sync スクリプトを TS 版マスターと統合検討。

目的:
  AI fallback (Browser Use + Claude) で消費した Anthropic トークンを USD コストへ
  換算する純粋関数を提供する。TypeScript 側 `src/lib/ai/pricing.ts` と単価・
  換算ロジックを数値一致させる（CLAUDE.md「マジックナンバー禁止」の遵守）。

設計原則:
  - 単価は全て名前付き定数（per MTok = per 1,000,000 tokens）。
  - コスト計算は純粋関数（副作用なし・ユニットテスト可能）。
  - import 副作用ゼロ（モジュール import だけでは何も起きない）。

単価出典（2026-05-26 時点、Sprint 3-C §1 調査で確定）:
  - claude-sonnet-4-6: base_in $3 / cache_write_5m $3.75 / cache_read $0.30 / output $15
  - claude-haiku-4-5 : base_in $1 / cache_write_5m $1.25 / cache_read $0.10 / output $5
  - gpt-4o-mini      : in $0.15 / out $0.60
  ※ 価格改定時はこの 1 ファイル + pricing.ts を修正すれば全体に反映される。
  ※ ai_usage_logs にはトークン生値を残すため、単価改定後も再計算で補正できる。
"""

from __future__ import annotations

import os
from typing import Optional, TypedDict

# 1 トークンあたり単価を出すための除数（per MTok 表記 → per token）。
TOKENS_PER_MTOK = 1_000_000

# USD → JPY 為替レート。env var USD_TO_JPY で上書き可能。
# 未設定 / 不正値ならデフォルト 150（2026-05-26 時点）。自動取得 API は YAGNI。
DEFAULT_USD_TO_JPY = 150.0

# --- ホワイトリストモデル名（A-3 / B-1 と一致させる）-----------------------
CLAUDE_SONNET_MODEL = "claude-sonnet-4-6"
CLAUDE_HAIKU_MODEL = "claude-haiku-4-5"
GPT_4O_MINI_MODEL = "gpt-4o-mini"


class AnthropicPricing(TypedDict):
    """Anthropic 系モデルの単価（per MTok, USD）。cache を含む 4 区分。"""

    base_input_per_mtok: float
    cache_write_per_mtok: float
    cache_read_per_mtok: float
    output_per_mtok: float


class OpenAIPricing(TypedDict):
    """OpenAI 系モデルの単価（per MTok, USD）。in / out の 2 区分。"""

    input_per_mtok: float
    output_per_mtok: float


# Sprint 3-C §1 確定単価（2026-05-26 時点）。pricing.ts と数値一致。
CLAUDE_SONNET_4_6_PRICING: AnthropicPricing = {
    "base_input_per_mtok": 3.0,
    "cache_write_per_mtok": 3.75,
    "cache_read_per_mtok": 0.3,
    "output_per_mtok": 15.0,
}

CLAUDE_HAIKU_4_5_PRICING: AnthropicPricing = {
    "base_input_per_mtok": 1.0,
    "cache_write_per_mtok": 1.25,
    "cache_read_per_mtok": 0.1,
    "output_per_mtok": 5.0,
}

GPT_4O_MINI_PRICING: OpenAIPricing = {
    "input_per_mtok": 0.15,
    "output_per_mtok": 0.6,
}


def resolve_usd_to_jpy() -> float:
    """env var USD_TO_JPY を解決する。未設定 / 不正値はデフォルト 150。"""
    raw = os.environ.get("USD_TO_JPY")
    if not raw:
        return DEFAULT_USD_TO_JPY
    try:
        parsed = float(raw)
    except (TypeError, ValueError):
        print(
            f"⚠️ [cost] Invalid USD_TO_JPY={raw!r}, falling back to {DEFAULT_USD_TO_JPY}",
            flush=True,
        )
        return DEFAULT_USD_TO_JPY
    if parsed <= 0:
        print(
            f"⚠️ [cost] Non-positive USD_TO_JPY={raw!r}, falling back to {DEFAULT_USD_TO_JPY}",
            flush=True,
        )
        return DEFAULT_USD_TO_JPY
    return parsed


def resolve_anthropic_pricing(model: Optional[str]) -> Optional[AnthropicPricing]:
    """model 名から Anthropic 単価表を引く。未知モデルは None（呼び出し側で warn）。

    未知モデルを高い側 (Sonnet) でデフォルト計算せず None を返すのは、
    黙って過小 / 過大評価しないため（Fail Loud な単価解決）。pricing.ts と同方針。
    """
    if model == CLAUDE_SONNET_MODEL:
        return CLAUDE_SONNET_4_6_PRICING
    if model == CLAUDE_HAIKU_MODEL:
        return CLAUDE_HAIKU_4_5_PRICING
    return None


def _sanitize_tokens(n: Optional[int]) -> int:
    """負値 / None / 非数を 0 に丸める（コスト計算を Fail Safe にする）。"""
    if not isinstance(n, (int, float)):
        return 0
    if n < 0:
        return 0
    return int(n)


def cost_anthropic_usd(
    base_input_tokens: Optional[int],
    cache_creation_tokens: Optional[int],
    cache_read_tokens: Optional[int],
    output_tokens: Optional[int],
    pricing: AnthropicPricing,
) -> float:
    """Anthropic 使用量 → USD コスト（純粋関数）。pricing.ts costAnthropicUsd と一致。"""
    base = _sanitize_tokens(base_input_tokens)
    cache_write = _sanitize_tokens(cache_creation_tokens)
    cache_read = _sanitize_tokens(cache_read_tokens)
    output = _sanitize_tokens(output_tokens)
    return (
        base * pricing["base_input_per_mtok"]
        + cache_write * pricing["cache_write_per_mtok"]
        + cache_read * pricing["cache_read_per_mtok"]
        + output * pricing["output_per_mtok"]
    ) / TOKENS_PER_MTOK


def cost_openai_usd(
    input_tokens: Optional[int],
    output_tokens: Optional[int],
    pricing: OpenAIPricing,
) -> float:
    """OpenAI 使用量 → USD コスト（純粋関数）。pricing.ts costOpenAiUsd と一致。"""
    inp = _sanitize_tokens(input_tokens)
    out = _sanitize_tokens(output_tokens)
    return (
        inp * pricing["input_per_mtok"] + out * pricing["output_per_mtok"]
    ) / TOKENS_PER_MTOK


def usd_to_jpy(usd: float, rate: Optional[float] = None) -> float:
    """USD → JPY 換算（純粋関数）。rate 未指定なら env から解決。pricing.ts usdToJpy と一致。"""
    if rate is None:
        rate = resolve_usd_to_jpy()
    return usd * rate
