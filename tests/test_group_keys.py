"""§4 group keys: required keys, closed vocabularies, kind-conditional
legality (max_picks / feeds / max_chars / options), scene_overridable."""

from conftest import free_text_group, group, load_strict, minimal_file, refuse

from app.options import errors as E


def _file_with(g):
    return {"format": 1, "rating": "standard", "groups": [g]}


def test_refuses_unknown_group_key(write_file):
    d = write_file("00.json", _file_with(group(widget="picker")))
    refuse(d, E.UNKNOWN_KEY)


def test_refuses_unknown_kind(write_file):
    d = write_file("00.json", _file_with(group(kind="single")))
    refuse(d, E.BAD_KIND)


def test_refuses_missing_kind(write_file):
    g = group()
    del g["kind"]
    refuse(write_file("00.json", _file_with(g)), E.MISSING_KEY)


def test_refuses_unknown_home(write_file):
    d = write_file("00.json", _file_with(group(home="global")))
    refuse(d, E.BAD_HOME)


def test_refuses_missing_home(write_file):
    g = group()
    del g["home"]
    refuse(write_file("00.json", _file_with(g)), E.MISSING_KEY)


def test_refuses_missing_label(write_file):
    g = group()
    del g["label"]
    refuse(write_file("00.json", _file_with(g)), E.MISSING_KEY)


def test_refuses_unknown_priority_value(write_file):
    g = group(
        priority="P0",
        options=[{"id": "opt_a", "label": "A", "image_text": "a"}],
    )
    refuse(write_file("00.json", _file_with(g)), E.BAD_PRIORITY)


def test_refuses_scene_overridable_on_non_identity(write_file):
    g = group(home="persona", scene_overridable=True)
    refuse(write_file("00.json", _file_with(g)), E.SCENE_OVERRIDABLE_NON_IDENTITY)


def test_refuses_scene_overridable_on_session(write_file):
    g = group(home="session", scene_overridable=True)
    refuse(write_file("00.json", _file_with(g)), E.SCENE_OVERRIDABLE_NON_IDENTITY)


def test_scene_overridable_on_identity_loads(write_file):
    g = group(home="identity", scene_overridable=True)
    catalog = load_strict(write_file("00.json", _file_with(g)))
    assert catalog.get("g1").scene_overridable is True


def test_refuses_non_bool_scene_overridable(write_file):
    g = group(scene_overridable="yes")
    refuse(write_file("00.json", _file_with(g)), E.BAD_KEY_TYPE)


def test_refuses_max_picks_on_pick_one(write_file):
    g = group(kind="pick_one", max_picks=3)
    refuse(write_file("00.json", _file_with(g)), E.MAX_PICKS_ON_NON_PICK_MANY)


def test_refuses_max_picks_on_free_text(write_file):
    g = free_text_group(max_picks=3)
    refuse(write_file("00.json", _file_with(g)), E.MAX_PICKS_ON_NON_PICK_MANY)


def test_refuses_max_picks_below_one(write_file):
    g = group(kind="pick_many", max_picks=0)
    refuse(write_file("00.json", _file_with(g)), E.BAD_MAX_PICKS)


def test_max_picks_on_pick_many_loads(write_file):
    g = group(kind="pick_many", max_picks=2)
    catalog = load_strict(write_file("00.json", _file_with(g)))
    assert catalog.get("g1").max_picks == 2


def test_pick_many_without_max_picks_is_uncapped(write_file):
    g = group(kind="pick_many")
    catalog = load_strict(write_file("00.json", _file_with(g)))
    assert catalog.get("g1").max_picks is None


def test_refuses_feeds_on_pick_kind(write_file):
    g = group(feeds="image")
    refuse(write_file("00.json", _file_with(g)), E.FEEDS_ON_PICK_KIND)


def test_refuses_unknown_feeds_value(write_file):
    g = free_text_group(feeds="video")
    refuse(write_file("00.json", _file_with(g)), E.BAD_FEEDS)


def test_refuses_free_text_missing_feeds(write_file):
    g = free_text_group()
    del g["feeds"]
    refuse(write_file("00.json", _file_with(g)), E.MISSING_KEY)


def test_refuses_free_text_missing_max_chars(write_file):
    g = free_text_group()
    del g["max_chars"]
    refuse(write_file("00.json", _file_with(g)), E.MISSING_KEY)


def test_refuses_max_chars_over_240(write_file):
    # §1.2 / Decision 7-amended: the FORMAT refuses any declared limit > 240.
    g = free_text_group(max_chars=241)
    refuse(write_file("00.json", _file_with(g)), E.BAD_MAX_CHARS)


def test_refuses_max_chars_below_one(write_file):
    g = free_text_group(max_chars=0)
    refuse(write_file("00.json", _file_with(g)), E.BAD_MAX_CHARS)


def test_refuses_max_chars_on_pick_kind(write_file):
    g = group(max_chars=100)
    refuse(write_file("00.json", _file_with(g)), E.MAX_CHARS_ON_PICK_KIND)


def test_refuses_free_text_with_options(write_file):
    g = free_text_group(options=[{"id": "opt_a", "label": "A"}])
    refuse(write_file("00.json", _file_with(g)), E.OPTIONS_ON_FREE_TEXT)


def test_refuses_pick_kind_without_options(write_file):
    g = group()
    del g["options"]
    refuse(write_file("00.json", _file_with(g)), E.OPTIONS_MISSING)


def test_refuses_free_text_home_session(write_file):
    g = free_text_group(home="session")
    refuse(write_file("00.json", _file_with(g)), E.FREE_TEXT_SESSION)


def test_free_text_slots_load_with_both_homes(write_file):
    data = {
        "format": 1,
        "rating": "standard",
        "groups": [
            free_text_group(id="ft_ident", home="identity"),
            free_text_group(id="ft_pers", home="persona"),
        ],
    }
    catalog = load_strict(write_file("00.json", data))
    assert catalog.get("ft_ident").is_free_text
    assert catalog.get("ft_pers").home == "persona"
    assert catalog.errors == []


def test_group_tags_and_hints_load(write_file):
    g = group(tags=["mammal"], hint="help text", section="Body", order=10)
    catalog = load_strict(write_file("00.json", _file_with(g)))
    loaded = catalog.get("g1")
    assert loaded.tags == ("mammal",)
    assert loaded.hint == "help text"
    assert loaded.section == "Body"
    assert loaded.order == 10
