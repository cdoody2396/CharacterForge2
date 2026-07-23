"""The character record: N1 file shape, N2 selections, mutations under the
N4 gate, N5 finalization, the N6 safety seam (opened by O4_INPUTS §F: the
free-text slots, the paragraph edit path, and name revalidation write when
a :class:`~app.safety.filter.SafetyFilter` is passed in; with none, every
O3 refusal stands unchanged).

One JSON object per character. Key spellings are the builder's (recorded in
SESSION_REPORT_O3 / SESSION_REPORT_O4):

    {
      "format": 1,
      "character_id": "...", "age": 25, "rating": "standard",
      "created": "<UTC ISO-8601>",
      "active_version": 1,                     # absent before v1 exists
      "identity_versions": [ { "version": 1, "selections": {...},
          "looks_text": "...",                 # slot; filtered write (O4)
          "appearance_paragraph": "...",
          "paragraph_author": "drafter",       # or "user"; absent = drafter
          "finalized": "<stamp>" } ],
      "draft_identity": { "selections": {...},     # at most one (N1)
          "paragraph_edit": "..." },           # pending user edit, if any
      "persona": { "name": "...", "name_safety": "pending",  # or "clear"
                   "selections": {...},
                   "story_text": "..." }       # slot; filtered write (O4)
    }

Immutability of committed versions is by convention inside the single file
(§A2, acceptable single-user): :class:`IdentityVersion` is frozen and NO
mutation API exists for it — finalize appends, the active pointer moves,
nothing rewrites history. Writes are atomic (temp file + ``os.replace``).

No JSON null exists anywhere in a record (N2, the data-file law): loads
refuse it, and the gate refuses null values before they can be stored.
"""

from __future__ import annotations

import copy
import json
import os
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from app.options.catalog import Catalog

if TYPE_CHECKING:  # §F wiring: the filter is passed in, never imported at
    from app.safety.filter import SafetyFilter  # runtime — duck-typed here.
from app.record import errors as E
from app.record.errors import (
    GateRefusal,
    RecordFormatError,
    SafetyNotInstalledError,
)
from app.record.gate import (
    check_age,
    check_full_state,
    check_rating_value,
    check_selection,
    resolve_group,
    RATING_ORDER,
)
from app.record.paragraph import draft_appearance_paragraph

RECORD_FORMAT = 1

# N6 name law: 1-60 chars, Unicode letters and marks, space, apostrophe,
# hyphen, period. ASCII-literal punctuation only (a curly quote is not an
# apostrophe) — builder detail, recorded.
_NAME_PUNCTUATION = frozenset(" '-.")
NAME_MAX_CHARS = 60

# N6: a filterless name write leaves the pending flag; a filtered write (or
# revalidation, explicit or at finalization) clears it. Exactly two values
# exist (§F); blocked is never a stored state.
NAME_SAFETY_PENDING = "pending"
NAME_SAFETY_CLEAR = "clear"
NAME_SAFETY_VALUES = frozenset({NAME_SAFETY_PENDING, NAME_SAFETY_CLEAR})

# §F DECIDED: the free-text slot ceiling (Decision 7-amended).
FREE_TEXT_MAX_CHARS = 240

# §F: the paragraph-edit cap EXISTS by contract; the value is ILLUSTRATIVE
# (builder's, recorded in SESSION_REPORT_O4).
PARAGRAPH_MAX_CHARS = 1200

# §F: every committed version records its paragraph's author; an absent key
# on load reads as the drafter (O3 files predate the key).
PARAGRAPH_AUTHOR_DRAFTER = "drafter"
PARAGRAPH_AUTHOR_USER = "user"
PARAGRAPH_AUTHORS = frozenset({PARAGRAPH_AUTHOR_DRAFTER, PARAGRAPH_AUTHOR_USER})


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class IdentityVersion:
    """One committed, immutable identity version (N1). Frozen: no mutation
    API exists for committed versions — re-finalization appends v(n+1)."""

    version: int
    selections: dict
    appearance_paragraph: str
    finalized: str
    looks_text: str | None = None  # the identity free-text slot (N6)
    paragraph_author: str = PARAGRAPH_AUTHOR_DRAFTER  # "drafter" | "user" (§F)


