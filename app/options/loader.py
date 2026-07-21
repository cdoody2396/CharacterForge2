"""Option file loader: parse, per-file validation, atomic apply, merge (§§3–7).

Carryover from v1 (spec §4, DECIDED, proven):
- Files load in (directory order, then filename order); a later file reusing
  a group id appends its options and overrides scalar keys.
- A re-declared option id REPLACES the earlier option in place (later file
  wins, position kept); new ids append.
- Files apply atomically: every change lands on a staged copy that replaces
  the live groups only if the whole file is clean — a malformed second group
  cannot leave the first behind.
- Default load is resilient (bad file skipped, error recorded on the
  catalog); ``strict=True`` raises for tests and authoring.
- An extension fragment is partial: required keys are enforced at first
  definition only. ``kind``, ``home``, ``feeds``, and ``scene_overridable``
  are merge-locked (O2_INPUTS answer 8.3): a fragment touching any of them
  is a format error.

v2 tightenings over v1: unknown keys are format errors (§1.9, ``_``-prefixed
comment keys legal and ignored anywhere); a present-but-invalid
``visible_when`` is a format error, never a silent degrade (§1.14).

Catalog-level laws (§7 + the merged-state checks of §§4 and 6) run after all
files merge; violations raise :class:`CatalogError` in strict mode and are
recorded on ``catalog.errors`` in resilient mode.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Iterable

from app.options import errors as E
from app.options.catalog import (
    VISIBLE_WHEN_PREDICATES,
    Catalog,
    Group,
    Option,
)
from app.options.errors import CatalogError, FormatErrorRecord, OptionFormatError

VALID_RATINGS = ("standard", "mature", "explicit")  # §1.1
VALID_KINDS = ("pick_one", "pick_many", "free_text")  # §1.3
PICK_KINDS = ("pick_one", "pick_many")
VALID_HOMES = ("identity", "persona", "session")  # §1.4
VALID_PRIORITIES = ("must", "should", "flavor")  # §1.5
VALID_STATUS = ("active", "retired")  # §1.7
VALID_FEEDS = ("image", "chat", "both")  # §4
FREE_TEXT_CEILING = 240  # §1.2 — the format refuses any limit above this

# §5: option ids are stable and chat-emittable — lowercase a–z0–9_, ≤ 40.
# O2_INPUTS answer 8.2: group ids obey the same hygiene rule.
_ID_RE = re.compile(r"^[a-z0-9_]{1,40}$")

# O2_INPUTS answer 8.3: merge-locked group keys — an extension fragment
# touching any of them is a format error.
_MERGE_LOCKED_KEYS = ("kind", "home", "feeds", "scene_overridable")
# §5: color is a #rrggbb swatch hint (hex case not significant).
_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

_FILE_KEYS = frozenset({"format", "rating", "groups"})
_GROUP_KEYS = frozenset(
    {
        "id",
        "label",
        "kind",
        "home",
        "scene_overridable",
        "priority",
        "max_picks",
        "feeds",
        "max_chars",
        "visible_when",
        "section",
        "order",
        "hint",
        "tags",
        "options",
    }
)
_OPTION_KEYS = frozenset(
    {"id", "label", "image_text", "chat_text", "tags", "color", "thumb", "status"}
)
_VISIBLE_WHEN_KEYS = frozenset({"group"} | set(VISIBLE_WHEN_PREDICATES))


def _err(file: str, code: str, subject: str | None, message: str) -> OptionFormatError:
    return OptionFormatError(file, code, subject, message)


def _visible_keys(data: dict) -> list[str]:
    """The keys validation sees: everything except §1.9 comment keys, which
    are legal and ignored anywhere."""
    return [k for k in data if not (isinstance(k, str) and k.startswith("_"))]


def _check_unknown_keys(
    data: dict, allowed: frozenset, file: str, subject: str | None, where: str
) -> None:
    for key in _visible_keys(data):
        if key not in allowed:
            raise _err(
                file, E.UNKNOWN_KEY, subject, f"{where} has unknown key {key!r}"
            )


def _require_str(
    data: dict, key: str, file: str, subject: str | None, where: str
) -> str:
    if key not in data:
        raise _err(file, E.MISSING_KEY, subject, f"{where} is missing {key!r}")
    return _opt_str(data, key, file, subject, where)  # type: ignore[return-value]


def _opt_str(
    data: dict, key: str, file: str, subject: str | None, where: str
) -> str | None:
    if key not in data:
        return None
    value = data[key]
    if not isinstance(value, str) or not value:
        raise _err(
            file,
            E.BAD_KEY_TYPE,
            subject,
            f"{where} key {key!r} must be a non-empty string, got {value!r}",
        )
    return value


def _opt_str_list(
    data: dict, key: str, file: str, subject: str | None, where: str
) -> tuple[str, ...]:
    if key not in data:
        return ()
    value = data[key]
    if not isinstance(value, list) or not all(
        isinstance(v, str) and v for v in value
    ):
        raise _err(
            file,
            E.BAD_KEY_TYPE,
            subject,
            f"{where} key {key!r} must be a list of non-empty strings",
        )
    return tuple(value)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


# --- option parsing (§5) ---------------------------------------------------


def _parse_option(
    data: object, file: str, group_id: str, rating: str
) -> Option:
    if not isinstance(data, dict):
        raise _err(
            file, E.BAD_KEY_TYPE, group_id, f"group {group_id!r}: option must be an object"
        )
    where = f"group {group_id!r} option"
    if "id" not in data:
        raise _err(file, E.MISSING_KEY, group_id, f"{where} is missing 'id'")
    oid = data["id"]
    subject = f"{group_id}/{oid}"
    if not isinstance(oid, str) or not _ID_RE.match(oid):
        raise _err(
            file,
            E.BAD_OPTION_ID,
            subject,
            f"{where} id {oid!r} violates the id rule (lowercase a-z0-9_, "
            f"1-40 chars, §5)",
        )
    where = f"group {group_id!r} option {oid!r}"
    _check_unknown_keys(data, _OPTION_KEYS, file, subject, where)
    label = _require_str(data, "label", file, subject, where)
    status = _opt_str(data, "status", file, subject, where)
    if status is not None and status not in VALID_STATUS:
        raise _err(
            file,
            E.BAD_STATUS,
            subject,
            f"{where} has invalid status {status!r}; expected one of {VALID_STATUS}",
        )
    color = _opt_str(data, "color", file, subject, where)
    if color is not None and not _COLOR_RE.match(color):
        raise _err(
            file, E.BAD_COLOR, subject, f"{where} color {color!r} is not '#rrggbb'"
        )
    # image_text / chat_text: presence is meaning (Decision 3) — a present
    # key must be a string; absence stays None.
    for key in ("image_text", "chat_text"):
        if key in data and not isinstance(data[key], str):
            raise _err(
                file, E.BAD_KEY_TYPE, subject, f"{where} key {key!r} must be a string"
            )
    return Option(
        id=oid,
        label=label,
        image_text=data.get("image_text"),
        chat_text=data.get("chat_text"),
        tags=_opt_str_list(data, "tags", file, subject, where),
        color=color,
        thumb=_opt_str(data, "thumb", file, subject, where),
        status=status or "active",
        source_file=file,
        rating=rating,
    )


def _parse_options_list(
    data: dict, file: str, group_id: str, rating: str
) -> list[Option]:
    raw = data["options"]
    if not isinstance(raw, list):
        raise _err(
            file, E.BAD_KEY_TYPE, group_id, f"group {group_id!r} 'options' must be a list"
        )
    options: list[Option] = []
    seen: set[str] = set()
    for entry in raw:
        opt = _parse_option(entry, file, group_id, rating)
        if opt.id in seen:
            # §7.3: duplicate option ids within a merged group are a format
            # error at merge time — within one file's group list this is the
            # only way a true duplicate can arise (cross-file re-declaration
            # is the v1 replace-in-place dedupe instead).
            raise _err(
                file,
                E.DUPLICATE_OPTION_ID,
                f"{group_id}/{opt.id}",
                f"group {group_id!r} lists option id {opt.id!r} twice",
            )
        seen.add(opt.id)
        options.append(opt)
    return options


# --- visible_when structural validation (§6, §1.14) ------------------------


def _parse_visible_when(data: dict, file: str, group_id: str) -> dict | None:
    """Validate and normalize a visible_when condition. Present but invalid
    is a FORMAT ERROR (§1.14) — v1's silent degrade is gone."""
    if "visible_when" not in data:
        return None
    value = data["visible_when"]

    def bad(reason: str) -> OptionFormatError:
        return _err(
            file,
            E.BAD_VISIBLE_WHEN,
            group_id,
            f"group {group_id!r} visible_when is invalid: {reason}",
        )

    if not isinstance(value, dict):
        raise bad("must be an object")
    _check_unknown_keys(
        value, _VISIBLE_WHEN_KEYS, file, group_id, f"group {group_id!r} visible_when"
    )
    ref = value.get("group")
    if not isinstance(ref, str) or not ref:
        raise bad("'group' must name a group id")
    preds = [p for p in VISIBLE_WHEN_PREDICATES if p in value]
    if len(preds) != 1:
        raise bad(
            f"exactly one predicate of {VISIBLE_WHEN_PREDICATES} is required, "
            f"got {preds or 'none'}"
        )
    pred = preds[0]
    pv = value[pred]
    if pred == "any":
        if pv is not True:
            raise bad("'any' must be true")
        return {"group": ref, "any": True}
    if pred in ("in", "not_in"):
        if (
            not isinstance(pv, list)
            or not pv
            or not all(isinstance(v, str) and v for v in pv)
        ):
            raise bad(f"{pred!r} must be a non-empty list of option ids")
        return {"group": ref, pred: list(pv)}
    # has_tag
    if not isinstance(pv, str) or not pv:
        raise bad("'has_tag' must be a non-empty tag string")
    return {"group": ref, "has_tag": pv}


