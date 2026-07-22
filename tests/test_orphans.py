"""N9 orphan report: at record load against the live catalog, unknown ids
are listed per character; the record still loads; orphaned picks stay
written but inert — restore the file and the character is whole."""

import json

import pytest

from app.options import load_catalog
from app.record import load_record, save_record
from app.record.errors import GateRefusal
from tests.conftest import (
    RECORD_EXPLICIT_FILE,
    new_record,
    record_catalog_dir,
)


@pytest.fixture
def env(tmp_path):
    """A saved whole record + its catalog directory (files removable)."""
    directory = record_catalog_dir(tmp_path)
    catalog = load_catalog([directory], strict=True)
    record = new_record()
    record.raise_rating("explicit")
    record.set_selection(catalog, "species", "cat")
    record.set_selection(catalog, "mane", "long_mane")
    record.set_selection(catalog, "fur_color", "red")
    record.set_selection(catalog, "callname", "soft")
    record.set_selection(catalog, "kink", "k1")  # lives in 90_explicit.json
    record.finalize(catalog)
    record.open_draft()
    path = tmp_path / "char.json"
    save_record(record, path)
    return directory, path


def test_no_orphans_against_the_full_catalog(env):
    directory, path = env
    catalog = load_catalog([directory], strict=True)
    _, orphans = load_record(path, catalog)
    assert orphans == []


def test_removed_file_orphans_listed_record_still_loads(env):
    directory, path = env
    removed = directory / "90_explicit.json"
    removed.unlink()  # the temporarily-removed drop-in
    catalog = load_catalog([directory], strict=True)
    record, orphans = load_record(path, catalog)
    # listed per character, with location — kink was persona-home
    assert [(e.location, e.group_id, e.option_id, e.reason) for e in orphans] == [
        ("persona", "kink", None, "UNKNOWN_GROUP")
    ]
    # still written (inert), not silently dropped
    assert record.persona.selections["kink"] == "k1"


def test_unknown_option_id_is_an_option_level_orphan(env, tmp_path):
    directory, path = env
    data = json.loads(path.read_text(encoding="utf-8"))
    data["identity_versions"][0]["selections"]["fur_color"] = "chartreuse"
    data["draft_identity"]["selections"]["fur_color"] = "chartreuse"
    path.write_text(json.dumps(data), encoding="utf-8")
    catalog = load_catalog([directory], strict=True)
    record, orphans = load_record(path, catalog)
    assert {(e.location, e.group_id, e.option_id) for e in orphans} == {
        ("identity_versions[v1]", "fur_color", "chartreuse"),
        ("draft_identity", "fur_color", "chartreuse"),
    }
    assert all(e.reason == "UNKNOWN_OPTION" for e in orphans)


def test_orphaned_pick_is_inert_not_writable(env):
    directory, path = env
    (directory / "90_explicit.json").unlink()
    catalog = load_catalog([directory], strict=True)
    record, orphans = load_record(path, catalog)
    assert orphans
    # inert: the gate refuses NEW writes to the unknown group…
    with pytest.raises(GateRefusal) as excinfo:
        record.set_selection(catalog, "kink", "k1")
    assert excinfo.value.code == "UNKNOWN_GROUP"
    # …and unrelated mutations keep working (per-write gate)
    record.set_selection(catalog, "traits", ["brave"])
    assert record.persona.selections["traits"] == ["brave"]


def test_restore_the_file_and_the_character_is_whole(env):
    directory, path = env
    removed = directory / "90_explicit.json"
    removed.unlink()
    catalog = load_catalog([directory], strict=True)
    _, orphans = load_record(path, catalog)
    assert orphans
    # restore — Decision 6 pt 3: nothing was destroyed in the meantime
    removed.write_text(json.dumps(RECORD_EXPLICIT_FILE), encoding="utf-8")
    catalog = load_catalog([directory], strict=True)
    record, orphans = load_record(path, catalog)
    assert orphans == []
    record.set_selection(catalog, "kink", "k1")  # fully functional again
    record.finalize(catalog)  # and finalizable