@dataclass
class _Draft:
    """The at-most-one uncommitted working copy of v(n+1) (N1)."""

    selections: dict = field(default_factory=dict)
    looks_text: str | None = None  # the identity free-text slot (N6)
    # §F: a pending user edit to the appearance paragraph; commits verbatim
    # at finalization with author "user". Never copied into a new draft —
    # user text must not survive an identity change it might misdescribe.
    paragraph_edit: str | None = None


@dataclass
class _Persona:
    """The persona block (N1): editable any time, never versioned."""

    name: str | None = None
    name_safety: str | None = None
    selections: dict = field(default_factory=dict)
    story_text: str | None = None  # the persona free-text slot (N6)


class CharacterRecord:
    """A character record plus its mutation surface. Every mutation runs the
    N4 construction gate; a refusal leaves the record unchanged."""

    def __init__(
        self,
        *,
        character_id: str,
        age: int,
        rating: str,
        created: str,
        active_version: int | None = None,
        identity_versions: list[IdentityVersion] | None = None,
        draft: _Draft | None = None,
        persona: _Persona | None = None,
    ):
        self.character_id = character_id
        self.age = age
        self.rating = rating
        self.created = created
        self.active_version = active_version
        self.identity_versions: list[IdentityVersion] = identity_versions or []
        self.draft = draft
        self.persona = persona if persona is not None else _Persona()
        # R5 seam: callables invoked as hook(record, touched_group_ids) after
        # a successful persona SELECTION mutation (the ledger registers one).
        # Not serialized.
        self.persona_edit_hooks: list[Callable] = []

    # -- creation -----------------------------------------------------------

    @classmethod
    def create(cls, character_id: str, age: int) -> "CharacterRecord":
        """A new record: age gated (N4), rating starts at the floor
        ('standard' — it only ever moves up, §A7), an empty draft open."""
        if not isinstance(character_id, str) or not character_id:
            raise RecordFormatError(
                E.RECORD_BAD_TYPE,
                "character_id",
                "character_id must be a non-empty string",
            )
        check_age(age)
        return cls(
            character_id=character_id,
            age=age,
            rating="standard",
            created=_utc_stamp(),
            draft=_Draft(),
        )

    # -- working views ------------------------------------------------------

    @property
    def active(self) -> IdentityVersion | None:
        if self.active_version is None:
            return None
        return self.identity_versions[self.active_version - 1]

    def _identity_values(self, *, working: bool) -> dict:
        """Identity-layer selections: the draft when asked for the working
        view (and one exists), else the active committed version."""
        if working and self.draft is not None:
            return self.draft.selections
        if self.active is not None:
            return self.active.selections
        if self.draft is not None:
            return self.draft.selections
        return {}

    def _current_values(self, *, working: bool) -> dict:
        """Visibility basis (builder detail, recorded): draft mutations
        evaluate against draft+persona; persona mutations against the LIVE
        identity (active version; the draft only before v1 exists)."""
        values = dict(self._identity_values(working=working))
        values.update(self.persona.selections)
        return values

    # -- header mutations (N4) ---------------------------------------------

    def set_age(self, age: int) -> None:
        check_age(age)
        self.age = age

    def raise_rating(self, rating: str) -> None:
        """§A7 made enforceable (N4): rating moves up or not at all."""
        check_rating_value(rating)
        if RATING_ORDER[rating] < RATING_ORDER[self.rating]:
            raise GateRefusal(
                E.RATING_DECREASE,
                "rating",
                f"rating {self.rating!r} cannot decrease to {rating!r}; "
                f"rating moves up or not at all",
            )
        self.rating = rating

    # -- selection mutations (N2 + N4) -------------------------------------

    def set_selection(self, catalog: Catalog, group_id: str, value: object) -> None:
        group = resolve_group(catalog, group_id)  # unknown/session/free_text
        layer = self._layer_for(group.home)
        previous = layer.get(group_id)
        previous_ids = (
            (previous,) if isinstance(previous, str) else tuple(previous or ())
        )
        working = group.home == "identity"
        ids = check_selection(
            catalog,
            group_id,
            value,
            record_rating=self.rating,
            previous_ids=previous_ids,
            current_values=self._current_values(working=working),
        )
        stored = ids[0] if group.kind == "pick_one" else list(ids)
        if layer.get(group_id) == stored:
            return  # no edit happened; marking staleness for it would lie
        layer[group_id] = stored
        if group.home == "persona":
            self._fire_persona_hooks((group_id,))

    def clear_selection(self, catalog: Catalog, group_id: str) -> None:
        """Clearing = removing the key (N2: absent = unselected; no nulls).
        Unknown groups refuse like any unknown-id write — an orphaned pick
        is cleared by restoring its file (Decision 6 pt 3), not by editing."""
        group = resolve_group(catalog, group_id)
        layer = self._layer_for(group.home)
        if group_id not in layer:
            return  # idempotent: clearing the unselected is no edit
        del layer[group_id]
        if group.home == "persona":
            self._fire_persona_hooks((group_id,))

    def _layer_for(self, home: str) -> dict:
        if home == "identity":
            if self.draft is None:
                raise GateRefusal(
                    E.IDENTITY_NO_DRAFT,
                    None,
                    "identity is locked at finalization; open a draft to "
                    "edit it (Decision 4)",
                )
            return self.draft.selections
        return self.persona.selections

    def _fire_persona_hooks(self, touched: tuple[str, ...]) -> None:
        for hook in self.persona_edit_hooks:
            hook(self, touched)

    # -- draft / finalization (N5) -----------------------------------------

    def open_draft(self) -> None:
        """Identity edits open v(n+1): a working copy of the active version
        (§A2). At most one draft exists (N1)."""
        if self.draft is not None:
            raise GateRefusal(
                E.DRAFT_ALREADY_OPEN, None, "a draft identity is already open"
            )
        active = self.active
        assert active is not None  # creation always leaves a draft open
        self.draft = _Draft(
            selections=copy.deepcopy(active.selections),
            looks_text=active.looks_text,
        )

    def finalize(
        self, catalog: Catalog, safety: "SafetyFilter | None" = None
    ) -> IdentityVersion:
        """The identity commit (N5): all of N4 over the whole character,
        required-when-visible across BOTH layers, then draft → v(n+1)
        verbatim, paragraph drafted (N7) — or the draft's user edit
        committed verbatim with author 'user' (§F) — stamp set, active
        pointer moves.

        §F: when a filter is supplied and a name exists still 'pending',
        finalization revalidates it — pass writes 'clear', fail refuses
        the whole finalization. With no filter, the O3 behavior stands
        (pending survives; nothing here refuses for it)."""
        if self.draft is None:
            raise GateRefusal(
                E.NO_DRAFT, None, "no draft identity is open; nothing to finalize"
            )
        check_full_state(
            catalog,
            age=self.age,
            rating=self.rating,
            identity_selections=self.draft.selections,
            persona_selections=self.persona.selections,
        )
        if safety is not None:
            self.revalidate_name(safety)  # refusal aborts before any commit
        if self.draft.paragraph_edit is not None:
            paragraph = self.draft.paragraph_edit
            author = PARAGRAPH_AUTHOR_USER
        else:
            paragraph = draft_appearance_paragraph(catalog, self.draft.selections)
            author = PARAGRAPH_AUTHOR_DRAFTER
        version = IdentityVersion(
            version=len(self.identity_versions) + 1,
            selections=copy.deepcopy(self.draft.selections),
            appearance_paragraph=paragraph,
            finalized=_utc_stamp(),
            looks_text=self.draft.looks_text,
            paragraph_author=author,
        )
        self.identity_versions.append(version)
        self.active_version = version.version
        self.draft = None
        return version

    # -- the safety seam (N6, opened by O4_INPUTS §F) -----------------------
    #
    # Wiring (builder's spelling, the catalog-argument precedent): the
    # filter arrives as a trailing optional argument on each write path.
    # LAW: with no filter supplied, every O3 SafetyNotInstalledError
    # refusal stands unchanged — the seam's honesty survives for tests
    # and for any caller without the filter.
    # §G: refusal, never redaction — a block refuses the whole write,
    # naming category and matched term; the record is unchanged.

    def _check_free_text(
        self, safety: "SafetyFilter", text: str, surface: str, max_chars: int
    ) -> None:
        """The shared §F write chain: shape, cap, then the filter in
        `freetext` context at the record's current rating."""
        if not isinstance(text, str) or not text.strip():
            raise GateRefusal(
                E.BAD_VALUE_TYPE,
                surface,
                f"{surface} must be a non-empty string; clearing is its own "
                f"API (no nulls, no empty-string spelling of 'cleared')",
            )
        if len(text) > max_chars:
            code = (
                E.PARAGRAPH_OVERLONG
                if surface == "appearance_paragraph"
                else E.FREE_TEXT_OVERLONG
            )
            raise GateRefusal(
                code,
                surface,
                f"{surface} is {len(text)} characters; the cap is {max_chars}",
            )
        result = safety.check(
            text, context="freetext", rating=self.rating, surface=surface
        )
        if not result.allowed:
            raise GateRefusal(
                E.TEXT_BLOCKED,
                surface,
                f"{surface} refused: category {result.category!r} matched "
                f"{result.matched!r}; rewrite and retry (§G: the write "
                f"refuses whole, nothing is redacted)",
            )

    def set_looks_text(
        self, text: str, safety: "SafetyFilter | None" = None
    ) -> None:
        """The identity free-text slot (§F). Draft-scoped like every
        identity write; cap FREE_TEXT_MAX_CHARS; filtered."""
        if safety is None:
            raise SafetyNotInstalledError(
                "looks_text",
                "the looks free-text slot refuses writes without the filter "
                "(N6); no filter has seen this text",
            )
        if self.draft is None:
            raise GateRefusal(
                E.IDENTITY_NO_DRAFT,
                "looks_text",
                "identity is locked at finalization; open a draft to edit "
                "its looks text (Decision 4)",
            )
        self._check_free_text(safety, text, "looks_text", FREE_TEXT_MAX_CHARS)
        self.draft.looks_text = text

    def clear_looks_text(self) -> None:
        """Explicit clear (§F; N2: no nulls, no empty-string spelling).
        Filter-free: clearing enters no text. Idempotent."""
        if self.draft is None:
            raise GateRefusal(
                E.IDENTITY_NO_DRAFT,
                "looks_text",
                "identity is locked at finalization; open a draft to clear "
                "its looks text (Decision 4)",
            )
        self.draft.looks_text = None

    def set_story_text(
        self, text: str, safety: "SafetyFilter | None" = None
    ) -> None:
        """The persona free-text slot (§F). Persona-scoped: no draft
        needed; cap FREE_TEXT_MAX_CHARS; filtered."""
        if safety is None:
            raise SafetyNotInstalledError(
                "story_text",
                "the story free-text slot refuses writes without the filter "
                "(N6); no filter has seen this text",
            )
        self._check_free_text(safety, text, "story_text", FREE_TEXT_MAX_CHARS)
        self.persona.story_text = text

    def clear_story_text(self) -> None:
        """Explicit clear for the story slot. Filter-free; idempotent."""
        self.persona.story_text = None

    def edit_appearance_paragraph(
        self, text: str, safety: "SafetyFilter | None" = None
    ) -> None:
        """§F: user edits target the DRAFT only — committed versions stay
        frozen (N1). The edit lands as a pending draft field and commits
        verbatim at finalization with author 'user'."""
        if safety is None:
            raise SafetyNotInstalledError(
                "appearance_paragraph",
                "user edits to the appearance paragraph refuse without the "
                "filter (N6); the drafter's output stands",
            )
        if self.draft is None:
            raise GateRefusal(
                E.IDENTITY_NO_DRAFT,
                "appearance_paragraph",
                "no draft identity is open; the paragraph edit targets the "
                "draft (§F) — committed versions stay frozen (N1)",
            )
        self._check_free_text(
            safety, text, "appearance_paragraph", PARAGRAPH_MAX_CHARS
        )
        self.draft.paragraph_edit = text

    def set_name(self, name: str, safety: "SafetyFilter | None" = None) -> None:
        """N6: charset law first (unchanged from O3), then — with a filter —
        the `name` context check (§F). A filtered pass stores
        name_safety='clear'; a filterless write stores 'pending' for later
        revalidation. Blocked is never a stored state."""
        if not isinstance(name, str):
            raise GateRefusal(E.BAD_VALUE_TYPE, "name", "name must be a string")
        if not 1 <= len(name) <= NAME_MAX_CHARS:
            raise GateRefusal(
                E.NAME_LENGTH,
                "name",
                f"name must be 1-{NAME_MAX_CHARS} characters, got {len(name)}",
            )
        for ch in name:
            if ch in _NAME_PUNCTUATION:
                continue
            if unicodedata.category(ch)[0] in ("L", "M"):  # letters, marks
                continue
            raise GateRefusal(
                E.NAME_CHARSET,
                "name",
                f"name contains {ch!r}; legal are letters, marks, spaces, "
                f"apostrophe, hyphen, period (N6)",
            )
        if safety is None:
            self.persona.name = name
            self.persona.name_safety = NAME_SAFETY_PENDING
            return
        result = safety.check_name(name, rating=self.rating, surface="name")
        if not result.allowed:
            raise GateRefusal(
                E.NAME_BLOCKED,
                "name",
                f"name refused: category {result.category!r} matched "
                f"{result.matched!r} (§G)",
            )
        self.persona.name = name
        self.persona.name_safety = NAME_SAFETY_CLEAR

    def revalidate_name(self, safety: "SafetyFilter | None" = None) -> None:
        """§F: the explicit revalidation path for a 'pending' name — pass
        writes 'clear', fail refuses and the record is unchanged.
        Idempotent when nothing is pending (the clear_selection
        precedent). Finalization also runs this automatically."""
        if safety is None:
            raise SafetyNotInstalledError(
                "name",
                "name revalidation needs the filter (N6)",
            )
        if (
            self.persona.name is None
            or self.persona.name_safety == NAME_SAFETY_CLEAR
        ):
            return  # nothing pending; revalidating it again would be noise
        result = safety.check_name(
            self.persona.name, rating=self.rating, surface="name"
        )
        if not result.allowed:
            raise GateRefusal(
                E.NAME_BLOCKED,
                "name",
                f"pending name refused on revalidation: category "
                f"{result.category!r} matched {result.matched!r} (§G)",
            )
        self.persona.name_safety = NAME_SAFETY_CLEAR


