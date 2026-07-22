"""Harvest engine: convert v1 option data into the v2 option format (stage O2).

Every transformation rule here is DECIDED in O2_INPUTS.md and
OPTION_FORMAT_SPEC.md (§§1, 11); the tool applies them mechanically and
FLAGS or REFUSES anything outside them — it never improvises:

- ``prompt`` -> ``image_text`` (v1 ``render`` true/absent) or ``chat_text``
  (``render: false``); never both. Text pours verbatim, empty strings kept
  (O2_INPUTS answer 2 — polish is a later authoring pass, see POLISH_FLAGS).
- rating: ungated files -> ``standard``, gated files -> ``explicit``; gated
  files move into the single output directory, rating declared in-file
  (answer 3, spec §1.13). Nothing maps to ``mature`` at harvest.
- old ``tier`` -> ``priority`` via the §1.6 default map (P0 must, P1 should,
  P2/P3 flavor) wherever the merged group carries image_text; NO overrides —
  the PRIORITY_REVIEW table is where overrides get decided (answer 4).
- ``class`` + ``tags`` -> one ``tags`` list (§1.8); option ``image`` ->
  ``thumb`` (§1.12); ``visible_when`` ``class`` predicate -> ``has_tag``.
- ``home`` per the answer-7 table, incl. the 10_identity per-group split.
- held keys -> one ``"_v1"`` comment object per group (answer 5); ``_``-
  prefixed comment keys carried verbatim at their original level (§1.9);
  ``render`` and ``tier`` are LOG-ONLY.
- ``00_age.json`` is CONSUMED, not emitted (answer 6; spec §8 struck).
- O2b: the planning gate's overrides file (``tools/harvest/overrides.json``)
  is consumed on top. Load order is DECIDED: the answer-7 home table first,
  THEN ``home`` overrides by group id (superseding the table wherever the
  group appears), then contradiction flagging on whatever remains.
  ``priority`` overrides apply after the §1.6 default map;
  ``scene_overridable`` entries with value true emit the group key on the
  first definition (identity homes only — the format error for a
  non-identity flag is the live safety net). Underscore-prefixed entries
  are comment records, not keys. ``why`` is required on every entry — an
  override without a reason is a tool error, and so is an override that
  never lands on an emitted group. Every override travels verbatim into
  ``OVERRIDES_APPLIED.md``.
- Any group contradicting its file's home, any numeric kind other than age,
  any un-mapped construct: FLAGGED in the log and HELD out of the emitted
  tree.
- The tool REFUSES to emit nulls or ``example_`` ids, and refuses an unknown
  source file (no decided home/rating exists for it).
- Deterministic: re-running over the same v1 tree emits byte-identical
  files and reports.

Emitted files keep their v1 filenames and numeric prefixes (load order) and
carry ``"format": 1``. The v2 validator is the gatekeeper: ``write_output``
strict-checks the staged tree and writes NOTHING unless it is clean.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from app.options.errors import FormatErrorRecord
from app.options.loader import load_catalog

# --- DECIDED tables (O2_INPUTS) --------------------------------------------

UNGATED_DIR = "app/data/options"
GATED_DIR = "app/data/options_gated"

# Answer 1: harvest exactly the repo-bundled files. An unknown file in a
# source directory is a refusal — no decided home/rating exists for it.
UNGATED_FILES = (
    "00_age.json",
    "10_identity.json",
    "20_appearance.json",
    "30_body.json",
    "35_species.json",
    "38_marks.json",
    "40_anatomy.json",
    "50_mind.json",
    "55_speech.json",
    "60_wardrobe.json",
    "70_life.json",
)
GATED_FILES = (
    "90_wardrobe_intimate.json",
    "91_anatomy_intimate.json",
    "92_piercings_intimate.json",
)

# Answer 6: consumed, not emitted (age lives on the record).
CONSUMED_FILES = ("00_age.json",)

# Answer 7: home per v1 file. 10_identity is a per-group split (function
# below); 00_age is consumed and has no home.
HOME_BY_FILE = {
    "20_appearance.json": "identity",
    "30_body.json": "identity",
    "35_species.json": "identity",
    "38_marks.json": "identity",
    "40_anatomy.json": "identity",
    "91_anatomy_intimate.json": "identity",
    "50_mind.json": "persona",
    "55_speech.json": "persona",
    "70_life.json": "persona",
    "60_wardrobe.json": "persona",
    "90_wardrobe_intimate.json": "persona",
    "92_piercings_intimate.json": "persona",
}

TIER_MAP = {"P0": "must", "P1": "should", "P2": "flavor", "P3": "flavor"}  # §1.6
KIND_MAP = {"single": "pick_one", "multi": "pick_many"}

# O2b: the shape of a planning-gate overrides file. Each section maps group
# ids to an entry carrying one value key and a required 'why'; the allowed
# value set is per section (None = must be a JSON bool).
OVERRIDE_SECTIONS = {
    "priority": ("to", {"must", "should", "flavor"}),
    "home": ("to", {"identity", "persona", "session"}),
    "scene_overridable": ("value", None),
}

# Answer 5: held in the per-group "_v1" comment object (field only if it
# differs from the group id), plus any unexpected leftover key.
HELD_GROUP_KEYS = ("field", "quick", "required", "widget", "region", "attribute", "aliases")
LOG_ONLY_KEYS = ("render", "tier")  # answer 5: information lives elsewhere
CARRIED_GROUP_KEYS = ("label", "section", "order", "hint")  # 1:1 to v2
V1_GROUP_KEYS = frozenset(
    {"id", "kind", "options", "visible_when"}
    | set(CARRIED_GROUP_KEYS)
    | set(HELD_GROUP_KEYS)
    | set(LOG_ONLY_KEYS)
)
V1_OPTION_KEYS = frozenset({"id", "label", "prompt", "tags", "class", "color", "image"})
V1_VW_PREDICATES = ("any", "in", "not_in", "class")  # class -> has_tag (§1.8)

# Answer 2 / POLISH_FLAGS: a group is flagged when its own _note or its
# file's _note marks the wording provisional. Detection is mechanical.
POLISH_MARKERS = ("provisional", "re-cut", "wording")


class HarvestError(ValueError):
    """The source contains something the harvest refuses to emit."""


@dataclass
class Flag:
    """A group flagged and held out of the emitted tree."""

    file: str
    group: str
    reason: str


@dataclass
class Overrides:
    """A validated planning-gate overrides file (O2b). ``why`` strings are
    authoritative and travel verbatim into OVERRIDES_APPLIED.md."""

    display: str  # how the reports name the source file
    note: str | None  # top-level _note, verbatim
    priority: dict[str, dict]  # gid -> {"to": ..., "why": ...}
    home: dict[str, dict]  # gid -> {"to": ..., "why": ...}
    scene_overridable: dict[str, dict]  # gid -> {"value": ..., "why": ...}
    comments: list  # (section, key, value) — comment records, never applied


@dataclass
class HarvestResult:
    source: dict  # {"url": ..., "commit": ...} of the v1 checkout
    files: dict[str, bytes]  # emitted filename -> serialized v2 file
    flags: list[Flag]
    inventory: list[dict]  # per-file counts and disposition
    log_md: str
    priority_md: str
    polish_md: str
    overrides_md: str = ""  # empty when no overrides file was given


@dataclass
class _Part:
    """One v1 group occurrence in one file (first definition or fragment)."""

    file: str
    rating: str
    raw: dict
    gid: str
    fragment: bool
    kind: str | None = None  # mapped v2 kind (first definitions only)
    home: str | None = None  # assigned home (first definitions only)
    tier: str | None = None
    render_eff: object = None  # effective v1 render (None = absent = image)
    vw: dict | None = None
    held: dict = field(default_factory=dict)  # the "_v1" content
    comments: list = field(default_factory=list)  # (key, value) in v1 order
    carried: dict = field(default_factory=dict)  # label/section/order/hint
    options: list | None = None  # emitted option dicts
    has_image: bool = False
    priority: str | None = None
    priority_default: str | None = None  # the §1.6 value before any override
    scene_over: bool = False  # O2b: gate override emits scene_overridable
    hold_reason: str | None = None

    def hold(self, reason: str) -> None:
        if self.hold_reason is None:
            self.hold_reason = reason


# --- helpers ----------------------------------------------------------------


def _git_source(root: Path) -> dict:
    def run(*args: str) -> str | None:
        try:
            proc = subprocess.run(
                ["git", "-C", str(root), *args], capture_output=True, text=True
            )
        except OSError:
            return None
        if proc.returncode != 0:
            return None
        return proc.stdout.strip() or None

    return {
        "url": run("config", "--get", "remote.origin.url"),
        "commit": run("rev-parse", "HEAD"),
    }


def _load_file(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HarvestError(f"{path.name}: cannot read v1 file: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("groups"), list):
        raise HarvestError(f"{path.name}: v1 file must be an object with a 'groups' list")
    return data


def load_overrides(path: Path | str) -> Overrides:
    """Read and validate a planning-gate overrides file (O2b).

    Raises :class:`HarvestError` on any violation: unreadable file, wrong
    ``format``, unknown section or entry key, bad value, or a missing
    ``why`` — an override without a reason is a tool error."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HarvestError(f"{path}: cannot read overrides file: {exc}") from exc
    if not isinstance(data, dict):
        raise HarvestError(f"{path.name}: overrides file must be a JSON object")
    if data.get("format") != 1:
        raise HarvestError(f"{path.name}: overrides file must carry \"format\": 1")
    note: str | None = None
    comments: list = []
    sections: dict[str, dict] = {k: {} for k in OVERRIDE_SECTIONS}
    for key, value in data.items():
        if key == "format":
            continue
        if key.startswith("_"):
            if key == "_note" and isinstance(value, str):
                note = value
            else:
                comments.append(("top-level", key, value))
            continue
        if key not in OVERRIDE_SECTIONS:
            raise HarvestError(f"{path.name}: unknown overrides section {key!r}")
        if not isinstance(value, dict):
            raise HarvestError(f"{path.name}: section {key!r} must be an object")
        value_key, allowed = OVERRIDE_SECTIONS[key]
        for gid, entry in value.items():
            if gid.startswith("_"):
                # Underscore-prefixed entries are comment records, not keys.
                comments.append((key, gid, entry))
                continue
            if not isinstance(entry, dict):
                raise HarvestError(f"{path.name}: override {key}/{gid} must be an object")
            why = entry.get("why")
            if not isinstance(why, str) or not why.strip():
                raise HarvestError(
                    f"{path.name}: override {key}/{gid} lacks a 'why' — an "
                    f"override without a reason is a tool error"
                )
            unknown = [
                k for k in entry if k not in (value_key, "why") and not k.startswith("_")
            ]
            if unknown:
                raise HarvestError(
                    f"{path.name}: override {key}/{gid} carries unknown key(s) {unknown}"
                )
            if value_key not in entry:
                raise HarvestError(f"{path.name}: override {key}/{gid} lacks {value_key!r}")
            val = entry[value_key]
            if allowed is None:
                if not isinstance(val, bool):
                    raise HarvestError(
                        f"{path.name}: override {key}/{gid} {value_key} must be a bool, "
                        f"got {val!r}"
                    )
            elif val not in allowed:
                raise HarvestError(
                    f"{path.name}: override {key}/{gid} {value_key} {val!r} not in "
                    f"{sorted(allowed)}"
                )
            sections[key][gid] = entry
    try:
        display = path.resolve().relative_to(Path.cwd()).as_posix()
    except ValueError:
        display = path.as_posix()
    return Overrides(
        display=display,
        note=note,
        priority=sections["priority"],
        home=sections["home"],
        scene_overridable=sections["scene_overridable"],
        comments=comments,
    )


