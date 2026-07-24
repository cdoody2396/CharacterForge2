"""Dev launcher (O6_INPUTS §C.4) — stdlib only.

Starts the spine over ``./.devroot`` (gitignored) as a subprocess,
reads ``runtime.json`` host-side (§D.2 forbids only the React app from
reading it), then launches Vite with VITE_SPINE_ORIGIN and
VITE_SPINE_TOKEN in the environment. The spine terminates when the
launcher exits, both platforms.

Usage:  python scripts/dev.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEVROOT = REPO / ".devroot"
DISCOVERY = DEVROOT / "runtime.json"
READY_DEADLINE = 30.0


def spine_command() -> list[str]:
    """The repo venv's python when present (a direct child process is
    what termination-on-exit needs, both platforms), else uv run."""
    venv_python = (
        REPO / ".venv" / ("Scripts" if os.name == "nt" else "bin")
    ) / ("python.exe" if os.name == "nt" else "python")
    if venv_python.exists():
        return [str(venv_python), "-m", "app.spine", "--data-root", str(DEVROOT)]
    uv = shutil.which("uv")
    if uv is None:
        sys.exit("neither .venv nor uv found — run `uv sync` first")
    return [uv, "run", "python", "-m", "app.spine", "--data-root", str(DEVROOT)]


def wait_for_spine(spine: subprocess.Popen) -> dict:
    """Poll for runtime.json, then confirm with a tokened /health."""
    deadline = time.monotonic() + READY_DEADLINE
    while time.monotonic() < deadline:
        if spine.poll() is not None:
            sys.exit(f"the spine exited before it was ready (rc={spine.returncode})")
        if DISCOVERY.exists():
            try:
                payload = json.loads(DISCOVERY.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                payload = None
            if payload:
                request = urllib.request.Request(
                    f"http://{payload['host']}:{payload['port']}/health",
                    headers={"X-Spine-Token": payload["token"]},
                )
                try:
                    with urllib.request.urlopen(request, timeout=2) as response:
                        if response.status == 200:
                            return payload
                except (urllib.error.URLError, OSError):
                    pass
        time.sleep(0.1)
    sys.exit("the spine did not become ready in time")


def terminate(process: subprocess.Popen, timeout: float = 10.0) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main() -> None:
    npm = shutil.which("npm")
    if npm is None:
        sys.exit("npm not on PATH — Node >= 20 is a prerequisite")
    if not (REPO / "frontend" / "node_modules").exists():
        sys.exit("frontend/node_modules missing — run `npm ci` in frontend/ first")

    # A stale discovery file from a crashed run must not win the wait
    # loop; the spine's own instance lock recovers separately.
    DEVROOT.mkdir(exist_ok=True)
    if DISCOVERY.exists():
        DISCOVERY.unlink()

    spine = subprocess.Popen(spine_command(), cwd=REPO)
    vite: subprocess.Popen | None = None
    try:
        payload = wait_for_spine(spine)
        print(
            f"spine ready on {payload['host']}:{payload['port']} "
            f"(data root {DEVROOT})"
        )
        env = dict(os.environ)
        env["VITE_SPINE_ORIGIN"] = f"http://{payload['host']}:{payload['port']}"
        env["VITE_SPINE_TOKEN"] = payload["token"]
        vite = subprocess.Popen([npm, "run", "dev"], cwd=REPO / "frontend", env=env)
        while spine.poll() is None and vite.poll() is None:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        if vite is not None:
            terminate(vite)
        terminate(spine)


if __name__ == "__main__":
    main()
