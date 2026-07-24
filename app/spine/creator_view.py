"""The creator view (O5_INPUTS §B/§F.3): the spine is the single
evaluator. For a given record: the groups visible under its current
state, each with derived widget, admissible options at the record's
rating, current value(s), required flag, and section/order/hint
passthrough. No client re-implements any of this.

Visibility basis — mirrors the record layer's own law exactly
(``CharacterRecord._current_values``/``_identity_values``,
app/record/model.py:193-210; parity is pinned by test): identity-home
groups evaluate against draft+persona (the working view); persona-home
groups against the live identity (active version; the draft only before
v1 exists) + persona.

Excluded from this view (recorded in SESSION_REPORT_O5): catalog-
declared ``free_text`` groups (sealed per §I.2; no widget in the closed
set — decided at the gate) and ``session``-home groups (not record-
storable, N4). Both keep their full facts on the raw catalog endpoint.

Widget mapping table (builder detail, recorded) — closed set seeded by
DECISIONS §10; derived over the non-retired option list so a group's
widget is stable across rating raises; first match wins:

    1. any menu option carries ``thumb``          -> picker
    2. any menu option carries ``color``          -> swatch
    3. kind ``pick_many``                         -> chips
    4. ``pick_one`` with <= SEGMENTED_MAX options -> segmented
    5. ``pick_one`` otherwise                     -> picker
"""

from __future__ import annotations

from app.options.catalog import Catalog, Group, Option
from app.record import CharacterRecord
from app.record.gate import RATING_ORDER

WIDGET_SEGMENTED = "segmented"
WIDGET_CHIPS = "chips"
WIDGET_SWATCH = "swatch"
WIDGET_PICKER = "picker"

SEGMENTED_MAX = 5


def identity_basis(record: CharacterRecord, *, working: bool) -> dict:
    """Mirror of ``CharacterRecord._identity_values`` (model.py:193)."""
    if working and record.draft is not None:
        return record.draft.selections
    if record.active is not None:
        return record.active.selections
    if record.draft is not None:
        return record.draft.selections
    return {}


def visibility_basis(record: CharacterRecord, *, working: bool) -> dict:
    """Mirror of ``CharacterRecord._current_values`` (model.py:204)."""
    values = dict(identity_basis(record, working=working))
    values.update(record.persona.selections)
    return values


def derive_widget(group: Group) -> str:
    menu = group.menu_options()
    if any(option.thumb for option in menu):
        return WIDGET_PICKER
    if any(option.color for option in menu):
        return WIDGET_SWATCH
    if group.kind == "pick_many":
        return WIDGET_CHIPS
    if len(menu) <= SEGMENTED_MAX:
        return WIDGET_SEGMENTED
    return WIDGET_PICKER


def _menu_entry(option: Option) -> dict:
    return {
        "id": option.id,
        "label": option.label,
        "rating": option.rating,
        "tags": list(option.tags),
        "color": option.color,
        "thumb": option.thumb,
    }


def _held_entry(group: Group, option_id: str) -> dict:
    """A held value, resolved retired-inclusive (the O1 law: excluded
    from menus but resolvable for held values)."""
    option = group.resolve(option_id)
    if option is None:
        # An orphaned pick: unknown to the catalog, surfaced verbatim.
        # No Option to resolve, so tags is empty (§G.1, builder detail).
        return {
            "id": option_id,
            "label": None,
            "retired": False,
            "orphaned": True,
            "tags": [],
        }
    return {
        "id": option.id,
        "label": option.label,
        "retired": option.retired,
        "orphaned": False,
        "color": option.color,
        "thumb": option.thumb,
        "tags": list(option.tags),
    }


def assemble(catalog: Catalog, record: CharacterRecord) -> list[dict]:
    rating_rank = RATING_ORDER[record.rating]
    groups: list[dict] = []
    for group in catalog.groups():
        if group.is_free_text or group.home == "session":
            continue
        working = group.home == "identity"
        if not catalog.visible_now(
            group.id, visibility_basis(record, working=working)
        ):
            continue
        layer = (
            identity_basis(record, working=True)
            if group.home == "identity"
            else record.persona.selections
        )
        held = layer.get(group.id)
        held_ids = [held] if isinstance(held, str) else list(held or ())
        menu = [
            _menu_entry(option)
            for option in group.menu_options()
            if RATING_ORDER[option.rating] <= rating_rank
        ]
        groups.append(
            {
                "id": group.id,
                "label": group.label,
                "kind": group.kind,
                "home": group.home,
                "widget": derive_widget(group),
                "required": group.required,
                "max_picks": group.max_picks,
                "section": group.section,
                "order": group.order,
                "hint": group.hint,
                "tags": list(group.tags),
                "options": menu,
                "value": held,
                "current": [_held_entry(group, oid) for oid in held_ids],
            }
        )
    return groups
