"""Error taxonomy for the safety filter (O4_INPUTS §C).

Coverage is DECIDED (§C law 2: every data-load refusal is a distinct,
testable error and the filter never starts over a bad data directory);
exact spellings are the builder's, recorded in SESSION_REPORT_O4.

One failure surface: :class:`SafetyDataError` — the word-file data
directory does not conform to the §C declaration laws at load. Same
strict-authoring stance as the option format and the record file: fail
loud, load nothing. Filter *usage* errors (unknown context, unknown
rating) are programmer errors and stay ``ValueError``, the v1 spelling.
"""

from __future__ import annotations

# --- §C declaration-law codes (load surface) --------------------------------
SAFETY_DATA_DIR_INVALID = "SAFETY_DATA_DIR_INVALID"
SAFETY_UNDECLARED_FILE = "SAFETY_UNDECLARED_FILE"
SAFETY_DECLARATION_MISSING = "SAFETY_DECLARATION_MISSING"
SAFETY_DECLARATION_UNKNOWN = "SAFETY_DECLARATION_UNKNOWN"
SAFETY_DECLARATION_DUPLICATE = "SAFETY_DECLARATION_DUPLICATE"
SAFETY_NO_PROXIMITY_VOCABULARY = "SAFETY_NO_PROXIMITY_VOCABULARY"
SAFETY_REGEX_IN_CONTEXTUAL = "SAFETY_REGEX_IN_CONTEXTUAL"
# §C law 3, the HARD LAW in code: minors/slurs load only at enforcement
# floor. A data edit cannot unlock these.
SAFETY_ENFORCEMENT_LOCKED = "SAFETY_ENFORCEMENT_LOCKED"


class SafetyDataError(ValueError):
    """A word-file data directory violates the §C laws; nothing loads."""

    def __init__(self, code: str, subject: str | None, message: str):
        self.code = code
        self.subject = subject  # file name (or data-dir path)
        super().__init__(f"[{code}] {message}")
