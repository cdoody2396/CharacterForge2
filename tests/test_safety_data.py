"""§C declaration laws: every load refusal distinctly, incl. the
minors/slurs hard law. Word-file variants are composed programmatically
into tmp_path (spec §0 stance); the maintained data directory is covered
by test_safety_filter.py's fidelity locks."""

import pytest

from app.safety import errors as E
from app.safety import SafetyFilter
from tests.conftest import refuse_safety_data

PROXIMITY = "#! role: proximity_vocabulary\nnaked\nnude\n"
GOOD_ALWAYS = (
    "#! category: noncon\n#! mode: always\n#! enforcement: floor\nrapeword\n"
)
GOOD_CONTEXTUAL = (
    "#! category: noncon\n#! mode: contextual\n#! enforcement: floor\nforced\n"
)


def write_data(tmp_path, files):
    d = tmp_path / "words"
    d.mkdir(exist_ok=True)
    for name, content in files.items():
        (d / name).write_text(content, encoding="utf-8")
    return d


# --- a legal directory loads -------------------------------------------------


def test_minimal_directory_loads(tmp_path):
    d = write_data(tmp_path, {"list.txt": GOOD_ALWAYS})
    f = SafetyFilter(d)
    assert not f.check("rapeword", "freetext").allowed
    assert f.check("harmless", "freetext").allowed


def test_contextual_with_proximity_loads(tmp_path):
    d = write_data(
        tmp_path,
        {"ctx.txt": GOOD_CONTEXTUAL, "sexual_context.txt": PROXIMITY},
    )
    f = SafetyFilter(d)
    assert not f.check("forced her, naked", "freetext").allowed
    assert f.check("forced to flee her homeland", "freetext").allowed


def test_declaration_lines_are_comments_to_the_term_parser(tmp_path):
    # the v1 line format survives (§C): '#!' never becomes a term.
    d = write_data(tmp_path, {"list.txt": GOOD_ALWAYS})
    assert SafetyFilter(d).check("category", "freetext").allowed


def test_non_txt_files_ignored(tmp_path):
    d = write_data(tmp_path, {"list.txt": GOOD_ALWAYS, "README.md": "notes"})
    SafetyFilter(d)  # does not refuse


# --- the data directory itself ----------------------------------------------


def test_missing_directory_refuses(tmp_path):
    refuse_safety_data(tmp_path / "absent", E.SAFETY_DATA_DIR_INVALID)


def test_empty_directory_refuses(tmp_path):
    d = tmp_path / "words"
    d.mkdir()
    refuse_safety_data(d, E.SAFETY_DATA_DIR_INVALID)


# --- §C law 2: missing / unknown / duplicate declarations --------------------


def test_undeclared_file_refuses(tmp_path):
    d = write_data(tmp_path, {"list.txt": "rapeword\n"})
    refuse_safety_data(d, E.SAFETY_UNDECLARED_FILE)


@pytest.mark.parametrize("dropped", ["category", "mode", "enforcement"])
def test_missing_declaration_refuses(tmp_path, dropped):
    lines = [
        line
        for line in GOOD_ALWAYS.splitlines()
        if not line.startswith(f"#! {dropped}:")
    ]
    d = write_data(tmp_path, {"list.txt": "\n".join(lines) + "\n"})
    refuse_safety_data(d, E.SAFETY_DECLARATION_MISSING)


def test_unknown_declaration_key_refuses(tmp_path):
    d = write_data(
        tmp_path, {"list.txt": "#! severity: high\n" + GOOD_ALWAYS}
    )
    refuse_safety_data(d, E.SAFETY_DECLARATION_UNKNOWN)


def test_duplicate_declaration_refuses(tmp_path):
    d = write_data(
        tmp_path, {"list.txt": GOOD_ALWAYS + "#! category: noncon\n"}
    )
    refuse_safety_data(d, E.SAFETY_DECLARATION_DUPLICATE)


def test_malformed_declaration_line_refuses(tmp_path):
    d = write_data(tmp_path, {"list.txt": "#! floor\n" + GOOD_ALWAYS})
    refuse_safety_data(d, E.SAFETY_DECLARATION_UNKNOWN)


def test_unknown_mode_refuses(tmp_path):
    bad = GOOD_ALWAYS.replace("mode: always", "mode: sometimes")
    d = write_data(tmp_path, {"list.txt": bad})
    refuse_safety_data(d, E.SAFETY_DECLARATION_UNKNOWN)


@pytest.mark.parametrize(
    "value", ["ceiling", "unlocked_at: standard", "unlocked_at: legendary"]
)
def test_unknown_enforcement_refuses(tmp_path, value):
    bad = GOOD_ALWAYS.replace("enforcement: floor", f"enforcement: {value}")
    d = write_data(tmp_path, {"list.txt": bad})
    refuse_safety_data(d, E.SAFETY_DECLARATION_UNKNOWN)


