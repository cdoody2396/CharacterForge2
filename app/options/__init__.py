"""Option format loader, catalog, and age-band lookup (stage O1).

Public API re-exports; internal module layout is builder's choice
(OPTION_FORMAT_SPEC.md §13).
"""

from app.options.age_bands import AgeBand, load_age_bands
from app.options.catalog import Catalog, Group, Option
from app.options.errors import (
    AgeBandFormatError,
    CatalogError,
    FormatErrorRecord,
    OptionFormatError,
)
from app.options.loader import load_catalog

__all__ = [
    "AgeBand",
    "AgeBandFormatError",
    "Catalog",
    "CatalogError",
    "FormatErrorRecord",
    "Group",
    "Option",
    "OptionFormatError",
    "load_age_bands",
    "load_catalog",
]
