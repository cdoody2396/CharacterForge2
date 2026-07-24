"""The creator view (O5_INPUTS §B/§F.3/§J): the single evaluator's
served facts — visibility shifting with selections, the two-basis
mirror of the record layer's own law, rating admissibility, retired
excluded-but-resolvable, required flags, and the widget table
exercised per widget.
"""

import pytest

from app.record import CharacterRecord, save_record
from app.spine.creator_view import visibility_basis
from tests.conftest import record_catalog
from tests.spine_helpers import (
    WIDGET_FILE,
    auth_headers,
    create_character,
    fill_required,
    make_ctx,
    spine_client,
)


def view_groups(client, ctx, cid) -> dict:
    response = client.get(
        f"/records/{cid}/creator-view", headers=auth_headers(ctx)
    )
    assert response.status_code == 200, response.text
    return {group["id"]: group for group in response.json()["groups"]}


def select(client, ctx, cid, group_id, value):
    response = client.post(
        f"/records/{cid}/selections",
        headers=auth_headers(ctx),
        json={"group_id": group_id, "value": value},
    )
    assert response.status_code == 200, response.text


class TestVisibility:
    def test_visibility_shifts_with_selections(self, tmp_path):
        ctx = make_ctx(tmp_path)
        with spine_client(ctx) as client:
            cid = create_character(client, ctx)
            before = view_groups(client, ctx, cid)
            assert "species" in before
            assert "mane" not in before
            assert "fur_color" not in before
            assert "purr" not in before

            select(client, ctx, cid, "species", "cat")
            furred = view_groups(client, ctx, cid)
            assert "mane" in furred
            assert "fur_color" in furred
            assert "purr" in furred

            select(client, ctx, cid, "species", "robot")
            bare = view_groups(client, ctx, cid)
            assert "mane" not in bare
            assert "purr" not in bare

    def test_free_text_and_session_groups_are_not_served_here(self, tmp_path):
        ctx = make_ctx(tmp_path)
        with spine_client(ctx) as client:
            cid = create_character(client, ctx)
            groups = view_groups(client, ctx, cid)
            assert "looks" not in groups  # sealed free_text (§I.2, gate ruling)
            assert "mood" not in groups  # session home: not record-storable

    def test_identity_reads_the_draft_while_persona_reads_the_live_identity(
        self, tmp_path
    ):
        """The two-basis law (model.py:193-210 mirrored): after v1 (cat)
        commits, a draft flipping species to robot hides the identity-
        home fur_color but persona-home purr still sees the LIVE cat."""
        ctx = make_ctx(tmp_path)
        with spine_client(ctx) as client:
            cid = create_character(client, ctx)
            fill_required(client, ctx, cid)
            headers = auth_headers(ctx)
            response = client.post(f"/records/{cid}/finalize", headers=headers)
            assert response.status_code == 200, response.text
            response = client.post(f"/records/{cid}/draft", headers=headers)
            assert response.status_code == 200, response.text
            select(client, ctx, cid, "species", "robot")

            groups = view_groups(client, ctx, cid)
            assert "fur_color" not in groups  # draft says robot
            assert "purr" in groups  # active v1 still says cat


class TestAdmissibilityAndRetired:
    def test_rating_gates_the_menu(self, tmp_path):
        ctx = make_ctx(tmp_path)
        with spine_client(ctx) as client:
            cid = create_character(client, ctx)
            standard = view_groups(client, ctx, cid)
            assert standard["kink"]["options"] == []  # explicit-only at standard

            response = client.post(
                f"/records/{cid}/rating",
                headers=auth_headers(ctx),
                json={"rating": "explicit"},
            )
            assert response.status_code == 200, response.text
            raised = view_groups(client, ctx, cid)
            assert [o["id"] for o in raised["kink"]["options"]] == ["k1"]

    def test_widget_is_stable_across_the_rating_raise(self, tmp_path):
        ctx = make_ctx(tmp_path)
        with spine_client(ctx) as client:
            cid = create_character(client, ctx)
            before = view_groups(client, ctx, cid)["kink"]["widget"]
            client.post(
                f"/records/{cid}/rating",
                headers=auth_headers(ctx),
                json={"rating": "explicit"},
            )
            after = view_groups(client, ctx, cid)["kink"]["widget"]
            assert before == after

    def test_retired_excluded_from_menus_but_resolvable_for_held_values(
        self, tmp_path
    ):
        ctx = make_ctx(tmp_path)
        # A record already holding the retired pick (written before
        # retirement) — composed via the library, the O1 story.
        record = CharacterRecord.create("held_retired", 25)
        record.draft.selections["old_look"] = ["legacy", "current"]
        save_record(record, ctx.store.path_for("held_retired"))

        with spine_client(ctx) as client:
            groups = view_groups(client, ctx, "held_retired")
            old_look = groups["old_look"]
            assert [o["id"] for o in old_look["options"]] == ["current", "extra"]
            held = {entry["id"]: entry for entry in old_look["current"]}
            assert held["legacy"]["retired"] is True
            assert held["legacy"]["label"] == "Legacy"
            assert held["current"]["retired"] is False
            assert old_look["value"] == ["legacy", "current"]