# --- group parsing / merging (§4) ------------------------------------------


def _scalar_setters(data: dict, file: str, gid: str, group: Group) -> None:
    """Apply the provided §4 scalar keys onto ``group`` (used by both the
    new-group and merge paths; required-key presence is the caller's)."""
    where = f"group {gid!r}"
    if "label" in data:
        group.label = _require_str(data, "label", file, gid, where)
    if "home" in data:
        home = _require_str(data, "home", file, gid, where)
        if home not in VALID_HOMES:
            raise _err(
                file,
                E.BAD_HOME,
                gid,
                f"{where} has invalid home {home!r}; expected one of {VALID_HOMES}",
            )
        group.home = home
    if "scene_overridable" in data:
        value = data["scene_overridable"]
        if not isinstance(value, bool):
            raise _err(
                file, E.BAD_KEY_TYPE, gid, f"{where} 'scene_overridable' must be a bool"
            )
        group.scene_overridable = value
    if "priority" in data:
        priority = _require_str(data, "priority", file, gid, where)
        if priority not in VALID_PRIORITIES:
            raise _err(
                file,
                E.BAD_PRIORITY,
                gid,
                f"{where} has invalid priority {priority!r}; expected one of "
                f"{VALID_PRIORITIES}",
            )
        group.priority = priority
    if "max_picks" in data:
        value = data["max_picks"]
        if not _is_int(value) or value < 1:
            raise _err(
                file, E.BAD_MAX_PICKS, gid, f"{where} 'max_picks' must be an int >= 1"
            )
        group.max_picks = value
    if "feeds" in data:
        feeds = _require_str(data, "feeds", file, gid, where)
        if feeds not in VALID_FEEDS:
            raise _err(
                file,
                E.BAD_FEEDS,
                gid,
                f"{where} has invalid feeds {feeds!r}; expected one of {VALID_FEEDS}",
            )
        group.feeds = feeds
    if "max_chars" in data:
        value = data["max_chars"]
        if not _is_int(value) or value < 1 or value > FREE_TEXT_CEILING:
            # §1.2 / Decision 7-amended: a declared limit above 240 is a
            # format error in the FORMAT itself.
            raise _err(
                file,
                E.BAD_MAX_CHARS,
                gid,
                f"{where} 'max_chars' must be an int in 1..{FREE_TEXT_CEILING}, "
                f"got {value!r}",
            )
        group.max_chars = value
    if "visible_when" in data:
        group.visible_when = _parse_visible_when(data, file, gid)
    if "section" in data:
        group.section = _require_str(data, "section", file, gid, where)
    if "order" in data:
        value = data["order"]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise _err(file, E.BAD_KEY_TYPE, gid, f"{where} 'order' must be a number")
        group.order = float(value)
    if "hint" in data:
        group.hint = _require_str(data, "hint", file, gid, where)
    if "tags" in data:
        group.tags = _opt_str_list(data, "tags", file, gid, where)


