"""N4 construction gate — every refusal individually, checked on every
mutation; per-write scope (O3 gate decision 3): a mutation that hides an
already-set OTHER group succeeds (value inert until cleared)."""

import json

import pytest

from app.options import load_catalog
from app.record import load_record, save_record
from app.record.errors import SafetyNotInstalledError
from tests.conftest import new_record, record_catalog, refuse_gate

REAL_DATA = "app/data/options"


@pytest.fixture
def catalog(tmp_path):
    return record_catalog(tmp_path)


# --- age law ----------------------------------------------------------------


def test_age_missing_refused():
    record = new_record()
    refuse_gate("AGE_MISSING", record.set_age, None)


def test_age_non_integer_refused():
    record = new_record()
    refuse_gate("AGE_NOT_INTEGER", record.set_age, "25")


def test_age_bool_is_not_an_integer():
    record = new_record()
    refuse_gate("AGE_NOT_INTEGER", record.set_age, True)


def test_age_under_floor_refused():
    record = new_record()
    refuse_gate("AGE_UNDER_FLOOR", record.set_age, 19)
    assert record.age == 25  # unchanged on refusal


def test_age_over_ceiling_refused():
    record = new_record()
    refuse_gate("AGE_OVER_CEILING", record.set_age, 10001)


def test_age_bounds_are_inclusive():
    record = new_record()
    record.set_age(20)
    record.set_age(10000)
    assert record.age == 10000


def test_create_gates_age():
    from app.record import CharacterRecord

    refuse_gate("AGE_UNDER_FLOOR", CharacterRecord.create, "kid", 19)


# --- unknown ids ------------------------------------------------------------


def test_unknown_group_refused(catalog):
    record = new_record()
    refuse_gate("UNKNOWN_GROUP", record.set_selection, catalog, "no_such", "x")


def test_unknown_option_refused(catalog):
    record = new_record()
    refuse_gate(
        "UNKNOWN_OPTION", record.set_selection, catalog, "species", "dragon"
    )


def test_clear_of_unknown_group_refused(catalog):
    # Strict reading (recorded): orphans are cleared by restoring their
    # file, not by editing — the gate knows no such group.
    record = new_record()
    refuse_gate("UNKNOWN_GROUP", record.clear_selection, catalog, "no_such")


# --- rating -----------------------------------------------------------------


def test_option_above_record_rating_refused(catalog):
    record = new_record()
    refuse_gate(
        "RATING_ABOVE_RECORD", record.set_selection, catalog, "kink", "k1"
    )


def test_raised_rating_admits_the_option(catalog):
    record = new_record()
    record.raise_rating("explicit")
    record.set_selection(catalog, "kink", "k1")
    assert record.persona.selections["kink"] == "k1"


def test_rating_decrease_refused():
    record = new_record()
    record.raise_rating("mature")
    refuse_gate("RATING_DECREASE", record.raise_rating, "standard")
    assert record.rating == "mature"


def test_rating_monotonicity():
    record = new_record()
    record.raise_rating("standard")  # equal is not a decrease
    record.raise_rating("mature")
    record.raise_rating("mature")
    record.raise_rating("explicit")
    refuse_gate("RATING_DECREASE", record.raise_rating, "mature")
    refuse_gate("RATING_DECREASE", record.raise_rating, "standard")
    assert record.rating == "explicit"


def test_unknown_rating_refused():
    record = new_record()
    refuse_gate("BAD_RATING", record.raise_rating, "ultra")


# --- retired asymmetry (Decision 6) -----------------------------------------


def test_retired_option_newly_introduced_refused(catalog):
    record = new_record()
    refuse_gate(
        "RETIRED_NEW_PICK", record.set_selection, catalog, "old_look", ["legacy"]
    )


