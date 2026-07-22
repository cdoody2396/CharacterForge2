"""Stage O2 harvest tool: every DECIDED transformation rule (O2_INPUTS.md),
the flag-and-hold rules, both refusals, the validator gate, and byte-identical
idempotence — all on small synthetic v1-shaped fixtures built in tmp_path
with neutral ids (spec §0: committed example data lives only in fixtures)."""

import json
from pathlib import Path

import pytest

from app.options import load_catalog
from tools.harvest import HarvestError, harvest_tree, load_overrides, write_output
from tools.harvest.__main__ import main as harvest_main


def v1_tree(tmp_path, ungated=None, gated=None):
    """Build a v1-shaped checkout (app/data/options[_gated]) in tmp_path."""
    root = tmp_path / "v1"
    for sub, files in (
        ("app/data/options", ungated or {}),
        ("app/data/options_gated", gated or {}),
    ):
        d = root / sub
        d.mkdir(parents=True, exist_ok=True)
        for name, obj in files.items():
            (d / name).write_text(json.dumps(obj), encoding="utf-8")
    return root


def v1_group(**overrides):
    """A minimal valid v1 image-side group (render absent, tier P2).
    Passing ``key=None`` REMOVES the key (absence, not a JSON null)."""
    g = {
        "id": "g1",
        "label": "G1",
        "kind": "single",
        "field": "g1",
        "order": 1,
        "tier": "P2",
        "options": [{"id": "opt_a", "label": "A", "prompt": "a prompt"}],
    }
    g.update(overrides)
    return {k: v for k, v in g.items() if v is not None}


def v1_file(*groups, **top):
    data = {"groups": list(groups)}
    data.update(top)
    return data


def emitted(result, name):
    return json.loads(result.files[name].decode("utf-8"))


def one_group(result, name="20_appearance.json"):
    return emitted(result, name)["groups"][0]


def harvest_one(tmp_path, group, name="20_appearance.json", gated=None):
    return harvest_tree(v1_tree(tmp_path, {name: v1_file(group)}, gated))


# --- prompt -> text mapping (answer 2) --------------------------------------


def test_render_absent_maps_prompt_to_image_text(tmp_path):
    g = one_group(harvest_one(tmp_path, v1_group()))
    opt = g["options"][0]
    assert opt["image_text"] == "a prompt"
    assert "chat_text" not in opt  # never both
    assert g["priority"] == "flavor"  # P2, required with image_text


def test_render_false_maps_prompt_to_chat_text(tmp_path):
    g = one_group(harvest_one(tmp_path, v1_group(render=False, tier=None)))
    opt = g["options"][0]
    assert opt["chat_text"] == "a prompt"
    assert "image_text" not in opt
    assert "priority" not in g  # forbidden without image_text


def test_empty_prompt_preserved_verbatim(tmp_path):
    g = v1_group(options=[{"id": "opt_none", "label": "None", "prompt": ""}])
    result = harvest_one(tmp_path, g)
    assert one_group(result)["options"][0]["image_text"] == ""


def test_option_without_prompt_is_menu_only(tmp_path):
    g = v1_group(
        tier="P2",
        options=[
            {"id": "opt_a", "label": "A", "prompt": "a"},
            {"id": "opt_b", "label": "B"},
        ],
    )
    opts = one_group(harvest_one(tmp_path, g))["options"]
    assert "image_text" not in opts[1] and "chat_text" not in opts[1]


# --- tier -> priority (§1.6, answer 4) --------------------------------------


def test_tier_default_map(tmp_path):
    groups = [
        v1_group(id=f"g_{t.lower()}", field=f"g_{t.lower()}", tier=t)
        for t in ("P0", "P1", "P2", "P3")
    ]
    result = harvest_tree(v1_tree(tmp_path, {"20_appearance.json": v1_file(*groups)}))
    got = {g["id"]: g["priority"] for g in emitted(result, "20_appearance.json")["groups"]}
    assert got == {"g_p0": "must", "g_p1": "should", "g_p2": "flavor", "g_p3": "flavor"}


def test_tier_on_chat_group_is_log_only_no_priority(tmp_path):
    result = harvest_one(tmp_path, v1_group(render=False, tier="P1"))
    g = one_group(result)
    assert "priority" not in g
    assert "tier" not in g
    assert "| 20_appearance.json | g1 | tier | `\"P1\"` |" in result.log_md