def _check_group_state(group: Group, file: str) -> None:
    """Laws on the RESULTING group state, run after every new-group build and
    after every merge fragment — neither path can leave an illegal state."""
    gid = group.id
    where = f"group {gid!r}"
    if group.is_free_text:
        # §7.1 (decidable per file): free_text with home session is illegal.
        if group.home == "session":
            raise _err(
                file,
                E.FREE_TEXT_SESSION,
                gid,
                f"{where} is free_text with home 'session'; free_text is legal "
                f"only for identity and persona (two-slot law, §7)",
            )
        # §4: feeds and max_chars are REQUIRED on free_text.
        if group.feeds is None:
            raise _err(
                file, E.MISSING_KEY, gid, f"{where} is free_text and missing 'feeds'"
            )
        if group.max_chars is None:
            raise _err(
                file,
                E.MISSING_KEY,
                gid,
                f"{where} is free_text and missing 'max_chars'",
            )
        if group.max_picks is not None:
            raise _err(
                file,
                E.MAX_PICKS_ON_NON_PICK_MANY,
                gid,
                f"{where} is free_text and may not carry 'max_picks'",
            )
    else:
        # §4: feeds/max_chars are free_text-only — typed content can't
        # declare its reader by presence (Decision 7 pt 1).
        if group.feeds is not None:
            raise _err(
                file,
                E.FEEDS_ON_PICK_KIND,
                gid,
                f"{where} is {group.kind} and may not carry 'feeds'",
            )
        if group.max_chars is not None:
            raise _err(
                file,
                E.MAX_CHARS_ON_PICK_KIND,
                gid,
                f"{where} is {group.kind} and may not carry 'max_chars'",
            )
        if group.max_picks is not None and group.kind != "pick_many":
            raise _err(
                file,
                E.MAX_PICKS_ON_NON_PICK_MANY,
                gid,
                f"{where} is {group.kind} and may not carry 'max_picks'",
            )
    # §4 / Decision 4a: scene_overridable is legal ONLY on home identity.
    if group.scene_overridable and group.home != "identity":
        raise _err(
            file,
            E.SCENE_OVERRIDABLE_NON_IDENTITY,
            gid,
            f"{where} has scene_overridable with home {group.home!r}; it is "
            f"legal only when home is 'identity' (Decision 4a)",
        )


