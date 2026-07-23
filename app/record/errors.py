"""Error taxonomy for the character record (O3_INPUTS N1–N7, N9).

Coverage is DECIDED (every N4/N5/N6 refusal is a distinct, testable error);
exact spellings are the builder's, recorded in SESSION_REPORT_O3.

Three failure surfaces:

- :class:`RecordFormatError` — a record FILE does not conform to the N1/N2
  shape at load (unknown keys, nulls, bad types, session-home values). The
  same strict-authoring stance as the option format: fail loud, load nothing.
- :class:`GateRefusal` — the construction gate (N4) or finalization gate
  (N5) refuses a mutation. The record is unchanged on refusal.
- :class:`SafetyNotInstalledError` — N6: no word filter was supplied to
  this write path; free-text and appearance-paragraph writes refuse
  HONESTLY instead of stubbing into silence (the v1 NOT_CONFIGURED
  pattern). O4 opened the seam: with a filter passed in (§F) these paths
  write; without one, every O3 refusal stands unchanged.

Unknown ids at LOAD are deliberately not errors — they are the orphan
report's business (N9): the record loads, orphaned picks stay written but
inert.
"""

from __future__ import annotations

# --- construction-gate refusal codes (N4) ----------------------------------
AGE_MISSING = "AGE_MISSING"
AGE_NOT_INTEGER = "AGE_NOT_INTEGER"
AGE_UNDER_FLOOR = "AGE_UNDER_FLOOR"
AGE_OVER_CEILING = "AGE_OVER_CEILING"
UNKNOWN_GROUP = "UNKNOWN_GROUP"
UNKNOWN_OPTION = "UNKNOWN_OPTION"
RATING_ABOVE_RECORD = "RATING_ABOVE_RECORD"
RETIRED_NEW_PICK = "RETIRED_NEW_PICK"
HIDDEN_GROUP_VALUE = "HIDDEN_GROUP_VALUE"
LIST_FOR_PICK_ONE = "LIST_FOR_PICK_ONE"
NOT_A_LIST_FOR_PICK_MANY = "NOT_A_LIST_FOR_PICK_MANY"
EMPTY_PICK_LIST = "EMPTY_PICK_LIST"
DUPLICATE_PICK = "DUPLICATE_PICK"
MAX_PICKS_EXCEEDED = "MAX_PICKS_EXCEEDED"
BAD_VALUE_TYPE = "BAD_VALUE_TYPE"
SESSION_HOME_VALUE = "SESSION_HOME_VALUE"
NULL_VALUE = "NULL_VALUE"
BAD_RATING = "BAD_RATING"
RATING_DECREASE = "RATING_DECREASE"
IDENTITY_NO_DRAFT = "IDENTITY_NO_DRAFT"
DRAFT_ALREADY_OPEN = "DRAFT_ALREADY_OPEN"

# --- finalization-gate refusal codes (N5) ----------------------------------
NO_DRAFT = "NO_DRAFT"
REQUIRED_GROUP_UNFILLED = "REQUIRED_GROUP_UNFILLED"

# --- safety seam (N6; opened by O4_INPUTS §F) -------------------------------
SAFETY_NOT_INSTALLED = "SAFETY_NOT_INSTALLED"
NAME_CHARSET = "NAME_CHARSET"
NAME_LENGTH = "NAME_LENGTH"
FREE_TEXT_OVERLONG = "FREE_TEXT_OVERLONG"
PARAGRAPH_OVERLONG = "PARAGRAPH_OVERLONG"
TEXT_BLOCKED = "TEXT_BLOCKED"
NAME_BLOCKED = "NAME_BLOCKED"

# --- record-file format codes (N1/N2, load surface) ------------------------
RECORD_NULL = "RECORD_NULL"
RECORD_UNKNOWN_KEY = "RECORD_UNKNOWN_KEY"
RECORD_MISSING_KEY = "RECORD_MISSING_KEY"
RECORD_BAD_TYPE = "RECORD_BAD_TYPE"
RECORD_BAD_VERSIONING = "RECORD_BAD_VERSIONING"
RECORD_INVALID_JSON = "RECORD_INVALID_JSON"


class RecordError(ValueError):
    """Base: any record-layer refusal, carrying a distinct code."""

    def __init__(self, code: str, subject: str | None, message: str):
        self.code = code
        self.subject = subject  # group/option id path or header field
        super().__init__(f"[{code}] {message}")


class RecordFormatError(RecordError):
    """A record file does not conform to the N1/N2 shape (load surface)."""


class GateRefusal(RecordError):
    """The construction (N4) or finalization (N5) gate refuses a mutation."""


class SafetyNotInstalledError(RecordError):
    """N6: no filter was supplied to this write path; it refuses honestly
    rather than accepting text no filter has seen (§F law)."""

    def __init__(self, subject: str | None, message: str):
        super().__init__(SAFETY_NOT_INSTALLED, subject, message)
