"""Single-instance law (O5_INPUTS §C): one spine per data root.

Mechanism (builder detail, recorded and tested): an OS advisory
exclusive lock on the first byte of ``spine.lock``, held for the process
lifetime. The OS releases the lock when the holder dies — including a
crash — so stale-lock recovery needs no PID bookkeeping: a leftover file
that locks cleanly WAS stale; a file that refuses the lock is a live
instance. The file itself is never deleted (Windows cannot unlink a
locked file; an unlocked leftover is inert).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


class LockHeld(OSError):
    """Another process holds the lock (a live instance)."""


class InstanceLock:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._fd: int | None = None

    @property
    def held(self) -> bool:
        return self._fd is not None

    def acquire(self) -> None:
        if self._fd is not None:
            return
        fd = os.open(str(self.path), os.O_RDWR | os.O_CREAT)
        try:
            if sys.platform == "win32":
                import msvcrt

                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(fd)
            raise LockHeld(str(self.path)) from exc
        self._fd = fd

    def release(self) -> None:
        if self._fd is None:
            return
        fd, self._fd = self._fd, None
        try:
            if sys.platform == "win32":
                import msvcrt

                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    def __enter__(self) -> "InstanceLock":
        self.acquire()
        return self

    def __exit__(self, *exc_info) -> None:
        self.release()
