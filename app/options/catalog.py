"""Catalog model: groups, options, menu view, visibility evaluation.

The catalog is what the loader produces after merging every file (§§3–5).
Visibility (§6) has exactly ONE implementation — this module's
``Catalog.visible_now`` — non-recursive, one hop; no second front-end
evaluator exists in v2 (the drift hazard is designed out).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.options.errors import FormatErrorRecord

# §6: the predicates a visible_when condition may carry — exactly one each.
VISIBLE_WHEN_PREDICATES = ("any", "in", "not_in", "has_tag")


@dataclass(frozen=True)
class Option:
    """One selectable option (§5). ``rating`` and ``source_file`` come from
    the file that (last) declared it — Decision 5: the file is the mark."""

    id: str
    label: str
    image_text: str | None = None  # presence = the picture engine reads it
    chat_text: str | None = None  # presence = the chat model reads it
    tags: tuple[str, ...] = ()
    color: str | None = None
    thumb: str | None = None
    status: str = "active"  # §1.7: active | retired
    source_file: str = ""
    rating: str = ""

    @property
    def retired(self) -> bool:
        return self.status == "retired"


@dataclass
class Group:
    """One merged option group (§4)."""

    id: str
    label: str
    kind: str  # §1.3: pick_one | pick_many | free_text
    home: str  # §1.4: identity | persona | session
    scene_overridable: bool = False
    priority: str | None = None  # §1.5, conditional (priority law, §4)
    max_picks: int | None = None  # pick_many only
    feeds: str | None = None  # free_text only: image | chat | both
    max_chars: int | None = None  # free_text only, 1–240
    visible_when: dict | None = None  # normalized §6 condition, or None
    section: str | None = None
    order: float | None = None
    hint: str | None = None  # display-only, never enters any prompt
    tags: tuple[str, ...] = ()
    options: list[Option] = field(default_factory=list)
    rating: str = ""  # rating of the file that first defined the group
    sources: list[str] = field(default_factory=list)  # provenance

    @property
    def is_free_text(self) -> bool:
        return self.kind == "free_text"

    def menu_options(self) -> list[Option]:
        """Options offered for NEW selection: retired excluded (Decision 6)."""
        return [o for o in self.options if not o.retired]

    def resolve(self, option_id: str) -> Option | None:
        """Resolve an option id INCLUDING retired ones — a retired option
        stays fully functional for existing characters (Decision 6)."""
        for opt in self.options:
            if opt.id == option_id:
                return opt
        return None

    @property
    def hidden(self) -> bool:
        """§1.7: a group whose options are all retired derives hidden — no
        group-level status key exists. free_text groups have no options and
        never derive hidden."""
        if self.is_free_text:
            return False
        return not any(not o.retired for o in self.options)


class Catalog:
    """All merged groups, in load order, plus recorded errors.

    ``errors`` holds a :class:`FormatErrorRecord` for every file skipped and
    every catalog-level law violated during a resilient load (strict loads
    raise instead)."""

    def __init__(
        self,
        groups: dict[str, Group],
        errors: list[FormatErrorRecord] | None = None,
    ):
        self._groups = groups
        self.errors: list[FormatErrorRecord] = errors if errors is not None else []

    def __len__(self) -> int:
        return len(self._groups)

    def __contains__(self, group_id: object) -> bool:
        return group_id in self._groups

    def __iter__(self):
        return iter(self._groups.values())

    def groups(self) -> list[Group]:
        """All groups in load (insertion) order. ``order`` (§4) is a display
        hint within a section for the creator stage, not a catalog ordering."""
        return list(self._groups.values())

    def group_ids(self) -> list[str]:
        return list(self._groups.keys())

    def get(self, group_id: str) -> Group | None:
        return self._groups.get(group_id)

    # -- visibility (§6) — the single evaluator ----------------------------

    def visible_now(self, group_id: str, values: dict) -> bool:
        """Evaluate a group's visibility against current values.

        ``values`` maps group id -> current value: an option id (pick_one),
        a list of option ids (pick_many), or entered text (free_text).

        Semantics (§6): absent condition -> always visible; one hop,
        non-recursive (the referenced group's own visibility is not
        consulted); ``not_in`` with an empty selection reads visible.
        Load-time law guarantees the referenced group exists and that a
        free_text group is only referenced by ``any``.

        An unknown ``group_id`` raises KeyError — fail loud, a typo'd query
        must not silently read visible.
        """
        group = self._groups.get(group_id)
        if group is None:
            raise KeyError(group_id)
        cond = group.visible_when
        if cond is None:
            return True
        ref = self._groups[cond["group"]]
        chosen = _chosen_values(values.get(ref.id))
        if "any" in cond:
            return bool(chosen)
        if "in" in cond:
            return any(c in cond["in"] for c in chosen)
        if "not_in" in cond:
            return not any(c in cond["not_in"] for c in chosen)
        # has_tag: a selected option in the referenced group carries the tag.
        # Retired options still resolve (Decision 6); unknown ids carry none.
        want = cond["has_tag"]
        return any(
            (opt := ref.resolve(c)) is not None and want in opt.tags for c in chosen
        )


def _chosen_values(value: object) -> list[str]:
    """Normalize a current value to a list of non-empty strings."""
    if value is None or value == "":
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if v not in (None, "")]
    return [str(value)]
