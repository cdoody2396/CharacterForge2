"""Process lifecycle (O5_INPUTS §C): loopback bind, random free port,
instance lock, discovery, uvicorn.

The spine binds its own socket to ``127.0.0.1:0`` — never ``0.0.0.0`` —
reads the real port synchronously, writes the discovery file, and only
then hands the already-listening socket to uvicorn. A client that reads
discovery and connects is queued by the OS until uvicorn accepts: no
window where discovery names a port nobody owns.

Shutdown: a graceful stop fires the app lifespan (the ``spine_stop``
audit line), then the discovery file is removed and the instance lock
released. A hard kill does neither — the OS drops the lock (stale
recovery is the next start's acquire) and the next start overwrites the
stale discovery file. The lock, not the discovery file, is the
authority on "is one running".
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import socket

import uvicorn

from app.spine.bootstrap import SpineContext, build_context
from app.spine.discovery import HOST, remove_discovery, write_discovery
from app.spine.errors import AlreadyRunningRefusal, StartupRefusal
from app.spine.instance_lock import InstanceLock, LockHeld
from app.spine.service import build_app


class SpineServer:
    """One bound loopback socket + one uvicorn server over ``build_app``."""

    def __init__(self, ctx: SpineContext):
        self.ctx = ctx
        self.app = build_app(ctx)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind((HOST, 0))
        self._sock.listen(128)
        self.port = self._sock.getsockname()[1]
        self._server = uvicorn.Server(
            uvicorn.Config(
                self.app, log_level="warning", access_log=False, lifespan="on"
            )
        )

    @property
    def started(self) -> bool:
        return self._server.started

    def bound_address(self) -> tuple[str, int]:
        return self._sock.getsockname()[:2]

    def serve(self) -> None:
        """Blocking; returns after a graceful stop."""
        write_discovery(
            self.ctx.paths.discovery_path,
            port=self.port,
            token=self.ctx.token,
            pid=os.getpid(),
            version=self.ctx.version,
        )
        try:
            self._server.run(sockets=[self._sock])
        finally:
            remove_discovery(self.ctx.paths.discovery_path)

    def stop(self) -> None:
        self._server.should_exit = True


def run(data_root: Path | str) -> int:
    """The full startup story (§C): validate everything, take the
    instance lock, serve. Every refusal is printed with its errors
    named and exits non-zero."""
    try:
        ctx = build_context(data_root)
    except StartupRefusal as refusal:
        for line in refusal.failures:
            print(line, file=sys.stderr)
        return 1

    lock = InstanceLock(ctx.paths.lock_path)
    try:
        lock.acquire()
    except LockHeld:
        refusal = AlreadyRunningRefusal(ctx.paths.data_root)
        for line in refusal.failures:
            print(line, file=sys.stderr)
        return 1

    try:
        server = SpineServer(ctx)
        print(
            f"spine {ctx.version} listening on {HOST}:{server.port} "
            f"(data root {ctx.paths.data_root})",
            flush=True,
        )
        server.serve()
    finally:
        lock.release()
    return 0
