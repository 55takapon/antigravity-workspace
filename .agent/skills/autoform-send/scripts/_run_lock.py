"""多重起動ガード（クロスプラットフォームの単一ランロック）。

同一の送信対象（入力CSV / スプレッドシート）に対する run_send.py・run_on_sheet.py の
二重起動を物理的にブロックする。長時間ランを待ちきれたエージェントや人が同じコマンドを
再実行して 2 プロセス並走 → 二重送信・ブラウザ暴走に至る事故を防ぐ。

方式:
- OS のアドバイザリ/領域ロックで相互排他する（Unix=fcntl.flock / Windows=msvcrt.locking）。
  プロセス死亡（クラッシュ・kill 含む）で OS が自動解放するため、stale PID 判定は不要。
- ロック取得後にメタ情報（pid / 開始時刻 / コマンド）を <lock>.info へ平文で書き、取得に
  失敗した側はそれを読んで「誰が実行中か」を人間可読で表示する。
- どちらの OS ロックも使えない環境では best-effort で通す（ロック無し＝従来動作）。

使い方:
    from _run_lock import SingleRunLock, LockBusyError
    lock = SingleRunLock("form-send", key)   # key=入力CSVの絶対パス等
    try:
        lock.acquire()
    except LockBusyError as e:
        print(e.message, file=sys.stderr); return 3
    try:
        ...送信処理...
    finally:
        lock.release()

環境変数 AUTOFORM_NO_LOCK=1 でガードを無効化できる（意図的な並行実行用・非推奨）。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

try:
    import fcntl  # Unix
    _HAVE_FCNTL = True
except ImportError:  # pragma: no cover - Windows
    _HAVE_FCNTL = False

try:
    import msvcrt  # Windows
    _HAVE_MSVCRT = True
except ImportError:  # pragma: no cover - Unix
    _HAVE_MSVCRT = False


class LockBusyError(Exception):
    """別プロセスが同じ対象のロックを保持しているときに送出。"""

    def __init__(self, message: str, holder: Optional[dict]):
        super().__init__(message)
        self.message = message
        self.holder = holder


def _lock_dir() -> Path:
    d = Path(tempfile.gettempdir()) / "simesapo-sales-locks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _lock_paths(namespace: str, key: str) -> tuple[Path, Path]:
    h = hashlib.sha1(f"{namespace}\x00{key}".encode("utf-8")).hexdigest()[:16]
    base = _lock_dir() / f"{namespace}-{h}"
    return Path(str(base) + ".lock"), Path(str(base) + ".lock.info")


class SingleRunLock:
    """送信対象ごとの単一ランロック。context manager としても使える。"""

    def __init__(self, namespace: str, key: str):
        self.namespace = namespace
        self.key = key
        self.lock_path, self.info_path = _lock_paths(namespace, key)
        self._fh = None
        self._disabled = os.environ.get("AUTOFORM_NO_LOCK", "").strip() == "1"

    # --- context manager ------------------------------------------------------
    def __enter__(self) -> "SingleRunLock":
        self.acquire()
        return self

    def __exit__(self, *exc) -> bool:
        self.release()
        return False

    # --- core -----------------------------------------------------------------
    def acquire(self) -> None:
        if self._disabled:
            return
        fh = open(self.lock_path, "a+")
        if not self._try_lock(fh):
            holder = self._read_info()
            fh.close()
            raise LockBusyError(self._busy_message(holder), holder)
        self._fh = fh
        self._write_info()

    def release(self) -> None:
        if self._fh is None:
            return
        try:
            if _HAVE_FCNTL:
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
            elif _HAVE_MSVCRT:
                self._fh.seek(0)
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        try:
            self._fh.close()
        finally:
            self._fh = None
        # ファイルは掃除する（残っても OS ロックは解放済みなので害はないが、綺麗に保つ）。
        for p in (self.info_path, self.lock_path):
            try:
                os.unlink(p)
            except OSError:
                pass

    # --- helpers --------------------------------------------------------------
    @staticmethod
    def _try_lock(fh) -> bool:
        try:
            if _HAVE_FCNTL:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            elif _HAVE_MSVCRT:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:  # ロック機構が無い環境は best-effort で通す
                return True
            return True
        except OSError:
            return False

    def _write_info(self) -> None:
        info = {
            "pid": os.getpid(),
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "cmd": " ".join(sys.argv),
            "key": self.key,
        }
        try:
            with open(self.info_path, "w", encoding="utf-8") as f:
                json.dump(info, f, ensure_ascii=False)
        except OSError:
            pass

    def _read_info(self) -> Optional[dict]:
        try:
            with open(self.info_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    @staticmethod
    def _busy_message(holder: Optional[dict]) -> str:
        lines = [
            "[エラー] 同じ送信対象に対する送信プロセスが既に実行中です。"
            "二重起動を防ぐため、この実行を中止しました。",
        ]
        if holder:
            lines.append(
                f"        実行中: PID {holder.get('pid', '?')} / "
                f"開始 {holder.get('started_at', '?')}"
            )
            cmd = holder.get("cmd")
            if cmd:
                lines.append(f"        コマンド: {cmd}")
        lines.append(
            "        → 実行中のプロセスの完了を待ってください"
            "（結果は完了時に出力CSV/シートへ反映されます。同じコマンドの再実行は不要です）。"
        )
        lines.append(
            "        本当に別ランを並行させたい場合のみ AUTOFORM_NO_LOCK=1 を設定（非推奨）。"
        )
        return "\n".join(lines)
