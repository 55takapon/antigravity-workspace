"""Sprint 6 Task 1 — Local SQLite connection + schema bootstrap.

Provides a single shared `sqlite3.Connection` per process, with WAL journal
mode enabled (so concurrent reads from the test harness don't deadlock
against the writer).

Schema is created via IF NOT EXISTS so calling `init_schema()` twice is a
no-op. Column names + types are kept compatible with the Web 版 Supabase
tables so Phase 3 統合時の `INSERT ... SELECT` 同期コストが最小化される。

Web 版 Supabase テーブルとのマッピング:
    label_dictionary   <-> public.label_dictionary
    workflow_cache     <-> public.form_workflow_cache (Sprint 6 では origin/
                          form_fingerprint をローカル主キーに変える点に注意)
    domain_cooldown    <-> public.domain_outcomes (consecutive_failure_count
                          のみ。スコアリング行はローカルでは不要)
    ai_usage_logs      <-> public.ai_usage_logs (per-call トークン記録)

Path resolution:
    1. AUTOFORM_LOCAL_DB_PATH env var (highest priority — explicit override)
    2. ${CLAUDE_SKILL_DIR}/data/skill_local.db — Skill standalone distribution
    3. <skill>/data/skill_local.db                — bundled in mono-repo context

NOTE: Sync schema notes with src/lib/supabase/types.ts (label_dictionary,
form_workflow_cache, domain_outcomes, ai_usage_logs).
"""

from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path
from typing import Optional

# -----------------------------------------------------------------------------
# Path resolution
# -----------------------------------------------------------------------------
_THIS_FILE = Path(__file__).resolve()
_SKILL_ROOT = _THIS_FILE.parents[1]  # skill/core/ -> skill/


def resolve_db_path() -> Path:
    """Resolve the SQLite file path; checks 3 locations in priority order."""
    override = os.environ.get("AUTOFORM_LOCAL_DB_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()

    skill_dir_env = os.environ.get("CLAUDE_SKILL_DIR", "").strip()
    if skill_dir_env:
        return Path(skill_dir_env).expanduser().resolve() / "data" / "skill_local.db"

    return _SKILL_ROOT / "data" / "skill_local.db"


# -----------------------------------------------------------------------------
# Connection management (per-process singleton)
# -----------------------------------------------------------------------------
_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None
_initialized_for_path: Optional[Path] = None


def get_connection() -> sqlite3.Connection:
    """Return the shared SQLite connection, creating + initializing if needed.

    Concurrency note: Sprint 6 sends rows sequentially (concurrency=1) so a
    single connection is fine. WAL mode is set for forward-compat with the
    future per-row async writes Phase 3 may introduce.
    """
    global _conn, _initialized_for_path
    with _lock:
        target = resolve_db_path()
        if _conn is not None and _initialized_for_path == target:
            return _conn

        # Close any stale connection (e.g. AUTOFORM_LOCAL_DB_PATH changed during tests).
        if _conn is not None:
            try:
                _conn.close()
            except sqlite3.Error:
                pass
            _conn = None

        target.parent.mkdir(parents=True, exist_ok=True)
        # `check_same_thread=False` is safe because we serialize writes via
        # the module-level lock; tests that use threading should still work.
        conn = sqlite3.connect(
            str(target),
            timeout=10.0,
            isolation_level=None,  # autocommit; we manage txn via BEGIN/COMMIT
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA synchronous=NORMAL")
        except sqlite3.Error:
            # Some sandboxed FS (network shares) can't do WAL — fall back silently.
            pass
        _init_schema_on_connection(conn)
        _conn = conn
        _initialized_for_path = target
        return conn


def init_schema() -> None:
    """Public entry point used by run_send.py at startup.

    Idempotent: safe to call multiple times. Creates the SQLite file +
    tables if they don't exist yet.
    """
    # Side effect: ensures get_connection has run init_schema_on_connection.
    get_connection()


def close_for_test() -> None:
    """Test-only helper: close + forget the shared connection.

    Useful after tests that point AUTOFORM_LOCAL_DB_PATH at a tmpdir and
    want to ensure the next test gets a fresh connection.
    """
    global _conn, _initialized_for_path
    with _lock:
        if _conn is not None:
            try:
                _conn.close()
            except sqlite3.Error:
                pass
        _conn = None
        _initialized_for_path = None


# -----------------------------------------------------------------------------
# Schema (compatible with Web 版 Supabase tables — see module docstring)
# -----------------------------------------------------------------------------
_SCHEMA_LABEL_DICTIONARY = """
CREATE TABLE IF NOT EXISTS label_dictionary (
    label_text TEXT NOT NULL,
    semantic TEXT NOT NULL,
    origin TEXT NOT NULL,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    is_approved INTEGER NOT NULL DEFAULT 0,
    last_used_at TEXT,
    PRIMARY KEY (label_text, semantic)
)
"""

_SCHEMA_WORKFLOW_CACHE = """
CREATE TABLE IF NOT EXISTS workflow_cache (
    origin TEXT NOT NULL,
    form_fingerprint TEXT NOT NULL,
    workflow_json TEXT NOT NULL,
    recorded_by TEXT NOT NULL,
    success_count INTEGER NOT NULL DEFAULT 1,
    failure_count INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    last_used_at TEXT,
    PRIMARY KEY (origin, form_fingerprint)
)
"""

_SCHEMA_DOMAIN_COOLDOWN = """
CREATE TABLE IF NOT EXISTS domain_cooldown (
    origin TEXT PRIMARY KEY,
    consecutive_failure_count INTEGER NOT NULL DEFAULT 0,
    cooldown_until TEXT
)
"""

_SCHEMA_AI_USAGE_LOGS = """
CREATE TABLE IF NOT EXISTS ai_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT,
    provider_used TEXT,
    model TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cache_read_tokens INTEGER,
    cache_creation_tokens INTEGER,
    cost_usd REAL,
    cost_jpy REAL,
    ended_at TEXT
)
"""

# Index for common Lookups
_INDEX_LABEL_LOOKUP = (
    "CREATE INDEX IF NOT EXISTS idx_label_dictionary_approved "
    "ON label_dictionary(is_approved, label_text)"
)
_INDEX_AI_USAGE_TS = (
    "CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_ended_at "
    "ON ai_usage_logs(ended_at)"
)


def _init_schema_on_connection(conn: sqlite3.Connection) -> None:
    """Create tables + indexes if absent (idempotent)."""
    statements = (
        _SCHEMA_LABEL_DICTIONARY,
        _SCHEMA_WORKFLOW_CACHE,
        _SCHEMA_DOMAIN_COOLDOWN,
        _SCHEMA_AI_USAGE_LOGS,
        _INDEX_LABEL_LOOKUP,
        _INDEX_AI_USAGE_TS,
    )
    for stmt in statements:
        conn.execute(stmt)


# -----------------------------------------------------------------------------
# Module self-check
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"[_local_db] DB path: {resolve_db_path()}")
    conn = get_connection()
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    print("[_local_db] tables:", [row[0] for row in cur])
