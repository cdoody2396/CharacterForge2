"""Ledger skeleton (O3_INPUTS N8/N10): sidecar receipts as the source of
truth, a rebuildable SQLite index of them, R4 staleness derivations, the
R5 edit-marking hook, and the grade-derivation seam.

No real artifacts exist at this stage — synthetic sidecar fixtures test
everything; rendering arrives with the image section.
"""

from app.ledger.grade import (
    GradeDerivation,
    NullRingProvider,
    derive_grade,
)
from app.ledger.index import Ledger
from app.ledger.receipts import Receipt, load_receipt

__all__ = [
    "GradeDerivation",
    "Ledger",
    "NullRingProvider",
    "Receipt",
    "derive_grade",
    "load_receipt",
]