# --- serialization (N1) ------------------------------------------------------


def _record_dict(record: CharacterRecord) -> dict:
    data: dict = {
        "format": RECORD_FORMAT,
        "character_id": record.character_id,
        "age": record.age,
        "rating": record.rating,
        "created": record.created,
    }
    if record.active_version is not None:
        data["active_version"] = record.active_version
    data["identity_versions"] = []
    for v in record.identity_versions:
        entry: dict = {
            "version": v.version,
            "selections": copy.deepcopy(v.selections),
            "appearance_paragraph": v.appearance_paragraph,
            "paragraph_author": v.paragraph_author,
            "finalized": v.finalized,
        }
        if v.looks_text is not None:
            entry["looks_text"] = v.looks_text
        data["identity_versions"].append(entry)
    if record.draft is not None:
        draft: dict = {"selections": copy.deepcopy(record.draft.selections)}
        if record.draft.looks_text is not None:
            draft["looks_text"] = record.draft.looks_text
        if record.draft.paragraph_edit is not None:
            draft["paragraph_edit"] = record.draft.paragraph_edit
        data["draft_identity"] = draft
    persona: dict = {"selections": copy.deepcopy(record.persona.selections)}
    if record.persona.name is not None:
        persona["name"] = record.persona.name
        persona["name_safety"] = record.persona.name_safety
    if record.persona.story_text is not None:
        persona["story_text"] = record.persona.story_text
    data["persona"] = persona
    return data