def _new_group(data: dict, file: str, rating: str) -> Group:
    gid = data["id"]
    where = f"group {gid!r}"
    _require_str(data, "label", file, gid, where)
    if "kind" not in data:
        raise _err(file, E.MISSING_KEY, gid, f"{where} is missing 'kind'")
    kind = data["kind"]
    if kind not in VALID_KINDS:
        raise _err(
            file,
            E.BAD_KIND,
            gid,
            f"{where} has invalid kind {kind!r}; expected one of {VALID_KINDS}",
        )
    if "home" not in data:
        raise _err(file, E.MISSING_KEY, gid, f"{where} is missing 'home'")
    if kind in PICK_KINDS and "options" not in data:
        raise _err(
            file,
            E.OPTIONS_MISSING,
            gid,
            f"{where} is {kind} and requires an 'options' list",
        )
    if kind == "free_text" and "options" in data:
        raise _err(
            file,
            E.OPTIONS_ON_FREE_TEXT,
            gid,
            f"{where} is free_text and may not carry 'options'",
        )
    # Rating is an OPTION-level fact only (O2_INPUTS answer 8.4): each option
    # is stamped with its file's rating; the group model carries none.
    group = Group(id=gid, label="", kind=kind, home="", sources=[file])
    _scalar_setters(data, file, gid, group)
    if "options" in data:
        group.options = _parse_options_list(data, file, gid, rating)
    return group


