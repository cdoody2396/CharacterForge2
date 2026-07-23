"""Shared test helpers.

Committed .json data files live ONLY under tests/fixtures/ (spec §0).
Refusal variants are composed programmatically into tmp_path with neutral
ids; ``example_`` ids appear only where a test proves the example guard.
"""

import json
from pathlib import Path

import pytest

from app.options import load_catalog
from app.options.errors import CatalogError, OptionFormatError

FIXTURES = Path(__file__).parent / "fixtures"


def load_strict(directory):
    return load_catalog([directory], strict=True)


def refuse(directory, code):
    """Assert a strict load refuses with the given per-file error code."""
    with pytest.raises(OptionFormatError) as excinfo:
        load_catalog([directory], strict=True)
    assert excinfo.value.code == code, excinfo.value
    return excinfo.value


def refuse_catalog(directory, code):
    """Assert a strict load refuses with the given catalog-law code (§7 /
    merged-state checks raise CatalogError after all files merge)."""
    with pytest.raises(CatalogError) as excinfo:
        load_catalog([directory], strict=True)
    codes = [r.code for r in excinfo.value.records]
    assert code in codes, f"expected {code} in {codes}"
    return excinfo.value


@pytest.fixture
def write_file(tmp_path):
    """Write one JSON option file into a per-test data directory and return
    the directory. Call repeatedly for multi-file merge scenarios; files
    load in filename order, so name them 00_*.json, 10_*.json, ..."""

    def _write(name: str, obj, *, encoding: str = "utf-8") -> Path:
        path = tmp_path / name
        path.write_text(json.dumps(obj), encoding=encoding)
        return tmp_path

    return _write


def minimal_file(**overrides):
    """A minimal valid option file (one pick_one group, one option) built
    from neutral ids. Keyword overrides replace top-level keys."""
    data = {
        "format": 1,
        "rating": "standard",
        "groups": [
            {
                "id": "g1",
                "label": "G1",
                "kind": "pick_one",
                "home": "identity",
                "options": [{"id": "opt_a", "label": "A"}],
            }
        ],
    }
    data.update(overrides)
    return data


def group(**overrides):
    """A minimal valid pick_one group dict; overrides replace keys.
    Pass e.g. options=[...] or kind="pick_many"."""
    data = {
        "id": "g1",
        "label": "G1",
        "kind": "pick_one",
        "home": "identity",
        "options": [{"id": "opt_a", "label": "A"}],
    }
    data.update(overrides)
    return data


def free_text_group(**overrides):
    """A minimal valid free_text group dict."""
    data = {
        "id": "ft1",
        "label": "FT1",
        "kind": "free_text",
        "home": "identity",
        "feeds": "both",
        "max_chars": 240,
    }
    data.update(overrides)
    return data


# --- record-layer test catalog (O3) ----------------------------------------
# Composed programmatically per §0 (no committed data outside fixtures).
# Exercises every gate-relevant shape: required (always-visible and
# tag-conditional, both homes), visibility chains, retired options, a
# pick_many cap, a session-home group, a free_text slot, an explicit-rated
# file for the rating gate.

