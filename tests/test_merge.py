"""§4 merge/extension semantics (v1 carryover, DECIDED, proven) and atomic
file apply; §7.3 within-file duplicate option ids."""

from conftest import group, load_strict, minimal_file, refuse

from app.options import errors as E
from app.options import load_catalog


def test_merge_extend_appends_and_overrides(write_file):
    write_file("00_base.json", minimal_file())
    write_file(
        "10_ext.json",
        {
            "format": 1,
            "rating": "standard",
            "groups": [
                {
                    "id": "g1",
                    "label": "G1 renamed",
                    "options": [{"id": "opt_b", "label": "B"}],
                }
            ],
        },
    )
    d = write_file("20_more.json", minimal_file(groups=[group(id="g2", label="G2")]))
    catalog = load_strict(d)
    g1 = catalog.get("g1")
    assert [o.id for o in g1.options] == ["opt_a", "opt_b"]  # append
    assert g1.label == "G1 renamed"  # scalar override
    assert g1.kind == "pick_one"  # untouched keys survive
    assert g1.sources == ["00_base.json", "10_ext.json"]
    assert catalog.group_ids() == ["g1", "g2"]


def test_redeclared_option_replaces_in_place(write_file):
    # v1 carryover, kickoff-pinned: later file wins, position kept.
    write_file(
        "00_base.json",
        minimal_file(
            groups=[
                group(
                    options=[
                        {"id": "opt_a", "label": "A"},
                        {"id": "opt_b", "label": "B"},
                    ]
                )
            ]
        ),
    )
    d = write_file(
        "10_ext.json",
        {
            "format": 1,
            "rating": "mature",
            "groups": [
                {"id": "g1", "options": [{"id": "opt_a", "label": "A v2"}]}
            ],
        },
    )
    g1 = load_strict(d).get("g1")
    assert [o.id for o in g1.options] == ["opt_a", "opt_b"]  # position kept
    assert g1.resolve("opt_a").label == "A v2"  # later file wins
    # Decision 5: the replacing option carries ITS file's rating and source.
    assert g1.resolve("opt_a").rating == "mature"
    assert g1.resolve("opt_a").source_file == "10_ext.json"
    assert g1.resolve("opt_b").rating == "standard"
    assert g1.rating == "standard"  # group keeps its defining file's rating


def test_extension_fragment_may_omit_required_keys(write_file):
    # v1 carryover: required keys are enforced at first definition only.
    write_file("00_base.json", minimal_file())
    d = write_file(
        "10_ext.json",
        {
            "format": 1,
            "rating": "standard",
            "groups": [{"id": "g1", "options": [{"id": "opt_b", "label": "B"}]}],
        },
    )
    assert len(load_strict(d).get("g1").options) == 2


def test_refuses_kind_change_on_extension(write_file):
    write_file("00_base.json", minimal_file())
    d = write_file(
        "10_ext.json",
        {
            "format": 1,
            "rating": "standard",
            "groups": [{"id": "g1", "kind": "pick_many"}],
        },
    )
    refuse(d, E.KIND_CHANGED)


def test_refuses_duplicate_option_id_within_one_file(write_file):
    # §7.3: within one file's group list, a repeated option id is a format
    # error at merge time (cross-file re-declaration is dedupe instead).
    d = write_file(
        "00.json",
        minimal_file(
            groups=[
                group(
                    options=[
                        {"id": "opt_a", "label": "A"},
                        {"id": "opt_a", "label": "A again"},
                    ]
                )
            ]
        ),
    )
    refuse(d, E.DUPLICATE_OPTION_ID)


def test_atomicity_second_group_malformed_first_absent(write_file):
    # §12: files apply atomically — a malformed second group leaves ZERO
    # effect from the file, not a half-applied first group.
    d = write_file(
        "00.json",
        minimal_file(
            groups=[
                group(id="good_group"),
                {"id": "bad_group", "label": "Bad"},  # missing kind/home/options
            ]
        ),
    )
    catalog = load_catalog([d])  # resilient
    assert "good_group" not in catalog
    assert "bad_group" not in catalog
    assert len(catalog.errors) == 1
    assert catalog.errors[0].file == "00.json"


def test_atomicity_bad_merge_fragment_leaves_base_untouched(write_file):
    write_file("00_base.json", minimal_file())
    d = write_file(
        "10_ext.json",
        {
            "format": 1,
            "rating": "standard",
            "groups": [
                {"id": "g1", "label": "Changed", "options": [{"id": "opt_b", "label": "B"}]},
                {"id": "g_bad", "kind": "bogus"},
            ],
        },
    )
    catalog = load_catalog([d])  # resilient
    g1 = catalog.get("g1")
    assert g1.label == "G1"  # the extension file had zero effect
    assert [o.id for o in g1.options] == ["opt_a"]
    assert g1.sources == ["00_base.json"]
    assert [e.file for e in catalog.errors] == ["10_ext.json"]


def test_same_file_self_extension_merges(write_file):
    # v1 carryover: a later group dict in the SAME file may extend an earlier
    # one (the staged copy already holds it).
    d = write_file(
        "00.json",
        minimal_file(
            groups=[
                group(),
                {"id": "g1", "options": [{"id": "opt_b", "label": "B"}]},
            ]
        ),
    )
    assert [o.id for o in load_strict(d).get("g1").options] == ["opt_a", "opt_b"]


def test_directory_order_then_filename_order(tmp_path, write_file):
    # §3: directories in given order, filenames sorted within each.
    import json

    d1 = tmp_path / "d1"
    d2 = tmp_path / "d2"
    d1.mkdir()
    d2.mkdir()
    base = minimal_file()
    (d2 / "00_second_dir.json").write_text(
        json.dumps(
            {
                "format": 1,
                "rating": "standard",
                "groups": [{"id": "g1", "label": "From d2"}],
            }
        ),
        encoding="utf-8",
    )
    (d1 / "00_first.json").write_text(json.dumps(base), encoding="utf-8")
    catalog = load_catalog([d1, d2], strict=True)
    assert catalog.get("g1").label == "From d2"  # d2 loads after d1
    assert catalog.get("g1").sources == ["00_first.json", "00_second_dir.json"]