def test_category_must_be_machine_id(tmp_path):
    bad = GOOD_ALWAYS.replace("category: noncon", "category: Non Consent")
    d = write_data(tmp_path, {"list.txt": bad})
    refuse_safety_data(d, E.SAFETY_DECLARATION_UNKNOWN)


# --- §C law 2: contextual needs the proximity vocabulary; literal-only ------


def test_contextual_without_proximity_vocabulary_refuses(tmp_path):
    d = write_data(tmp_path, {"ctx.txt": GOOD_CONTEXTUAL})
    refuse_safety_data(d, E.SAFETY_NO_PROXIMITY_VOCABULARY)


def test_regex_in_contextual_refuses(tmp_path):
    d = write_data(
        tmp_path,
        {
            "ctx.txt": GOOD_CONTEXTUAL + "re: forc(ed|ing)\n",
            "sexual_context.txt": PROXIMITY,
        },
    )
    refuse_safety_data(d, E.SAFETY_REGEX_IN_CONTEXTUAL)


def test_regex_in_proximity_vocabulary_refuses(tmp_path):
    d = write_data(
        tmp_path,
        {
            "ctx.txt": GOOD_CONTEXTUAL,
            "sexual_context.txt": PROXIMITY + "re: nud(e|ity)\n",
        },
    )
    refuse_safety_data(d, E.SAFETY_REGEX_IN_CONTEXTUAL)


# --- §C law 4: the proximity file's own declaration --------------------------


def test_proximity_file_without_role_refuses(tmp_path):
    d = write_data(
        tmp_path,
        {"ctx.txt": GOOD_CONTEXTUAL, "sexual_context.txt": "naked\n"},
    )
    refuse_safety_data(d, E.SAFETY_DECLARATION_MISSING)


def test_proximity_file_with_category_refuses(tmp_path):
    d = write_data(
        tmp_path,
        {
            "ctx.txt": GOOD_CONTEXTUAL,
            "sexual_context.txt": "#! category: sexual\n" + PROXIMITY,
        },
    )
    refuse_safety_data(d, E.SAFETY_DECLARATION_UNKNOWN)


def test_role_on_a_blocklist_file_refuses(tmp_path):
    d = write_data(
        tmp_path,
        {"list.txt": "#! role: proximity_vocabulary\n" + GOOD_ALWAYS},
    )
    refuse_safety_data(d, E.SAFETY_DECLARATION_UNKNOWN)


# --- §C law 3: the HARD LAW — a data edit cannot unlock minors/slurs --------


@pytest.mark.parametrize("category", ["minors", "slurs"])
@pytest.mark.parametrize("rating", ["mature", "explicit"])
def test_floor_locked_categories_refuse_unlock(tmp_path, category, rating):
    content = (
        f"#! category: {category}\n#! mode: always\n"
        f"#! enforcement: unlocked_at: {rating}\nbadword\n"
    )
    d = write_data(tmp_path, {"list.txt": content})
    refuse_safety_data(d, E.SAFETY_ENFORCEMENT_LOCKED)


@pytest.mark.parametrize("category", ["minors", "slurs"])
def test_floor_locked_categories_load_at_floor(tmp_path, category):
    content = (
        f"#! category: {category}\n#! mode: always\n"
        f"#! enforcement: floor\nbadword\n"
    )
    d = write_data(tmp_path, {"list.txt": content})
    result = SafetyFilter(d).check("badword", "freetext", rating="explicit")
    assert not result.allowed and result.category == category


# --- §E enforcement gating on composed lists --------------------------------


def test_unlocked_at_explicit_applies_below_only(tmp_path):
    content = (
        "#! category: vice\n#! mode: always\n"
        "#! enforcement: unlocked_at: explicit\nviceword\n"
    )
    d = write_data(tmp_path, {"list.txt": content})
    f = SafetyFilter(d)
    assert not f.check("viceword", "freetext", rating="standard").allowed
    assert not f.check("viceword", "freetext", rating="mature").allowed
    assert f.check("viceword", "freetext", rating="explicit").allowed


def test_unknown_category_scans_after_known(tmp_path):
    # builder detail (recorded): unknown categories rank below the eight
    # known ones, so a multi-hit still reports the known category.
    content_known = GOOD_ALWAYS  # noncon
    content_new = (
        "#! category: aaa_custom\n#! mode: always\n"
        "#! enforcement: floor\ncustomword\n"
    )
    d = write_data(
        tmp_path, {"known.txt": content_known, "new.txt": content_new}
    )
    f = SafetyFilter(d)
    assert f.check("customword rapeword", "freetext").category == "noncon"
    assert f.check("customword", "freetext").category == "aaa_custom"