def test_image_group_without_tier_flagged_and_held(tmp_path):
    result = harvest_one(tmp_path, v1_group(tier=None))
    assert "20_appearance.json" not in result.files  # only group held
    assert any("no v1 tier" in f.reason for f in result.flags)


# --- metadata unification (§1.8, §1.12) -------------------------------------


def test_class_and_tags_merge_into_one_tags_list(tmp_path):
    g = v1_group(
        options=[
            {
                "id": "opt_a",
                "label": "A",
                "prompt": "a",
                "class": ["beast", "mammal"],
                "tags": ["furry", "beast"],
            }
        ]
    )
    opt = one_group(harvest_one(tmp_path, g))["options"][0]
    assert opt["tags"] == ["beast", "mammal", "furry"]  # class first, deduped


def test_visible_when_class_becomes_has_tag(tmp_path):
    ref = v1_group(id="ref", field="ref")
    dep = v1_group(
        id="dep", field="dep", visible_when={"group": "ref", "class": "beast"}
    )
    result = harvest_tree(
        v1_tree(tmp_path, {"20_appearance.json": v1_file(ref, dep)})
    )
    groups = {g["id"]: g for g in emitted(result, "20_appearance.json")["groups"]}
    assert groups["dep"]["visible_when"] == {"group": "ref", "has_tag": "beast"}


def test_visible_when_in_not_in_any_carry_over(tmp_path):
    ref = v1_group(id="ref", field="ref")
    deps = [
        v1_group(id="dep_in", field="dep_in", visible_when={"group": "ref", "in": ["opt_a"]}),
        v1_group(id="dep_not", field="dep_not", visible_when={"group": "ref", "not_in": ["opt_a"]}),
        v1_group(id="dep_any", field="dep_any", visible_when={"group": "ref", "any": True}),
    ]
    result = harvest_tree(
        v1_tree(tmp_path, {"20_appearance.json": v1_file(ref, *deps)})
    )
    groups = {g["id"]: g for g in emitted(result, "20_appearance.json")["groups"]}
    assert groups["dep_in"]["visible_when"] == {"group": "ref", "in": ["opt_a"]}
    assert groups["dep_not"]["visible_when"] == {"group": "ref", "not_in": ["opt_a"]}
    assert groups["dep_any"]["visible_when"] == {"group": "ref", "any": True}


def test_option_image_renames_to_thumb_and_color_carries(tmp_path):
    g = v1_group(
        options=[
            {
                "id": "opt_a",
                "label": "A",
                "prompt": "a",
                "image": "thumbs/a.png",
                "color": "#aabbcc",
            }
        ]
    )
    opt = one_group(harvest_one(tmp_path, g))["options"][0]
    assert opt["thumb"] == "thumbs/a.png"
    assert "image" not in opt
    assert opt["color"] == "#aabbcc"


# --- rating (answer 3) and home (answer 7) ----------------------------------


def test_rating_standard_ungated_explicit_gated_single_tree(tmp_path):
    root = v1_tree(
        tmp_path,
        {"20_appearance.json": v1_file(v1_group())},
        {"91_anatomy_intimate.json": v1_file(v1_group(id="g2", field="g2"))},
    )
    result = harvest_tree(root)
    assert emitted(result, "20_appearance.json")["rating"] == "standard"
    assert emitted(result, "91_anatomy_intimate.json")["rating"] == "explicit"
    assert set(result.files) == {"20_appearance.json", "91_anatomy_intimate.json"}


def test_home_table_and_identity_split(tmp_path):
    root = v1_tree(
        tmp_path,
        {
            "20_appearance.json": v1_file(v1_group()),
            "50_mind.json": v1_file(v1_group(id="g_mind", field="g_mind", render=False, tier=None)),
            "10_identity.json": v1_file(
                v1_group(id="apparent_age", field="apparent_age", tier="P1"),
                v1_group(id="g_other", field="g_other", render=False, tier=None),
            ),
        },
    )
    result = harvest_tree(root)
    assert one_group(result, "20_appearance.json")["home"] == "identity"
    assert one_group(result, "50_mind.json")["home"] == "persona"
    identity = {g["id"]: g["home"] for g in emitted(result, "10_identity.json")["groups"]}
    assert identity == {"apparent_age": "identity", "g_other": "persona"}


