"""Shared test helpers.

Committed .json data files live ONLY under tests/fixtures/ (spec §0).
Refusal variants are composed programmatically into tmp_path with neutral
ids; ``example_`` ids appear only where a test proves the example guard.
"""

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


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
