"""§7 catalog-level laws: two-slot law, example guard, and the §4 priority
law on the MERGED group (checked after all files merge; strict raises
CatalogError, resilient records)."""

from conftest import (
    FIXTURES,
    free_text_group,
    group,
    load_strict,
    minimal_file,
    refuse_catalog,
)

from app.options import errors as E


# --- §7.1 two-slot law -----------------------------------------------------


def test_refuses_two_identity_free_text_slots(write_file):
    d = write_file(
        "00.json",
        minimal_file(
            groups=[
                free_text_group(id="ft_one", home="identity"),
                free_text_group(id="ft_two", home="identity"),
            ]
        ),
    )
    err = refuse_catalog(d, E.TWO_SLOT_LAW)
    assert any(r.subject == "ft_two" for r in err.records)


def test_refuses_two_persona_free_text_slots(write_file):
    d = write_file(
        "00.json",
        minimal_file(
            groups=[
                free_text_group(id="ft_one", home="persona"),
                free_text_group(id="ft_two", home="persona"),
            ]
        ),
    )
    refuse_catalog(d, E.TWO_SLOT_LAW)


def test_two_slot_law_applies_across_files(write_file):
    write_file(
        "00.json", minimal_file(groups=[free_text_group(id="ft_one", home="identity")])
    )
    d = write_file(
        "10.json", minimal_file(groups=[free_text_group(id="ft_two", home="identity")])
    )
    refuse_catalog(d, E.TWO_SLOT_LAW)


# --- §7.2 / §0 example guard ----------------------------------------------


def test_refuses_example_group_and_option_ids():
    # The committed fixture is the ONLY legal home for example_ ids (§0);
    # loading it as data must refuse both the group id and the option id.
    err = refuse_catalog(FIXTURES / "example_guard", E.EXAMPLE_ID_IN_DATA)
    subjects = {r.subject for r in err.records if r.code == E.EXAMPLE_ID_IN_DATA}
    assert subjects == {"example_group", "fx_group/example_option"}


def test_example_guard_names_file_and_id():
    err = refuse_catalog(FIXTURES / "example_guard", E.EXAMPLE_ID_IN_DATA)
    rec = next(r for r in err.records if r.subject == "example_group")
    assert rec.file == "10_example_ids.json"
    assert "example_group" in rec.message


# --- empty pick groups (O2_INPUTS answer 8.1) ------------------------------


def test_refuses_empty_pick_group(write_file):
    # Zero options DEFINED after merge is a catalog error, replacing O1's
    # derives-hidden — hidden would vanish a group silently.
    d = write_file("00.json", minimal_file(groups=[group(options=[])]))
    err = refuse_catalog(d, E.EMPTY_PICK_GROUP)
    assert any(r.subject == "g1" for r in err.records)


def test_refuses_empty_pick_many_group(write_file):
    d = write_file(
        "00.json", minimal_file(groups=[group(kind="pick_many", options=[])])
    )
    refuse_catalog(d, E.EMPTY_PICK_GROUP)


def test_all_retired_group_is_not_empty(write_file):
    # "Empty" means zero options DEFINED; all-retired still derives hidden
    # and is NOT a catalog error.
    d = write_file(
        "00.json",
        minimal_file(
            groups=[
                group(options=[{"id": "opt_old", "label": "Old", "status": "retired"}])
            ]
        ),
    )
    catalog = load_strict(d)
    assert catalog.errors == []
    assert catalog.get("g1").hidden is True


def test_empty_base_filled_by_extension_loads(write_file):
    # The law reads the MERGED group: a base declared empty is legal once a
    # later file appends options.
    write_file("00_base.json", minimal_file(groups=[group(options=[])]))
    d = write_file(
        "10_ext.json",
        {
            "format": 1,
            "rating": "standard",
            "groups": [{"id": "g1", "options": [{"id": "opt_a", "label": "A"}]}],
        },
    )
    catalog = load_strict(d)
    assert [o.id for o in catalog.get("g1").options] == ["opt_a"]


# --- §4 priority law on the merged group ----------------------------------


def test_refuses_priority_without_image_text(write_file):
    # A priority with nothing to prioritize is a latent lie (Decision 3).
    d = write_file(
        "00.json", minimal_file(groups=[group(priority="must")])
    )
    refuse_catalog(d, E.PRIORITY_WITHOUT_IMAGE_TEXT)


def test_refuses_image_text_without_priority(write_file):
    d = write_file(
        "00.json",
        minimal_file(
            groups=[
                group(options=[{"id": "opt_a", "label": "A", "image_text": "a"}])
            ]
        ),
    )
    refuse_catalog(d, E.IMAGE_TEXT_WITHOUT_PRIORITY)


def test_priority_with_image_text_loads(write_file):
    d = write_file(
        "00.json",
        minimal_file(
            groups=[
                group(
                    priority="flavor",
                    options=[{"id": "opt_a", "label": "A", "image_text": "a"}],
                )
            ]
        ),
    )
    assert load_strict(d).get("g1").priority == "flavor"


def test_priority_law_evaluates_the_merged_group(write_file):
    # Base group is legal alone; a later file adds an image_text option
    # without adding priority -> the MERGED group violates the law.
    write_file("00_base.json", minimal_file())
    d = write_file(
        "10_ext.json",
        {
            "format": 1,
            "rating": "standard",
            "groups": [
                {"id": "g1", "options": [{"id": "opt_b", "label": "B", "image_text": "b"}]}
            ],
        },
    )
    refuse_catalog(d, E.IMAGE_TEXT_WITHOUT_PRIORITY)


def test_priority_satisfied_across_files_loads(write_file):
    write_file("00_base.json", minimal_file())
    d = write_file(
        "10_ext.json",
        {
            "format": 1,
            "rating": "standard",
            "groups": [
                {
                    "id": "g1",
                    "priority": "should",
                    "options": [
                        {"id": "opt_b", "label": "B", "image_text": "b"}
                    ],
                }
            ],
        },
    )
    assert load_strict(d).get("g1").priority == "should"
