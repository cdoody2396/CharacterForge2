"""The refusal matrix (O5_INPUTS §F.4/§J): every N4/N5/O4 code arrives
over HTTP structured — {code, subject, message} — with the library's
code verbatim, never renamed, never softened. Statuses per the recorded
mapping: 409 for state/law-in-context refusals, 422 for payload/content
refusals, 401 auth, 404 unknown record.
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


@pytest.fixture(scope="module")
def ctx(tmp_path_factory):
    return make_ctx(tmp_path_factory.mktemp("spine_refusals"))


@pytest.fixture(scope="module")
def client(ctx):
    with spine_client(ctx) as client:
        yield client


@pytest.fixture()
def cid(client, ctx):
    return create_character(client, ctx)


def assert_refusal(response, status, code):
    assert response.status_code == status, response.text
    body = response.json()
    assert body["code"] == code
    assert "subject" in body
    assert body["message"]
    return body


class TestHeaderGate:
    @pytest.mark.parametrize(
        "body,code",
        [
            ({}, E.AGE_MISSING),
            ({"age": "old"}, E.AGE_NOT_INTEGER),
            ({"age": 19}, E.AGE_UNDER_FLOOR),
            ({"age": 10001}, E.AGE_OVER_CEILING),
        ],
    )
    def test_age_codes_on_create(self, client, ctx, body, code):
        assert_refusal(
            client.post("/records", headers=auth_headers(ctx), json=body), 422, code
        )

    def test_age_codes_on_mutation(self, client, ctx, cid):
        response = client.put(
            f"/records/{cid}/age", headers=auth_headers(ctx), json={"age": 12}
        )
        assert_refusal(response, 422, E.AGE_UNDER_FLOOR)

    def test_bad_rating(self, client, ctx, cid):
        response = client.post(
            f"/records/{cid}/rating", headers=auth_headers(ctx), json={"rating": "wild"}
        )
        assert_refusal(response, 422, E.BAD_RATING)

    def test_rating_decrease(self, client, ctx, cid):
        headers = auth_headers(ctx)
        assert (
            client.post(
                f"/records/{cid}/rating", headers=headers, json={"rating": "explicit"}
            ).status_code
            == 200
        )
        response = client.post(
            f"/records/{cid}/rating", headers=headers, json={"rating": "mature"}
        )
        assert_refusal(response, 409, E.RATING_DECREASE)


class TestSelectionGate:
    @pytest.mark.parametrize(
        "body,status,code",
        [
            ({"group_id": "nope", "value": "x"}, 422, E.UNKNOWN_GROUP),
            ({"group_id": "mood", "value": "happy"}, 422, E.SESSION_HOME_VALUE),
            ({"group_id": "looks", "value": "text"}, 409, E.SAFETY_NOT_INSTALLED),
            ({"group_id": "species", "value": "dragon"}, 422, E.UNKNOWN_OPTION),
            ({"group_id": "kink", "value": "k1"}, 409, E.RATING_ABOVE_RECORD),
            ({"group_id": "old_look", "value": ["legacy"]}, 409, E.RETIRED_NEW_PICK),
            ({"group_id": "mane", "value": "short_mane"}, 409, E.HIDDEN_GROUP_VALUE),
            ({"group_id": "species", "value": None}, 422, E.NULL_VALUE),
            ({"group_id": "species", "value": ["cat"]}, 422, E.LIST_FOR_PICK_ONE),
            ({"group_id": "species", "value": 42}, 422, E.BAD_VALUE_TYPE),
            (
                {"group_id": "traits", "value": "brave"},
                422,
                E.NOT_A_LIST_FOR_PICK_MANY,
            ),
            ({"group_id": "traits", "value": []}, 422, E.EMPTY_PICK_LIST),
            (
                {"group_id": "traits", "value": ["brave", "brave"]},
                422,
                E.DUPLICATE_PICK,
            ),
            (
                {"group_id": "traits", "value": ["brave", "shy", "calm"]},
                422,
                E.MAX_PICKS_EXCEEDED,
            ),
        ],
    )
    def test_selection_codes(self, client, ctx, cid, body, status, code):
        response = client.post(
            f"/records/{cid}/selections", headers=auth_headers(ctx), json=body
        )
        assert_refusal(response, status, code)

    def test_subject_carries_the_id_path(self, client, ctx, cid):
        response = client.post(
            f"/records/{cid}/selections",
            headers=auth_headers(ctx),
            json={"group_id": "species", "value": "dragon"},
        )
        assert response.json()["subject"] == "species/dragon"


class TestDraftAndFinalize:
    def test_draft_already_open(self, client, ctx, cid):
        response = client.post(f"/records/{cid}/draft", headers=auth_headers(ctx))
        assert_refusal(response, 409, E.DRAFT_ALREADY_OPEN)

    def test_required_group_unfilled(self, client, ctx, cid):
        response = client.post(f"/records/{cid}/finalize", headers=auth_headers(ctx))
        assert_refusal(response, 409, E.REQUIRED_GROUP_UNFILLED)

    def test_no_draft_and_identity_no_draft(self, client, ctx, cid):
        headers = auth_headers(ctx)
        fill_required(client, ctx, cid)
        assert (
            client.post(f"/records/{cid}/finalize", headers=headers).status_code
            == 200
        )
        response = client.post(f"/records/{cid}/finalize", headers=headers)
        assert_refusal(response, 409, E.NO_DRAFT)
        response = client.put(
            f"/records/{cid}/looks-text", headers=headers, json={"text": "x"}
        )
        assert_refusal(response, 409, E.IDENTITY_NO_DRAFT)


class TestFilteredSurfaces:
    def test_name_charset(self, client, ctx, cid):
        response = client.put(
            f"/records/{cid}/name", headers=auth_headers(ctx), json={"name": "Bad;Name"}
        )
        assert_refusal(response, 422, E.NAME_CHARSET)

    def test_name_length(self, client, ctx, cid):
        response = client.put(
            f"/records/{cid}/name", headers=auth_headers(ctx), json={"name": "x" * 61}
        )
        assert_refusal(response, 422, E.NAME_LENGTH)

    def test_name_bad_type(self, client, ctx, cid):
        response = client.put(
            f"/records/{cid}/name", headers=auth_headers(ctx), json={"name": 42}
        )
        assert_refusal(response, 422, E.BAD_VALUE_TYPE)

    def test_name_blocked(self, client, ctx, cid):
        response = client.put(
            f"/records/{cid}/name", headers=auth_headers(ctx), json={"name": "loli"}
        )
        assert_refusal(response, 422, E.NAME_BLOCKED)

    def test_free_text_overlong(self, client, ctx, cid):
        response = client.put(
            f"/records/{cid}/looks-text",
            headers=auth_headers(ctx),
            json={"text": "x" * 241},
        )
        assert_refusal(response, 422, E.FREE_TEXT_OVERLONG)

    def test_paragraph_overlong(self, client, ctx, cid):
        response = client.put(
            f"/records/{cid}/appearance-paragraph",
            headers=auth_headers(ctx),
            json={"text": "x" * 1201},
        )
        assert_refusal(response, 422, E.PARAGRAPH_OVERLONG)

    def test_text_blocked(self, client, ctx, cid):
        response = client.put(
            f"/records/{cid}/story-text",
            headers=auth_headers(ctx),
            json={"text": "a loli appears"},
        )
        assert_refusal(response, 422, E.TEXT_BLOCKED)

    def test_text_bad_type(self, client, ctx, cid):
        response = client.put(
            f"/records/{cid}/story-text", headers=auth_headers(ctx), json={"text": 9}
        )
        assert_refusal(response, 422, E.BAD_VALUE_TYPE)
