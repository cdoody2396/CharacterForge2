"""Error taxonomy for the option format (spec §10, as amended by O2_INPUTS).

Coverage is DECIDED — every law fails with a distinct, testable error naming
the file and the offending group/option id. Exact spellings are the
builder's, with one exception: ``EXAMPLE_ID_IN_DATA`` is spelled by §0.

Two failure surfaces exist:

- :class:`OptionFormatError` — a per-FILE format violation. Files apply
  atomically, so in resilient mode the whole file is skipped and the error
  recorded on the catalog; in strict mode it raises.
- Catalog-level law violations (§7, plus the merged-state checks of §§4/6
  that are only decidable after all files merge). These are recorded on the
  catalog in resilient mode and raised as :class:`CatalogError` in strict
  mode. Both surfaces record as :class:`FormatErrorRecord`.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- per-file format error codes -------------------------------------------
NOT_AN_OBJECT = "NOT_AN_OBJECT"
INVALID_JSON = "INVALID_JSON"
BAD_ENCODING = "BAD_ENCODING"
UNREADABLE_FILE = "UNREADABLE_FILE"
UNKNOWN_KEY = "UNKNOWN_KEY"
MISSING_KEY = "MISSING_KEY"
BAD_FORMAT_VERSION = "BAD_FORMAT_VERSION"
BAD_RATING = "BAD_RATING"
BAD_KIND = "BAD_KIND"
BAD_HOME = "BAD_HOME"
BAD_PRIORITY = "BAD_PRIORITY"
BAD_STATUS = "BAD_STATUS"
BAD_FEEDS = "BAD_FEEDS"
BAD_KEY_TYPE = "BAD_KEY_TYPE"
BAD_OPTION_ID = "BAD_OPTION_ID"
BAD_GROUP_ID = "BAD_GROUP_ID"
BAD_COLOR = "BAD_COLOR"
BAD_VISIBLE_WHEN = "BAD_VISIBLE_WHEN"
SCENE_OVERRIDABLE_NON_IDENTITY = "SCENE_OVERRIDABLE_NON_IDENTITY"
MAX_PICKS_ON_NON_PICK_MANY = "MAX_PICKS_ON_NON_PICK_MANY"
BAD_MAX_PICKS = "BAD_MAX_PICKS"
FEEDS_ON_PICK_KIND = "FEEDS_ON_PICK_KIND"
MAX_CHARS_ON_PICK_KIND = "MAX_CHARS_ON_PICK_KIND"
BAD_MAX_CHARS = "BAD_MAX_CHARS"
OPTIONS_ON_FREE_TEXT = "OPTIONS_ON_FREE_TEXT"
OPTIONS_MISSING = "OPTIONS_MISSING"
FREE_TEXT_SESSION = "FREE_TEXT_SESSION"
DUPLICATE_OPTION_ID = "DUPLICATE_OPTION_ID"
# O2_INPUTS answer 8.3: kind, home, feeds, scene_overridable are merge-locked;
# an extension fragment touching any of them is a format error (subsumes O1's
# KIND_CHANGED).
MERGE_LOCKED_KEY = "MERGE_LOCKED_KEY"

# --- catalog-level law codes (§7 + merged-state checks) --------------------
EXAMPLE_ID_IN_DATA = "EXAMPLE_ID_IN_DATA"  # spelling DECIDED by §0
TWO_SLOT_LAW = "TWO_SLOT_LAW"
PRIORITY_WITHOUT_IMAGE_TEXT = "PRIORITY_WITHOUT_IMAGE_TEXT"
IMAGE_TEXT_WITHOUT_PRIORITY = "IMAGE_TEXT_WITHOUT_PRIORITY"
VISIBLE_WHEN_UNKNOWN_GROUP = "VISIBLE_WHEN_UNKNOWN_GROUP"
VISIBLE_WHEN_FREE_TEXT_PREDICATE = "VISIBLE_WHEN_FREE_TEXT_PREDICATE"
# O2_INPUTS answer 8.1: a pick-kind group with zero options DEFINED after
# merge is a catalog error (recorded resilient, raised strict) — hidden would
# vanish a group silently.
EMPTY_PICK_GROUP = "EMPTY_PICK_GROUP"


@dataclass(frozen=True)
class FormatErrorRecord:
    """One recorded violation: which file, which law, which id."""

    file: str
    code: str
    subject: str | None  # group/option id path, e.g. "g1" or "g1/opt_a"
    message: str


class OptionFormatError(ValueError):
    """A data file does not conform to the option-definition format."""

    def __init__(self, file: str, code: str, subject: str | None, message: str):
        self.file = file
        self.code = code
        self.subject = subject
        super().__init__(f"{file}: [{code}] {message}")

    def record(self) -> FormatErrorRecord:
        return FormatErrorRecord(self.file, self.code, self.subject, str(self))


class CatalogError(ValueError):
    """A catalog-level law (§7 / merged-state §§4, 6) is violated.

    Raised in strict mode; in resilient mode the same violations are
    recorded on ``catalog.errors`` instead."""

    def __init__(self, records: list[FormatErrorRecord]):
        self.records = records
        super().__init__("; ".join(r.message for r in records))
