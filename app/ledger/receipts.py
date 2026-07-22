"""Sidecar receipt schema (N8) — the SOURCE OF TRUTH for every rendered
artifact. One JSON per artifact, next to it, named ``*.receipt.json``
(naming convention builder's, recorded).

Fields (N8, plus ``character_id`` — O3 gate decision 4, taken with Casey
this session: R4's version-vs-active comparison needs to know WHICH
character's pointer to read, and a self-contained receipt beats a path
convention):

    { "format": 1,
      "character_id": "...", "kind": "...", "identity_version": 2,
      "method": "...",
      "variables": { "<group_id>": "<option_id>" | ["..."] },   # {} legal
      "rating_at_render": "standard",
      "created": "<stamp>", "artifact_path": "...", "content_hash": "..." }

The variable receipt is EXPLICIT-EMPTY legal (§A6): ``{}`` states "this
render used no variables" — different in kind from a missing key, which is
a schema error. No nulls anywhere (the record/data-file law). The SQLite
index is DERIVED from these files and rebuildable at any time; when index
and sidecar disagree, the sidecar wins.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.options.loader import VALID_RATINGS
from app.ledger import errors as E
from app.ledger.errors import ReceiptError

RECEIPT_FORMAT = 1
SIDECAR_SUFFIX = ".receipt.json"

_RECEIPT_KEYS = frozenset(
    {
        "format",
        "character_id",
        "kind",
        "identity_version",
        "method",
        "variables",
        "rating_at_render",
        "created",
        "artifact_path",
        "content_hash",
    }
)


@dataclass(frozen=True)
class Receipt:
    """One parsed sidecar receipt. ``sidecar_path`` is where it was read
    from (the index key), not a schema field."""

    sidecar_path: str
    character_id: str
    kind: str
    identity_version: int
    method: str
    variables: dict
    rating_at_render: str
    created: str
    artifact_path: str
    content_hash: str


def _fail(code: str, file: str, subject: str | None, message: str) -> ReceiptError:
    return ReceiptError(file, code, subject, message)


def _reject_nulls(value: object, file: str, where: str) -> None:
    if value is None:
        raise _fail(E.RECEIPT_NULL, file, where, f"{where}: null is illegal")
    if isinstance(value, dict):
        for key, entry in value.items():
            _reject_nulls(entry, file, f"{where}.{key}")
    elif isinstance(value, list):
        for i, entry in enumerate(value):
            _reject_nulls(entry, file, f"{where}[{i}]")


def _read_str(data: dict, key: str, file: str) -> str:
    if key not in data:
        raise _fail(E.RECEIPT_MISSING_KEY, file, key, f"receipt is missing {key!r}")
    value = data[key]
    if not isinstance(value, str) or not value:
        raise _fail(
            E.RECEIPT_BAD_TYPE, file, key, f"{key!r} must be a non-empty string"
        )
    return value


def load_receipt(path: Path | str) -> Receipt:
    """Strict-load one sidecar receipt (schema above; fail loud)."""
    path = Path(path)
    file = path.name
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise _fail(E.RECEIPT_INVALID_JSON, file, None, f"cannot read: {exc}")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise _fail(E.RECEIPT_INVALID_JSON, file, None, f"invalid JSON ({exc})")
    if not isinstance(data, dict):
        raise _fail(E.RECEIPT_BAD_TYPE, file, None, "receipt must be one JSON object")
    _reject_nulls(data, file, "receipt")
    for key in data:
        if isinstance(key, str) and key.startswith("_"):
            continue  # §1.9 comment-key family
        if key not in _RECEIPT_KEYS:
            raise _fail(
                E.RECEIPT_UNKNOWN_KEY, file, key, f"receipt has unknown key {key!r}"
            )
    if data.get("format") != RECEIPT_FORMAT or isinstance(data.get("format"), bool):
        raise _fail(
            E.RECEIPT_BAD_TYPE,
            file,
            "format",
            f"'format' must equal {RECEIPT_FORMAT}, got {data.get('format')!r}",
        )
    version = data.get("identity_version")
    if "identity_version" not in data:
        raise _fail(
            E.RECEIPT_MISSING_KEY, file, "identity_version",
            "receipt is missing 'identity_version'",
        )
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise _fail(
            E.RECEIPT_BAD_TYPE,
            file,
            "identity_version",
            f"'identity_version' must be an int >= 1, got {version!r}",
        )
    if "variables" not in data:
        raise _fail(
            E.RECEIPT_MISSING_KEY, file, "variables",
            "receipt is missing 'variables' (explicit-empty {} is legal; "
            "absence is not)",
        )
    variables = data["variables"]
    if not isinstance(variables, dict):
        raise _fail(
            E.RECEIPT_BAD_TYPE, file, "variables", "'variables' must be an object"
        )
    for group_id, value in variables.items():
        ok = (isinstance(value, str) and value) or (
            isinstance(value, list)
            and value
            and all(isinstance(v, str) and v for v in value)
        )
        if not ok:
            raise _fail(
                E.RECEIPT_BAD_TYPE,
                file,
                group_id,
                f"variable {group_id!r} must be an option id or a non-empty "
                f"list of option ids",
            )
    rating = _read_str(data, "rating_at_render", file)
    if rating not in VALID_RATINGS:
        raise _fail(
            E.RECEIPT_BAD_TYPE,
            file,
            "rating_at_render",
            f"invalid rating {rating!r}; expected one of {VALID_RATINGS}",
        )
    return Receipt(
        sidecar_path=str(path),
        character_id=_read_str(data, "character_id", file),
        kind=_read_str(data, "kind", file),
        identity_version=version,
        method=_read_str(data, "method", file),
        variables=dict(variables),
        rating_at_render=rating,
        created=_read_str(data, "created", file),
        artifact_path=_read_str(data, "artifact_path", file),
        content_hash=_read_str(data, "content_hash", file),
    )