RECORD_STD_FILE = {
    "format": 1,
    "rating": "standard",
    "groups": [
        {
            "id": "species",
            "label": "Species",
            "kind": "pick_one",
            "home": "identity",
            "required": True,
            "options": [
                {"id": "cat", "label": "Cat", "tags": ["furred"]},
                {"id": "wolf", "label": "Wolf", "tags": ["furred"]},
                {"id": "robot", "label": "Robot"},
            ],
        },
        {
            "id": "mane",
            "label": "Mane",
            "kind": "pick_one",
            "home": "identity",
            "required": True,
            "visible_when": {"group": "species", "has_tag": "furred"},
            "options": [
                {"id": "short_mane", "label": "Short Mane"},
                {"id": "long_mane", "label": "Long Mane"},
            ],
        },
        {
            "id": "fur_color",
            "label": "Fur Color",
            "kind": "pick_one",
            "home": "identity",
            "visible_when": {"group": "species", "has_tag": "furred"},
            "options": [
                {"id": "red", "label": "Red"},
                {"id": "blue", "label": "Blue"},
            ],
        },
        {
            "id": "old_look",
            "label": "Old Look",
            "kind": "pick_many",
            "home": "identity",
            "options": [
                {"id": "current", "label": "Current"},
                {"id": "legacy", "label": "Legacy", "status": "retired"},
                {"id": "extra", "label": "Extra"},
            ],
        },
        {
            "id": "traits",
            "label": "Traits",
            "kind": "pick_many",
            "home": "persona",
            "max_picks": 2,
            "options": [
                {"id": "brave", "label": "Brave"},
                {"id": "shy", "label": "Shy"},
                {"id": "calm", "label": "Calm"},
            ],
        },
        {
            "id": "callname",
            "label": "Callname",
            "kind": "pick_one",
            "home": "persona",
            "required": True,
            "options": [
                {"id": "soft", "label": "Soft"},
                {"id": "loud", "label": "Loud"},
            ],
        },
        {
            "id": "purr",
            "label": "Purr",
            "kind": "pick_one",
            "home": "persona",
            "visible_when": {"group": "species", "has_tag": "furred"},
            "options": [
                {"id": "quiet", "label": "Quiet"},
                {"id": "rumbling", "label": "Rumbling"},
            ],
        },
        {
            "id": "mood",
            "label": "Mood",
            "kind": "pick_one",
            "home": "session",
            "options": [
                {"id": "happy", "label": "Happy"},
                {"id": "sad", "label": "Sad"},
            ],
        },
        {
            "id": "looks",
            "label": "Looks",
            "kind": "free_text",
            "home": "identity",
            "feeds": "both",
            "max_chars": 240,
        },
    ],
}

RECORD_EXPLICIT_FILE = {
    "format": 1,
    "rating": "explicit",
    "groups": [
        {
            "id": "kink",
            "label": "Kink",
            "kind": "pick_one",
            "home": "persona",
            "options": [{"id": "k1", "label": "K1"}],
        }
    ],
}


def record_catalog_dir(tmp_path):
    """Write the record-test catalog files into ``tmp_path/options`` and
    return that directory (tests strict-load it themselves; orphan tests
    remove/restore individual files)."""
    directory = tmp_path / "options"
    directory.mkdir(exist_ok=True)
    (directory / "00_std.json").write_text(
        json.dumps(RECORD_STD_FILE), encoding="utf-8"
    )
    (directory / "90_explicit.json").write_text(
        json.dumps(RECORD_EXPLICIT_FILE), encoding="utf-8"
    )
    return directory


def record_catalog(tmp_path):
    return load_strict(record_catalog_dir(tmp_path))


def new_record(character_id="test_char", age=25):
    from app.record import CharacterRecord

    return CharacterRecord.create(character_id, age)


# --- safety-layer test filter (O4) ------------------------------------------

SAFETY_DATA_DIR = Path(__file__).parent.parent / "app" / "safety" / "data"


@pytest.fixture(scope="session")
def content_filter():
    """One SafetyFilter over the REAL maintained word data (§I transplant
    fidelity: the vector tables run against what actually ships). Session
    scoped — compiling the term sets is the expensive part."""
    from app.safety import SafetyFilter

    return SafetyFilter(SAFETY_DATA_DIR)


def refuse_safety_data(data_dir, code):
    """Assert SafetyFilter refuses to start over ``data_dir`` with the
    given §C code (the filter never starts over a bad data directory)."""
    from app.safety import SafetyDataError, SafetyFilter

    with pytest.raises(SafetyDataError) as excinfo:
        SafetyFilter(data_dir)
    assert excinfo.value.code == code, excinfo.value
    return excinfo.value


def refuse_gate(code, fn, *args, **kwargs):
    """Assert a record mutation refuses with the given gate code and, when
    a record is passed as the bound method's owner, leaves it unchanged."""
    from app.record.errors import GateRefusal

    with pytest.raises(GateRefusal) as excinfo:
        fn(*args, **kwargs)
    assert excinfo.value.code == code, excinfo.value
    return excinfo.value