def _merge_group(existing: Group, data: dict, file: str, rating: str) -> None:
    """Extend an existing group from a later file's fragment (v1 semantics):
    scalar keys override; options append, with a re-declared option id
    replacing the earlier one in place (later file wins, position kept).
    ``kind``, ``home``, ``feeds``, ``scene_overridable`` are merge-locked
    (O2_INPUTS answer 8.3): a fragment touching any of them — even with an
    identical value — is a format error."""
    gid = existing.id
    for key in _MERGE_LOCKED_KEYS:
        if key in data:
            raise _err(
                file,
                E.MERGE_LOCKED_KEY,
                gid,
                f"group {gid!r} extension touches merge-locked key {key!r}; "
                f"{_MERGE_LOCKED_KEYS} are fixed at first definition",
            )
    _scalar_setters(data, file, gid, existing)
    if "options" in data:
        incoming = _parse_options_list(data, file, gid, rating)
        current = {o.id: i for i, o in enumerate(existing.options)}
        for opt in incoming:
            if opt.id in current:
                existing.options[current[opt.id]] = opt
            else:
                current[opt.id] = len(existing.options)
                existing.options.append(opt)
    existing.sources.append(file)


def _apply_group(data: object, staged: dict[str, Group], file: str, rating: str) -> None:
    if not isinstance(data, dict):
        raise _err(file, E.BAD_KEY_TYPE, None, "each group must be an object")
    _check_unknown_keys(data, _GROUP_KEYS, file, None, "a group")
    gid = data.get("id")
    if not isinstance(gid, str) or not gid:
        raise _err(file, E.MISSING_KEY, None, "a group is missing 'id'")
    if not _ID_RE.match(gid):
        # O2_INPUTS answer 8.2: group ids obey the option-id hygiene rule.
        raise _err(
            file,
            E.BAD_GROUP_ID,
            gid,
            f"group id {gid!r} violates the id rule (lowercase a-z0-9_, "
            f"1-40 chars)",
        )
    existing = staged.get(gid)
    if existing is None:
        staged[gid] = _new_group(data, file, rating)
    else:
        # §4: options are forbidden on free_text — catch a fragment trying to
        # bolt options onto a free_text group before parsing them.
        if existing.is_free_text and "options" in data:
            raise _err(
                file,
                E.OPTIONS_ON_FREE_TEXT,
                gid,
                f"group {gid!r} is free_text and may not carry 'options'",
            )
        _merge_group(existing, data, file, rating)
    _check_group_state(staged[gid], file)


# --- file model (§3) -------------------------------------------------------


