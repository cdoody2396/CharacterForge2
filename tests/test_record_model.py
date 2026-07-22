"""N1 record file shape: creation, atomic writes, load/save round-trip,
strict load surface (no nulls, no unknown keys, versioning laws), and the
no-mutation-API immutability of committed versions."""

import dataclasses
import json

import pytest

from app.record import CharacterRecord, load_record, save_record
from app.record.errors import RecordFormatError
from tests.conftest import new_record, record_catalog


def _finalized_record(catalog):
    record = new_record()
    record.set_selection(catalog, "species", "cat")
    record.set_selection(catalog, "mane", "long_mane")
    record.set_selection(catalog, "callname", "soft")
    record.set_name("Mara")
    record.finalize(catalog)
    return record


def _saved_dict(record, tmp_path):
    path = tmp_path / "char.json"
    save_record(record, path)
    return json.loads(path.read_text(encoding="utf-8")), path


def _refuse_load(tmp_path, catalog, data, code):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(RecordFormatError) as excinfo:
        load_record(path, catalog)
    assert excinfo.value.code == code, excinfo.value
    return excinfo.value


def test_create_shape(tmp_path):
    record = new_record("aria", 30)
    assert record.character_id == "aria"
    assert record.age == 30
    assert record.rating == "standard"  # the floor; it only moves up
    assert record.active_version is None
    assert record.identity_versions == []
    assert record.draft is not None and record.draft.selections == {}
    assert record.persona.name is None
    assert isinstance(record.created, str) and record.created


def test_create_refuses_bad_character_id():
    with pytest.raises(RecordFormatError):
        CharacterRecord.create("", 25)


def test_round_trip(tmp_path):
    catalog = record_catalog(tmp_path)
    record = _finalized_record(catalog)
    record.set_selection(catalog, "traits", ["brave", "shy"])
    path = tmp_path / "char.json"
    save_record(record, path)
    loaded, orphans = load_record(path, catalog)
    assert orphans == []
    assert loaded.character_id == record.character_id
    assert loaded.age == record.age
    assert loaded.rating == record.rating
    assert loaded.created == record.created
    assert loaded.active_version == 1
    assert loaded.draft is None
    assert loaded.persona.name == "Mara"
    assert loaded.persona.name_safety == "pending"
    assert loaded.persona.selections == {"callname": "soft", "traits": ["brave", "shy"]}
    v1 = loaded.identity_versions[0]
    assert v1.version == 1
    assert v1.selections == {"species": "cat", "mane": "long_mane"}
    assert v1.appearance_paragraph == record.identity_versions[0].appearance_paragraph
    assert v1.finalized == record.identity_versions[0].finalized


def test_saved_shape_keys(tmp_path):
    catalog = record_catalog(tmp_path)
    data, _ = _saved_dict(_finalized_record(catalog), tmp_path)
    assert data["format"] == 1
    assert set(data) == {
        "format",
        "character_id",
        "age",
        "rating",
        "created",
        "active_version",
        "identity_versions",
        "persona",
    }  # no draft after finalize; no nulls serialized anywhere
    assert "null" not in json.dumps(data)


def test_atomic_write_failure_leaves_original(tmp_path, monkeypatch):
    catalog = record_catalog(tmp_path)
    record = _finalized_record(catalog)
    path = tmp_path / "char.json"
    save_record(record, path)
    before = path.read_text(encoding="utf-8")

    import app.record.model as model_mod

    def boom(src, dst):
        raise OSError("disk gone")

    monkeypatch.setattr(model_mod.os, "replace", boom)
    record.set_name("Newname")
    with pytest.raises(OSError):
        save_record(record, path)
    assert path.read_text(encoding="utf-8") == before  # untouched (N1 atomic)


def test_load_refuses_null_anywhere(tmp_path):
    catalog = record_catalog(tmp_path)
    data, _ = _saved_dict(_finalized_record(catalog), tmp_path)
    data["identity_versions"][0]["selections"]["species"] = None
    _refuse_load(tmp_path, catalog, data, "RECORD_NULL")


def test_load_refuses_unknown_key(tmp_path):
    catalog = record_catalog(tmp_path)
    data, _ = _saved_dict(_finalized_record(catalog), tmp_path)
    data["persona"]["mood_ring"] = "blue"
    _refuse_load(tmp_path, catalog, data, "RECORD_UNKNOWN_KEY")


def test_load_ignores_comment_keys(tmp_path):
    catalog = record_catalog(tmp_path)
    data, _ = _saved_dict(_finalized_record(catalog), tmp_path)
    data["_note"] = "hand annotation"
    data["persona"]["_note"] = "also fine"
    path = tmp_path / "annotated.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    loaded, orphans = load_record(path, catalog)
    assert orphans == []
    assert loaded.persona.name == "Mara"


def test_load_refuses_session_home_value(tmp_path):
    catalog = record_catalog(tmp_path)
    data, _ = _saved_dict(_finalized_record(catalog), tmp_path)
    data["persona"]["selections"]["mood"] = "happy"
    _refuse_load(tmp_path, catalog, data, "SESSION_HOME_VALUE")


def test_load_refuses_noncontiguous_versions(tmp_path):
    catalog = record_catalog(tmp_path)
    data, _ = _saved_dict(_finalized_record(catalog), tmp_path)
    data["identity_versions"][0]["version"] = 3
    data["active_version"] = 3
    _refuse_load(tmp_path, catalog, data, "RECORD_BAD_VERSIONING")


def test_load_refuses_dangling_active_pointer(tmp_path):
    catalog = record_catalog(tmp_path)
    data, _ = _saved_dict(_finalized_record(catalog), tmp_path)
    data["active_version"] = 2
    _refuse_load(tmp_path, catalog, data, "RECORD_BAD_VERSIONING")


def test_load_refuses_versions_without_active_pointer(tmp_path):
    catalog = record_catalog(tmp_path)
    data, _ = _saved_dict(_finalized_record(catalog), tmp_path)
    del data["active_version"]
    _refuse_load(tmp_path, catalog, data, "RECORD_BAD_VERSIONING")


def test_load_refuses_name_without_safety_flag(tmp_path):
    catalog = record_catalog(tmp_path)
    data, _ = _saved_dict(_finalized_record(catalog), tmp_path)
    del data["persona"]["name_safety"]
    _refuse_load(tmp_path, catalog, data, "RECORD_BAD_TYPE")


def test_load_refuses_out_of_law_age(tmp_path):
    catalog = record_catalog(tmp_path)
    data, _ = _saved_dict(_finalized_record(catalog), tmp_path)
    data["age"] = 19
    _refuse_load(tmp_path, catalog, data, "AGE_UNDER_FLOOR")


def test_committed_versions_are_frozen(tmp_path):
    catalog = record_catalog(tmp_path)
    record = _finalized_record(catalog)
    v1 = record.identity_versions[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        v1.appearance_paragraph = "rewritten history"
    # And no CharacterRecord method takes a committed version as a target:
    # the only identity mutations are draft-routed (proven across the gate
    # tests); here we prove the draft copy is deep — editing it cannot
    # reach committed state.
    record.open_draft()
    record.set_selection(catalog, "species", "wolf")
    assert record.identity_versions[0].selections["species"] == "cat"