def test_00_age_is_consumed_not_emitted(tmp_path):
    root = v1_tree(
        tmp_path,
        {
            "00_age.json": v1_file(
                {"id": "age", "label": "Age", "kind": "number", "min": 20, "_note": "n"}
            ),
            "20_appearance.json": v1_file(v1_group()),
        },
    )
    result = harvest_tree(root)
    assert "00_age.json" not in result.files
    assert not result.flags  # consumed is decided, not a flag
    row = next(r for r in result.inventory if r["file"] == "00_age.json")
    assert row["disposition"] == "consumed"
    assert "consumed whole" in result.log_md


# --- holding (§11, answer 5) ------------------------------------------------


def test_held_keys_go_to_v1_comment_object(tmp_path):
    g = v1_group(
        quick=True,
        required=True,
        widget="picker",
        region="Chest",
        attribute="Size",
        aliases=["old_name"],
    )
    out = one_group(harvest_one(tmp_path, g))
    assert out["_v1"] == {
        "quick": True,
        "required": True,
        "widget": "picker",
        "region": "Chest",
        "attribute": "Size",
        "aliases": ["old_name"],
    }
    assert "quick" not in out


def test_field_equal_to_id_dropped_differing_field_held(tmp_path):
    root = v1_tree(
        tmp_path,
        {
            "20_appearance.json": v1_file(
                v1_group(),  # field == id -> dropped
                v1_group(id="g2", field="old_field"),
            )
        },
    )
    result = harvest_tree(root)
    groups = {g["id"]: g for g in emitted(result, "20_appearance.json")["groups"]}
    assert "_v1" not in groups["g1"]
    assert groups["g2"]["_v1"] == {"field": "old_field"}


def test_unexpected_leftover_key_held_in_v1(tmp_path):
    result = harvest_one(tmp_path, v1_group(mystery="value"))
    assert one_group(result)["_v1"] == {"mystery": "value"}
    assert "| 20_appearance.json | g1 | mystery | `\"value\"` |" in result.log_md


def test_notes_carried_verbatim_render_tier_not_emitted(tmp_path):
    g = v1_group(_note="group note", _render_note="render note")
    g["options"][0]["_note"] = "option note"
    root = v1_tree(tmp_path, {"20_appearance.json": v1_file(g, _note="file note")})
    result = harvest_tree(root)
    data = emitted(result, "20_appearance.json")
    assert data["_note"] == "file note"
    out = data["groups"][0]
    assert out["_note"] == "group note"
    assert out["_render_note"] == "render note"
    assert out["options"][0]["_note"] == "option note"
    blob = result.files["20_appearance.json"].decode("utf-8")
    assert '"render"' not in blob and '"tier"' not in blob  # log-only


def test_emitted_file_shape(tmp_path):
    data = emitted(harvest_one(tmp_path, v1_group()), "20_appearance.json")
    assert data["format"] == 1
    assert list(data) == ["format", "rating", "groups"]


# --- fragments and flag-and-hold rules --------------------------------------


def test_fragment_emits_id_and_options_only(tmp_path):
    root = v1_tree(
        tmp_path,
        {"60_wardrobe.json": v1_file(v1_group(id="outfit", field="outfit", kind="multi"))},
        {
            "90_wardrobe_intimate.json": v1_file(
                {"id": "outfit", "options": [{"id": "opt_x", "label": "X", "prompt": "x"}]}
            )
        },
    )
    result = harvest_tree(root)
    frag = emitted(result, "90_wardrobe_intimate.json")["groups"][0]
    assert set(frag) == {"id", "options"}  # no kind/home/label restated
    # options inherit the DEFINING group's render (absent -> image_text)
    assert frag["options"][0]["image_text"] == "x"
    assert not result.flags


def test_fragment_contradicting_file_home_flagged_and_held(tmp_path):
    # Synthetic mirror of the real 92_piercings case: the fragment's file is
    # persona (answer-7 table) but it extends a group defined identity.
    root = v1_tree(
        tmp_path,
        {"38_marks.json": v1_file(v1_group(id="piercings", field="piercings", kind="multi", tier="P3"))},
        {
            "92_piercings_intimate.json": v1_file(
                {"id": "piercings", "options": [{"id": "opt_x", "label": "X", "prompt": "x"}]}
            )
        },
    )
    result = harvest_tree(root)
    assert "92_piercings_intimate.json" not in result.files  # zero groups left
    assert "38_marks.json" in result.files
    flag = next(f for f in result.flags if f.group == "piercings")
    assert "contradicts its file's home" in flag.reason
    row = next(r for r in result.inventory if r["file"] == "92_piercings_intimate.json")
    assert row["disposition"] == "held (no groups left)"


