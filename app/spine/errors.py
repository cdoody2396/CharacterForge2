"""Spine-level errors and the refusal→HTTP mapping (O5_INPUTS §F.4).

Library refusal codes pass through verbatim — never renamed, never
softened. The HTTP status is a coarse secondary signal; the body's
``code`` is the contract-bound truth. Codes minted HERE (auth, record
not found, startup refusals) are spine-origin facts about the service,
not library renames (builder detail, recorded).
"""

from __future__ import annotations

from app.record import errors as record_errors
from app.record.errors import (
    GateRefusal,
    RecordError,
    RecordFormatError,
    SafetyNotInstalledError,
)

# -- spine-origin codes ------------------------------------------------------

AUTH_MISSING = "AUTH_MISSING"
AUTH_INVALID = "AUTH_INVALID"
RECORD_NOT_FOUND = "RECORD_NOT_FOUND"

# startup refusal codes (§C — fail-loud, every error named)
DATA_ROOT_UNWRITABLE = "DATA_ROOT_UNWRITABLE"
MAINTAINED_TREE_MISSING = "MAINTAINED_TREE_MISSING"
CATALOG_EMPTY = "CATALOG_EMPTY"
SPINE_ALREADY_RUNNING = "SPINE_ALREADY_RUNNING"


class StartupRefusal(Exception):
    """§C: a spine that starts is a spine whose data all validated.
    Carries every failure, each line ``[CODE] detail``."""

    def __init__(self, failures: list[str]):
        self.failures = list(failures)
        super().__init__("; ".join(self.failures))


class AlreadyRunningRefusal(StartupRefusal):
    """The distinct second-instance error (§C)."""

    def __init__(self, data_root):
        super().__init__(
            [
                f"[{SPINE_ALREADY_RUNNING}] another spine already serves "
                f"data root {data_root}"
            ]
        )


class RecordNotFound(Exception):
    """No record file for this character id (spine-origin; 404)."""

    def __init__(self, character_id: str):
        self.character_id = character_id
        super().__init__(f"[{RECORD_NOT_FOUND}] no record for {character_id!r}")


# -- refusal → HTTP status ---------------------------------------------------
#
# 409 = the record's current state refuses the move (law-in-context);
# 422 = the request's payload/content refuses on its own terms. The split
# is a builder detail (recorded); clients dispatch on ``code``, not status.

CONFLICT_CODES = frozenset(
    {
        record_errors.RATING_DECREASE,
        record_errors.IDENTITY_NO_DRAFT,
        record_errors.DRAFT_ALREADY_OPEN,
        record_errors.NO_DRAFT,
        record_errors.REQUIRED_GROUP_UNFILLED,
        record_errors.RETIRED_NEW_PICK,
        record_errors.HIDDEN_GROUP_VALUE,
        record_errors.RATING_ABOVE_RECORD,
    }
)


def status_for(exc: RecordError) -> int:
    if isinstance(exc, SafetyNotInstalledError):
        # The spine always passes the real filter; reaching this is a
        # spine-invariant breach, not a client error.
        return 500
    if isinstance(exc, GateRefusal):
        return 409 if exc.code in CONFLICT_CODES else 422
    if isinstance(exc, RecordFormatError):
        return 422
    return 422


def error_body(exc: RecordError) -> dict:
    """The structured refusal (§F.4): existing code and subject, verbatim."""
    return {"code": exc.code, "subject": exc.subject, "message": str(exc)}
