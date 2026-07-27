"""Sprint 6 Task 4 — Local SQLite-backed learned label dictionary.

Mirrors Web 版 `label_dictionary` table for the Skill. Backed by SQLite
table `label_dictionary` initialised in `_local_db.py`.

Lifecycle:
    1. At Stage 1.5 entry, `load_learned_dictionary()` populates an in-memory
       cache (TTL 1h). Only `is_approved=1` rows are loaded.
    2. While filling fields, `match_learned_label(raw_label)` checks the
       cache for a normalized substring match.
    3. After a successful send, `accumulate_on_success([{...}, ...])`
       upserts (label_text, semantic) rows with origin="ai_resolved" or
       origin="learned". `success_count` is incremented; reaching the
       approval threshold flips `is_approved=1`.
    4. After a failed send (when we suspect a mis-mapping), the caller may
       invoke `record_label_failure(label, semantic)` to bump the failure
       counter; reaching the demotion threshold flips `is_approved=0`.

Thresholds (match Web 版 dictionary-updater.ts):
    APPROVAL_THRESHOLD = 3   (success_count >= 3 -> is_approved=1)
    DEMOTION_THRESHOLD = 5   (failure_count >= 5 -> is_approved=0)

NOTE: Sync with src/lib/browser/learning/dictionary-loader.ts +
dictionary-updater.ts.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from typing import Optional

try:
    from skill.core._local_db import get_connection
    from skill.core._pattern_loader import normalize_l1
except ImportError:
    from _local_db import get_connection  # type: ignore
    from _pattern_loader import normalize_l1  # type: ignore


# -----------------------------------------------------------------------------
# Tunables (Sync with Web 版 dictionary-updater.ts)
# -----------------------------------------------------------------------------
APPROVAL_THRESHOLD = 3
DEMOTION_THRESHOLD = 5
TTL_SECONDS = 3600  # 1h memoization, matches Web ensureLearnedDictionaryLoaded


# -----------------------------------------------------------------------------
# In-memory cache (TTL 1h)
# -----------------------------------------------------------------------------
# {label_text_normalized: semantic}
_cache: dict[str, str] = {}
_cache_loaded_at: float = 0.0


def _now_iso() -> str:
    return datetime.now().isoformat()


def _is_cache_fresh() -> bool:
    return _cache_loaded_at > 0 and (time.time() - _cache_loaded_at) < TTL_SECONDS


def load_learned_dictionary(force: bool = False) -> dict[str, str]:
    """Load all approved learned labels into a normalize_l1 → semantic map.

    Args:
        force: if True, bypass the TTL cache and re-read SQLite.

    Returns:
        The cache mapping (also stored at module level for match_learned_label).
    """
    global _cache, _cache_loaded_at
    if not force and _is_cache_fresh():
        return _cache

    try:
        conn = get_connection()
        cur = conn.execute(
            """
            SELECT label_text, semantic
            FROM label_dictionary
            WHERE is_approved = 1
            """,
        )
        new_cache: dict[str, str] = {}
        for row in cur.fetchall():
            label = row["label_text"]
            semantic = row["semantic"]
            if not label or not semantic:
                continue
            new_cache[normalize_l1(label)] = semantic
        _cache = new_cache
        _cache_loaded_at = time.time()
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_learning_dictionary] load failed (continuing with empty cache): "
            f"{type(e).__name__}: {e}\n"
        )
        _cache = {}
        _cache_loaded_at = time.time()
    return _cache


def match_learned_label(raw_label: str) -> Optional[str]:
    """Look up a raw label against the in-memory learned dictionary.

    Substring contain-match (the learned label may be a fragment of the
    actual page label, e.g. learned "お問合せ内容" should match "お問合せ内容（必須）").

    Returns the semantic string, or None.
    """
    if not raw_label:
        return None
    cache = load_learned_dictionary()
    if not cache:
        return None
    normalized = normalize_l1(raw_label)
    if not normalized:
        return None
    # Exact match (fast path)
    semantic = cache.get(normalized)
    if semantic:
        return semantic
    # Contain match (slower)
    for learned_label, sem in cache.items():
        if learned_label and learned_label in normalized:
            return sem
    return None


# -----------------------------------------------------------------------------
# Accumulators (write path)
# -----------------------------------------------------------------------------
def accumulate_on_success(field_entries: list[dict]) -> int:
    """Upsert successful field mappings.

    Each entry: {"normalized_label": str, "semantic": str, "origin": str}
    Only `origin in ("learned", "ai_resolved")` rows are recorded; static
    dictionary hits are skipped (they're already in the read-only JSON).

    Returns the number of rows touched.
    """
    if not field_entries:
        return 0
    touched = 0
    now = _now_iso()
    try:
        conn = get_connection()
        for entry in field_entries:
            label = (entry.get("normalized_label") or "").strip()
            semantic = (entry.get("semantic") or "").strip()
            origin = (entry.get("origin") or "").strip()
            if not label or not semantic:
                continue
            if origin not in ("learned", "ai_resolved"):
                continue

            cur = conn.execute(
                "SELECT success_count, failure_count, is_approved FROM label_dictionary "
                "WHERE label_text = ? AND semantic = ?",
                (label, semantic),
            )
            row = cur.fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO label_dictionary
                        (label_text, semantic, origin, success_count, failure_count,
                         is_approved, last_used_at)
                    VALUES (?, ?, ?, 1, 0, ?, ?)
                    """,
                    (
                        label,
                        semantic,
                        origin,
                        1 if APPROVAL_THRESHOLD <= 1 else 0,
                        now,
                    ),
                )
            else:
                new_success = int(row["success_count"]) + 1
                new_approved = 1 if new_success >= APPROVAL_THRESHOLD else int(
                    row["is_approved"]
                )
                conn.execute(
                    """
                    UPDATE label_dictionary
                       SET success_count = ?,
                           is_approved = ?,
                           last_used_at = ?
                     WHERE label_text = ? AND semantic = ?
                    """,
                    (new_success, new_approved, now, label, semantic),
                )
            touched += 1
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_learning_dictionary] accumulate_on_success error (continuing): "
            f"{type(e).__name__}: {e}\n"
        )

    if touched > 0:
        # Invalidate cache so next match_learned_label sees the new rows.
        _invalidate_cache()
    return touched


