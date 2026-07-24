"""The discovery file (O5_INPUTS §C): port + token written atomically
under the data root so a shell or front-end can find the spine.

Shape (builder detail, recorded): runtime.json —
``{"host", "port", "token", "pid", "version", "started"}``. Written with
the record layer's atomic idiom (same-directory tmp + os.replace).
"""

from __future__ import annotations

import json
import os
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

HOST = "127.0.0.1"  # loopback-only (§C); never 0.0.0.0


def write_discovery(
    path: Path | str, *, port: int, token: str, pid: int, version: str
) -> None:
    path = Path(path)
    payload = {
        "host": HOST,
        "port": port,
        "token": token,
        "pid": pid,
        "version": version,
        "started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    os.replace(tmp, path)


def read_discovery(path: Path | str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def remove_discovery(path: Path | str) -> None:
    with suppress(FileNotFoundError):
        Path(path).unlink()
