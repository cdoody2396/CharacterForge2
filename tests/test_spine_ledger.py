"""Ledger endpoints (O5_INPUTS §F.5/§J): artifact and staleness queries
over the (empty this stage) index, and the derive_grade passthrough —
the honestly undeterminable G1 served as-is under the null ring
provider.
"""

import pytest

from tests.spine_helpers import auth_headers, create_character, make_ctx, spine_client


@pytest.fixture(scope="module")
def ctx(tmp_path_factory):
    return make_ctx(tmp_path_factory.mktemp("spine_ledger"))


@pytest.fixture(scope="module")
def client(ctx):
    with spine_client(ctx) as client:
        yield client


@pytest.fixture(scope="module")
def cid(client, ctx):
    return create_character(client, ctx)


def test_artifacts_empty_this_stage(client, ctx, cid):
    response = client.get(f"/records/{cid}/artifacts", headers=auth_headers(ctx))
    assert response.status_code == 200
    assert response.json() == {"artifacts": []}


def test_staleness_queries(client, ctx, cid):
    response = client.get(f"/records/{cid}/staleness", headers=auth_headers(ctx))
    assert response.status_code == 200
    assert response.json() == {
        "identity_stale": [],
        "variable_stale_marked": [],
    }


def test_grade_passthrough_is_honestly_undeterminable(client, ctx, cid):
    response = client.get(f"/records/{cid}/grade", headers=auth_headers(ctx))
    assert response.status_code == 200
    derivation = response.json()
    assert derivation["character_id"] == cid
    assert derivation["grade"] is None
    assert derivation["determinable"] is False
    assert derivation["g1_determinable"] is False
    assert derivation["ladder_decided"] is True
    assert derivation["evidence"]["floor"] == "G0"
    assert derivation["evidence"]["artifacts"] == 0
    assert "undeterminable" in derivation["notes"]


def test_ledger_queries_404_on_unknown_character(client, ctx):
    for surface in ("artifacts", "staleness", "grade"):
        response = client.get(
            f"/records/ghost/{surface}", headers=auth_headers(ctx)
        )
        assert response.status_code == 404, surface
        assert response.json()["code"] == "RECORD_NOT_FOUND"
