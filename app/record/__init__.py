"""Character record model, construction/finalization gates, orphan report.

Stage O3 (O3_INPUTS.md §B): one JSON file per character (N1), selections
keyed by group id (N2), the construction gate on every mutation (N4), the
finalization gate and commit mechanics (N5), the safety seam (N6), the
appearance-paragraph drafter (N7), and the orphan report (N9).
"""

from app.record.model import (
    CharacterRecord,
    IdentityVersion,
    load_record,
    save_record,
)
from app.record.orphans import OrphanEntry, orphan_report

__all__ = [
    "CharacterRecord",
    "IdentityVersion",
    "OrphanEntry",
    "load_record",
    "orphan_report",
    "save_record",
]