def test_numeric_kind_other_than_age_flagged_and_held(tmp_path):
    root = v1_tree(
        tmp_path,
        {"30_body.json": v1_file(v1_group(id="height_cm", field="height_cm", kind="number"), v1_group())},
    )
    result = harvest_tree(root)
    ids = [g["id"] for g in emitted(result, "30_body.json")["groups"]]
    assert ids == ["g1"]  # numeric group held, sibling emitted
    assert any("numeric-kind" in f.reason for f in result.flags)


def test_unknown_kind_flagged_and_held(tmp_path):
    result = harvest_one(tmp_path, v1_group(kind="slider"))
    assert "20_appearance.json" not in result.files
    assert any("un-mapped kind" in f.reason for f in result.flags)


def test_fragment_touching_locked_kind_flagged(tmp_path):
    root = v1_tree(
        tmp_path,
        {"60_wardrobe.json": v1_file(v1_group(id="outfit", field="outfit", kind="multi"))},
        {
            "90_wardrobe_intimate.json": v1_file(
                {"id": "outfit", "kind": "multi", "options": []}
            )
        },
    )
    result = harvest_tree(root)
    assert any("merge-locked" in f.reason for f in result.flags)
    assert "90_wardrobe_intimate.json" not in result.files


# --- refusals ---------------------------------------------------------------


def test_unknown_source_file_refused(tmp_path):
    root = v1_tree(tmp_path, {"99_custom.json": v1_file(v1_group())})
    with pytest.raises(HarvestError, match="unknown source file"):
        harvest_tree(root)


def test_null_value_refused(tmp_path):
    g = v1_group()
    g["hint"] = None  # a real JSON null in the source
    with pytest.raises(HarvestError, match="null"):
        harvest_one(tmp_path, g)


def test_example_group_id_refused(tmp_path):
    with pytest.raises(HarvestError, match="example_"):
        harvest_one(tmp_path, v1_group(id="example_group", field="example_group"))


def test_example_option_id_refused(tmp_path):
    g = v1_group(options=[{"id": "example_opt", "label": "A", "prompt": "a"}])
    with pytest.raises(HarvestError, match="example_"):
        harvest_one(tmp_path, g)


# --- artifacts --------------------------------------------------------------


def test_priority_review_table(tmp_path):
    # Final column repeats the default on rows the gate did not override.
    result = harvest_one(tmp_path, v1_group(tier="P1"))
    assert "| 20_appearance.json | g1 | P1 | should | should |" in result.priority_md
    assert "Overridden rows in this emission: 0." in result.priority_md


def test_polish_flags_from_group_and_file_notes(tmp_path):
    root = v1_tree(
        tmp_path,
        {
            "20_appearance.json": v1_file(
                v1_group(_note="prompt wording lands later"),
                v1_group(id="g2", field="g2", _note="final wording, done"),
                v1_group(id="g3", field="g3"),
            ),
            "50_mind.json": v1_file(
                v1_group(id="g_m", field="g_m", render=False, tier=None),
                _note="Mem provisional; fragments best-effort",
            ),
        },
    )
    result = harvest_tree(root)
    assert "| 20_appearance.json | g1 | group _note |" in result.polish_md
    assert "| 20_appearance.json | g2 | group _note |" in result.polish_md  # 'wording'
    assert "| 20_appearance.json | g3 " not in result.polish_md
    assert "| 50_mind.json | g_m | file _note |" in result.polish_md


def test_log_counts_per_file_vs_v1(tmp_path):
    result = harvest_one(tmp_path, v1_group())
    assert "| 20_appearance.json | standard | 1 | 1 | 1 | 1 | emitted |" in result.log_md


# --- CLI, validator gate, idempotence ---------------------------------------


def empty_overrides(tmp_path):
    """A minimal valid overrides file: nothing overridden (O2b)."""
    path = tmp_path / "overrides_empty.json"
    path.write_text(json.dumps({"format": 1}), encoding="utf-8")
    return path


def _run_cli(root, out, report, overrides):
    return harvest_main(
        [str(root), "--out", str(out), "--report", str(report),
         "--overrides", str(overrides)]
    )


