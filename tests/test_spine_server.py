"""Process lifecycle over a REAL server (O5_INPUTS §C/§J): loopback
bind asserted, clean start writes the discovery file with the real
bound port, graceful stop removes it and lands both audit lifecycle
lines.
"""

import httpx

from app.spine.discovery import read_discovery, write_discovery
from app.spine.service import TOKEN_HEADER
from tests.spine_helpers import audit_events, make_ctx, run_server, stop_server


def test_write_discovery_is_atomic_and_shaped(tmp_path):
    path = tmp_path / "runtime.json"
    write_discovery(path, port=4242, token="t0k3n", pid=999, version="0.1.0")
    assert not path.with_name(path.name + ".tmp").exists()
    payload = read_discovery(path)
    assert payload["host"] == "127.0.0.1"
    assert payload["port"] == 4242
    assert payload["token"] == "t0k3n"
    assert payload["pid"] == 999
    assert payload["version"] == "0.1.0"


def test_real_server_lifecycle(tmp_path):
    ctx = make_ctx(tmp_path)
    server, thread = run_server(ctx)
    try:
        # Loopback bind asserted (§J): the real socket, never 0.0.0.0.
        host, port = server.bound_address()
        assert host == "127.0.0.1"
        assert port == server.port

        # Clean start wrote discovery with the REAL port + this run's token.
        payload = read_discovery(ctx.paths.discovery_path)
        assert payload["port"] == server.port
        assert payload["token"] == ctx.token
        assert payload["host"] == "127.0.0.1"

        # The discovered address answers — tokened only.
        base = f"http://127.0.0.1:{server.port}"
        with httpx.Client(timeout=10) as web:
            refused = web.get(f"{base}/health")
            assert refused.status_code == 401
            answered = web.get(
                f"{base}/health", headers={TOKEN_HEADER: ctx.token}
            )
            assert answered.status_code == 200
            assert answered.json()["version"] == ctx.version
    finally:
        stop_server(server, thread)

    # Graceful stop: discovery removed, both lifecycle lines landed (§H).
    assert not ctx.paths.discovery_path.exists()
    kinds = [event["kind"] for event in audit_events(ctx)]
    assert kinds[0] == "spine_start"
    assert kinds[-1] == "spine_stop"