def save_record(record: CharacterRecord, path: Path | str) -> None:
    """Atomic write (N1): serialize to a temp file in the same directory,
    then ``os.replace`` — a crash mid-write cannot half-eat the record."""
    path = Path(path)
    payload = json.dumps(_record_dict(record), indent=2, ensure_ascii=False) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, path)


# --- load (strict; N9 orphans are the caller's report, not an error) ---------

_HEADER_KEYS = frozenset(
    {
        "format",
        "character_id",
        "age",
        "rating",
        "created",
        "active_version",
        "identity_versions",
        "draft_identity",
        "persona",
    }
)
_VERSION_KEYS = frozenset(
    {
        "version",
        "selections",
        "appearance_paragraph",
        "paragraph_author",
        "finalized",
        "looks_text",
    }
)
_DRAFT_KEYS = frozenset({"selections", "looks_text", "paragraph_edit"})
_PERSONA_KEYS = frozenset({"name", "name_safety", "selections", "story_text"})


def _fail(code: str, subject: str | None, message: str) -> RecordFormatError:
    return RecordFormatError(code, subject, message)


def _reject_nulls(value: object, where: str) -> None:
    """N2: no JSON null anywhere in a record — the data-file law."""
    if value is None:
        raise _fail(E.RECORD_NULL, where, f"{where}: null is illegal in a record")
    if isinstance(value, dict):
        for key, entry in value.items():
            _reject_nulls(entry, f"{where}.{key}")
    elif isinstance(value, list):
        for i, entry in enumerate(value):
            _reject_nulls(entry, f"{where}[{i}]")


