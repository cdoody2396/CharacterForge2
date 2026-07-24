"""Auth law (O5_INPUTS §C/§J): every endpoint refuses without the
token — the middleware runs before routing, so even unknown paths
answer 401 untokened. No unauthenticated surface exists (docs and
openapi are disabled outright).
"""

import pytest

from app.spine.service import TOKEN_HEADER
from tests.spine_helpers import auth_headers, create_character, make_ctx, spine_client

# (method, path template, body) — the full endpoint inventory (§F).
ROUTES = [
    ("GET", "/health", None),
    ("GET", "/catalog", None),
    ("POST", "/records", {"age": 25}),
    ("GET", "/records", None),
    ("GET", "/records/{cid}", None),
    ("GET", "/records/{cid}/creator-view", None),
    ("PUT", "/records/{cid}/age", {"age": 30}),
    ("POST", "/records/{cid}/rating", {"rating": "standard"}),
    ("POST", "/records/{cid}/selections", {"group_id": "species", "value": "cat"}),
    ("DELETE", "/records/{cid}/selections/species", None),
    ("POST", "/records/{cid}/draft", None),
    ("POST", "/records/{cid}/finalize", None),
    ("PUT", "/records/{cid}/name", {"name": "Mira"}),
    ("POST", "/records/{cid}/name/revalidate", None),
    ("PUT", "/records/{cid}/looks-text", {"text": "sleek"}),
    ("DELETE", "/records/{cid}/looks-text", None),
    ("PUT", "/records/{cid}/story-text", {"text": "calm"}),
    ("DELETE", "/records/{cid}/story-text", None),
    ("PUT", "/records/{cid}/appearance-paragraph", {"text": "Tall."}),
    ("GET", "/records/{cid}/artifacts", None),
    ("GET", "/records/{cid}/staleness", None),
    ("GET", "/records/{cid}/grade", None),
]


@pytest.fixture(scope="module")
def ctx(tmp_path_factory):
    return make_ctx(tmp_path_factory.mktemp("spine_auth"))


@pytest.fixture(scope="module")
def client(ctx):
    with spine_client(ctx) as client:
        yield client


@pytest.fixture(scope="module")
def cid(client, ctx):
    return create_character(client, ctx)


@pytest.mark.parametrize("method,template,body", ROUTES)
def test_every_endpoint_refuses_without_the_token(
    client, cid, method, template, body
):
    response = client.request(method, template.format(cid=cid), json=body)
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_MISSING"


@pytest.mark.parametrize("method,template,body", ROUTES)
def test_every_endpoint_refuses_a_wrong_token(client, cid, method, template, body):
    response = client.request(
        method,
        template.format(cid=cid),
        json=body,
        headers={TOKEN_HEADER: "not-the-token"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_INVALID"


@pytest.mark.parametrize("method,template,body", ROUTES)
def test_every_endpoint_answers_with_the_token(
    client, ctx, cid, method, template, body
):
    response = client.request(
        method, template.format(cid=cid), json=body, headers=auth_headers(ctx)
    )
    assert response.status_code != 401, (method, template, response.text)


def test_unknown_paths_refuse_untokened_too(client, ctx):
    assert client.get("/no-such-surface").status_code == 401
    tokened = client.get("/no-such-surface", headers=auth_headers(ctx))
    assert tokened.status_code == 404


def test_docs_surfaces_do_not_exist(client, ctx):
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path, headers=auth_headers(ctx)).status_code == 404