def test_cli_end_to_end_validator_clean(tmp_path):
    root = v1_tree(
        tmp_path,
        {"20_appearance.json": v1_file(v1_group())},
        {"91_anatomy_intimate.json": v1_file(v1_group(id="g2", field="g2"))},
    )
    out, report = tmp_path / "out", tmp_path / "report"
    assert _run_cli(root, out, report, empty_overrides(tmp_path)) == 0
    assert sorted(p.name for p in out.glob("*.json")) == [
        "20_appearance.json",
        "91_anatomy_intimate.json",
    ]
    for name in (
        "HARVEST_LOG.md",
        "PRIORITY_REVIEW.md",
        "POLISH_FLAGS.md",
        "OVERRIDES_APPLIED.md",
    ):
        assert (report / name).is_file()
    catalog = load_catalog([out], strict=True)  # the gate agrees
    assert catalog.errors == []
    assert catalog.get("g2").options[0].rating == "explicit"


def test_cli_idempotent_byte_identical(tmp_path):
    root = v1_tree(
        tmp_path,
        {"20_appearance.json": v1_file(v1_group(_note="note"))},
        {"90_wardrobe_intimate.json": v1_file(v1_group(id="g9", field="g9", render=False, tier=None))},
    )
    out, report = tmp_path / "out", tmp_path / "report"
    ov = empty_overrides(tmp_path)
    assert _run_cli(root, out, report, ov) == 0
    snapshot = {
        p.name: p.read_bytes() for d in (out, report) for p in d.iterdir()
    }
    assert _run_cli(root, out, report, ov) == 0
    again = {p.name: p.read_bytes() for d in (out, report) for p in d.iterdir()}
    assert snapshot == again


def test_validation_failure_writes_nothing(tmp_path):
    # visible_when referencing a group that never exists survives the harvest
    # mapping but violates the v2 catalog laws -> the gate refuses, exit 1,
    # and the output directory is untouched.
    g = v1_group(visible_when={"group": "no_such_group", "any": True})
    root = v1_tree(tmp_path, {"20_appearance.json": v1_file(g)})
    out, report = tmp_path / "out", tmp_path / "report"
    assert _run_cli(root, out, report, empty_overrides(tmp_path)) == 1
    assert not out.exists()
    assert not report.exists()


def test_foreign_json_in_out_dir_refused(tmp_path):
    root = v1_tree(tmp_path, {"20_appearance.json": v1_file(v1_group())})
    out = tmp_path / "out"
    out.mkdir()
    (out / "55_foreign.json").write_text("{}", encoding="utf-8")
    assert _run_cli(root, out, tmp_path / "report", empty_overrides(tmp_path)) == 2


def test_harvest_tree_is_deterministic(tmp_path):
    root = v1_tree(tmp_path, {"20_appearance.json": v1_file(v1_group())})
    a, b = harvest_tree(root), harvest_tree(root)
    assert a.files == b.files
    assert a.log_md == b.log_md


# --- planning-gate overrides (stage O2b) ------------------------------------


def overrides_file(tmp_path, data, name="overrides.json"):
    data.setdefault("format", 1)
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def ov(tmp_path, **sections):
    return load_overrides(overrides_file(tmp_path, dict(sections)))


def test_home_override_supersedes_table_on_first_definition(tmp_path):
    # g1 sits in 50_mind -> persona by the answer-7 table; the gate moves it.
    root = v1_tree(tmp_path, {"50_mind.json": v1_file(v1_group())})
    overrides = ov(tmp_path, home={"g1": {"to": "identity", "why": "gate ruling"}})
    result = harvest_tree(root, overrides)
    assert one_group(result, "50_mind.json")["home"] == "identity"


def test_home_override_clears_fragment_contradiction(tmp_path):
    # The real 92_piercings case in miniature: table homes disagree
    # (38_marks identity vs 92 persona) until the override makes both say
    # identity — the hold clears itself and the fragment emits.
    root = v1_tree(
        tmp_path,
        {"38_marks.json": v1_file(v1_group(id="piercings", field="piercings", kind="multi", tier="P3"))},
        {
            "92_piercings_intimate.json": v1_file(
                {"id": "piercings", "options": [{"id": "opt_x", "label": "X", "prompt": "x"}]}
            )
        },
    )
    overrides = ov(tmp_path, home={"piercings": {"to": "identity", "why": "gate ruling"}})
    result = harvest_tree(root, overrides)
    assert not result.flags
    assert "92_piercings_intimate.json" in result.files
    frag = emitted(result, "92_piercings_intimate.json")["groups"][0]
    assert frag["options"][0]["image_text"] == "x"
    assert one_group(result, "38_marks.json")["home"] == "identity"


