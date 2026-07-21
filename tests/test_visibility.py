"""§6 visibility: structural refusals (§1.14 — no silent degrade) and
evaluation semantics (one hop, non-recursive, single implementation)."""

import pytest
from conftest import free_text_group, group, load_strict, refuse, refuse_catalog

from app.options import errors as E


def _two_groups(visible_when, ref_group=None):
    """A referenced group plus a dependent group carrying visible_when."""
    ref = ref_group or group(
        id="ref",
        options=[
            {"id": "opt_x", "label": "X", "tags": ["furry"]},
            {"id": "opt_y", "label": "Y"},
        ],
    )
    dep = group(id="dep")
    if visible_when is not None:
        dep["visible_when"] = visible_when
    return {"format": 1, "rating": "standard", "groups": [ref, dep]}


# --- structural refusals (per-file format errors, §1.14) -------------------


def test_refuses_visible_when_not_an_object(write_file):
    refuse(write_file("00.json", _two_groups("ref")), E.BAD_VISIBLE_WHEN)


def test_refuses_visible_when_without_group(write_file):
    refuse(write_file("00.json", _two_groups({"any": True})), E.BAD_VISIBLE_WHEN)


def test_refuses_visible_when_without_predicate(write_file):
    refuse(write_file("00.json", _two_groups({"group": "ref"})), E.BAD_VISIBLE_WHEN)


def test_refuses_visible_when_with_two_predicates(write_file):
    d = write_file(
        "00.json", _two_groups({"group": "ref", "any": True, "in": ["opt_x"]})
    )
    refuse(d, E.BAD_VISIBLE_WHEN)


def test_refuses_unknown_predicate(write_file):
    # v1's "class" predicate became has_tag (§1.8); the old spelling is an
    # unknown key now, not a silent no-op.
    d = write_file("00.json", _two_groups({"group": "ref", "class": "furry"}))
    refuse(d, E.UNKNOWN_KEY)


def test_refuses_any_false(write_file):
    d = write_file("00.json", _two_groups({"group": "ref", "any": False}))
    refuse(d, E.BAD_VISIBLE_WHEN)


def test_refuses_empty_in_list(write_file):
    d = write_file("00.json", _two_groups({"group": "ref", "in": []}))
    refuse(d, E.BAD_VISIBLE_WHEN)


def test_refuses_non_list_in(write_file):
    d = write_file("00.json", _two_groups({"group": "ref", "in": "opt_x"}))
    refuse(d, E.BAD_VISIBLE_WHEN)


def test_refuses_non_string_has_tag(write_file):
    d = write_file("00.json", _two_groups({"group": "ref", "has_tag": 1}))
    refuse(d, E.BAD_VISIBLE_WHEN)


# --- reference laws (catalog-level: decidable only after all files merge) --


def test_refuses_reference_to_missing_group(write_file):
    d = write_file(
        "00.json", _two_groups({"group": "no_such_group", "any": True})
    )
    refuse_catalog(d, E.VISIBLE_WHEN_UNKNOWN_GROUP)


def test_refuses_in_predicate_against_free_text(write_file):
    # Kickoff-pinned: only "any" may reference a free_text group.
    d = write_file(
        "00.json",
        _two_groups(
            {"group": "ref", "in": ["opt_x"]},
            ref_group=free_text_group(id="ref"),
        ),
    )
    refuse_catalog(d, E.VISIBLE_WHEN_FREE_TEXT_PREDICATE)


def test_refuses_has_tag_against_free_text(write_file):
    d = write_file(
        "00.json",
        _two_groups(
            {"group": "ref", "has_tag": "furry"},
            ref_group=free_text_group(id="ref"),
        ),
    )
    refuse_catalog(d, E.VISIBLE_WHEN_FREE_TEXT_PREDICATE)