class TestTagsServed:
    """§G.1 (O6): option tags are served facts — pinned in the menu
    entry shape and in the held entry shape, resolved and orphaned."""

    def test_menu_entries_carry_tags_as_a_list_of_strings(self, tmp_path):
        ctx = make_ctx(tmp_path)
        with spine_client(ctx) as client:
            cid = create_character(client, ctx)
            species = view_groups(client, ctx, cid)["species"]
            by_id = {option["id"]: option for option in species["options"]}
            for option in by_id.values():
                assert isinstance(option["tags"], list)
                assert all(isinstance(tag, str) for tag in option["tags"])
            assert by_id["cat"]["tags"] == ["furred"]
            assert by_id["robot"]["tags"] == []  # untagged serves empty, not absent

    def test_held_entries_carry_tags_resolved_and_retired(self, tmp_path):
        ctx = make_ctx(tmp_path)
        record = CharacterRecord.create("held_tags", 25)
        record.draft.selections["old_look"] = ["legacy"]  # retired, resolvable
        save_record(record, ctx.store.path_for("held_tags"))

        with spine_client(ctx) as client:
            select(client, ctx, "held_tags", "species", "cat")
            groups = view_groups(client, ctx, "held_tags")
            held_species = groups["species"]["current"]
            assert [entry["tags"] for entry in held_species] == [["furred"]]
            held_legacy = groups["old_look"]["current"][0]
            assert held_legacy["retired"] is True
            assert held_legacy["tags"] == []  # untagged retired option

    def test_orphaned_held_entry_carries_empty_tags(self, tmp_path):
        ctx = make_ctx(tmp_path)
        record = CharacterRecord.create("orphan_tags", 25)
        record.draft.selections["old_look"] = ["ghost"]  # unknown to the catalog
        save_record(record, ctx.store.path_for("orphan_tags"))

        with spine_client(ctx) as client:
            entry = view_groups(client, ctx, "orphan_tags")["old_look"]["current"][0]
            assert entry["orphaned"] is True
            assert entry["tags"] == []


class TestFactsAndWidgets:
    def test_required_flags_and_passthrough(self, tmp_path):
        ctx = make_ctx(tmp_path)
        with spine_client(ctx) as client:
            cid = create_character(client, ctx)
            select(client, ctx, cid, "species", "cat")
            groups = view_groups(client, ctx, cid)
            assert groups["species"]["required"] is True
            assert groups["mane"]["required"] is True
            assert groups["fur_color"]["required"] is False
            assert groups["traits"]["max_picks"] == 2
            assert groups["species"]["home"] == "identity"
            assert groups["callname"]["home"] == "persona"

    def test_widget_derivation_table_exercised_per_widget(self, tmp_path):
        ctx = make_ctx(tmp_path, extra_files={"70_widgets.json": WIDGET_FILE})
        with spine_client(ctx) as client:
            cid = create_character(client, ctx)
            groups = view_groups(client, ctx, cid)
            assert groups["species"]["widget"] == "segmented"  # pick_one <= 5
            assert groups["stance"]["widget"] == "picker"  # pick_one > 5
            assert groups["portrait"]["widget"] == "picker"  # thumb wins
            assert groups["eye_color"]["widget"] == "swatch"  # color
            assert groups["quirks"]["widget"] == "chips"  # pick_many
            assert groups["old_look"]["widget"] == "chips"  # pick_many


class TestBasisParity:
    def test_visibility_basis_mirrors_the_record_law(self, tmp_path):
        """Pins the mirror to the private it mirrors (drift fails loud)."""
        catalog = record_catalog(tmp_path)
        record = CharacterRecord.create("parity", 25)

        def assert_parity():
            for working in (True, False):
                assert visibility_basis(record, working=working) == (
                    record._current_values(working=working)
                )

        assert_parity()  # fresh: open draft, nothing committed
        record.set_selection(catalog, "species", "cat")
        record.set_selection(catalog, "mane", "short_mane")
        record.set_selection(catalog, "callname", "soft")
        assert_parity()  # draft + persona selections
        record.finalize(catalog)
        assert_parity()  # committed v1, no draft
        record.open_draft()
        record.set_selection(catalog, "species", "robot")
        record.set_selection(catalog, "traits", ["brave"])
        assert_parity()  # committed v1 + diverging draft + persona