def test_priority_override_applies_after_default_map(tmp_path):
    root = v1_tree(tmp_path, {"20_appearance.json": v1_file(v1_group(tier="P2"))})
    overrides = ov(tmp_path, priority={"g1": {"to": "must", "why": "gate ruling"}})
    result = harvest_tree(root, overrides)
    assert one_group(result)["priority"] == "must"
    assert "| 20_appearance.json | g1 | P2 | flavor | must — OVERRIDE |" in result.priority_md
    assert "Overridden rows in this emission: 1." in result.priority_md


def test_scene_overridable_true_emitted_on_identity_first_definition(tmp_path):
    root = v1_tree(tmp_path, {"20_appearance.json": v1_file(v1_group())})
    overrides = ov(tmp_path, scene_overridable={"g1": {"value": True, "why": "gate ruling"}})
    g = one_group(harvest_tree(root, overrides))
    assert g["scene_overridable"] is True
    keys = list(g)
    assert keys.index("home") < keys.index("scene_overridable") < keys.index("priority")


def test_scene_overridable_false_emits_nothing(tmp_path):
    root = v1_tree(tmp_path, {"20_appearance.json": v1_file(v1_group())})
    overrides = ov(tmp_path, scene_overridable={"g1": {"value": False, "why": "gate ruling"}})
    assert "scene_overridable" not in one_group(harvest_tree(root, overrides))


def test_scene_override_on_persona_home_fails_the_gate(tmp_path):
    # The spec §4 format error (scene_overridable on non-identity) is the
    # live safety net: the emission fails validation and nothing is written.
    root = v1_tree(tmp_path, {"50_mind.json": v1_file(v1_group())})
    overrides = overrides_file(
        tmp_path, {"scene_overridable": {"g1": {"value": True, "why": "bad ruling"}}}
    )
    out, report = tmp_path / "out", tmp_path / "report"
    assert _run_cli(root, out, report, overrides) == 1
    assert not out.exists()


def test_override_without_why_is_tool_error(tmp_path):
    with pytest.raises(HarvestError, match="why"):
        ov(tmp_path, priority={"g1": {"to": "must"}})
    with pytest.raises(HarvestError, match="why"):
        ov(tmp_path, home={"g1": {"to": "identity", "why": "   "}})


def test_override_bad_value_is_tool_error(tmp_path):
    with pytest.raises(HarvestError, match="not in"):
        ov(tmp_path, priority={"g1": {"to": "urgent", "why": "w"}})
    with pytest.raises(HarvestError, match="bool"):
        ov(tmp_path, scene_overridable={"g1": {"value": "yes", "why": "w"}})


def test_override_unknown_section_or_key_is_tool_error(tmp_path):
    with pytest.raises(HarvestError, match="unknown overrides section"):
        ov(tmp_path, colour={"g1": {"to": "must", "why": "w"}})
    with pytest.raises(HarvestError, match="unknown key"):
        ov(tmp_path, priority={"g1": {"to": "must", "why": "w", "extra": 1}})
    with pytest.raises(HarvestError, match="format"):
        load_overrides(overrides_file(tmp_path, {"format": 2}))


def test_unapplied_override_is_tool_error(tmp_path):
    root = v1_tree(tmp_path, {"20_appearance.json": v1_file(v1_group())})
    overrides = ov(tmp_path, priority={"no_such_group": {"to": "must", "why": "w"}})
    with pytest.raises(HarvestError, match="never landed"):
        harvest_tree(root, overrides)
    overrides = ov(tmp_path, home={"no_such_group": {"to": "identity", "why": "w"}})
    with pytest.raises(HarvestError, match="never landed"):
        harvest_tree(root, overrides)


def test_comment_record_entries_not_applied_but_reported(tmp_path):
    root = v1_tree(tmp_path, {"20_appearance.json": v1_file(v1_group())})
    overrides = ov(
        tmp_path,
        scene_overridable={"_denied_g1": {"value": False, "why": "recorded refusal"}},
    )
    result = harvest_tree(root, overrides)
    assert "scene_overridable" not in one_group(result)  # never applied as a key
    assert "`scene_overridable` / `_denied_g1`" in result.overrides_md
    assert "recorded refusal" in result.overrides_md