def _assign_home(fname: str, gid: str, ov: Overrides | None, log: "_Log") -> str:
    # Answer 7: 10_identity splits per group — apparent_age is identity,
    # every other group is persona.
    if fname == "10_identity.json":
        table = "identity" if gid == "apparent_age" else "persona"
    else:
        table = HOME_BY_FILE[fname]
    # O2b: `home` overrides supersede the table wherever the group appears;
    # contradiction flagging runs on what remains after this.
    if ov is not None and gid in ov.home:
        log.home_overrides.append((gid, fname, table))
        return ov.home[gid]["to"]
    return table


def _serialize(obj: dict) -> bytes:
    return (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _refuse_nulls(obj: object, file: str, path: str) -> None:
    """The emitted tree may contain no nulls (tool refusal; v2 makes null a
    format error anywhere — O2_INPUTS answer 8.5)."""
    if obj is None:
        raise HarvestError(f"{file}: null value at {path}; the tool refuses to emit nulls")
    if isinstance(obj, dict):
        for k, v in obj.items():
            _refuse_nulls(v, file, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _refuse_nulls(v, file, f"{path}[{i}]")


def _refuse_example_id(file: str, kind: str, ident: str) -> None:
    if ident.startswith("example_"):
        raise HarvestError(
            f"{file}: {kind} id {ident!r} begins 'example_'; the tool refuses "
            f"to emit illustrative ids (spec §0)"
        )


def _note_matches_polish(note: object) -> bool:
    return isinstance(note, str) and any(m in note.lower() for m in POLISH_MARKERS)


# --- per-group parsing (sweep A) --------------------------------------------


def _parse_option(o: object, part: _Part, text_key: str, log: "_Log") -> dict | None:
    """Map one v1 option to its v2 dict; None means the group must be held."""
    gid = part.gid
    if not isinstance(o, dict):
        part.hold(f"option in group {gid!r} is not an object")
        return None
    unknown = [k for k in o if k not in V1_OPTION_KEYS and not k.startswith("_")]
    if unknown:
        part.hold(f"option {o.get('id')!r} carries un-mapped key(s) {unknown}")
        return None
    oid, label = o.get("id"), o.get("label")
    if not isinstance(oid, str) or not oid or not isinstance(label, str) or not label:
        part.hold(f"option {oid!r} lacks a usable id/label")
        return None
    for key in ("class", "tags"):
        v = o.get(key)
        if v is not None and not (
            isinstance(v, list) and all(isinstance(t, str) for t in v)
        ):
            part.hold(f"option {oid!r} key {key!r} is not a list of strings")
            return None
    out: dict = {}
    for k, v in o.items():  # comment keys carried verbatim, in order (§1.9)
        if k.startswith("_"):
            out[k] = v
            if k != "_note":
                log.comment_rows.append((part.file, f"{gid}/{oid}", k))
    out["id"] = oid
    out["label"] = label
    if "prompt" in o:  # answer 2: verbatim, one text key, empty strings kept
        prompt = o["prompt"]
        if not isinstance(prompt, str):
            part.hold(f"option {oid!r} prompt is not a string")
            return None
        out[text_key] = prompt
        if text_key == "image_text":
            part.has_image = True
        if prompt == "":
            log.empty_prompts += 1
    merged: list[str] = []  # §1.8: class + tags -> one tags list, deduped
    for t in list(o.get("class") or []) + list(o.get("tags") or []):
        if t not in merged:
            merged.append(t)
    if merged:
        out["tags"] = merged
    if "color" in o:
        out["color"] = o["color"]
    if "image" in o:  # §1.12: option image (thumbnail) renames to thumb
        out["thumb"] = o["image"]
        log.mapped_thumbs.append((part.file, f"{gid}/{oid}"))
    return out


def _map_visible_when(vw: object, part: _Part) -> dict | None:
    if not isinstance(vw, dict) or not isinstance(vw.get("group"), str):
        part.hold("un-mapped visible_when shape (no group reference)")
        return None
    preds = [p for p in V1_VW_PREDICATES if p in vw]
    extras = [k for k in vw if k != "group" and k not in V1_VW_PREDICATES]
    if len(preds) != 1 or extras:
        part.hold(f"un-mapped visible_when predicate(s) {preds + extras}")
        return None
    pred = preds[0]
    out_pred = "has_tag" if pred == "class" else pred  # §1.8
    return {"group": vw["group"], out_pred: vw[pred]}


class _Log:
    """Accumulates every log row the harvest log must carry."""

    def __init__(self) -> None:
        self.log_only_rows: list = []  # (file, gid, key, value)
        self.held_rows: list = []  # (file, gid, key, value)
        self.comment_rows: list = []  # (file, subject, key) — non-_note
        self.mapped_thumbs: list = []  # (file, subject)
        self.consumed_rows: list = []  # (file, text)
        self.field_drops = 0  # field == id, dropped per §1.10
        self.empty_prompts = 0  # empty v1 prompts preserved as empty texts
        self.home_overrides: list = []  # (gid, file, superseded table home)


def _parse_group(
    raw: object,
    fname: str,
    rating: str,
    defined: dict[str, _Part],
    log: _Log,
    ov: Overrides | None,
) -> _Part:
    part = _Part(file=fname, rating=rating, raw=raw if isinstance(raw, dict) else {}, gid="", fragment=False)
    if not isinstance(raw, dict) or not isinstance(raw.get("id"), str) or not raw["id"]:
        part.gid = "<no id>"
        part.hold("group without a usable string 'id'")
        return part
    gid = part.gid = raw["id"]
    part.fragment = gid in defined

    for k, v in raw.items():  # comment keys, in v1 order (§1.9)
        if k.startswith("_"):
            part.comments.append((k, v))
            if k != "_note":
                log.comment_rows.append((fname, gid, k))

    # LOG-ONLY keys (answer 5): recorded, never emitted.
    for k in LOG_ONLY_KEYS:
        if k in raw:
            log.log_only_rows.append((fname, gid, k, json.dumps(raw[k])))
    part.tier = raw.get("tier") if isinstance(raw.get("tier"), str) else (
        None if "tier" not in raw else str(raw["tier"])
    )

    # kind (merge-locked in v2 — a fragment may not touch it)
    if part.fragment:
        for locked in ("kind", "home"):
            if locked in raw:
                part.hold(f"extension fragment touches merge-locked key {locked!r}")
        base = defined[gid]
        part.render_eff = raw["render"] if "render" in raw else base.render_eff
        base_home = base.home
        file_home = _assign_home(fname, gid, ov, log)
        if base_home != file_home and part.hold_reason is None:
            part.hold(
                f"contradicts its file's home: fragment file {fname!r} is "
                f"{file_home!r} but group {gid!r} is defined in {base.file!r} "
                f"with home {base_home!r}"
            )
    else:
        kind = raw.get("kind")
        if kind == "number":
            # Answer 7: any numeric-kind group other than age is flagged and
            # held (age itself lives in the consumed 00_age.json).
            part.hold(f"numeric-kind group {gid!r} — only age is decided, and age is consumed")
        elif kind in KIND_MAP:
            part.kind = KIND_MAP[kind]
        else:
            part.hold(f"un-mapped kind {kind!r}")
        part.home = _assign_home(fname, gid, ov, log)
        part.render_eff = raw.get("render")

    if "render" in raw and not isinstance(raw["render"], bool):
        part.hold(f"un-mapped render value {raw['render']!r}")

    # held keys -> _v1 (answer 5); field only where it differs from the id
    for k in HELD_GROUP_KEYS:
        if k in raw:
            if k == "field" and raw[k] == gid:
                log.field_drops += 1  # §1.10: dropped, its info IS the id
                continue
            part.held[k] = raw[k]
            log.held_rows.append((fname, gid, k, json.dumps(raw[k])))
    for k in raw:  # any unexpected leftover key -> _v1 too (answer 5)
        if k.startswith("_") or k in V1_GROUP_KEYS:
            continue
        part.held[k] = raw[k]
        log.held_rows.append((fname, gid, k, json.dumps(raw[k])))

    for k in CARRIED_GROUP_KEYS:
        if k in raw:
            part.carried[k] = raw[k]

    if "visible_when" in raw:
        part.vw = _map_visible_when(raw["visible_when"], part)

    if "options" in raw:
        if not isinstance(raw["options"], list):
            part.hold("'options' is not a list")
        else:
            text_key = "chat_text" if part.render_eff is False else "image_text"
            opts = []
            for o in raw["options"]:
                out = _parse_option(o, part, text_key, log)
                if out is None:
                    break
                opts.append(out)
            else:
                part.options = opts
    elif not part.fragment:
        # v2 pick kinds require options; nothing decided maps a first
        # definition without them.
        part.hold("first definition without an 'options' list")
    return part


# --- assembly (sweep B) ------------------------------------------------------


def _assemble_group(part: _Part) -> dict:
    out: dict = {"id": part.gid}
    _refuse_example_id(part.file, "group", part.gid)
    for k, v in part.comments:
        out[k] = v
    if "label" in part.carried:
        out["label"] = part.carried["label"]
    if not part.fragment:
        out["kind"] = part.kind
        out["home"] = part.home
        if part.scene_over:  # O2b gate override; spec §4 key order
            out["scene_overridable"] = True
        if part.priority is not None:
            out["priority"] = part.priority
    if part.vw is not None:
        out["visible_when"] = part.vw
    for k in ("section", "order", "hint"):
        if k in part.carried:
            out[k] = part.carried[k]
    if part.held:
        out["_v1"] = part.held
    if part.options is not None:
        for o in part.options:
            _refuse_example_id(part.file, "option", o["id"])
        out["options"] = part.options
    return out


def harvest_tree(
    v1_root: Path | str, overrides: Overrides | None = None
) -> HarvestResult:
    """Read a v1 checkout and produce the full emission set and reports.

    Pure transformation — writes nothing. Raises :class:`HarvestError` on a
    refusal (unknown source file, unreadable source, null, example_ id, or
    an override that never lands on an emitted group)."""
    v1_root = Path(v1_root)
    log = _Log()
    flags: list[Flag] = []
    inventory: list[dict] = []
    defined: dict[str, _Part] = {}
    parts_by_file: list[tuple[str, str, dict, list[_Part]]] = []

    for dirname, names, rating in (
        (UNGATED_DIR, UNGATED_FILES, "standard"),
        (GATED_DIR, GATED_FILES, "explicit"),
    ):
        directory = v1_root / dirname
        found = (
            sorted(p.name for p in directory.glob("*.json") if p.is_file())
            if directory.is_dir()
            else []
        )
        unknown = [n for n in found if n not in names]
        if unknown:
            raise HarvestError(
                f"unknown source file(s) {unknown} in {dirname}; the harvest "
                f"inventory is decided (O2_INPUTS answer 1) and carries no "
                f"home/rating for them"
            )
        for name in names:
            if name not in found:
                inventory.append(
                    {"file": name, "rating": rating, "disposition": "absent",
                     "v1_groups": 0, "v1_options": 0, "groups": 0, "options": 0}
                )
                continue
            data = _load_file(directory / name)
            v1_groups = data["groups"]
            v1_options = sum(
                len(g.get("options", [])) for g in v1_groups if isinstance(g, dict)
            )
            if name in CONSUMED_FILES:
                # Answer 6: consumed, not emitted — age lives on the record.
                ids = [g.get("id") for g in v1_groups if isinstance(g, dict)]
                log.consumed_rows.append(
                    (name, f"consumed whole (answer 6): groups {ids}")
                )
                inventory.append(
                    {"file": name, "rating": rating, "disposition": "consumed",
                     "v1_groups": len(v1_groups), "v1_options": v1_options,
                     "groups": 0, "options": 0}
                )
                continue
            file_comments = [(k, v) for k, v in data.items() if k.startswith("_")]
            parts: list[_Part] = []
            for raw in v1_groups:
                part = _parse_group(raw, name, rating, defined, log, overrides)
                parts.append(part)
                if not part.fragment and part.gid != "<no id>" and part.gid not in defined:
                    defined[part.gid] = part
            parts_by_file.append((name, rating, dict(file_comments), parts))
            inventory.append(
                {"file": name, "rating": rating, "disposition": "emitted",
                 "v1_groups": len(v1_groups), "v1_options": v1_options,
                 "groups": 0, "options": 0}
            )

    # A fragment of a held defining group cannot merge — hold it too.
    for _, _, _, parts in parts_by_file:
        for part in parts:
            if part.fragment and defined[part.gid].hold_reason is not None:
                part.hold(f"defining group (in {defined[part.gid].file!r}) is held")

    # §1.6 priority on the MERGED group: required wherever any option carries
    # image_text; mapped from the first definition's tier. O2b: the gate's
    # priority overrides apply AFTER the default map.
    merged_image: dict[str, bool] = {}
    for _, _, _, parts in parts_by_file:
        for part in parts:
            if part.hold_reason is None and part.has_image:
                merged_image[part.gid] = True
    applied_priority: dict[str, tuple[str, str]] = {}  # gid -> (default, final)
    for _, _, _, parts in parts_by_file:
        for part in parts:
            if part.fragment or part.hold_reason is not None:
                continue
            if merged_image.get(part.gid):
                if part.tier is None:
                    part.hold(
                        "carries image_text but no v1 tier — the §1.6 map has "
                        "no input and priority overrides are the gate's, not "
                        "the harvest's"
                    )
                elif part.tier not in TIER_MAP:
                    part.hold(f"un-mapped tier {part.tier!r}")
                else:
                    part.priority_default = TIER_MAP[part.tier]
                    part.priority = part.priority_default
                    entry = overrides.priority.get(part.gid) if overrides else None
                    if entry is not None:
                        part.priority = entry["to"]
                        applied_priority[part.gid] = (part.priority_default, part.priority)

    # Holds cascade once more (a group held for priority may have fragments).
    for _, _, _, parts in parts_by_file:
        for part in parts:
            if part.fragment and part.hold_reason is None:
                base = defined[part.gid]
                if base.hold_reason is not None:
                    part.hold(f"defining group (in {base.file!r}) is held")

    # O2b: scene_overridable overrides with value true emit the group key on
    # the first definition (identity homes only — the validator's format
    # error for a non-identity flag is the live safety net).
    if overrides is not None:
        for _, _, _, parts in parts_by_file:
            for part in parts:
                if part.fragment or part.hold_reason is not None:
                    continue
                entry = overrides.scene_overridable.get(part.gid)
                if entry is not None and entry["value"] is True:
                    part.scene_over = True

    files: dict[str, bytes] = {}
    inv_by_name = {row["file"]: row for row in inventory}
    priority_rows: list = []
    polish_rows: list = []
    emitted_gids: set[str] = set()
    emitted_first_defs: set[str] = set()
    for name, rating, file_comments, parts in parts_by_file:
        emitted_groups = []
        file_note = file_comments.get("_note")
        for part in parts:
            if part.hold_reason is not None:
                flags.append(Flag(name, part.gid, part.hold_reason))
                continue
            emitted_groups.append(_assemble_group(part))
            emitted_gids.add(part.gid)
            if not part.fragment:
                emitted_first_defs.add(part.gid)
            if not part.fragment and part.priority is not None:
                final = part.priority
                if part.gid in applied_priority:
                    final = f"{part.priority} — OVERRIDE"
                priority_rows.append(
                    (name, part.gid, part.tier, part.priority_default, final)
                )
            elif part.fragment:
                base = defined[part.gid]
                priority_rows.append(
                    (name, part.gid, "—", f"(fragment — inherits from {base.file})", "—")
                )
            own_note = dict(part.comments).get("_note")
            if _note_matches_polish(own_note):
                polish_rows.append((name, part.gid, "group _note", own_note))
            elif _note_matches_polish(file_note):
                polish_rows.append((name, part.gid, "file _note", file_note))
        row = inv_by_name[name]
        row["groups"] = len(emitted_groups)
        row["options"] = sum(len(g.get("options", [])) for g in emitted_groups)
        if not emitted_groups:
            row["disposition"] = "held (no groups left)"
            continue
        obj: dict = {}
        for k, v in file_comments.items():
            obj[k] = v
        obj["format"] = 1
        obj["rating"] = rating
        obj["groups"] = emitted_groups
        _refuse_nulls(obj, name, "$")
        files[name] = _serialize(obj)

    # O2b: every non-comment override entry must have landed on an emitted
    # group — an override that targets nothing is a tool error.
    if overrides is not None:
        unapplied = [
            f"priority/{gid}" for gid in overrides.priority if gid not in applied_priority
        ]
        unapplied += [f"home/{gid}" for gid in overrides.home if gid not in emitted_gids]
        unapplied += [
            f"scene_overridable/{gid}"
            for gid in overrides.scene_overridable
            if gid not in emitted_first_defs
        ]
        if unapplied:
            raise HarvestError(
                "override(s) never landed on an emitted group: "
                + ", ".join(unapplied)
                + " — an override that targets nothing is a tool error"
            )

    source = _git_source(v1_root)
    result = HarvestResult(
        source=source,
        files=files,
        flags=flags,
        inventory=inventory,
        log_md="",
        priority_md="",
        polish_md="",
    )
    result.log_md = _render_log(result, log)
    result.priority_md = _render_priority(priority_rows, len(applied_priority))
    result.polish_md = _render_polish(polish_rows)
    if overrides is not None:
        n_first = sum(1 for r in priority_rows if r[3] in TIER_MAP.values())
        n_frag = len(priority_rows) - n_first
        result.overrides_md = _render_overrides(
            overrides, applied_priority, log.home_overrides, n_first, n_frag
        )
    return result


# --- report rendering --------------------------------------------------------


def _render_log(result: HarvestResult, log: _Log) -> str:
    lines = ["# HARVEST LOG — v1 → v2 option data (stage O2)", ""]
    lines += [
        f"- v1 source: {result.source['url'] or '(no git remote found)'}",
        f"- v1 commit: {result.source['commit'] or '(not a git checkout)'}",
        f"- emitted files: {len(result.files)}",
        "",
        "## Inventory — per-file counts vs v1",
        "",
        "| v1 file | rating | v1 groups | v1 options | emitted groups | emitted options | disposition |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in result.inventory:
        lines.append(
            f"| {row['file']} | {row['rating']} | {row['v1_groups']} | "
            f"{row['v1_options']} | {row['groups']} | {row['options']} | "
            f"{row['disposition']} |"
        )
    lines += ["", "## Flags — groups held out of the emitted tree", ""]
    if result.flags:
        for i, f in enumerate(result.flags, 1):
            lines.append(f"{i}. `{f.file}` / `{f.group}`: {f.reason}")
    else:
        lines.append("(none)")
    for title, rows in (
        ("Consumed", log.consumed_rows),
    ):
        lines += ["", f"## {title}", ""]
        if rows:
            for name, text in rows:
                lines.append(f"- `{name}`: {text}")
        else:
            lines.append("(none)")
    lines += [
        "",
        "## Log-only keys (`render`, `tier`) — information lives in text presence and `priority`",
        "",
        "| file | group | key | value |",
        "|---|---|---|---|",
    ]
    for file, gid, key, value in log.log_only_rows:
        lines.append(f"| {file} | {gid} | {key} | `{value}` |")
    lines += [
        "",
        "## Held keys — carried in each group's `_v1` comment object",
        "",
        "| file | group | key | value |",
        "|---|---|---|---|",
    ]
    if log.held_rows:
        for file, gid, key, value in log.held_rows:
            lines.append(f"| {file} | {gid} | {key} | `{value}` |")
    else:
        lines.append("| (none) | | | |")
    lines += ["", "## Comment keys other than `_note` carried verbatim (§1.9)", ""]
    if log.comment_rows:
        for file, subject, key in log.comment_rows:
            lines.append(f"- `{file}` / `{subject}`: `{key}`")
    else:
        lines.append("(none)")
    lines += ["", "## Option `image` → `thumb` renames (§1.12)", ""]
    if log.mapped_thumbs:
        for file, subject in log.mapped_thumbs:
            lines.append(f"- `{file}` / `{subject}`")
    else:
        lines.append("(none — v1 carries no option `image` keys)")
    lines += [
        "",
        "## Notes",
        "",
        f"- `field` equal to the group id dropped per §1.10: {log.field_drops} "
        f"occurrence(s); zero differed (a differing `field` would be held in `_v1`).",
        f"- Empty v1 `prompt` strings preserved verbatim as empty text values "
        f"(answer 2 — delete nothing silently): {log.empty_prompts} option(s).",
        "",
    ]
    return "\n".join(lines)


def _render_priority(rows: list, overridden: int) -> str:
    lines = [
        "# PRIORITY REVIEW — §1.6 default map, then the gate's overrides",
        "",
        "Map: P0→must, P1→should, P2→flavor, P3→flavor (O2_INPUTS answer 4).",
        "Overrides are the planning gate's, recorded in the overrides file and",
        "OVERRIDES_APPLIED.md, applied after the default map; overridden rows",
        f"are marked in the final column. Overridden rows in this emission: {overridden}.",
        "",
        "| file | group | v1 tier | default priority | final |",
        "|---|---|---|---|---|",
    ]
    for file, gid, tier, default, final in rows:
        lines.append(f"| {file} | {gid} | {tier} | {default} | {final} |")
    lines.append("")
    return "\n".join(lines)


def _render_overrides(
    ov: Overrides,
    applied_priority: dict[str, tuple[str, str]],
    home_overrides: list,
    first_def_rows: int,
    fragment_rows: int,
) -> str:
    def esc(s: str) -> str:
        return s.replace("|", "\\|")

    lines = [
        "# OVERRIDES APPLIED — planning-gate decisions consumed by this run",
        "",
        f"- overrides file: `{ov.display}`",
    ]
    if ov.note is not None:
        lines.append(f"- source `_note`, verbatim: {ov.note}")
    lines += ["", "## `priority` — applied after the §1.6 default map", ""]
    if ov.priority:
        lines += [
            "| group | default | override | why (verbatim) |",
            "|---|---|---|---|",
        ]
        for gid, entry in ov.priority.items():
            default, final = applied_priority[gid]
            lines.append(f"| {gid} | {default} | {final} | {esc(entry['why'])} |")
    else:
        lines.append("(none)")
    lines += [
        "",
        "## `home` — applied after the answer-7 table, superseding it wherever the group appears",
        "",
    ]
    if ov.home:
        lines += [
            "| group | override | supersedes (answer-7 table) | why (verbatim) |",
            "|---|---|---|---|",
        ]
        for gid, entry in ov.home.items():
            occ = [f"{table} ({fname})" for g, fname, table in home_overrides if g == gid]
            lines.append(
                f"| {gid} | {entry['to']} | {', '.join(occ)} | {esc(entry['why'])} |"
            )
    else:
        lines.append("(none)")
    lines += [
        "",
        "## `scene_overridable` — identity homes only; value true emits the group key",
        "",
    ]
    if ov.scene_overridable:
        lines += ["| group | value | why (verbatim) |", "|---|---|---|"]
        for gid, entry in ov.scene_overridable.items():
            lines.append(
                f"| {gid} | {json.dumps(entry['value'])} | {esc(entry['why'])} |"
            )
    else:
        lines.append("(none)")
    lines += ["", "## Comment records — recorded verbatim, never applied as keys", ""]
    if ov.comments:
        for section, key, value in ov.comments:
            lines.append(
                f"- `{section}` / `{key}`: `{json.dumps(value, ensure_ascii=False)}`"
            )
    else:
        lines.append("(none)")
    overridden = len(applied_priority)
    lines += [
        "",
        "## Defaulted rows",
        "",
        f"- First-definition priority rows in this emission: {first_def_rows}; "
        f"overridden: {overridden}; standing as defaulted: {first_def_rows - overridden}.",
        f"- Fragment rows (inherit the defining group's priority, no default of "
        f"their own): {fragment_rows}.",
        "- The source `_note`'s own row arithmetic, where present, was counted at",
        "  the gate against the review table as it then stood — before any held",
        "  group returned; the counts above are recomputed from this emission.",
        "",
    ]
    return "\n".join(lines)


def _render_polish(rows: list) -> str:
    lines = [
        "# POLISH_FLAGS — wording poured verbatim, polish is a later pass",
        "",
        "O2_INPUTS answer 2: chat-text wording polish is NOT done during",
        "harvest. A group is flagged here when its own `_note` or its file's",
        "`_note` marks wording provisional (mechanical detection: the note",
        f"contains one of {list(POLISH_MARKERS)}, case-insensitive).",
        "",
        "| file | group | trigger | note excerpt |",
        "|---|---|---|---|",
    ]
    for file, gid, trigger, note in rows:
        excerpt = note if len(note) <= 120 else note[:117] + "..."
        excerpt = excerpt.replace("|", "\\|")
        lines.append(f"| {file} | {gid} | {trigger} | {excerpt} |")
    lines.append("")
    return "\n".join(lines)


# --- output ------------------------------------------------------------------


def write_output(
    result: HarvestResult, out_dir: Path | str, report_dir: Path | str
) -> list[FormatErrorRecord]:
    """Validate the emission set and, only if clean, write it.

    The v2 validator is the gatekeeper: the emission set is staged to a temp
    directory and loaded with the full rule set; any error means NOTHING is
    written and the errors are returned. On success the data files land in
    ``out_dir`` and the three reports in ``report_dir``, all LF/UTF-8."""
    out_dir, report_dir = Path(out_dir), Path(report_dir)
    with tempfile.TemporaryDirectory() as staging:
        for name, blob in result.files.items():
            (Path(staging) / name).write_bytes(blob)
        catalog = load_catalog([staging])
        if catalog.errors:
            return catalog.errors
    foreign = [
        p.name
        for p in sorted(out_dir.glob("*.json"))
        if p.is_file() and p.name not in result.files
    ] if out_dir.is_dir() else []
    if foreign:
        raise HarvestError(
            f"output directory {out_dir} contains foreign data file(s) "
            f"{foreign}; refusing to mix them with the emission set"
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, blob in result.files.items():
        (out_dir / name).write_bytes(blob)
    report_dir.mkdir(parents=True, exist_ok=True)
    reports = [
        ("HARVEST_LOG.md", result.log_md),
        ("PRIORITY_REVIEW.md", result.priority_md),
        ("POLISH_FLAGS.md", result.polish_md),
    ]
    if result.overrides_md:  # only a run with an overrides file writes this
        reports.append(("OVERRIDES_APPLIED.md", result.overrides_md))
    for name, text in reports:
        (report_dir / name).write_bytes(text.encode("utf-8"))
    return []
