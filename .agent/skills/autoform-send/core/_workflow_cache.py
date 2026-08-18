"""Sprint 6 Task 5 — Workflow cache (form fingerprint + replay).

Mirrors Web 版 `form_workflow_cache` table for the Skill. Backed by SQLite
table `workflow_cache` initialised in `_local_db.py`.

Key features:
    - compute_form_fingerprint(page) -> 16-char hex hash (bit-equivalent to
      Web fingerprint.ts)
    - lookup_workflow(origin, fingerprint) -> stored workflow dict or None
    - replay_workflow(page, workflow, fill_data) -> {"success": bool, ...}
    - record_successful_workflow / record_workflow_failure with auto-demote
    - build_workflow_from_general_form_success() helper for Stage 1.5

NOTE: Sync with src/lib/browser/workflow-cache/{fingerprint.ts,
lookup.ts, recorder.ts, replay.ts, builder.ts, demoter.ts}.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime
from typing import Any, Optional

try:
    from skill.core._local_db import get_connection
    from skill.core._pattern_loader import (
        load_confirmation_signals,
        load_dynamic_detection,
        load_submit_buttons,
        normalize_l1,
    )
except ImportError:
    from _local_db import get_connection  # type: ignore
    from _pattern_loader import (  # type: ignore
        load_confirmation_signals,
        load_dynamic_detection,
        load_submit_buttons,
        normalize_l1,
    )


# -----------------------------------------------------------------------------
# Constants — bit-equivalent to fingerprint.ts L27
# -----------------------------------------------------------------------------
_FINGERPRINT_HEX_LENGTH = 16  # = 2^64 collision space

# Demotion threshold — after this many failures, is_active flips to 0.
# (Sync with workflow-cache/demoter.ts)
_DEMOTION_THRESHOLD = 3

# Replay confirmation polling
_REPLAY_CONFIRMATION_TIMEOUT_MS = 8_000
_REPLAY_POLL_INTERVAL_MS = 250


# -----------------------------------------------------------------------------
# Fingerprint computation
# -----------------------------------------------------------------------------
# NOTE: Sync with src/lib/browser/workflow-cache/fingerprint.ts:64-88.
# JS pseudo-code:
#   const fields = Array.from(document.querySelectorAll('form input, form textarea, form select'));
#   return fields.map(el => `${el.tagName}:${name}:${type}:${required ? '1' : '0'}`).sort().join('|');
_FINGERPRINT_JS = r"""
() => {
    const fields = Array.from(
        document.querySelectorAll('form input, form textarea, form select')
    );
    return fields
        .map(el => {
            const name = el.getAttribute('name') || '';
            const type = el.getAttribute('type') || '';
            const required = el.required ? '1' : '0';
            return el.tagName + ':' + name + ':' + type + ':' + required;
        })
        .sort()
        .join('|');
}
"""


def hash_form_structure(inputs_serialized: str) -> str:
    """SHA-256 the serialized form structure, return first 16 hex chars.

    Bit-equivalent to fingerprint.ts hashFormStructure (L40-42).
    """
    digest = hashlib.sha256(inputs_serialized.encode("utf-8")).hexdigest()
    return digest[:_FINGERPRINT_HEX_LENGTH]


async def compute_form_fingerprint(page: Any) -> Optional[str]:
    """Compute the form fingerprint for the given Playwright page.

    Returns:
        16-char hex string, or None if no form fields are present.

    Mirrors fingerprint.ts computeFormFingerprint (L64-88). Errors during
    evaluate propagate to the caller per the TS spec.
    """
    inputs_serialized = await page.evaluate(_FINGERPRINT_JS)
    if not inputs_serialized:
        return None
    return hash_form_structure(str(inputs_serialized))


# -----------------------------------------------------------------------------
# Lookup / Record (SQLite I/O)
# -----------------------------------------------------------------------------
def lookup_workflow(origin: str, fingerprint: str) -> Optional[dict]:
    """Return the stored workflow dict, or None if not cached / inactive."""
    if not origin or not fingerprint:
        return None
    try:
        conn = get_connection()
        cur = conn.execute(
            """
            SELECT workflow_json, recorded_by, success_count, failure_count, is_active
            FROM workflow_cache
            WHERE origin = ? AND form_fingerprint = ? AND is_active = 1
            """,
            (origin, fingerprint),
        )
        row = cur.fetchone()
        if row is None:
            return None
        try:
            workflow = json.loads(row["workflow_json"])
        except (TypeError, ValueError):
            return None
        if not isinstance(workflow, dict):
            return None
        workflow["__meta__"] = {
            "recorded_by": row["recorded_by"],
            "success_count": row["success_count"],
            "failure_count": row["failure_count"],
        }
        return workflow
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_workflow_cache] lookup_workflow error (treating as miss): "
            f"{type(e).__name__}: {e}\n"
        )
        return None


def record_successful_workflow(
    origin: str,
    fingerprint: str,
    workflow: dict,
    recorded_by: str,
) -> None:
    """Upsert a successful workflow into the cache.

    On conflict (same origin+fingerprint), success_count is incremented.
    """
    if not origin or not fingerprint or not workflow:
        return
    # Strip the meta tag we add on lookup (don't persist it).
    persistable = {k: v for k, v in workflow.items() if k != "__meta__"}
    payload = json.dumps(persistable, ensure_ascii=False)
    now = datetime.now().isoformat()
    try:
        conn = get_connection()
        conn.execute(
            """
            INSERT INTO workflow_cache
                (origin, form_fingerprint, workflow_json, recorded_by,
                 success_count, failure_count, is_active, last_used_at)
            VALUES (?, ?, ?, ?, 1, 0, 1, ?)
            ON CONFLICT(origin, form_fingerprint) DO UPDATE SET
                workflow_json = excluded.workflow_json,
                recorded_by = excluded.recorded_by,
                success_count = workflow_cache.success_count + 1,
                is_active = 1,
                last_used_at = excluded.last_used_at
            """,
            (origin, fingerprint, payload, recorded_by, now),
        )
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_workflow_cache] record_successful_workflow error (continuing): "
            f"{type(e).__name__}: {e}\n"
        )


def record_workflow_failure(origin: str, fingerprint: str) -> None:
    """Increment failure_count; if >= DEMOTION_THRESHOLD, deactivate."""
    if not origin or not fingerprint:
        return
    try:
        conn = get_connection()
        cur = conn.execute(
            "SELECT failure_count FROM workflow_cache "
            "WHERE origin = ? AND form_fingerprint = ?",
            (origin, fingerprint),
        )
        row = cur.fetchone()
        if row is None:
            return
        new_failure = int(row["failure_count"]) + 1
        new_active = 0 if new_failure >= _DEMOTION_THRESHOLD else 1
        conn.execute(
            "UPDATE workflow_cache SET failure_count = ?, is_active = ? "
            "WHERE origin = ? AND form_fingerprint = ?",
            (new_failure, new_active, origin, fingerprint),
        )
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_workflow_cache] record_workflow_failure error (continuing): "
            f"{type(e).__name__}: {e}\n"
        )


# -----------------------------------------------------------------------------
# Builder — convert a Stage 1.5 success run into a persistable workflow dict
# -----------------------------------------------------------------------------
def build_workflow_from_general_form_success(
    *,
    fingerprint: str,
    field_mapping: list[dict],
    submit_selector: Optional[str],
    consent_selectors: Optional[list[str]] = None,
    confirm_button_selector: Optional[str] = None,
) -> dict:
    """Construct the workflow dict that will be stored as JSON.

    field_mapping is a list of:
        {"selector": str, "semantic": str, "type": str}

    submit_selector / consent_selectors / confirm_button_selector are the
    raw CSS selectors found during the successful run.

    NOTE: Sync with workflow-cache/builder.ts.
    """
    return {
        "version": 1,
        "fingerprint": fingerprint,
        "fieldMapping": list(field_mapping or []),
        "submitSelector": submit_selector or "",
        "consentSelectors": list(consent_selectors or []),
        "confirmButtonSelector": confirm_button_selector or "",
    }


# -----------------------------------------------------------------------------
# Replay
# -----------------------------------------------------------------------------
async def replay_workflow(
    page: Any,
    workflow: dict,
    fill_data: dict,
    *,
    semantic_resolver: Any = None,
) -> dict:
    """Re-execute a previously-recorded workflow on the current page.

    Args:
        page: Playwright Page (already navigated to the form URL).
        workflow: dict produced by build_workflow_from_general_form_success.
        fill_data: sender_info + message dict.
        semantic_resolver: callable (semantic, fill_data) -> Optional[str].
            If None, we fall back to skill.core._form_filler_lite._semantic_to_value.

    Returns:
        {"success": bool, "stage": "workflow_cache",
         "reason": str, "error_category": Optional[str]}
    """
    if semantic_resolver is None:
        try:
            from skill.core._form_filler_lite import _semantic_to_value
        except ImportError:
            from _form_filler_lite import _semantic_to_value  # type: ignore
        semantic_resolver = _semantic_to_value

    field_mapping = workflow.get("fieldMapping") or []
    submit_selector = workflow.get("submitSelector") or ""
    consent_selectors = workflow.get("consentSelectors") or []
    confirm_button_selector = workflow.get("confirmButtonSelector") or ""

    # 本文欄が記録されていない workflow は、本文を入れずに送るか、本文欄を別 semantic と
    # 取り違えて記録している(実DBに4件実在)。replay しない。
    # ★この判定と直下の resolver 判定の2つで、replay は submit へ到達し得なくなる
    #   (message_body があれば resolver が None を返して中断／無ければここで中断)。
    if not any(isinstance(e, dict) and e.get("semantic") == "message_body"
               for e in field_mapping):
        return {
            "success": False,
            "stage": "workflow_cache",
            "reason": "replay_no_message_body",
            "error_category": "FIELD_MAPPING",
        }

    # 1. Fill each field via its persisted selector + value hint.
    for entry in field_mapping:
        if not isinstance(entry, dict):
            continue
        selector = entry.get("selector") or ""
        semantic = entry.get("semantic") or ""
        if not selector:
            continue
        value = semantic_resolver(semantic, fill_data) if semantic else None
        if value is None:
            # 記録元(=他社)の literal を絶対に送らない。message_body / claude_decision /
            # heuristic_default はここに落ちる。replay を中止して素の解析へ返す。
            return {
                "success": False,
                "stage": "workflow_cache",
                "reason": f"replay_unsafe_valuehint:{semantic}",
                "error_category": "FIELD_MAPPING",
            }
        try:
            await page.fill(selector, str(value), timeout=4_000)
        except BaseException as e:  # noqa: BLE001 — Fail Safe
            sys.stderr.write(
                f"[_workflow_cache] fill failed selector={selector!r}: "
                f"{type(e).__name__}: {e}\n"
            )
            return {
                "success": False,
                "stage": "workflow_cache",
                "reason": f"replay_fill_failed:{selector}",
                "error_category": "FIELD_MAPPING",
            }

    # 2. Tick any consent boxes.
    for sel in consent_selectors:
        try:
            await page.check(sel, timeout=2_000)
        except BaseException:  # noqa: BLE001 — best effort
            pass

    # 3. Click confirm/preview button if present.
    if confirm_button_selector:
        try:
            await page.click(confirm_button_selector, timeout=4_000)
        except BaseException:  # noqa: BLE001 — best effort
            pass

    # 4. Submit.
    if not submit_selector:
        return {
            "success": False,
            "stage": "workflow_cache",
            "reason": "replay_no_submit_selector",
            "error_category": "SUBMIT_STUCK",
        }
    try:
        await page.click(submit_selector, timeout=4_000)
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        return {
            "success": False,
            "stage": "workflow_cache",
            "reason": f"replay_submit_click_failed: {type(e).__name__}",
            "error_category": "SUBMIT_STUCK",
        }

    # 5. Look for success keywords in the page body.
    ok = await _wait_for_success_signals(page, _REPLAY_CONFIRMATION_TIMEOUT_MS)
    if ok:
        return {
            "success": True,
            "stage": "workflow_cache",
            "reason": "success_signal_detected",
            "error_category": None,
        }
    return {
        "success": False,
        "stage": "workflow_cache",
        "reason": "no_success_signal",
        "error_category": "SUBMIT_STUCK",
    }


# -----------------------------------------------------------------------------
# Success-signal detection (replay confirmation)
# -----------------------------------------------------------------------------
def _build_success_keyword_set() -> list[str]:
    """Build the success keyword list from confirmation-signals + dynamic-detection."""
    keywords: list[str] = []
    try:
        signals = load_confirmation_signals()
        for alias in signals.get("contentKeywords", {}).get("aliases", []):
            if alias and alias not in keywords:
                keywords.append(alias)
    except BaseException:  # noqa: BLE001 — best effort
        pass
    try:
        dyn = load_dynamic_detection()
        # successKeywords section name varies by repo version; we accept either.
        for section_name in ("successKeywords", "successContent", "contentKeywords"):
            section = dyn.get(section_name) or {}
            for alias in section.get("aliases", []):
                if alias and alias not in keywords:
                    keywords.append(alias)
    except BaseException:  # noqa: BLE001 — best effort
        pass

    # Always add hardcoded fallbacks (mirror _skill_core._SUCCESS_KEYWORDS_HARDCODED).
    for hardcoded in (
        "送信完了", "送信しました", "ありがとう", "完了しました", "受け付けました",
    ):
        if hardcoded not in keywords:
            keywords.append(hardcoded)
    return keywords


async def _wait_for_success_signals(page: Any, timeout_ms: int) -> bool:
    """Poll the page text/title/url for any success keyword.

    Returns True if any keyword is observed within timeout_ms.
    """
    keywords = _build_success_keyword_set()
    if not keywords:
        return False
    deadline = time.time() + (timeout_ms / 1000.0)
    while time.time() < deadline:
        try:
            text = await page.content()
            if any(kw in text for kw in keywords):
                return True
            url = page.url
            if isinstance(url, str) and any(
                key in url.lower() for key in ("/thanks", "/complete", "/done", "/success")
            ):
                return True
        except BaseException:  # noqa: BLE001 — page may not be ready yet
            pass
        # Sleep is sync — but we're inside async — use asyncio.sleep
        import asyncio
        await asyncio.sleep(_REPLAY_POLL_INTERVAL_MS / 1000.0)
    return False


# -----------------------------------------------------------------------------
# Utilities exposed for tests
# -----------------------------------------------------------------------------
def normalize_form_input(label: str) -> str:
    """Re-export for callers (KISS — they import from one module)."""
    return normalize_l1(label)


def has_record(origin: str, fingerprint: str) -> bool:
    """Diagnostic helper for tests."""
    if not origin or not fingerprint:
        return False
    conn = get_connection()
    cur = conn.execute(
        "SELECT 1 FROM workflow_cache WHERE origin = ? AND form_fingerprint = ?",
        (origin, fingerprint),
    )
    return cur.fetchone() is not None


def submit_button_aliases() -> list[str]:
    """Return positive submit-button keyword list (for general_form_sender)."""
    sb = load_submit_buttons()
    pos = sb.get("positive", {}).get("aliases", []) or []
    fb = sb.get("fallback", {}).get("aliases", []) or []
    return list(pos) + list(fb)
