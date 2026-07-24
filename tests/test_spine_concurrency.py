"""Per-character mutation serialization (O5_INPUTS §F/§J) under REAL
concurrent requests: N threads each mutate a different field of one
record; a lost update would drop one (each op is a whole-file
read-modify-write), so all N landing proves the spine serialized them.
"""

from concurrent.futures import ThreadPoolExecutor

import httpx

from app.spine.service import TOKEN_HEADER
from tests.spine_helpers import make_ctx, run_server, stop_server


def test_concurrent_mutations_of_one_record_all_land(tmp_path):
    ctx = make_ctx(tmp_path)
    server, thread = run_server(ctx)
    try:
        base = f"http://127.0.0.1:{server.port}"
        headers = {TOKEN_HEADER: ctx.token}
        with httpx.Client(base_url=base, headers=headers, timeout=30) as web:
            created = web.post("/records", json={"age": 25})
            assert created.status_code == 201, created.text
            cid = created.json()["record"]["character_id"]

        operations = [
            ("POST", f"/records/{cid}/selections", {"group_id": "species", "value": "cat"}),
            ("POST", f"/records/{cid}/selections", {"group_id": "old_look", "value": ["current"]}),
            ("POST", f"/records/{cid}/selections", {"group_id": "traits", "value": ["brave"]}),
            ("POST", f"/records/{cid}/selections", {"group_id": "callname", "value": "soft"}),
            ("PUT", f"/records/{cid}/age", {"age": 30}),
            ("PUT", f"/records/{cid}/name", {"name": "Mira"}),
            ("PUT", f"/records/{cid}/story-text", {"text": "calm and kind"}),
        ]

        def fire(operation):
            method, path, body = operation
            with httpx.Client(base_url=base, headers=headers, timeout=30) as web:
                return web.request(method, path, json=body)

        with ThreadPoolExecutor(max_workers=len(operations)) as pool:
            responses = list(pool.map(fire, operations))
        assert all(r.status_code == 200 for r in responses), [
            (r.status_code, r.text) for r in responses
        ]

        with httpx.Client(base_url=base, headers=headers, timeout=30) as web:
            record = web.get(f"/records/{cid}").json()["record"]
        assert record["draft_identity"]["selections"]["species"] == "cat"
        assert record["draft_identity"]["selections"]["old_look"] == ["current"]
        assert record["persona"]["selections"]["traits"] == ["brave"]
        assert record["persona"]["selections"]["callname"] == "soft"
        assert record["age"] == 30
        assert record["persona"]["name"] == "Mira"
        assert record["persona"]["story_text"] == "calm and kind"
    finally:
        stop_server(server, thread)