def test_overrides_applied_report_content(tmp_path):
    root = v1_tree(
        tmp_path,
        {
            "20_appearance.json": v1_file(v1_group(tier="P2")),
            "50_mind.json": v1_file(v1_group(id="g_m", field="g_m", tier="P1")),
        },
    )
    overrides = ov(
        tmp_path,
        _note="gate note",
        priority={"g1": {"to": "must", "why": "the gate's exact words"}},
        home={"g_m": {"to": "identity", "why": "moves home"}},
    )
    result = harvest_tree(root, overrides)
    md = result.overrides_md
    assert "- source `_note`, verbatim: gate note" in md
    assert "| g1 | flavor | must | the gate's exact words |" in md
    assert "| g_m | identity | persona (50_mind.json) | moves home |" in md
    # Mechanical counts: two first-definition priority rows, one overridden.
    assert (
        "First-definition priority rows in this emission: 2; overridden: 1; "
        "standing as defaulted: 1." in md
    )


def test_cli_loads_committed_overrides_by_default(tmp_path, capsys):
    # No --overrides flag: the committed tools/harvest/overrides.json loads;
    # its entries target real v1 groups absent from this synthetic tree, so
    # the unapplied-override refusal proves the default file was consumed.
    root = v1_tree(tmp_path, {"20_appearance.json": v1_file(v1_group())})
    out, report = tmp_path / "out", tmp_path / "report"
    code = harvest_main([str(root), "--out", str(out), "--report", str(report)])
    assert code == 2
    assert "never landed" in capsys.readouterr().out
    assert not out.exists()


def test_out_targeting_maintained_tree_requires_flag(tmp_path, capsys):
    # O2b freeze: app/data/options/ is the maintained source; overwriting it
    # is never implicit. The check fires before any work happens.
    import tools.harvest.__main__ as cli_mod

    maintained = Path(cli_mod.__file__).resolve().parents[2] / "app" / "data" / "options"
    root = v1_tree(tmp_path, {"20_appearance.json": v1_file(v1_group())})
    code = harvest_main(
        [str(root), "--out", str(maintained), "--report", str(tmp_path / "report"),
         "--overrides", str(empty_overrides(tmp_path))]
    )
    assert code == 2
    out = capsys.readouterr().out
    assert "MAINTAINED SOURCE" in out
    assert "--i-know-this-overwrites-maintained-data" in out
    assert not (tmp_path / "report").exists()  # refused before any work


def test_out_targeting_maintained_tree_proceeds_with_flag(tmp_path):
    # With the flag the guard steps aside; the foreign-file refusal then
    # fires because the synthetic emission does not match the real tree —
    # proof the run got past the guard without touching anything.
    import tools.harvest.__main__ as cli_mod

    maintained = Path(cli_mod.__file__).resolve().parents[2] / "app" / "data" / "options"
    root = v1_tree(tmp_path, {"20_appearance.json": v1_file(v1_group())})
    code = harvest_main(
        [str(root), "--out", str(maintained), "--report", str(tmp_path / "report"),
         "--overrides", str(empty_overrides(tmp_path)),
         "--i-know-this-overwrites-maintained-data"]
    )
    assert code == 2  # foreign data files in the maintained tree, untouched


def test_unrelated_out_dir_needs_no_flag(tmp_path):
    root = v1_tree(tmp_path, {"20_appearance.json": v1_file(v1_group())})
    out, report = tmp_path / "out", tmp_path / "report"
    assert _run_cli(root, out, report, empty_overrides(tmp_path)) == 0
    assert (out / "20_appearance.json").is_file()


def test_cli_idempotent_byte_identical_with_overrides(tmp_path):
    root = v1_tree(tmp_path, {"20_appearance.json": v1_file(v1_group(tier="P2"))})
    overrides = overrides_file(
        tmp_path,
        {
            "priority": {"g1": {"to": "must", "why": "gate ruling"}},
            "scene_overridable": {"g1": {"value": True, "why": "gate ruling"}},
        },
    )
    out, report = tmp_path / "out", tmp_path / "report"
    assert _run_cli(root, out, report, overrides) == 0
    snapshot = {p.name: p.read_bytes() for d in (out, report) for p in d.iterdir()}
    assert "OVERRIDES_APPLIED.md" in snapshot
    assert _run_cli(root, out, report, overrides) == 0
    again = {p.name: p.read_bytes() for d in (out, report) for p in d.iterdir()}
    assert snapshot == again
