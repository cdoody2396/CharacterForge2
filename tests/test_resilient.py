"""Resilient-mode loading: bad files are skipped whole and recorded on the
catalog; catalog-law violations are recorded too; strict raises instead
(§4). Strict mode is the default for every other test in this suite."""

import pytest
from conftest import free_text_group, group, minimal_file

from app.options import errors as E
from app.options import load_catalog
from app.options.errors import CatalogError, OptionFormatError


def test_resilient_records_bad_file_and_keeps_good(write_file):
    # §12 happy path: resilient multi-file load records the bad file and
    # keeps the good.
    write_file("00_good.json", minimal_file())
    d = write_file("10_bad.json", minimal_file(rating="bogus"))
    catalog = load_catalog([d])
    assert catalog.group_ids() == ["g1"]
    assert len(catalog.errors) == 1
    rec = catalog.errors[0]
    assert rec.file == "10_bad.json"
    assert rec.code == E.BAD_RATING
    assert "10_bad.json" in rec.message


def test_resilient_records_invalid_json(write_file, tmp_path):
    write_file("00_good.json", minimal_file())
    (tmp_path / "10_broken.json").write_text("{not json", encoding="utf-8")
    catalog = load_catalog([tmp_path])
    assert catalog.group_ids() == ["g1"]
    assert [e.code for e in catalog.errors] == [E.INVALID_JSON]


def test_strict_raises_on_bad_file(write_file):
    write_file("00_good.json", minimal_file())
    d = write_file("10_bad.json", minimal_file(rating="bogus"))
    with pytest.raises(OptionFormatError):
        load_catalog([d], strict=True)


def test_resilient_records_catalog_law_violations(write_file):
    d = write_file(
        "00.json",
        minimal_file(
            groups=[
                free_text_group(id="ft_one", home="identity"),
                free_text_group(id="ft_two", home="identity"),
            ]
        ),
    )
    catalog = load_catalog([d])  # resilient: records, does not raise
    assert [e.code for e in catalog.errors] == [E.TWO_SLOT_LAW]
    # §7: "checked after all files merge ... resilient mode records" — the
    # groups themselves remain in the catalog; refusal is the gatekeeper's
    # (strict mode / validator CLI exit 1).
    assert "ft_two" in catalog


def test_strict_raises_catalog_error_for_law_violations(write_file):
    d = write_file(
        "00.json", minimal_file(groups=[group(priority="must")])
    )
    with pytest.raises(CatalogError):
        load_catalog([d], strict=True)


def test_missing_directory_is_skipped(tmp_path, write_file):
    d = write_file("00_good.json", minimal_file())
    catalog = load_catalog([tmp_path / "does_not_exist", d], strict=True)
    assert catalog.group_ids() == ["g1"]


def test_empty_directory_yields_empty_catalog(tmp_path):
    catalog = load_catalog([tmp_path], strict=True)
    assert len(catalog) == 0
    assert catalog.errors == []
