"""Group key `required` (O3_INPUTS N3, spec §4).

required-when-visible, bool, default false; legal on pick kinds only —
meaningless on free_text and on session homes, format error there. Not
merge-locked (O2_INPUTS answer 8.3's list is fixed): fragments override it
with normal scalar semantics.
"""

from tests.conftest import free_text_group, group, load_strict, minimal_file, refuse


def test_required_true_accepted_on_pick_one_identity(write_file):
    d = write_file(
        "00.json", minimal_file(groups=[group(required=True)])
    )
    catalog = load_strict(d)
    assert catalog.get("g1").required is True


def test_required_accepted_on_pick_many_persona_home(write_file):
    g = group(
        kind="pick_many",
        home="persona",
        options=[{"id": "opt_a", "label": "A"}, {"id": "opt_b", "label": "B"}],
        required=True,
    )
    d = write_file("00.json", minimal_file(groups=[g]))
    assert load_strict(d).get("g1").required is True


def test_required_defaults_false_when_absent(write_file):
    d = write_file("00.json", minimal_file())
    assert load_strict(d).get("g1").required is False


def test_required_non_bool_refused(write_file):
    d = write_file("00.json", minimal_file(groups=[group(required="yes")]))
    refuse(d, "BAD_KEY_TYPE")


def test_required_on_free_text_refused(write_file):
    d = write_file(
        "00.json", minimal_file(groups=[free_text_group(required=True)])
    )
    refuse(d, "REQUIRED_ON_FREE_TEXT")


def test_required_on_session_home_refused(write_file):
    d = write_file(
        "00.json", minimal_file(groups=[group(home="session", required=True)])
    )
    refuse(d, "REQUIRED_ON_SESSION_HOME")


def test_required_false_on_free_text_passes(write_file):
    # Value-based, mirroring scene_overridable: an explicit false is the
    # default state, not a declaration (builder detail, SESSION_REPORT_O3).
    d = write_file(
        "00.json", minimal_file(groups=[free_text_group(required=False)])
    )
    assert load_strict(d).get("ft1").required is False


def test_required_overridable_by_extension_fragment(write_file):
    # `required` is NOT merge-locked — answer 8.3 fixed the locked list at
    # kind/home/feeds/scene_overridable; required keeps v1 override semantics.
    write_file("00.json", minimal_file(groups=[group()]))
    d = write_file(
        "10.json",
        {"format": 1, "rating": "standard", "groups": [{"id": "g1", "required": True}]},
    )
    assert load_strict(d).get("g1").required is True
