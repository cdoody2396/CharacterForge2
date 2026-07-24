"""Data-root resolution and layout (O5_INPUTS §D).

One data root holds all mutable state; nothing mutable is ever written
beside the program install. Program-bundled data — the maintained option
tree and the safety word data — is read-only at runtime and never
written by the spine.

Spellings here are the builder's (recorded, SESSION_REPORT_O5): the env
var is CHARACTERFORGE2_DATA_ROOT, the flag --data-root (flag wins), the
drop-in directory options_dropin/, the discovery file runtime.json, the
instance lock spine.lock, the database db/ledger.sqlite.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent.parent

# Program-bundled, read-only at runtime (§D).
PROGRAM_OPTIONS_DIR = _APP_DIR / "data" / "options"
SAFETY_DATA_DIR = _APP_DIR / "safety" / "data"

ENV_DATA_ROOT = "CHARACTERFORGE2_DATA_ROOT"
DEFAULT_DIR_NAME = "CharacterForge2"

DROPIN_DIR_NAME = "options_dropin"
DISCOVERY_FILE_NAME = "runtime.json"
LOCK_FILE_NAME = "spine.lock"
DB_FILE_NAME = "ledger.sqlite"


def default_data_root() -> Path:
    """%LOCALAPPDATA%/CharacterForge2 (§D); a home-relative fallback keeps
    non-Windows test environments runnable."""
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / DEFAULT_DIR_NAME
    return Path.home() / ".local" / "share" / DEFAULT_DIR_NAME


def resolve_data_root(flag_value: str | None = None) -> Path:
    """--data-root flag > CHARACTERFORGE2_DATA_ROOT > default (§D)."""
    if flag_value:
        return Path(flag_value)
    env = os.environ.get(ENV_DATA_ROOT)
    if env:
        return Path(env)
    return default_data_root()


@dataclass(frozen=True)
class SpinePaths:
    """Every path the spine derives from one data root."""

    data_root: Path
    records_dir: Path
    artifacts_dir: Path
    db_dir: Path
    audit_dir: Path
    dropin_dir: Path
    db_path: Path
    discovery_path: Path
    lock_path: Path

    @classmethod
    def under(cls, data_root: Path | str) -> "SpinePaths":
        root = Path(data_root)
        return cls(
            data_root=root,
            records_dir=root / "records",
            artifacts_dir=root / "artifacts",
            db_dir=root / "db",
            audit_dir=root / "audit",
            dropin_dir=root / DROPIN_DIR_NAME,
            db_path=root / "db" / DB_FILE_NAME,
            discovery_path=root / DISCOVERY_FILE_NAME,
            lock_path=root / LOCK_FILE_NAME,
        )

    def created_dirs(self) -> tuple[Path, ...]:
        """The layout first run creates (§D). artifacts/<character_id>/
        subdirectories stay lazy; the drop-in dir is the user's to make."""
        return (
            self.data_root,
            self.records_dir,
            self.artifacts_dir,
            self.db_dir,
            self.audit_dir,
        )
