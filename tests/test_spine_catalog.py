"""The raw catalog endpoint (O5_INPUTS §F.2): full group/option facts —
ratings, tags, retired status — including the groups the creator view
curates away (free_text, session-home).
"""

import pytest

from tests.spine_helpers import auth_headers, make_ctx, spine_client


@pytest.fixture(scope="module")
def ctx(tmp_path_factory):
    return make_ctx(tmp_path_factory.mktemp("spine_catalog"))


@pytest.fixture(scope="module")
def groups(ctx):
    with spine_client(ctx) as client:
        response = client.get("/catalog", headers=auth_headers(ctx))
    assert response.status_code == 200
    payload = response.json()["groups"]
    return {group["id"]: group for group in payload}


def test_every_group_is_listed_raw(groups):
    assert set(groups) == {
        "species",
        "mane",
        "fur_color",
        "old_look",
        "traits",
        "callname",
        "purr",
        "mood",
        "looks",
        "kink",
    }


def test_free_text_and_session_groups_keep_their_facts(groups):
    looks = groups["looks"]
    assert looks["kind"] == "free_text"
    assert looks["feeds"] == "both"
    assert looks["max_chars"] == 240
    assert looks["options"] == []
    mood = groups["mood"]
    assert mood["home"] == "session"
    assert [option["id"] for option in mood["options"]] == ["happy", "sad"]


def test_retired_status_is_served(groups):
    legacy = next(
        option
        for option in groups["old_look"]["options"]
        if option["id"] == "legacy"
    )
    assert legacy["status"] == "retired"
    assert legacy["retired"] is True
    assert groups["old_look"]["hidden"] is False


def test_option_ratings_are_served(groups):
    assert {option["rating"] for option in groups["species"]["options"]} == {
        "standard"
    }
    assert groups["kink"]["options"][0]["rating"] == "explicit"


def test_declared_semantics_pass_through(groups):
    assert groups["species"]["required"] is True
    assert groups["traits"]["max_picks"] == 2
    visible_when = groups["mane"]["visible_when"]
    assert visible_when["group"] == "species"
    assert visible_when["has_tag"] == "furred"
