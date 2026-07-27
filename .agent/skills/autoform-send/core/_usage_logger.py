"""Sprint 6 Task 1 — Local ai_usage_logs writer.

Mirrors Web 版 Supabase `ai_usage_logs` table (per-call token usage + JPY
cost) into the local SQLite DB. Used by:
    - LocalGeneralFormProvider (form-reasoning gpt-4o-mini calls)
    - LocalBrowserUseProvider via HybridProvider (Claude Sonnet AI fallback)

Schema columns mirror Web 版 1:1 so Phase 3 統合時の同期コストが最小化される。

NOTE: Sync with src/lib/billing/ai-usage-logger.ts (Web 版での記録ロジック)
and src/lib/ai/pricing.ts (single-source-of-truth for unit prices).
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Optional

try:
    from skill.core._cost_pricing import (
        CLAUDE_HAIKU_MODEL,
        CLAUDE_SONNET_MODEL,
        GPT_4O_MINI_MODEL,
        GPT_4O_MINI_PRICING,
        cost_anthropic_usd,
        cost_openai_usd,
        resolve_anthropic_pricing,
        usd_to_jpy,
    )
    from skill.core._local_db import get_connection
except ImportError:  # flat sys.path (run_send.py)
    from _cost_pricing import (  # type: ignore
        CLAUDE_HAIKU_MODEL,
        CLAUDE_SONNET_MODEL,
        GPT_4O_MINI_MODEL,
        GPT_4O_MINI_PRICING,
        cost_anthropic_usd,
        cost_openai_usd,
        resolve_anthropic_pricing,
        usd_to_jpy,
    )
    from _local_db import get_connection  # type: ignore


def _now_iso() -> str:
    return datetime.now().isoformat()


def _compute_cost_usd(
    model: Optional[str],
    *,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int,
    cache_creation_tokens: int,
) -> float:
    """Compute USD cost for a known model. Returns 0.0 for unknown models."""
    if model in (CLAUDE_SONNET_MODEL, CLAUDE_HAIKU_MODEL):
        pricing = resolve_anthropic_pricing(model)
        if pricing is None:
            return 0.0
        return cost_anthropic_usd(
            input_tokens,
            cache_creation_tokens,
            cache_read_tokens,
            output_tokens,
            pricing,
        )
    if model == GPT_4O_MINI_MODEL:
        return cost_openai_usd(input_tokens, output_tokens, GPT_4O_MINI_PRICING)
    return 0.0


def log_usage(
    *,
    company_name: Optional[str],
    provider_used: str,
    model: Optional[str],
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
    cost_usd: Optional[float] = None,
    cost_jpy: Optional[float] = None,
    ended_at: Optional[str] = None,
) -> Optional[int]:
    """Insert one row into the local ai_usage_logs table.

    Returns the SQLite row id, or None if the env opted out (`COST_TRACKING_ENABLED=false`).

    Fail Safe: any SQLite error is swallowed (the actual send already
    succeeded — we don't want a logging bug to fail the company).
    """
    import os

    if os.environ.get("COST_TRACKING_ENABLED", "true").strip().lower() == "false":
        return None

    if cost_usd is None:
        cost_usd = _compute_cost_usd(
            model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_creation_tokens=cache_creation_tokens,
        )
    if cost_jpy is None:
        cost_jpy = usd_to_jpy(cost_usd)

    if ended_at is None:
        ended_at = _now_iso()

    try:
        conn = get_connection()
        cur = conn.execute(
            """
            INSERT INTO ai_usage_logs (
                company_name, provider_used, model,
                input_tokens, output_tokens,
                cache_read_tokens, cache_creation_tokens,
                cost_usd, cost_jpy, ended_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                company_name,
                provider_used,
                model,
                int(input_tokens or 0),
                int(output_tokens or 0),
                int(cache_read_tokens or 0),
                int(cache_creation_tokens or 0),
                float(cost_usd),
                float(cost_jpy),
                ended_at,
            ),
        )
        return cur.lastrowid
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_usage_logger] log_usage failed (continuing): "
            f"{type(e).__name__}: {e}\n"
        )
        return None


def aggregate_by_provider(*, since: Optional[str] = None) -> list[dict]:
    """Aggregate ai_usage_logs by (provider_used, model).

    Used by `skill/scripts/local_cost_report.py`.
    """
    conn = get_connection()
    if since:
        cur = conn.execute(
            """
            SELECT
                COALESCE(provider_used, 'none') AS provider_used,
                COALESCE(model, 'unknown') AS model,
                COUNT(*) AS call_count,
                SUM(input_tokens) AS sum_input,
                SUM(output_tokens) AS sum_output,
                SUM(cache_read_tokens) AS sum_cache_read,
                SUM(cache_creation_tokens) AS sum_cache_create,
                SUM(cost_usd) AS sum_usd,
                SUM(cost_jpy) AS sum_jpy
            FROM ai_usage_logs
            WHERE ended_at >= ?
            GROUP BY provider_used, model
            ORDER BY sum_jpy DESC
            """,
            (since,),
        )
    else:
        cur = conn.execute(
            """
            SELECT
                COALESCE(provider_used, 'none') AS provider_used,
                COALESCE(model, 'unknown') AS model,
                COUNT(*) AS call_count,
                SUM(input_tokens) AS sum_input,
                SUM(output_tokens) AS sum_output,
                SUM(cache_read_tokens) AS sum_cache_read,
                SUM(cache_creation_tokens) AS sum_cache_create,
                SUM(cost_usd) AS sum_usd,
                SUM(cost_jpy) AS sum_jpy
            FROM ai_usage_logs
            GROUP BY provider_used, model
            ORDER BY sum_jpy DESC
            """,
        )
    return [dict(row) for row in cur.fetchall()]