def record_label_failure(
    raw_label: str,
    inferred_semantic: Optional[str],
) -> None:
    """Increment failure_count for an existing (label, semantic) row.

    If the row reaches DEMOTION_THRESHOLD failures, it's demoted out of
    the approved set (`is_approved=0`).

    NOTE: We deliberately do NOT insert a new row for unseen labels
    (Sprint 6 KISS — label_failures table is Phase 2-C). If the row
    doesn't exist, this is a no-op.
    """
    if not raw_label or not inferred_semantic:
        return
    label = normalize_l1(raw_label)
    if not label:
        return
    try:
        conn = get_connection()
        cur = conn.execute(
            "SELECT failure_count FROM label_dictionary WHERE label_text = ? AND semantic = ?",
            (label, inferred_semantic),
        )
        row = cur.fetchone()
        if row is None:
            return
        new_failure = int(row["failure_count"]) + 1
        new_approved = 0 if new_failure >= DEMOTION_THRESHOLD else None
        if new_approved is None:
            conn.execute(
                "UPDATE label_dictionary SET failure_count = ? "
                "WHERE label_text = ? AND semantic = ?",
                (new_failure, label, inferred_semantic),
            )
        else:
            conn.execute(
                "UPDATE label_dictionary SET failure_count = ?, is_approved = ? "
                "WHERE label_text = ? AND semantic = ?",
                (new_failure, new_approved, label, inferred_semantic),
            )
            _invalidate_cache()
    except BaseException as e:  # noqa: BLE001 — Fail Safe
        sys.stderr.write(
            f"[_learning_dictionary] record_label_failure error (continuing): "
            f"{type(e).__name__}: {e}\n"
        )


def _invalidate_cache() -> None:
    global _cache_loaded_at
    _cache_loaded_at = 0.0


# -----------------------------------------------------------------------------
# Test helpers
# -----------------------------------------------------------------------------
def _reset_cache_for_test() -> None:
    """Test-only helper to drop the in-memory cache."""
    global _cache, _cache_loaded_at
    _cache = {}
    _cache_loaded_at = 0.0
