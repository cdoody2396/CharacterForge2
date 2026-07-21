"""§3 file model: one JSON object, format/rating/groups, BOM, comment keys,
unknown-key strictness (§1.9)."""

import json

from conftest import load_strict, minimal_file, refuse

from app.options import errors as E


def test_minimal_valid_file(write_file):
    d = write_file("00_min.json", minimal_file())
    catalog = load_strict(d)
    assert catalog.group_ids() == ["g1"]
    g = catalog.get("g1")
    assert g.kind == "pick_one"
    assert g.home == "identity"
    assert [o.id for o in g.options] == ["opt_a"]
    assert g.rating == "standard"
    assert g.options[0].rating == "standard"  # Decision 5: the file is the mark
    assert catalog.errors == []


def test_bom_file_loads(tmp_path):
    path = tmp_path / "00_bom.json"
    path.write_text(json.dumps(minimal_file()), encoding="utf-8-sig")
    catalog = load_strict(tmp_path)
    assert catalog.group_ids() == ["g1"]


def test_comment_keys_ignored_everywhere(write_file):
    data = minimal_file()
    data["_note"] = "file-level provenance"
    data["groups"][0]["_note"] = "group-level"
    data["groups"][0]["options"][0]["_note"] = "option-level"
    d = write_file("00_notes.json", data)
    catalog = load_strict(d)
    assert catalog.group_ids() == ["g1"]


def test_non_json_files_are_not_scanned(write_file, tmp_path):
    (tmp_path / "README.md").write_text("ships empty by design", encoding="utf-8")
    d = write_file("00_min.json", minimal_file())
    assert load_strict(d).group_ids() == ["g1"]


def test_refuses_unknown_top_level_key(write_file):
    d = write_file("00_bad.json", minimal_file(extra="nope"))
    err = refuse(d, E.UNKNOWN_KEY)
    assert "00_bad.json" in str(err)


def test_refuses_missing_format(write_file):
    data = minimal_file()
    del data["format"]
    refuse(write_file("00_bad.json", data), E.MISSING_KEY)


def test_refuses_wrong_format_version(write_file):
    refuse(write_file("00_bad.json", minimal_file(format=2)), E.BAD_FORMAT_VERSION)


def test_refuses_non_integer_format(write_file):
    refuse(write_file("00_bad.json", minimal_file(format=True)), E.BAD_FORMAT_VERSION)


def test_refuses_missing_rating(write_file):
    data = minimal_file()
    del data["rating"]
    refuse(write_file("00_bad.json", data), E.MISSING_KEY)


def test_refuses_unknown_rating(write_file):
    refuse(write_file("00_bad.json", minimal_file(rating="adult")), E.BAD_RATING)


def test_refuses_missing_groups(write_file):
    data = minimal_file()
    del data["groups"]
    refuse(write_file("00_bad.json", data), E.MISSING_KEY)


def test_refuses_groups_not_a_list(write_file):
    refuse(write_file("00_bad.json", minimal_file(groups={})), E.BAD_KEY_TYPE)


def test_refuses_file_not_an_object(tmp_path):
    (tmp_path / "00_bad.json").write_text("[]", encoding="utf-8")
    refuse(tmp_path, E.NOT_AN_OBJECT)


def test_refuses_invalid_json(tmp_path):
    (tmp_path / "00_bad.json").write_text("{not json", encoding="utf-8")
    refuse(tmp_path, E.INVALID_JSON)
