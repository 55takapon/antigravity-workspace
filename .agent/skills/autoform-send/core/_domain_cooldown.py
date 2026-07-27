"""Sprint 6 Task 1 — Domain cooldown manager (consecutive failure tracker).

Mirrors the Web 版 `domain_outcomes` table's `consecutive_failure_count`
column. Avoids hammering a host that has failed 3+ times in a row.

Thresholds (matching Web 版 engine.ts L1142 と同期):
    3 consecutive failures -> 24 h cooldown
    5 consecutive failures -> 72 h cooldown (more aggressive backoff)

NOTE: Sync with src/lib/browser/engine.ts L1100-1150 domain_outcomes
update logic. The Web 版 also tracks success rate / total volume for
scoring; Sprint 6 keeps only the cooldown column to stay minimal.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlparse

try:
    from skill.core._local_db import get_connection
except ImportError:
    from _local_db import get_connection  # type: ignore

# -----------------------------------------------------------------------------
# Tunables (kept as module constants; env-var override is Phase 2-C, KISS)
# -----------------------------------------------------------------------------
_COOLDOWN_24H_THRESHOLD = 3
_COOLDOWN_72H_THRESHOLD = 5
_COOLDOWN_24H = timedelta(hours=24)
_COOLDOWN_72H = timedelta(hours=72)


# -----------------------------------------------------------------------------
# Origin extraction
# -----------------------------------------------------------------------------
def origin_for_url(url: str) -> Optional[str]:
    """Return the canonical origin (host without leading 'www.').

    None if the URL is unparseable. Lowercase + strip default ports.
    """
    if not url:
        return None
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if not host:
            return None
        if host.startswith("www."):
            host = host[4:]
        return host
    except BaseException:  # noqa: BLE001 — defensive
        return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------
def is_cooldown(origin: str) -> bool:
    """Return True if `origin` is currently in cooldown."""
    if not origin:
        return False
    conn = get_connection()
    cur = conn.execute(
        "SELECT cooldown_until FROM domain_cooldown WHERE origin = ?",
        (origin,),
    )
    row = cur.fetchone()
    if row is None:
        return False
    until = _parse_iso(row["cooldown_until"])
    if until is None:
        return False
    return until > datetime.now(timezone.utc)


def record_failure(origin: str) -> tuple[int, Optional[str]]:
    """Record a failure for `origin`, possibly activating cooldown.

    Returns (new_consecutive_failure_count, cooldown_until_iso or None).
    """
    if not origin:
        return 0, None
    conn = get_connection()
    cur = conn.execute(
        "SELECT consecutive_failure_count FROM domain_cooldown WHERE origin = ?",
        (origin,),
    )
    row = cur.fetchone()
    current = int(row["consecutive_failure_count"]) if row else 0
    new_count = current + 1

    cooldown_until: Optional[str] = None
    if new_count >= _COOLDOWN_72H_THRESHOLD:
        cooldown_until = (datetime.now(timezone.utc) + _COOLDOWN_72H).isoformat()
    elif new_count >= _COOLDOWN_24H_THRESHOLD:
        cooldown_until = (datetime.now(timezone.utc) + _COOLDOWN_24H).isoformat()

    conn.execute(
        """
        INSERT INTO domain_cooldown (origin, consecutive_failure_count, cooldown_until)
        VALUES (?, ?, ?)
        ON CONFLICT(origin) DO UPDATE SET
            consecutive_failure_count = excluded.consecutive_failure_count,
            cooldown_until = excluded.cooldown_until
        """,
        (origin, new_count, cooldown_until),
    )
    return new_count, cooldown_until


def record_success(origin: str) -> None:
    """Reset the failure counter for `origin` and clear cooldown."""
    if not origin:
        return
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO domain_cooldown (origin, consecutive_failure_count, cooldown_until)
        VALUES (?, 0, NULL)
        ON CONFLICT(origin) DO UPDATE SET
            consecutive_failure_count = 0,
            cooldown_until = NULL
        """,
        (origin,),
    )


def get_state(origin: str) -> Optional[dict]:
    """Return the raw row for `origin` (or None) — diagnostic helper."""
    if not origin:
        return None
    conn = get_connection()
    cur = conn.execute(
        "SELECT origin, consecutive_failure_count, cooldown_until "
        "FROM domain_cooldown WHERE origin = ?",
        (origin,),
    )
    row = cur.fetchone()
    if row is None:
        return None
    return {
        "origin": row["origin"],
        "consecutive_failure_count": row["consecutive_failure_count"],
        "cooldown_until": row["cooldown_until"],
    }
