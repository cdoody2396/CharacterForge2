"""§5 option keys: id hygiene, status/retired semantics, color, unknown keys."""

from conftest import group, load_strict, refuse

from app.options import errors as E


def _file_with_options(options):
    return {"format": 1, "rating": "standard", "groups": [group(options=options)]}


def test_refuses_unknown_option_key(write_file):
    d = write_file(
        "00.json", _file_with_options([{"id": "opt_a", "label": "A", "prompt": "x"}])
    )
    refuse(d, E.UNKNOWN_KEY)


def test_refuses_missing_option_id(write_file):
    refuse(write_file("00.json", _file_with_options([{"label": "A"}])), E.MISSING_KEY)


def test_refuses_missing_option_label(write_file):
    refuse(write_file("00.json", _file_with_options([{"id": "opt_a"}])), E.MISSING_KEY)


def test_refuses_uppercase_option_id(write_file):
    d = write_file("00.json", _file_with_options([{"id": "Opt_A", "label": "A"}]))
    refuse(d, E.BAD_OPTION_ID)


def test_refuses_option_id_with_illegal_chars(write_file):
    d = write_file("00.json", _file_with_options([{"id": "opt-a", "label": "A"}]))
    refuse(d, E.BAD_OPTION_ID)


def test_refuses_option_id_over_40_chars(write_file):
    d = write_file("00.json", _file_with_options([{"id": "a" * 41, "label": "A"}]))
    refuse(d, E.BAD_OPTION_ID)


def test_option_id_exactly_40_chars_loads(write_file):
    oid = "a" * 40
    catalog = load_strict(
        write_file("00.json", _file_with_options([{"id": oid, "label": "A"}]))
    )
    assert catalog.get("g1").resolve(oid) is not None


def test_refuses_unknown_status(write_file):
    d = write_file(
        "00.json", _file_with_options([{"id": "opt_a", "label": "A", "status": "dead"}])
    )
    refuse(d, E.BAD_STATUS)


def test_refuses_bad_color(write_file):
    d = write_file(
        "00.json", _file_with_options([{"id": "opt_a", "label": "A", "color": "red"}])
    )
    refuse(d, E.BAD_COLOR)


def test_valid_color_loads(write_file):
    catalog = load_strict(
        write_file(
            "00.json",
            _file_with_options([{"id": "opt_a", "label": "A", "color": "#c99b6f"}]),
        )
    )
    assert catalog.get("g1").resolve("opt_a").color == "#c99b6f"


def test_refuses_non_string_image_text(write_file):
    d = write_file(
        "00.json", _file_with_options([{"id": "opt_a", "label": "A", "image_text": 1}])
    )
    refuse(d, E.BAD_KEY_TYPE)


def test_texts_absent_is_menu_only(write_file):
    # Decision 3 pt 3: neither text present = menu-only, legal.
    catalog = load_strict(
        write_file("00.json", _file_with_options([{"id": "opt_a", "label": "A"}]))
    )
    opt = catalog.get("g1").resolve("opt_a")
    assert opt.image_text is None
    assert opt.chat_text is None


def test_retired_excluded_from_menu_but_resolvable(write_file):
    # §12 happy path; Decision 6: retired = hidden from new selection, fully
    # functional for existing characters.
    catalog = load_strict(
        write_file(
            "00.json",
            _file_with_options(
                [
                    {"id": "opt_a", "label": "A"},
                    {"id": "opt_old", "label": "Old", "status": "retired"},
                ]
            ),
        )
    )
    g = catalog.get("g1")
    assert [o.id for o in g.menu_options()] == ["opt_a"]
    assert g.resolve("opt_old") is not None
    assert g.resolve("opt_old").retired
    assert g.hidden is False


def test_group_with_all_options_retired_derives_hidden(write_file):
    # §1.7: no group-level status exists; all-retired derives hidden.
    catalog = load_strict(
        write_file(
            "00.json",
            _file_with_options(
                [{"id": "opt_old", "label": "Old", "status": "retired"}]
            ),
        )
    )
    assert catalog.get("g1").hidden is True
