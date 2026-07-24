"""Records over HTTP (O5_INPUTS §F.4/§J): the full lifecycle — create →
select → finalize → filtered writes → rating raise — plus load/list
shapes and the stored-file truth the spine serves.
"""

import pytest

from app.record import errors as E
from tests.spine_helpers import (
    auth_headers,
    create_character,
    fill_required,
    make_ctx,
    spine_client,
)


@pytest.fixture()
def ctx(tmp_path):
    return make_ctx(tmp_path)


def test_full_lifecycle_over_http(ctx):
    with spine_client(ctx) as client:
        headers = auth_headers(ctx)
        cid = create_character(client, ctx)

        # created: standard rating, open draft, no committed version
        loaded = client.get(f"/records/{cid}", headers=headers).json()
        assert loaded["record"]["rating"] == "standard"
        assert "draft_identity" in loaded["record"]
        assert "active_version" not in loaded["record"]

        fill_required(client, ctx, cid)
        response = client.put(
            f"/records/{cid}/name", headers=headers, json={"name": "Mira"}
        )
        assert response.status_code == 200, response.text
        assert response.json()["record"]["persona"]["name_safety"] == "clear"

        response = client.put(
            f"/records/{cid}/looks-text", headers=headers, json={"text": "Sleek fur"}
        )
        assert response.status_code == 200, response.text
        response = client.put(
            f"/records/{cid}/story-text",
            headers=headers,
            json={"text": "Calm and kind"},
        )
        assert response.status_code == 200, response.text

        # finalize commits v1; the paragraph is drafted (author: drafter)
        response = client.post(f"/records/{cid}/finalize", headers=headers)
        assert response.status_code == 200, response.text
        record = response.json()["record"]
        assert record["active_version"] == 1
        version = record["identity_versions"][0]
        assert version["looks_text"] == "Sleek fur"
        assert version["paragraph_author"] == "drafter"
        assert version["appearance_paragraph"]
        assert "draft_identity" not in record

        # identity is locked at finalization: a new draft reopens it
        response = client.post(
            f"/records/{cid}/selections",
            headers=headers,
            json={"group_id": "species", "value": "wolf"},
        )
        assert response.status_code == 409
        assert response.json()["code"] == E.IDENTITY_NO_DRAFT

        response = client.post(f"/records/{cid}/draft", headers=headers)
        assert response.status_code == 200, response.text
        response = client.put(
            f"/records/{cid}/appearance-paragraph",
            headers=headers,
            json={"text": "She stands tall and quiet."},
        )
        assert response.status_code == 200, response.text
        response = client.post(f"/records/{cid}/finalize", headers=headers)
        assert response.status_code == 200, response.text
        record = response.json()["record"]
        assert record["active_version"] == 2
        version = record["identity_versions"][1]
        assert version["appearance_paragraph"] == "She stands tall and quiet."
        assert version["paragraph_author"] == "user"

        # rating raise opens the explicit shelf
        response = client.post(
            f"/records/{cid}/rating", headers=headers, json={"rating": "explicit"}
        )
        assert response.status_code == 200, response.text
        response = client.post(
            f"/records/{cid}/selections",
            headers=headers,
            json={"group_id": "kink", "value": "k1"},
        )
        assert response.status_code == 200, response.text

        # the list surfaces id, name, rating, active version, grade summary
        listing = client.get("/records", headers=headers).json()["records"]
        assert len(listing) == 1
        entry = listing[0]
        assert entry["character_id"] == cid
        assert entry["name"] == "Mira"
        assert entry["rating"] == "explicit"
        assert entry["active_version"] == 2
        assert entry["grade"]["determinable"] is False
        assert entry["orphan_count"] == 0


def test_clears_and_revalidate(ctx):
    with spine_client(ctx) as client:
        headers = auth_headers(ctx)
        cid = create_character(client, ctx)

        client.put(f"/records/{cid}/looks-text", headers=headers, json={"text": "x"})
        response = client.delete(f"/records/{cid}/looks-text", headers=headers)
        assert response.status_code == 200
        assert "looks_text" not in response.json()["record"].get(
            "draft_identity", {}
        )

        client.put(f"/records/{cid}/story-text", headers=headers, json={"text": "y"})
        response = client.delete(f"/records/{cid}/story-text", headers=headers)
        assert response.status_code == 200
        assert "story_text" not in response.json()["record"]["persona"]

        response = client.post(
            f"/records/{cid}/selections",
            headers=headers,
            json={"group_id": "species", "value": "cat"},
        )
        assert response.status_code == 200
        response = client.delete(
            f"/records/{cid}/selections/species", headers=headers
        )
        assert response.status_code == 200
        assert (
            "species"
            not in response.json()["record"]["draft_identity"]["selections"]
        )

        # a spine-set name is already clear; revalidation is idempotent
        client.put(f"/records/{cid}/name", headers=headers, json={"name": "Rin"})
        response = client.post(f"/records/{cid}/name/revalidate", headers=headers)
        assert response.status_code == 200
        assert response.json()["record"]["persona"]["name_safety"] == "clear"


def test_age_mutation(ctx):
    with spine_client(ctx) as client:
        headers = auth_headers(ctx)
        cid = create_character(client, ctx)
        response = client.put(
            f"/records/{cid}/age", headers=headers, json={"age": 30}
        )
        assert response.status_code == 200
        assert response.json()["record"]["age"] == 30


def test_unknown_record_is_404(ctx):
    with spine_client(ctx) as client:
        response = client.get(
            "/records/never_created", headers=auth_headers(ctx)
        )
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "RECORD_NOT_FOUND"
        assert body["subject"] == "never_created"


def test_corrupt_record_file_refuses_loudly(ctx):
    (ctx.paths.records_dir / "broken.json").write_text(
        "{not json", encoding="utf-8"
    )
    with spine_client(ctx) as client:
        response = client.get("/records/broken", headers=auth_headers(ctx))
        assert response.status_code == 422
        assert response.json()["code"] == E.RECORD_INVALID_JSON


def test_mutation_refusal_persists_nothing(ctx):
    with spine_client(ctx) as client:
        headers = auth_headers(ctx)
        cid = create_character(client, ctx)
        response = client.post(
            f"/records/{cid}/selections",
            headers=headers,
            json={"group_id": "traits", "value": ["brave", "shy", "calm"]},
        )
        assert response.status_code == 422
        assert response.json()["code"] == E.MAX_PICKS_EXCEEDED
        reloaded = client.get(f"/records/{cid}", headers=headers).json()
        assert "traits" not in reloaded["record"]["persona"]["selections"]
