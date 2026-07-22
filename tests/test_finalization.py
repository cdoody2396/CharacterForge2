"""N5 finalization gate and commit mechanics: all of N4 over the whole
character, required-when-visible across BOTH layers, draft → v(n+1)
verbatim, paragraph drafted, stamp set, pointer moves."""

import json

import pytest

from app.record import load_record, save_record
from tests.conftest import new_record, record_catalog, refuse_gate


@pytest.fixture
def catalog(tmp_path):
    return record_catalog(tmp_path)


def _whole(catalog, record=None):
    record = record or new_record()
    record.set_selection(catalog, "species", "cat")
    record.set_selection(catalog, "mane", "long_mane")
    record.set_selection(catalog, "callname", "soft")
    return record


def test_finalize_without_draft_refused(catalog):
    record = _whole(catalog)
    record.finalize(catalog)
    refuse_gate("NO_DRAFT", record.finalize, catalog)


def test_required_identity_group_unfilled_refused(catalog):
    record = new_record()
    record.set_selection(catalog, "callname", "soft")
    exc = refuse_gate("REQUIRED_GROUP_UNFILLED", record.finalize, catalog)
    assert exc.subject == "species"


def test_required_persona_group_checked_too(catalog):
    # N5: across BOTH layers — a character must be whole to finalize.
    record = new_record()
    record.set_selection(catalog, "species", "cat")
    record.set_selection(catalog, "mane", "long_mane")
    exc = refuse_gate("REQUIRED_GROUP_UNFILLED", record.finalize, catalog)
    assert exc.subject == "callname"


def test_required_only_when_visible(catalog):
    # mane is required but hidden for a robot — a hidden required group
    # does not block (required-when-visible, N3/N5).
    record = new_record()
    record.set_selection(catalog, "species", "robot")
    record.set_selection(catalog, "callname", "soft")
    version = record.finalize(catalog)
    assert version.version == 1


def test_required_revealed_by_tag_blocks(catalog):
    record = new_record()
    record.set_selection(catalog, "species", "wolf")
    record.set_selection(catalog, "callname", "soft")
    exc = refuse_gate("REQUIRED_GROUP_UNFILLED", record.finalize, catalog)
    assert exc.subject == "mane"


def test_inert_hidden_value_blocks_finalize_until_cleared(catalog):
    # The other half of gate decision 3: allow-inert on mutation, refuse at
    # finalization until the stale value is cleared.
    record = _whole(catalog)
    record.set_selection(catalog, "fur_color", "red")
    record.set_selection(catalog, "species", "robot")  # hides fur_color+mane
    exc = refuse_gate("HIDDEN_GROUP_VALUE", record.finalize, catalog)
    record.clear_selection(catalog, "fur_color")
    record.clear_selection(catalog, "mane")
    version = record.finalize(catalog)
    assert version.version == 1


def test_first_finalization_creates_v1(catalog):
    record = _whole(catalog)
    version = record.finalize(catalog)
    assert version.version == 1
    assert record.active_version == 1
    assert record.draft is None
    assert isinstance(version.finalized, str) and version.finalized
    assert version.selections == {"species": "cat", "mane": "long_mane"}
    assert "Cat" in version.appearance_paragraph  # drafted from labels (N7)


def test_draft_commits_verbatim_and_deep(catalog):
    record = _whole(catalog)
    draft_selections = dict(record.draft.selections)
    record.finalize(catalog)
    assert record.identity_versions[0].selections == draft_selections


def test_refinalization_appends_and_moves_pointer(catalog):
    record = _whole(catalog)
    record.finalize(catalog)
    v1 = record.identity_versions[0]
    record.open_draft()
    record.set_selection(catalog, "fur_color", "blue")
    v2 = record.finalize(catalog)
    assert v2.version == 2
    assert record.active_version == 2
    assert len(record.identity_versions) == 2
    # v1 untouched — versions are immutable, history never rewrites
    assert record.identity_versions[0] is v1
    assert "fur_color" not in v1.selections


def test_paragraph_redrafts_on_refinalize(catalog):
    record = _whole(catalog)
    record.finalize(catalog)
    p1 = record.identity_versions[0].appearance_paragraph
    record.open_draft()
    record.set_selection(catalog, "fur_color", "blue")
    record.finalize(catalog)
    p2 = record.identity_versions[1].appearance_paragraph
    assert p1 != p2
    assert "Blue" in p2 and "Blue" not in p1


def test_open_draft_copies_active_version(catalog):
    record = _whole(catalog)
    record.finalize(catalog)
    record.open_draft()
    assert record.draft.selections == record.identity_versions[0].selections
    record.set_selection(catalog, "species", "wolf")
    assert record.identity_versions[0].selections["species"] == "cat"


def test_open_draft_twice_refused(catalog):
    record = _whole(catalog)
    record.finalize(catalog)
    record.open_draft()
    refuse_gate("DRAFT_ALREADY_OPEN", record.open_draft)


def test_finalize_with_orphaned_draft_value_refused(catalog, tmp_path):
    # An orphan (file removed) loads fine but cannot finalize — N4's
    # unknown-id law over the full state; restore the file to be whole.
    record = _whole(catalog)
    record.set_selection(catalog, "fur_color", "red")
    path = tmp_path / "char.json"
    save_record(record, path)
    shrunk_dir = tmp_path / "shrunk"
    shrunk_dir.mkdir()
    src = json.loads(
        (tmp_path / "options" / "00_std.json").read_text(encoding="utf-8")
    )
    src["groups"] = [g for g in src["groups"] if g["id"] != "fur_color"]
    (shrunk_dir / "00_std.json").write_text(json.dumps(src), encoding="utf-8")
    from app.options import load_catalog

    shrunk = load_catalog([shrunk_dir], strict=True)
    loaded, orphans = load_record(path, shrunk)
    assert [e.group_id for e in orphans] == ["fur_color"]
    refuse_gate("UNKNOWN_GROUP", loaded.finalize, shrunk)


def test_finalize_leaves_record_unchanged_on_refusal(catalog):
    record = new_record()
    record.set_selection(catalog, "species", "cat")
    refuse_gate("REQUIRED_GROUP_UNFILLED", record.finalize, catalog)
    assert record.active_version is None
    assert record.identity_versions == []
    assert record.draft is not None  # still open, still editable
