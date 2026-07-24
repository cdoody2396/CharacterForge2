"""Shared builders for the spine tests (O5).

A plain module, not a conftest — tests/conftest.py stays untouched
(additive-only). Spine tests compose the O3 record catalog through the
bootstrap test seam and run the real SafetyFilter over the real word
data, exactly what a running spine does.
"""

import json
import threading
import time

from fastapi.testclient import TestClient

from app.spine import build_app, build_context
from app.spine.server import SpineServer
from app.spine.service import TOKEN_HEADER
from tests.conftest import record_catalog_dir

# One group per widget-derivation rule (§F.3; the table is recorded in
# SESSION_REPORT_O5). species (3 plain options, pick_one) in the record
# catalog covers `segmented`.
WIDGET_FILE = {
    "format": 1,
    "rating": "standard",
    "groups": [
        {
            "id": "eye_color",
            "label": "Eye Color",
            "kind": "pick_one",
            "home": "identity",
            "options": [
                {"id": "amber", "label": "Amber", "color": "#ffbf00"},
                {"id": "jade", "label": "Jade", "color": "#00a86b"},
            ],
        },
        {
            "id": "portrait",
            "label": "Portrait",
            "kind": "pick_one",
            "home": "identity",
            "options": [
                {"id": "p1", "label": "P1", "thumb": "thumbs/p1.png"},
                {"id": "p2", "label": "P2"},
            ],
        },
        {
            "id": "stance",
            "label": "Stance",
            "kind": "pick_one",
            "home": "identity",
            "options": [{"id": f"s{i}", "label": f"S{i}"} for i in range(6)],
        },
        {
            "id": "quirks",
            "label": "Quirks",
            "kind": "pick_many",
            "home": "persona",
            "options": [
                {"id": "hums", "label": "Hums"},
                {"id": "naps", "label": "Naps"},
            ],
        },
    ],
}


def make_ctx(
    tmp_path,
    *,
    extra_files=None,
    root="root",
    options_dirs=None,
    safety_data_dir=None,
):
    """A SpineContext over ``tmp_path/root`` and the composed record
    catalog (plus any extra option files written beside it)."""
    if options_dirs is None:
        catalog_dir = record_catalog_dir(tmp_path)
        if extra_files:
            for name, obj in extra_files.items():
                (catalog_dir / name).write_text(json.dumps(obj), encoding="utf-8")
        options_dirs = [catalog_dir]
    kwargs = {"options_dirs": options_dirs}
    if safety_data_dir is not None:
        kwargs["safety_data_dir"] = safety_data_dir
    return build_context(tmp_path / root, **kwargs)


def auth_headers(ctx):
    return {TOKEN_HEADER: ctx.token}


def spine_client(ctx) -> TestClient:
    """Use as a context manager where the lifespan (audit lifecycle
    lines) matters; plain requests work either way."""
    return TestClient(build_app(ctx))


def create_character(client, ctx, age=25) -> str:
    response = client.post("/records", headers=auth_headers(ctx), json={"age": age})
    assert response.status_code == 201, response.text
    return response.json()["record"]["character_id"]


def fill_required(client, ctx, cid):
    """species=cat (makes mane visible+required), mane, callname — the
    minimum that lets finalize pass over the record catalog."""
    headers = auth_headers(ctx)
    for group_id, value in (
        ("species", "cat"),
        ("mane", "short_mane"),
        ("callname", "soft"),
    ):
        response = client.post(
            f"/records/{cid}/selections",
            headers=headers,
            json={"group_id": group_id, "value": value},
        )
        assert response.status_code == 200, response.text


def run_server(ctx) -> tuple[SpineServer, threading.Thread]:
    server = SpineServer(ctx)
    thread = threading.Thread(target=server.serve, daemon=True)
    thread.start()
    deadline = time.monotonic() + 15
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.02)
    assert server.started, "spine server did not start in time"
    return server, thread


def stop_server(server, thread):
    server.stop()
    thread.join(timeout=15)
    assert not thread.is_alive(), "spine server did not stop in time"


def audit_events(ctx) -> list[dict]:
    events = []
    for path in sorted(ctx.paths.audit_dir.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            events.append(json.loads(line))
    return events
