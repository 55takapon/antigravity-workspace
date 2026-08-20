"""ドメインごとの連続失敗カウンタ（★待機＝cooldown は 2026-08-19 に撤去）。

元は Web 版 `domain_outcomes` からの移植で、「3回連続失敗 → 24時間・5回 → 72時間、
そのドメインへは送らない」という待機を持っていた。**待機だけを外し、カウンタは残す。**

なぜ外すか:
  - 同じ会社を叩き続けない歯止めは、今はシートの status（失敗も書き戻される＝候補から
    外れる）と送信済み台帳 `_sent_ledger`（#55 F2）が担う。待機はその代役だった。
  - 代役のままだと副作用のほうが大きい。待機で見送った行は status を書かず空のまま残す
    ため（#52 の修正）、次のランでも先頭から `--limit` 件の枠を食い続ける＝定期実行で
    新しい会社へ届く件数が静かに減る。100社送るつもりが 0 件で終わりうる。
  - ★時間窓を外して「N回失敗したら以後スキップ」だけ残すのは**永久除外**であり、
    #52（一度も送っていない16社が二度と送られない）の再来なので採らない。
  - 待機が置かれていたのは Python 経路（Stage 0/1/1.5＝AI不使用・¥0）で、トークンを
    使う Tier B はこのゲートを通らない＝待機はトークン節約に効いていなかった。

残すもの: `consecutive_failure_count`（どのドメインが繰り返し失敗しているかを後から
数えるための材料）。連打の抑制は run_send.py の社間ランダム待機（2〜5秒）が担う。
`cooldown_until` 列はスキーマ互換のため残すが、常に NULL を書く（読む側はもう無い）。
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse

try:
    from skill.core._local_db import get_connection
except ImportError:
    from _local_db import get_connection  # type: ignore


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


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------
def record_failure(origin: str) -> tuple[int, Optional[str]]:
    """`origin` の連続失敗を1つ数える。**送信は止めない**（待機は撤去済み）。

    戻り値は (new_consecutive_failure_count, None)。第2要素は旧 cooldown_until の
    名残で、常に None＝「この失敗で待機に入った会社は無い」。呼び出し側が真偽で
    分岐しても待機が復活しないよう、値ではなく型として固定しておく。
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

    conn.execute(
        """
        INSERT INTO domain_cooldown (origin, consecutive_failure_count, cooldown_until)
        VALUES (?, ?, NULL)
        ON CONFLICT(origin) DO UPDATE SET
            consecutive_failure_count = excluded.consecutive_failure_count,
            cooldown_until = NULL
        """,
        (origin, new_count),
    )
    return new_count, None


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
