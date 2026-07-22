"""SQLite ledger index (N8/N10): a DERIVED, rebuildable index of the
sidecar receipts, plus the R4 staleness derivations and the R5
edit-marking hook.

N10 scope: one database file, stdlib ``sqlite3`` (zero-dependency rule),
WAL mode, schema-version pragma, path injected. O3 creates ONLY the
ledger-index table — transcripts, memory, and jobs tables belong to their
own stages.

Two stalenesses (§A6):

- identity-stale — receipt ``identity_version`` != the character's active
  pointer. DERIVED at query time; no stored marker exists to rot.
- variable-stale — the receipt's variable values no longer match the
  record's current values. Expensive to derive on every read, so the row
  carries a CACHED marker — and RECEIPTS WIN: the marker is recomputable
  from sidecars at any time, and a corrupted marker is corrected, never
  believed.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from app.ledger.receipts import SIDECAR_SUFFIX, Receipt, load_receipt

SCHEMA_VERSION = 1

_CREATE = """
CREATE TABLE IF NOT EXISTS ledger_index (
    sidecar_path     TEXT PRIMARY KEY,
    character_id     TEXT NOT NULL,
    kind             TEXT NOT NULL,
    identity_version INTEGER NOT NULL,
    method           TEXT NOT NULL,
    variables        TEXT NOT NULL,   -- JSON copy of the receipt's variables
    rating_at_render TEXT NOT NULL,
    created          TEXT NOT NULL,
    artifact_path    TEXT NOT NULL,
    content_hash     TEXT NOT NULL,
    variable_stale   INTEGER NOT NULL DEFAULT 0   -- CACHE; receipts win
)
"""


def variables_mismatch(receipt_variables: dict, current_values: dict) -> bool:
    """The variable-stale TRUTH (§A6): any variable the receipt recorded
    whose current record value differs (a cleared value differs too).
    Explicit-empty receipts can never mismatch."""
    return any(
        current_values.get(group_id) != value
        for group_id, value in receipt_variables.items()
    )


class Ledger:
    """The index plus its query/maintenance surface. ``db_path`` injected
    (tests use temp dirs)."""

    def __init__(self, db_path: Path | str):
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        if self._conn.execute("PRAGMA user_version").fetchone()[0] == 0:
            self._conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        self._conn.execute(_CREATE)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # -- indexing ------------------------------------------------------------

    def index_receipt(self, receipt: Receipt, current_values: dict | None = None) -> None:
        """Insert/replace one receipt's row. ``current_values`` (the
        character's current variable values) primes the variable-stale
        cache; without them the row starts fresh (0) and a later recompute
        settles it — the receipt on disk stays the truth either way."""
        stale = (
            variables_mismatch(receipt.variables, current_values)
            if current_values is not None
            else False
        )
        self._conn.execute(
            "INSERT OR REPLACE INTO ledger_index VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                receipt.sidecar_path,
                receipt.character_id,
                receipt.kind,
                receipt.identity_version,
                receipt.method,
                json.dumps(receipt.variables, sort_keys=True),
                receipt.rating_at_render,
                receipt.created,
                receipt.artifact_path,
                receipt.content_hash,
                int(stale),
            ),
        )
        self._conn.commit()

    def rebuild(
        self,
        sidecar_dirs: Iterable[Path | str],
        current_values_for: dict[str, dict] | None = None,
    ) -> int:
        """Reconstruct the WHOLE index from sidecar files (the AR
        derived-index law: the index is never the truth, so it can always
        be thrown away). ``current_values_for`` maps character id -> its
        current variable values, so the variable-stale cache recomputes
        from receipts; characters absent from the map index as fresh.
        Returns the number of receipts indexed."""
        self._conn.execute("DELETE FROM ledger_index")
        self._conn.commit()
        count = 0
        for directory in sidecar_dirs:
            directory = Path(directory)
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob(f"*{SIDECAR_SUFFIX}")):
                receipt = load_receipt(path)
                values = (current_values_for or {}).get(receipt.character_id)
                self.index_receipt(receipt, values)
                count += 1
        return count

    # -- R4: staleness -------------------------------------------------------

    def identity_stale(self, character_id: str, active_version: int) -> list[str]:
        """Sidecar paths of this character's artifacts whose identity
        version is not the active one. DERIVED — no marker column exists
        for this (§A6: version != active is cheap and always current)."""
        rows = self._conn.execute(
            "SELECT sidecar_path FROM ledger_index "
            "WHERE character_id = ? AND identity_version != ? "
            "ORDER BY sidecar_path",
            (character_id, active_version),
        )
        return [row[0] for row in rows]

    def variable_stale_marked(self, character_id: str) -> list[str]:
        """Sidecar paths currently CACHED as variable-stale. The cache is
        exactly that — ``recompute_variable_stale`` is the truth path."""
        rows = self._conn.execute(
            "SELECT sidecar_path FROM ledger_index "
            "WHERE character_id = ? AND variable_stale = 1 ORDER BY sidecar_path",
            (character_id,),
        )
        return [row[0] for row in rows]

    def recompute_variable_stale(
        self, character_id: str, current_values: dict
    ) -> list[str]:
        """Recompute every marker for the character from the indexed
        receipt copies — receipts win; a corrupted marker is corrected.
        Returns the sidecar paths now marked stale."""
        rows = self._conn.execute(
            "SELECT sidecar_path, variables FROM ledger_index WHERE character_id = ?",
            (character_id,),
        ).fetchall()
        stale_paths = []
        for sidecar_path, variables_json in rows:
            stale = variables_mismatch(json.loads(variables_json), current_values)
            if stale:
                stale_paths.append(sidecar_path)
            self._conn.execute(
                "UPDATE ledger_index SET variable_stale = ? WHERE sidecar_path = ?",
                (int(stale), sidecar_path),
            )
        self._conn.commit()
        return sorted(stale_paths)

    # -- R5: the edit-marking hook -------------------------------------------

    def mark_persona_edit(
        self, character_id: str, touched: tuple[str, ...], current_values: dict
    ) -> None:
        """R5: edits mark EXACTLY what they touched — only artifacts whose
        receipts mention a touched group are re-evaluated; every other
        marker is left alone."""
        rows = self._conn.execute(
            "SELECT sidecar_path, variables FROM ledger_index WHERE character_id = ?",
            (character_id,),
        ).fetchall()
        for sidecar_path, variables_json in rows:
            variables = json.loads(variables_json)
            if not any(group_id in variables for group_id in touched):
                continue
            stale = variables_mismatch(variables, current_values)
            self._conn.execute(
                "UPDATE ledger_index SET variable_stale = ? WHERE sidecar_path = ?",
                (int(stale), sidecar_path),
            )
        self._conn.commit()

    def attach(self, record) -> None:
        """Wire the R5 hook to a record's persona mutations: successful
        persona selection edits call back with the touched group ids."""

        def hook(rec, touched):
            self.mark_persona_edit(
                rec.character_id, touched, _record_variable_values(rec)
            )

        record.persona_edit_hooks.append(hook)

    # -- introspection -------------------------------------------------------

    def artifacts_for(self, character_id: str) -> list[sqlite3.Row]:
        self._conn.row_factory = sqlite3.Row
        try:
            return self._conn.execute(
                "SELECT * FROM ledger_index WHERE character_id = ? "
                "ORDER BY sidecar_path",
                (character_id,),
            ).fetchall()
        finally:
            self._conn.row_factory = None

    def rows(self) -> list[tuple]:
        """Every row, deterministically ordered — rebuild-equivalence's
        comparison surface."""
        return self._conn.execute(
            "SELECT * FROM ledger_index ORDER BY sidecar_path"
        ).fetchall()


def _record_variable_values(record) -> dict:
    """The current variable values a receipt compares against: the persona
    selections over the ACTIVE identity's (committed) selections. Draft
    state never marks anything — it is not live until finalization."""
    values = {}
    if record.active is not None:
        values.update(record.active.selections)
    values.update(record.persona.selections)
    return values
