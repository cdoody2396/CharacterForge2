"""Option format loader, catalog, and validator (stages O1–O2).

Public API re-exports; internal module layout is builder's choice
(OPTION_FORMAT_SPEC.md §13). The age-band subsystem was removed whole in
stage O2 (O2_INPUTS answer 6: spec §8 struck — apparent age is the
user-picked ``apparent_age`` group, not derivable from the record number).
"""

from app.options.catalog import Catalog, Group, Option
from app.options.errors import (
    CatalogError,
    FormatErrorRecord,
    OptionFormatError,
)
from app.options.loader import load_catalog

__all__ = [
    "Catalog",
    "CatalogError",
    "FormatErrorRecord",
    "Group",
    "Option",
    "OptionFormatError",
    "load_catalog",
]