def test_retired_existing_pick_keeps_working(catalog, tmp_path):
    # An EXISTING retired pick stays fully functional: the record loads
    # with it and mutations that keep it pass the gate.
    record = new_record()
    record.set_selection(catalog, "species", "cat")
    record.set_selection(catalog, "mane", "long_mane")
    record.set_selection(catalog, "callname", "soft")
    record.set_selection(catalog, "old_look", ["current"])
    record.finalize(catalog)
    path = tmp_path / "char.json"
    save_record(record, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    # The pick predates retirement (composed directly: load does not gate).
    data["identity_versions"][0]["selections"]["old_look"] = ["legacy"]
    path.write_text(json.dumps(data), encoding="utf-8")
    loaded, orphans = load_record(path, catalog)
    assert orphans == []
    loaded.open_draft()
    # keeping legacy while adding an active option: legal (existing pick)
    loaded.set_selection(catalog, "old_look", ["legacy", "current"])
    # but a DIFFERENT record still cannot newly select it
    fresh = new_record("other")
    refuse_gate(
        "RETIRED_NEW_PICK", fresh.set_selection, catalog, "old_look", ["legacy"]
    )


# --- visibility -------------------------------------------------------------


def test_hidden_group_write_refused(catalog):
    record = new_record()
    refuse_gate(
        "HIDDEN_GROUP_VALUE", record.set_selection, catalog, "fur_color", "red"
    )


def test_visible_after_revealing_selection(catalog):
    record = new_record()
    record.set_selection(catalog, "species", "cat")
    record.set_selection(catalog, "fur_color", "red")
    assert record.draft.selections["fur_color"] == "red"


def test_hidden_refusal_against_real_maintained_catalog():
    # The REAL tree: fur_color (35_species.json) is visible only when
    # skin_type is fur_over_skin (20_appearance.json).
    catalog = load_catalog([REAL_DATA], strict=True)
    record = new_record()
    refuse_gate(
        "HIDDEN_GROUP_VALUE", record.set_selection, catalog, "fur_color", "white"
    )
    record.set_selection(catalog, "skin_type", "fur_over_skin")
    record.set_selection(catalog, "fur_color", "white")
    assert record.draft.selections["fur_color"] == "white"


def test_mutation_hiding_existing_value_allowed_value_inert(catalog):
    # Gate decision 3 (this session): per-write gate — hiding an already-set
    # group succeeds; the stale value sits inert (finalization refuses it).
    record = new_record()
    record.set_selection(catalog, "species", "cat")
    record.set_selection(catalog, "fur_color", "red")
    record.set_selection(catalog, "species", "robot")  # hides fur_color
    assert record.draft.selections["fur_color"] == "red"  # written, inert


def test_persona_visibility_reads_the_active_identity(catalog):
    # Builder detail (recorded): persona mutations evaluate against the
    # LIVE identity (active version), not an open draft.
    record = new_record()
    record.set_selection(catalog, "species", "cat")
    record.set_selection(catalog, "mane", "short_mane")
    record.set_selection(catalog, "callname", "soft")
    record.finalize(catalog)
    record.open_draft()
    record.set_selection(catalog, "species", "robot")  # draft only
    record.set_selection(catalog, "purr", "quiet")  # active species is cat
    assert record.persona.selections["purr"] == "quiet"


def test_persona_visibility_reads_the_draft_before_v1(catalog):
    record = new_record()
    refuse_gate("HIDDEN_GROUP_VALUE", record.set_selection, catalog, "purr", "quiet")
    record.set_selection(catalog, "species", "cat")
    record.set_selection(catalog, "purr", "quiet")
    assert record.persona.selections["purr"] == "quiet"


# --- kind / value-shape violations ------------------------------------------


def test_list_for_pick_one_refused(catalog):
    record = new_record()
    refuse_gate(
        "LIST_FOR_PICK_ONE", record.set_selection, catalog, "species", ["cat"]
    )


def test_single_for_pick_many_refused(catalog):
    record = new_record()
    refuse_gate(
        "NOT_A_LIST_FOR_PICK_MANY",
        record.set_selection,
        catalog,
        "traits",
        "brave",
    )


def test_empty_pick_list_refused(catalog):
    record = new_record()
    refuse_gate("EMPTY_PICK_LIST", record.set_selection, catalog, "traits", [])


def test_duplicate_picks_refused(catalog):
    record = new_record()
    refuse_gate(
        "DUPLICATE_PICK",
        record.set_selection,
        catalog,
        "traits",
        ["brave", "brave"],
    )


def test_max_picks_exceeded_refused(catalog):
    record = new_record()
    refuse_gate(
        "MAX_PICKS_EXCEEDED",
        record.set_selection,
        catalog,
        "traits",
        ["brave", "shy", "calm"],
    )


def test_non_string_value_refused(catalog):
    record = new_record()
    refuse_gate("BAD_VALUE_TYPE", record.set_selection, catalog, "species", 7)


def test_pick_many_order_as_picked_kept(catalog):
    record = new_record()
    record.set_selection(catalog, "traits", ["shy", "brave"])
    assert record.persona.selections["traits"] == ["shy", "brave"]


# --- session home / null / free text ----------------------------------------


def test_session_home_value_refused(catalog):
    record = new_record()
    refuse_gate(
        "SESSION_HOME_VALUE", record.set_selection, catalog, "mood", "happy"
    )


def test_session_home_clear_refused_too(catalog):
    record = new_record()
    refuse_gate("SESSION_HOME_VALUE", record.clear_selection, catalog, "mood")


def test_null_value_refused(catalog):
    record = new_record()
    refuse_gate("NULL_VALUE", record.set_selection, catalog, "species", None)


def test_null_inside_pick_list_refused(catalog):
    record = new_record()
    refuse_gate(
        "NULL_VALUE", record.set_selection, catalog, "traits", ["brave", None]
    )


def test_free_text_write_refuses_per_n6(catalog):
    record = new_record()
    with pytest.raises(SafetyNotInstalledError):
        record.set_selection(catalog, "looks", "tall and green")


# --- draft routing ----------------------------------------------------------


def test_identity_mutation_without_draft_refused(catalog):
    record = new_record()
    record.set_selection(catalog, "species", "cat")
    record.set_selection(catalog, "mane", "long_mane")
    record.set_selection(catalog, "callname", "soft")
    record.finalize(catalog)  # draft consumed
    refuse_gate(
        "IDENTITY_NO_DRAFT", record.set_selection, catalog, "species", "wolf"
    )


def test_persona_stays_editable_without_draft(catalog):
    record = new_record()
    record.set_selection(catalog, "species", "cat")
    record.set_selection(catalog, "mane", "long_mane")
    record.set_selection(catalog, "callname", "soft")
    record.finalize(catalog)
    record.set_selection(catalog, "traits", ["calm"])  # Decision 4: any time
    assert record.persona.selections["traits"] == ["calm"]