def _check_keys(data: dict, allowed: frozenset, where: str) -> None:
    for key in data:
        if isinstance(key, str) and key.startswith("_"):
            continue  # §1.9 comment-key family, honored here too
        if key not in allowed:
            raise _fail(
                E.RECORD_UNKNOWN_KEY, where, f"{where} has unknown key {key!r}"
            )


def _require(data: dict, key: str, where: str) -> object:
    if key not in data:
        raise _fail(E.RECORD_MISSING_KEY, where, f"{where} is missing {key!r}")
    return data[key]


def _read_str(data: dict, key: str, where: str) -> str:
    value = _require(data, key, where)
    if not isinstance(value, str) or not value:
        raise _fail(
            E.RECORD_BAD_TYPE, where, f"{where} key {key!r} must be a non-empty string"
        )
    return value


def _read_selections(data: dict, where: str) -> dict:
    value = _require(data, "selections", where)
    if not isinstance(value, dict):
        raise _fail(E.RECORD_BAD_TYPE, where, f"{where} 'selections' must be an object")
    for group_id, entry in value.items():
        w = f"{where}.selections.{group_id}"
        if isinstance(entry, str):
            if not entry:
                raise _fail(E.RECORD_BAD_TYPE, w, f"{w} must not be empty")
        elif isinstance(entry, list):
            if not entry or not all(isinstance(v, str) and v for v in entry):
                raise _fail(
                    E.RECORD_BAD_TYPE,
                    w,
                    f"{w} must be a non-empty list of option ids",
                )
            if len(set(entry)) != len(entry):
                raise _fail(E.RECORD_BAD_TYPE, w, f"{w} holds duplicate picks")
        else:
            raise _fail(
                E.RECORD_BAD_TYPE,
                w,
                f"{w} must be an option id or a list of option ids",
            )
    return copy.deepcopy(value)