def test_cross_file_reference_is_legal(write_file):
    # The reference check runs post-merge, so a group may depend on a group
    # a LATER file defines.
    write_file(
        "00_dep.json",
        {
            "format": 1,
            "rating": "standard",
            "groups": [group(id="dep", visible_when={"group": "ref", "any": True})],
        },
    )
    d = write_file(
        "10_ref.json",
        {"format": 1, "rating": "standard", "groups": [group(id="ref")]},
    )
    assert load_strict(d).get("dep") is not None


# --- evaluation semantics --------------------------------------------------


def _catalog(write_file, visible_when, ref_group=None):
    return load_strict(write_file("00.json", _two_groups(visible_when, ref_group)))


def test_absent_condition_is_always_visible(write_file):
    catalog = _catalog(write_file, None)
    assert catalog.get("dep").visible_when is None
    assert catalog.visible_now("dep", {}) is True


def test_any_needs_a_value(write_file):
    catalog = _catalog(write_file, {"group": "ref", "any": True})
    assert catalog.visible_now("dep", {}) is False
    assert catalog.visible_now("dep", {"ref": "opt_x"}) is True
    assert catalog.visible_now("dep", {"ref": ""}) is False


def test_any_against_free_text_value(write_file):
    catalog = _catalog(
        write_file,
        {"group": "ref", "any": True},
        ref_group=free_text_group(id="ref"),
    )
    assert catalog.visible_now("dep", {"ref": "some entered text"}) is True
    assert catalog.visible_now("dep", {"ref": ""}) is False


def test_in_predicate(write_file):
    catalog = _catalog(write_file, {"group": "ref", "in": ["opt_x"]})
    assert catalog.visible_now("dep", {"ref": "opt_x"}) is True
    assert catalog.visible_now("dep", {"ref": "opt_y"}) is False
    assert catalog.visible_now("dep", {}) is False
    # pick_many-style list values intersect
    assert catalog.visible_now("dep", {"ref": ["opt_y", "opt_x"]}) is True


def test_not_in_empty_selection_reads_visible(write_file):
    # §6: DECIDED polarity — an empty selection reads visible.
    catalog = _catalog(write_file, {"group": "ref", "not_in": ["opt_x"]})
    assert catalog.visible_now("dep", {}) is True
    assert catalog.visible_now("dep", {"ref": "opt_x"}) is False
    assert catalog.visible_now("dep", {"ref": "opt_y"}) is True


def test_has_tag_predicate(write_file):
    catalog = _catalog(write_file, {"group": "ref", "has_tag": "furry"})
    assert catalog.visible_now("dep", {"ref": "opt_x"}) is True  # carries tag
    assert catalog.visible_now("dep", {"ref": "opt_y"}) is False
    assert catalog.visible_now("dep", {}) is False
    assert catalog.visible_now("dep", {"ref": "unknown_id"}) is False


def test_has_tag_resolves_retired_options(write_file):
    # Decision 6: a retired option stays fully functional for existing
    # values — including its tags feeding visibility.
    ref = group(
        id="ref",
        options=[
            {"id": "opt_x", "label": "X", "tags": ["furry"], "status": "retired"}
        ],
    )
    catalog = _catalog(write_file, {"group": "ref", "has_tag": "furry"}, ref)
    assert catalog.visible_now("dep", {"ref": "opt_x"}) is True


def test_evaluation_is_one_hop_non_recursive(write_file):
    # §6: dep depends on mid; mid itself depends on far and would be hidden —
    # but evaluation is one hop, so mid's own visibility is NOT consulted.
    data = {
        "format": 1,
        "rating": "standard",
        "groups": [
            group(id="far"),
            group(id="mid", visible_when={"group": "far", "in": ["opt_a"]}),
            group(id="dep", visible_when={"group": "mid", "any": True}),
        ],
    }
    catalog = load_strict(write_file("00.json", data))
    values = {"mid": "opt_a"}  # far unset -> mid itself evaluates hidden
    assert catalog.visible_now("mid", values) is False
    assert catalog.visible_now("dep", values) is True  # one hop only


def test_unknown_group_query_raises(write_file):
    catalog = _catalog(write_file, {"group": "ref", "any": True})
    with pytest.raises(KeyError):
        catalog.visible_now("no_such_group", {})
