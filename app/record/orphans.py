"""Orphan report (N9) — closes O1's deferral.

At record load against the live catalog, unknown group ids and unknown
option ids are LISTED per character; the record still loads, the orphaned
picks stay written but inert — restore the missing file and the character
is whole (Decision 6 pt 3, now buildable). Orphans are a report, never a
load error; the strict N4 gate is what keeps them out of NEW writes and
out of finalization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.options.catalog import Catalog
from app.record import errors as E

if TYPE_CHECKING:  # import cycle guard: model imports this module lazily
    from app.record.model import CharacterRecord

# Where an orphan can live inside the record file.
LOCATION_DRAFT = "draft_identity"
LOCATION_PERSONA = "persona"


def _location_version(number: int) -> str:
    return f"identity_versions[v{number}]"


@dataclass(frozen=True)
class OrphanEntry:
    """One inert pick: which part of the record, which ids, why."""

    location: str  # e.g. "draft_identity", "persona", "identity_versions[v2]"
    group_id: str
    option_id: str | None  # None when the whole group is unknown
    reason: str  # E.UNKNOWN_GROUP | E.UNKNOWN_OPTION


def _scan(catalog: Catalog, selections: dict, location: str) -> list[OrphanEntry]:
    entries: list[OrphanEntry] = []
    for group_id, value in selections.items():
        group = catalog.get(group_id)
        if group is None:
            entries.append(
                OrphanEntry(location, group_id, None, E.UNKNOWN_GROUP)
            )
            continue
        picked = [value] if isinstance(value, str) else list(value)
        for option_id in picked:
            # Retired options RESOLVE (Decision 6) — only truly unknown ids
            # are orphans.
            if group.resolve(option_id) is None:
                entries.append(
                    OrphanEntry(location, group_id, option_id, E.UNKNOWN_OPTION)
                )
    return entries


def orphan_report(record: "CharacterRecord", catalog: Catalog) -> list[OrphanEntry]:
    """Every unknown id in the record, across all identity versions, the
    draft, and the persona block — in record order."""
    entries: list[OrphanEntry] = []
    for version in record.identity_versions:
        entries.extend(
            _scan(catalog, version.selections, _location_version(version.version))
        )
    if record.draft is not None:
        entries.extend(_scan(catalog, record.draft.selections, LOCATION_DRAFT))
    entries.extend(_scan(catalog, record.persona.selections, LOCATION_PERSONA))
    return entries