def _check_no_session_values(catalog: Catalog, selections: dict, where: str) -> None:
    """N2: session-home values are unstorable — a stored one is a format
    violation, not an orphan."""
    for group_id in selections:
        group = catalog.get(group_id)
        if group is not None and group.home == "session":
            raise _fail(
                E.SESSION_HOME_VALUE,
                group_id,
                f"{where} stores a value for session-home group {group_id!r}; "
                f"session values never land on a record (N2)",
            )


def load_record(path: Path | str, catalog: Catalog):
    """Strict-load one record file against the live catalog.

    Returns ``(record, orphans)`` — the N9 report is part of loading: the
    record loads WITH unknown ids (listed, inert), while shape violations
    (unknown keys, nulls, bad types, session-home values, broken
    versioning) refuse whole.
    """
    from app.record.orphans import orphan_report  # local: avoids cycle

    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise _fail(E.RECORD_INVALID_JSON, None, f"cannot read {path.name}: {exc}")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise _fail(E.RECORD_INVALID_JSON, None, f"{path.name}: invalid JSON ({exc})")
    if not isinstance(data, dict):
        raise _fail(E.RECORD_BAD_TYPE, None, "record must be one JSON object")
    _reject_nulls(data, "record")
    _check_keys(data, _HEADER_KEYS, "record")

    fmt = _require(data, "format", "record")
    if fmt != RECORD_FORMAT:
        raise _fail(
            E.RECORD_BAD_TYPE, "format", f"'format' must equal {RECORD_FORMAT}"
        )
    character_id = _read_str(data, "character_id", "record")
    age = _require(data, "age", "record")
    try:
        check_age(age)
    except GateRefusal as exc:
        raise _fail(exc.code, "age", f"record age is out of law: {exc}")
    rating = _read_str(data, "rating", "record")
    try:
        check_rating_value(rating)
    except GateRefusal as exc:
        raise _fail(exc.code, "rating", str(exc))
    created = _read_str(data, "created", "record")

    raw_versions = data.get("identity_versions", [])
    if not isinstance(raw_versions, list):
        raise _fail(E.RECORD_BAD_TYPE, None, "'identity_versions' must be a list")
    versions: list[IdentityVersion] = []
    for i, raw in enumerate(raw_versions):
        where = f"identity_versions[{i}]"
        if not isinstance(raw, dict):
            raise _fail(E.RECORD_BAD_TYPE, where, f"{where} must be an object")
        _check_keys(raw, _VERSION_KEYS, where)
        number = _require(raw, "version", where)
        if number != i + 1:
            # Append-only, contiguous from 1 — anything else means history
            # was rewritten, which no API can do (§A2).
            raise _fail(
                E.RECORD_BAD_VERSIONING,
                where,
                f"{where} carries version {number!r}; expected {i + 1}",
            )
        selections = _read_selections(raw, where)
        _check_no_session_values(catalog, selections, where)
        paragraph = _require(raw, "appearance_paragraph", where)
        if not isinstance(paragraph, str):
            raise _fail(
                E.RECORD_BAD_TYPE, where, f"{where} 'appearance_paragraph' must be a string"
            )
        looks = raw.get("looks_text")
        if looks is not None and not isinstance(looks, str):
            raise _fail(E.RECORD_BAD_TYPE, where, f"{where} 'looks_text' must be a string")
        # §F: absent author key reads as the drafter (O3 files predate it).
        author = raw.get("paragraph_author", PARAGRAPH_AUTHOR_DRAFTER)
        if author not in PARAGRAPH_AUTHORS:
            raise _fail(
                E.RECORD_BAD_TYPE,
                where,
                f"{where} 'paragraph_author' must be one of "
                f"{sorted(PARAGRAPH_AUTHORS)}, got {author!r}",
            )
        versions.append(
            IdentityVersion(
                version=i + 1,
                selections=selections,
                appearance_paragraph=paragraph,
                finalized=_read_str(raw, "finalized", where),
                looks_text=looks,
                paragraph_author=author,
            )
        )

    active_version = data.get("active_version")
    if active_version is not None:
        if (
            isinstance(active_version, bool)
            or not isinstance(active_version, int)
            or not 1 <= active_version <= len(versions)
        ):
            raise _fail(
                E.RECORD_BAD_VERSIONING,
                "active_version",
                f"active_version {active_version!r} names no committed version",
            )
    elif versions:
        raise _fail(
            E.RECORD_BAD_VERSIONING,
            "active_version",
            "committed versions exist but no active_version is set",
        )

    draft = None
    if "draft_identity" in data:
        raw = data["draft_identity"]
        if not isinstance(raw, dict):
            raise _fail(E.RECORD_BAD_TYPE, "draft_identity", "'draft_identity' must be an object")
        _check_keys(raw, _DRAFT_KEYS, "draft_identity")
        selections = _read_selections(raw, "draft_identity")
        _check_no_session_values(catalog, selections, "draft_identity")
        looks = raw.get("looks_text")
        if looks is not None and not isinstance(looks, str):
            raise _fail(
                E.RECORD_BAD_TYPE, "draft_identity", "'looks_text' must be a string"
            )
        paragraph_edit = raw.get("paragraph_edit")
        if paragraph_edit is not None and not isinstance(paragraph_edit, str):
            raise _fail(
                E.RECORD_BAD_TYPE,
                "draft_identity",
                "'paragraph_edit' must be a string",
            )
        draft = _Draft(
            selections=selections, looks_text=looks, paragraph_edit=paragraph_edit
        )

    raw_persona = _require(data, "persona", "record")
    if not isinstance(raw_persona, dict):
        raise _fail(E.RECORD_BAD_TYPE, "persona", "'persona' must be an object")
    _check_keys(raw_persona, _PERSONA_KEYS, "persona")
    selections = _read_selections(raw_persona, "persona")
    _check_no_session_values(catalog, selections, "persona")
    name = raw_persona.get("name")
    name_safety = raw_persona.get("name_safety")
    if name is not None:
        if not isinstance(name, str):
            raise _fail(E.RECORD_BAD_TYPE, "persona", "'name' must be a string")
        # §F: exactly two safety states exist — 'pending' (unrevalidated)
        # and 'clear' (filtered). Blocked is never a stored state, so any
        # other spelling is a format lie. Loads never mutate: a pending
        # name loads pending; revalidation is an explicit write path.
        if name_safety not in NAME_SAFETY_VALUES:
            raise _fail(
                E.RECORD_BAD_TYPE,
                "persona",
                f"'name_safety' must be one of {sorted(NAME_SAFETY_VALUES)}, "
                f"got {name_safety!r}",
            )
    elif name_safety is not None:
        raise _fail(
            E.RECORD_BAD_TYPE, "persona", "'name_safety' without a 'name' is a lie"
        )
    story = raw_persona.get("story_text")
    if story is not None and not isinstance(story, str):
        raise _fail(E.RECORD_BAD_TYPE, "persona", "'story_text' must be a string")

    record = CharacterRecord(
        character_id=character_id,
        age=age,
        rating=rating,
        created=created,
        active_version=active_version,
        identity_versions=versions,
        draft=draft,
        persona=_Persona(
            name=name,
            name_safety=name_safety,
            selections=selections,
            story_text=story,
        ),
    )
    return record, orphan_report(record, catalog)
