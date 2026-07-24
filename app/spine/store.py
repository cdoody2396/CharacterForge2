"""The record store the spine owns (O5_INPUTS §F.4/§G).

The record layer is pure library code taking explicit paths; this store
supplies what it deferred: the records directory, the file naming
scheme (``<character_id>.json``; ids the spine mints are uuid4 hex —
builder detail, recorded), and the per-character serialization around
the read-modify-write. The record layer's atomic-write law protects the
file; the store's per-character lock protects the read-modify-write.

Ledger wiring (§G): ``Ledger.attach`` on every record load served.
Ledgers are constructed per call — the sqlite3 connection inside
``Ledger`` is thread-bound (``check_same_thread``), and requests run on
a thread pool; a fresh short-lived connection per use is the safe shape.
"""

from __future__ import annotations

import json
import re
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path

from app.ledger import Ledger
from app.options.catalog import Catalog
from app.record import CharacterRecord, OrphanEntry, load_record, save_record
from app.spine.errors import RecordNotFound

# The spine's naming scheme keeps ids filesystem-safe; anything outside
# it cannot name a record file this store wrote.
_SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")


class RecordStore:
    def __init__(self, records_dir: Path, db_path: Path, catalog: Catalog):
        self._records_dir = Path(records_dir)
        self._db_path = Path(db_path)
        self._catalog = catalog
        self._locks: dict[str, threading.Lock] = {}
        self._registry_lock = threading.Lock()

    # -- paths and locks -----------------------------------------------------

    def path_for(self, character_id: str) -> Path:
        return self._records_dir / f"{character_id}.json"

    def _lock_for(self, character_id: str) -> threading.Lock:
        with self._registry_lock:
            return self._locks.setdefault(character_id, threading.Lock())

    def list_ids(self) -> list[str]:
        return sorted(p.stem for p in self._records_dir.glob("*.json"))

    @contextmanager
    def open_ledger(self):
        ledger = Ledger(self._db_path)
        try:
            yield ledger
        finally:
            ledger.close()

    # -- operations ----------------------------------------------------------

    def create(self, age: object) -> tuple[str, dict]:
        """Mint an id, run creation through the gate, persist."""
        character_id = uuid.uuid4().hex
        record = CharacterRecord.create(character_id, age)
        with self._lock_for(character_id):
            path = self.path_for(character_id)
            save_record(record, path)
            raw = self._read_raw(path)
        return character_id, raw

    def load(self, character_id: str) -> tuple[CharacterRecord, list[OrphanEntry], dict]:
        """Load + ledger attach + orphan report (§G), under the lock so a
        read never races a same-character ``os.replace``."""
        with self._lock_for(character_id):
            path = self._existing_path(character_id)
            with self.open_ledger() as ledger:
                record, orphans = load_record(path, self._catalog)
                ledger.attach(record)
            raw = self._read_raw(path)
        return record, orphans, raw

    def mutate(self, character_id: str, fn) -> tuple[CharacterRecord, list[OrphanEntry], dict]:
        """The serialized read-modify-write (§F): load → attach → mutate →
        atomic save, all under this character's lock. A gate refusal
        leaves the record unchanged and nothing is saved."""
        with self._lock_for(character_id):
            path = self._existing_path(character_id)
            with self.open_ledger() as ledger:
                record, orphans = load_record(path, self._catalog)
                ledger.attach(record)
                fn(record)
                save_record(record, path)
            raw = self._read_raw(path)
        return record, orphans, raw

    def ensure_exists(self, character_id: str) -> None:
        self._existing_path(character_id)

    # -- helpers -------------------------------------------------------------

    def _existing_path(self, character_id: str) -> Path:
        if not _SAFE_ID.fullmatch(character_id):
            raise RecordNotFound(character_id)
        path = self.path_for(character_id)
        if not path.is_file():
            raise RecordNotFound(character_id)
        return path

    @staticmethod
    def _read_raw(path: Path) -> dict:
        # The on-disk shape IS the record layer's declared contract; the
        # spine serves it rather than maintaining a second projection.
        return json.loads(path.read_text(encoding="utf-8-sig"))