def _read_file(path: Path) -> dict:
    file = path.name
    try:
        # utf-8-sig transparently strips a BOM (§3: BOM tolerated).
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise _err(
            file, E.BAD_ENCODING, None, f"file is not UTF-8 (§3): {exc}"
        ) from exc
    except OSError as exc:
        raise _err(file, E.UNREADABLE_FILE, None, f"cannot read file: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise _err(file, E.INVALID_JSON, None, f"invalid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise _err(file, E.NOT_AN_OBJECT, None, "file must be one JSON object")
    _check_unknown_keys(data, _FILE_KEYS, file, None, "file")
    if "format" not in data:
        raise _err(file, E.MISSING_KEY, None, "file is missing 'format'")
    if not _is_int(data["format"]) or data["format"] != 1:
        raise _err(
            file,
            E.BAD_FORMAT_VERSION,
            None,
            f"'format' must equal 1, got {data['format']!r}",
        )
    if "rating" not in data:
        raise _err(file, E.MISSING_KEY, None, "file is missing 'rating'")
    if data["rating"] not in VALID_RATINGS:
        raise _err(
            file,
            E.BAD_RATING,
            None,
            f"invalid rating {data['rating']!r}; expected one of {VALID_RATINGS}",
        )
    if "groups" not in data:
        raise _err(file, E.MISSING_KEY, None, "file is missing 'groups'")
    if not isinstance(data["groups"], list):
        raise _err(file, E.BAD_KEY_TYPE, None, "'groups' must be a list")
    return data


def _apply_file(path: Path, groups: dict[str, Group]) -> None:
    """Parse one file and merge its groups, ATOMICALLY: every change lands on
    a staged copy that replaces ``groups`` only if the whole file applies
    cleanly. A raise means the file had zero effect (§4)."""
    data = _read_file(path)
    staged = copy.deepcopy(groups)
    for group_data in data["groups"]:
        _apply_group(group_data, staged, path.name, data["rating"])
    groups.clear()
    groups.update(staged)


# --- catalog laws (§7 + merged-state checks) -------------------------------


def _rec(file: str, code: str, subject: str | None, message: str) -> FormatErrorRecord:
    return FormatErrorRecord(file, code, subject, f"{file}: [{code}] {message}")


def _check_catalog_laws(groups: dict[str, Group]) -> list[FormatErrorRecord]:
    """§7: checked after all files merge. Also the §4 priority law and the §6
    reference checks, which are only decidable against the merged catalog."""
    records: list[FormatErrorRecord] = []

    # §7.1 two-slot law: at most one free_text per home (identity, persona).
    for home in ("identity", "persona"):
        slots = [g for g in groups.values() if g.is_free_text and g.home == home]
        for extra in slots[1:]:
            records.append(
                _rec(
                    extra.sources[-1],
                    E.TWO_SLOT_LAW,
                    extra.id,
                    f"group {extra.id!r} is a second free_text slot for home "
                    f"{home!r} (first: {slots[0].id!r}); at most one is legal",
                )
            )

    # §7.2 / §0 example guard: no group or option id beginning 'example_'.
    for g in groups.values():
        if g.id.startswith("example_"):
            records.append(
                _rec(
                    g.sources[0],
                    E.EXAMPLE_ID_IN_DATA,
                    g.id,
                    f"group id {g.id!r} begins 'example_'; illustrative ids are "
                    f"legal only in test fixtures (§0)",
                )
            )
        for o in g.options:
            if o.id.startswith("example_"):
                records.append(
                    _rec(
                        o.source_file,
                        E.EXAMPLE_ID_IN_DATA,
                        f"{g.id}/{o.id}",
                        f"option id {o.id!r} in group {g.id!r} begins 'example_'; "
                        f"illustrative ids are legal only in test fixtures (§0)",
                    )
                )

    # O2_INPUTS answer 8.1: a pick-kind group with zero options DEFINED after
    # merge is a catalog error — hidden would vanish a group silently. A group
    # whose options are merely all retired (or rating-filtered by a future
    # gate) is NOT empty; that family still derives hidden.
    for g in groups.values():
        if not g.is_free_text and not g.options:
            records.append(
                _rec(
                    g.sources[-1],
                    E.EMPTY_PICK_GROUP,
                    g.id,
                    f"group {g.id!r} is {g.kind} with zero options defined "
                    f"after merge; a pick group must define options",
                )
            )

    # §4 priority law, on the MERGED group: priority is required iff any
    # option carries image_text, forbidden otherwise (a priority with nothing
    # to prioritize is a latent lie — Decision 3's principle).
    for g in groups.values():
        has_image_text = any(o.image_text is not None for o in g.options)
        if has_image_text and g.priority is None:
            records.append(
                _rec(
                    g.sources[-1],
                    E.IMAGE_TEXT_WITHOUT_PRIORITY,
                    g.id,
                    f"group {g.id!r} has options carrying image_text but no "
                    f"'priority'; priority is required when image_text is present",
                )
            )
        elif not has_image_text and g.priority is not None:
            records.append(
                _rec(
                    g.sources[-1],
                    E.PRIORITY_WITHOUT_IMAGE_TEXT,
                    g.id,
                    f"group {g.id!r} declares priority {g.priority!r} but no "
                    f"option carries image_text; priority is forbidden without it",
                )
            )

    # §6 / §1.14 reference checks, on the merged catalog.
    for g in groups.values():
        cond = g.visible_when
        if cond is None:
            continue
        ref = groups.get(cond["group"])
        if ref is None:
            records.append(
                _rec(
                    g.sources[-1],
                    E.VISIBLE_WHEN_UNKNOWN_GROUP,
                    g.id,
                    f"group {g.id!r} visible_when references missing group "
                    f"{cond['group']!r}",
                )
            )
        elif ref.is_free_text and "any" not in cond:
            # Kickoff-pinned: only "any" may reference a free_text group —
            # in/not_in/has_tag need option ids or tags, which free text lacks.
            pred = next(p for p in VISIBLE_WHEN_PREDICATES if p in cond)
            records.append(
                _rec(
                    g.sources[-1],
                    E.VISIBLE_WHEN_FREE_TEXT_PREDICATE,
                    g.id,
                    f"group {g.id!r} visible_when uses {pred!r} against "
                    f"free_text group {ref.id!r}; only 'any' may reference a "
                    f"free_text group",
                )
            )
    return records


# --- entry point -----------------------------------------------------------


def load_catalog(
    dirs: Iterable[Path | str], *, strict: bool = False
) -> Catalog:
    """Load and merge every ``*.json`` option file from ``dirs``.

    Files load in (directory order, then filename order) (§3). Missing
    directories are skipped (v1 carryover; the validator CLI is stricter).

    Resilient by default: a malformed file is skipped whole (atomic apply)
    and recorded on ``catalog.errors``; catalog-law violations are recorded
    too. ``strict=True`` raises :class:`OptionFormatError` on the first bad
    file, or :class:`CatalogError` for post-merge law violations — used by
    tests and authoring (§4).
    """
    groups: dict[str, Group] = {}
    errors: list[FormatErrorRecord] = []
    for directory in dirs:
        directory = Path(directory)
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.json")):
            if not path.is_file():
                continue  # a directory named *.json is not an option file
            try:
                _apply_file(path, groups)
            except OptionFormatError as exc:
                if strict:
                    raise
                errors.append(exc.record())
            except Exception as exc:
                # Resilient contract (v1): no drop-in can brick the load —
                # including OSError and RecursionError, so catch broadly.
                if strict:
                    raise
                errors.append(
                    FormatErrorRecord(
                        path.name, E.UNREADABLE_FILE, None, f"{path.name}: {exc}"
                    )
                )
    law_records = _check_catalog_laws(groups)
    if law_records and strict:
        raise CatalogError(law_records)
    errors.extend(law_records)
    return Catalog(groups, errors)
