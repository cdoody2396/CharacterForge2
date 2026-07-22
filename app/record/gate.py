"""Construction gate (N4) and finalization checks (N5) — pure functions.

The gate is PER-WRITE on mutations (O3 gate decision 3, taken with Casey
this session): writing a value to a group hidden under current selections
is refused, but a mutation that HIDES an already-set other group succeeds —
the stale value sits inert and finalization's full-state re-check refuses
until it is cleared.

Visibility runs through the single evaluator ``Catalog.visible_now`` (§6:
no second implementation exists).
"""

from __future__ import annotations

from app.options.catalog import Catalog, Group
from app.options.loader import VALID_RATINGS
from app.record import errors as E
from app.record.errors import GateRefusal, SafetyNotInstalledError

# N4: age is a typed integer, floor 20 (the adult anchor), ceiling 10000.
AGE_FLOOR = 20
AGE_CEILING = 10000

# §A7 / N4: ratings are ordered; a record's rating moves up or not at all.
RATING_ORDER = {rating: i for i, rating in enumerate(VALID_RATINGS)}


def check_age(age: object) -> None:
    """N4 age law: missing, non-integer, < 20, or > 10000 → refused."""
    if age is None:
        raise GateRefusal(E.AGE_MISSING, "age", "age is missing")
    if isinstance(age, bool) or not isinstance(age, int):
        raise GateRefusal(
            E.AGE_NOT_INTEGER, "age", f"age must be an integer, got {age!r}"
        )
    if age < AGE_FLOOR:
        raise GateRefusal(
            E.AGE_UNDER_FLOOR, "age", f"age {age} is under the {AGE_FLOOR}+ floor"
        )
    if age > AGE_CEILING:
        raise GateRefusal(
            E.AGE_OVER_CEILING, "age", f"age {age} exceeds the {AGE_CEILING} ceiling"
        )


def check_rating_value(rating: object) -> None:
    if rating not in RATING_ORDER:
        raise GateRefusal(
            E.BAD_RATING,
            "rating",
            f"invalid rating {rating!r}; expected one of {VALID_RATINGS}",
        )


def _normalized_ids(group: Group, value: object) -> list[str]:
    """Validate the VALUE SHAPE for the group's kind (N2) and return the
    picked option ids in order. Raises GateRefusal on any violation."""
    gid = group.id
    if value is None:
        raise GateRefusal(E.NULL_VALUE, gid, f"group {gid!r}: null is never a value")
    if group.kind == "pick_one":
        if isinstance(value, list):
            raise GateRefusal(
                E.LIST_FOR_PICK_ONE, gid, f"group {gid!r} is pick_one; got a list"
            )
        if not isinstance(value, str) or not value:
            raise GateRefusal(
                E.BAD_VALUE_TYPE,
                gid,
                f"group {gid!r}: value must be a non-empty option id string",
            )
        return [value]
    # pick_many
    if not isinstance(value, list):
        raise GateRefusal(
            E.NOT_A_LIST_FOR_PICK_MANY,
            gid,
            f"group {gid!r} is pick_many; value must be a list of option ids",
        )
    if not value:
        # A written empty list would be a second spelling of "unselected"
        # (absent key, N2) — one fact, one spelling. Clearing is the API.
        raise GateRefusal(
            E.EMPTY_PICK_LIST,
            gid,
            f"group {gid!r}: an empty list is not a value; clear the selection",
        )
    ids: list[str] = []
    for entry in value:
        if entry is None:
            raise GateRefusal(
                E.NULL_VALUE, gid, f"group {gid!r}: null is never a value"
            )
        if not isinstance(entry, str) or not entry:
            raise GateRefusal(
                E.BAD_VALUE_TYPE,
                gid,
                f"group {gid!r}: every pick must be a non-empty option id string",
            )
        if entry in ids:
            raise GateRefusal(
                E.DUPLICATE_PICK, f"{gid}/{entry}", f"group {gid!r} picks {entry!r} twice"
            )
        ids.append(entry)
    if group.max_picks is not None and len(ids) > group.max_picks:
        raise GateRefusal(
            E.MAX_PICKS_EXCEEDED,
            gid,
            f"group {gid!r} caps at {group.max_picks} picks; got {len(ids)}",
        )
    return ids


