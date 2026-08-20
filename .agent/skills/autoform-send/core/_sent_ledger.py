"""送信済み台帳 — 「この会社にはもう送った」をシートとは独立に持つ（#55 F2）。

なぜ必要か:
    送信済みの真実がスプレッドシートにしか無かった。書き戻す前に落ちると
    「送信は飛んでいるのにシートは空欄」になり、空欄を見た再開で二重送信になる
    （実運用で80社）。チャンク分割（F4）で空欄の最大件数は減るが、ゼロにはならない。
    そこで、送信の直前に**手元の台帳へ問い合わせて**、送信済みなら送らない。

設計の要点:
    - **completed だけを記録・ブロックする**。失敗記録まで一律ブロックすると「送るべき
      相手に永久に送れない」行が静かに積もる（#52 で実際に踏んだ型）。届いたかもしれない
      失敗社は #56 の「要目視」で人が判断する担当であって、ここで機械的に殺さない。
    - **キーの正規化は shared/exclude_filter に合わせる**。#53 で NFKC 由来の
      ValueError を踏んでいるので、正規化を新規実装しない。
    - **読めないときは例外を投げる**（LedgerUnavailable）。呼び出し側が送信を止める。
      ここで「読めないから送ってしまえ」にすると台帳の意味が無い（fail-closed）。
      なお「テーブルが空」は正常＝初回。無いことと壊れていることを区別する。
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    from skill.core._local_db import get_connection
except ImportError:
    from _local_db import get_connection  # type: ignore

# 正規化は除外リスト（#40/#53）と同じ実装を使う。
# このファイルは <repo>/.claude/skills/005-form-send/core/_sent_ledger.py。
# ディレクトリ（core）から数えて parents[3] が <repo>（run_on_sheet.py の REPO_ROOT と同じ数え方）。
_SHARED = Path(__file__).resolve().parent.parents[3] / "shared"
if str(_SHARED) not in sys.path:
    sys.path.insert(0, str(_SHARED))
try:
    from exclude_filter import norm_company, norm_domain  # type: ignore
except ImportError:  # 配布の取りこぼし等。台帳を黙って無効化しないため呼び出し側へ伝える
    norm_company = norm_domain = None  # type: ignore


class LedgerUnavailable(RuntimeError):
    """台帳を読み書きできない。呼び出し側は**送信を止める**こと（fail-closed）。"""


def _require_normalizers() -> None:
    if norm_company is None or norm_domain is None:
        raise LedgerUnavailable(
            "shared/exclude_filter.py を読み込めません（送信済みの照合ができません）"
        )


def make_key(company_name: str, url: str) -> tuple[str, str]:
    """台帳のキー（正規化済みの社名, 正規化済みドメイン）を作る。

    社名とドメインの**両方**をキーにする。社名だけだと同名の別会社を巻き込み、
    ドメインだけだと1ドメインに複数社が同居するケース（グループ会社の共有サイト等）で
    送るべき相手を止めてしまう。
    """
    _require_normalizers()
    return norm_company(company_name or ""), norm_domain(url or "")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _conn():
    try:
        return get_connection()
    except BaseException as e:  # noqa: BLE001
        raise LedgerUnavailable(f"{type(e).__name__}: {e}") from e


def probe() -> None:
    """送信を始める前に、台帳が読める状態かを確かめる（読めなければ例外）。

    1社目を送ってから気づくのでは遅い（送ってしまってから記録できないと分かる）ので、
    ループに入る前に1回だけ叩く。
    """
    _require_normalizers()
    try:
        _conn().execute("SELECT 1 FROM sent_ledger LIMIT 1").fetchone()
    except LedgerUnavailable:
        raise
    except BaseException as e:  # noqa: BLE001
        raise LedgerUnavailable(f"{type(e).__name__}: {e}") from e


def find_sent(company_name: str, url: str) -> Optional[dict]:
    """送信済みなら台帳のレコードを返す。未送信なら None。読めなければ例外。"""
    ck, uk = make_key(company_name, url)
    if not ck and not uk:
        return None                     # 照合材料が無い＝止められない（送信側の検証に任せる）
    try:
        cur = _conn().execute(
            "SELECT company_name, url, sent_at, status, provider_used, run_id, evidence "
            "FROM sent_ledger WHERE company_key = ? AND url_key = ?",
            (ck, uk),
        )
        row = cur.fetchone()
    except BaseException as e:  # noqa: BLE001
        raise LedgerUnavailable(f"{type(e).__name__}: {e}") from e
    if row is None:
        return None
    cols = ("company_name", "url", "sent_at", "status", "provider_used", "run_id", "evidence")
    return dict(zip(cols, row))


def record_sent(company_name: str, url: str, *, sent_at: str, status: str,
                provider_used: str = "", run_id: str = "", evidence: str = "") -> bool:
    """送信できた1社を台帳へ書く。書けたら True。

    記録できないことは「次のランで二重送信しうる」を意味するので、
    呼び出し側は False を握り潰さずに扱うこと。
    """
    if status != "completed":
        return False                    # ★completed だけを台帳に載せる（設計の要点を参照）
    try:
        ck, uk = make_key(company_name, url)
    except LedgerUnavailable:
        return False
    if not ck and not uk:
        return False
    try:
        conn = _conn()
        conn.execute(
            "INSERT OR REPLACE INTO sent_ledger "
            "(company_key, url_key, company_name, url, sent_at, status, provider_used, "
            " run_id, evidence) VALUES (?,?,?,?,?,?,?,?,?)",
            (ck, uk, company_name, url, sent_at or _now_iso(), status,
             provider_used, run_id, evidence[:500]),
        )
        conn.commit()
        return True
    except BaseException:  # noqa: BLE001
        return False
