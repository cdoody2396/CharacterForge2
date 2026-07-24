"""Audit write sites (O5_INPUTS §H/§J): the real AuditLog under
audit/, filter refusal events landing through the spine's sink with the
caller's surface code, lifecycle lines from the lifespan — and
vocabulary-blindness holding across the whole file.
"""

import httpx

from app.spine.service import TOKEN_HEADER
from tests.spine_helpers import (
    audit_events,
    auth_headers,
    create_character,
    make_ctx,
    run_server,
    spine_client,
    stop_server,
)


def test_lifecycle_lines_land_in_order(tmp_path):
    ctx = make_ctx(tmp_path)
    with spine_client(ctx):
        pass
    events = audit_events(ctx)
    assert [event["kind"] for event in events] == ["spine_start", "spine_stop"]
    start = events[0]
    assert start["version"] == ctx.version
    assert start["data_root"] == str(ctx.paths.data_root)
    assert "ts" in start


def test_filter_refusals_land_vocabulary_blind(tmp_path):
    ctx = make_ctx(tmp_path)
    with spine_client(ctx) as client:
        headers = auth_headers(ctx)
        cid = create_character(client, ctx)
        response = client.put(
            f"/records/{cid}/story-text",
            headers=headers,
            json={"text": "a loli appears"},
        )
        assert response.status_code == 422
        response = client.put(
            f"/records/{cid}/name", headers=headers, json={"name": "loli"}
        )
        assert response.status_code == 422

    events = audit_events(ctx)
    blocks = [event for event in events if event["kind"] == "filter_block"]
    assert len(blocks) == 2
    story_block, name_block = blocks
    assert story_block["context"] == "freetext"
    assert story_block["category"] == "minors"
    assert story_block["surface"] == "story_text"
    assert name_block["context"] == "name"
    assert name_block["surface"] == "name"

    # Vocabulary-blind: the matched term appears nowhere in the log.
    for path in ctx.paths.audit_dir.glob("*.jsonl"):
        assert "loli" not in path.read_text(encoding="utf-8")


def test_token_never_lands_in_audit(tmp_path):
    """§G.3 (O6): a real start → mutate → stop flow, then the token
    string appears nowhere under audit/ — pinned across every event
    kind the spine can emit (lifecycle, filter_block)."""
    ctx = make_ctx(tmp_path)
    server, thread = run_server(ctx)
    try:
        base = f"http://127.0.0.1:{server.port}"
        headers = {TOKEN_HEADER: ctx.token}
        with httpx.Client(timeout=10) as web:
            created = web.post(f"{base}/records", headers=headers, json={"age": 25})
            assert created.status_code == 201, created.text
            cid = created.json()["record"]["character_id"]
            selected = web.post(
                f"{base}/records/{cid}/selections",
                headers=headers,
                json={"group_id": "species", "value": "cat"},
            )
            assert selected.status_code == 200, selected.text
            # A filter refusal lands the richest audit line there is.
            blocked = web.put(
                f"{base}/records/{cid}/name", headers=headers, json={"name": "loli"}
            )
            assert blocked.status_code == 422, blocked.text
    finally:
        stop_server(server, thread)

    audit_files = sorted(ctx.paths.audit_dir.glob("*"))
    assert audit_files, "the flow above must land audit lines"
    kinds = [event["kind"] for event in audit_events(ctx)]
    assert "filter_block" in kinds  # the mutate leg really wrote
    for path in audit_files:
        assert ctx.token not in path.read_text(encoding="utf-8")


def test_allowed_writes_emit_no_events(tmp_path):
    ctx = make_ctx(tmp_path)
    with spine_client(ctx) as client:
        headers = auth_headers(ctx)
        cid = create_character(client, ctx)
        assert (
            client.put(
                f"/records/{cid}/story-text",
                headers=headers,
                json={"text": "calm and kind"},
            ).status_code
            == 200
        )
    kinds = [event["kind"] for event in audit_events(ctx)]
    assert kinds == ["spine_start", "spine_stop"]