def resolve_group(catalog: Catalog, group_id: str) -> Group:
    group = catalog.get(group_id)
    if group is None:
        raise GateRefusal(
            E.UNKNOWN_GROUP, group_id, f"unknown group id {group_id!r}"
        )
    if group.home == "session":
        # N2: session vocabulary never lands on the record (Decision 4).
        raise GateRefusal(
            E.SESSION_HOME_VALUE,
            group_id,
            f"group {group_id!r} has home 'session'; session values are "
            f"unstorable on a record",
        )
    if group.is_free_text:
        # N4: free-text writes go through the slot setters, which refuse
        # per N6 until the safety stage lands.
        raise SafetyNotInstalledError(
            group_id,
            f"group {group_id!r} is free_text; free-text writes refuse until "
            f"the safety stage lands (N6)",
        )
    return group


def check_selection(
    catalog: Catalog,
    group_id: str,
    value: object,
    *,
    record_rating: str,
    previous_ids: tuple[str, ...],
    current_values: dict,
    existing_ok: bool = False,
) -> list[str]:
    """The per-write N4 chain for one selection value. Returns the picked
    option ids. ``previous_ids`` = the ids currently stored for this group
    (the retired new-vs-existing asymmetry needs the delta); ``existing_ok``
    skips the retired-new check for full-state re-validation, where every
    stored pick is an existing one (Decision 6).
    """
    group = resolve_group(catalog, group_id)
    ids = _normalized_ids(group, value)
    for oid in ids:
        option = group.resolve(oid)  # resolves retired too (Decision 6)
        if option is None:
            raise GateRefusal(
                E.UNKNOWN_OPTION,
                f"{group_id}/{oid}",
                f"group {group_id!r} has no option {oid!r}",
            )
        if RATING_ORDER[option.rating] > RATING_ORDER[record_rating]:
            raise GateRefusal(
                E.RATING_ABOVE_RECORD,
                f"{group_id}/{oid}",
                f"option {oid!r} is rated {option.rating!r}, above the "
                f"record's {record_rating!r}; raise the record rating first",
            )
        if option.retired and not existing_ok and oid not in previous_ids:
            # Decision 6 asymmetry: existing picks keep working; only NEW
            # selection of a retired option is blocked.
            raise GateRefusal(
                E.RETIRED_NEW_PICK,
                f"{group_id}/{oid}",
                f"option {oid!r} is retired; it cannot be newly selected",
            )
    if not catalog.visible_now(group_id, current_values):
        raise GateRefusal(
            E.HIDDEN_GROUP_VALUE,
            group_id,
            f"group {group_id!r} is hidden under current selections; a hidden "
            f"group cannot take a value",
        )
    return ids


def check_full_state(
    catalog: Catalog,
    *,
    age: object,
    rating: str,
    identity_selections: dict,
    persona_selections: dict,
) -> None:
    """N5's "all of N4" over the WHOLE character state (both layers), plus
    the required-when-visible law. Used by finalization; a draft that hides
    one of its own values, holds an orphan, or leaves a visible required
    group empty refuses here."""
    check_age(age)
    check_rating_value(rating)
    combined = dict(identity_selections)
    combined.update(persona_selections)
    for layer in (identity_selections, persona_selections):
        for group_id, value in layer.items():
            # Every stored pick is an existing pick at re-validation time
            # (Decision 6: retired options stay functional for them).
            check_selection(
                catalog,
                group_id,
                value,
                record_rating=rating,
                previous_ids=(),
                current_values=combined,
                existing_ok=True,
            )
    # N5: every `required` group that is visible under current selections
    # has a value — across BOTH layers (a character must be whole to
    # finalize; persona stays editable after).
    for group in catalog:
        if not group.required:
            continue
        if not catalog.visible_now(group.id, combined):
            continue
        if not combined.get(group.id):
            raise GateRefusal(
                E.REQUIRED_GROUP_UNFILLED,
                group.id,
                f"required group {group.id!r} is visible and has no value; "
                f"a character must be whole to finalize (N5)",
            )
