"""§8 age-band lookup: structure laws (floor 20, contiguity, exactly one
final open band), required image_text, strict file hygiene."""

import json

import pytest
from conftest import FIXTURES

from app.options import errors as E
from app.options import AgeBandFormatError, load_age_bands
from app.options.age_bands import select_band


def _write(tmp_path, bands, *, encoding="utf-8", **extra):
    data = {"format": 1, "bands": bands}
    data.update(extra)
    path = tmp_path / "age_bands.json"
    path.write_text(json.dumps(data), encoding=encoding)
    return path


def _refuse(path, code):
    with pytest.raises(AgeBandFormatError) as excinfo:
        load_age_bands(path)
    assert excinfo.value.code == code, excinfo.value
    return excinfo.value


BANDS = [
    {"min": 20, "max": 29, "image_text": "text_a"},
    {"min": 30, "max": 49, "image_text": "text_b"},
    {"min": 50, "image_text": "text_c"},
]


def test_valid_fixture_loads():
    bands = load_age_bands(FIXTURES / "age_bands" / "valid.json")
    assert [b.min for b in bands] == [20, 30, 50]
    assert bands[-1].max is None


def test_valid_case_and_selection(tmp_path):
    bands = load_age_bands(_write(tmp_path, BANDS))
    assert select_band(bands, 20).image_text == "text_a"
    assert select_band(bands, 29).image_text == "text_a"
    assert select_band(bands, 30).image_text == "text_b"
    assert select_band(bands, 120).image_text == "text_c"  # open band
    assert select_band(bands, 19) is None  # below the floor


def test_bom_tolerated(tmp_path):
    bands = load_age_bands(_write(tmp_path, BANDS, encoding="utf-8-sig"))
    assert len(bands) == 3


def test_comment_keys_ignored(tmp_path):
    bands = [dict(b, _note="harvest provenance") for b in BANDS]
    assert len(load_age_bands(_write(tmp_path, bands, _note="file note"))) == 3


def test_refuses_gap(tmp_path):
    bands = [
        {"min": 20, "max": 29, "image_text": "a"},
        {"min": 31, "image_text": "b"},  # 30 is uncovered
    ]
    _refuse(_write(tmp_path, bands), E.BAND_GAP)


def test_refuses_overlap(tmp_path):
    bands = [
        {"min": 20, "max": 30, "image_text": "a"},
        {"min": 30, "image_text": "b"},  # 30 covered twice
    ]
    _refuse(_write(tmp_path, bands), E.BAND_OVERLAP)


def test_refuses_wrong_floor(tmp_path):
    bands = [{"min": 18, "max": 29, "image_text": "a"}, {"min": 30, "image_text": "b"}]
    _refuse(_write(tmp_path, bands), E.BAND_WRONG_FLOOR)


def test_refuses_two_open_bands(tmp_path):
    bands = [{"min": 20, "image_text": "a"}, {"min": 30, "image_text": "b"}]
    _refuse(_write(tmp_path, bands), E.BAND_OPEN_NOT_LAST)


def test_refuses_no_open_final_band(tmp_path):
    bands = [{"min": 20, "max": 29, "image_text": "a"}]
    _refuse(_write(tmp_path, bands), E.BAND_NO_OPEN_BAND)


def test_refuses_empty_bands(tmp_path):
    # An empty list has no final open band — "exactly one" fails.
    _refuse(_write(tmp_path, []), E.BAND_NO_OPEN_BAND)


def test_refuses_missing_image_text(tmp_path):
    # Kickoff-pinned: image_text is required on every band.
    bands = [{"min": 20, "max": 29, "image_text": "a"}, {"min": 30}]
    _refuse(_write(tmp_path, bands), E.BAND_MISSING_IMAGE_TEXT)


def test_refuses_non_integer_bound(tmp_path):
    bands = [{"min": 20.5, "max": 29, "image_text": "a"}, {"min": 30, "image_text": "b"}]
    _refuse(_write(tmp_path, bands), E.BAND_BAD_BOUND)


def test_refuses_max_below_min(tmp_path):
    bands = [{"min": 20, "max": 19, "image_text": "a"}, {"min": 30, "image_text": "b"}]
    _refuse(_write(tmp_path, bands), E.BAND_BAD_BOUND)


def test_refuses_unknown_band_key(tmp_path):
    bands = [
        {"min": 20, "max": 29, "image_text": "a", "prompt": "x"},
        {"min": 30, "image_text": "b"},
    ]
    _refuse(_write(tmp_path, bands), E.UNKNOWN_KEY)


def test_refuses_unknown_file_key(tmp_path):
    _refuse(_write(tmp_path, BANDS, rating="standard"), E.UNKNOWN_KEY)


def test_refuses_wrong_format_version(tmp_path):
    _refuse(_write(tmp_path, BANDS, format=2), E.BAD_FORMAT_VERSION)


def test_refuses_missing_file(tmp_path):
    _refuse(tmp_path / "age_bands.json", E.BAND_FILE_MISSING)
