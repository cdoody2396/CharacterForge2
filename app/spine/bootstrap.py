"""Fail-loud startup (O5_INPUTS §C/§D/§E): a spine that starts is a
spine whose data all validated.

Catalog load (§E): the bundled maintained tree, then the optional user
drop-in directory under the data root, through the full validator rule
set — resilient reporting (every error collected), strict acceptance
(any error refuses start). The maintained tree is required; an absent
drop-in directory is merely absent. No hot reload — restart only.

The ``options_dirs`` / ``safety_data_dir`` overrides are the test seam;
production passes neither and gets the program-bundled data (§D).
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from pathlib import Path

from app.options import load_catalog
from app.options.catalog import Catalog
from app.safety import AuditLog, SafetyFilter
from app.safety.errors import SafetyDataError
from app.spine.errors import (
    CATALOG_EMPTY,
    DATA_ROOT_UNWRITABLE,
    MAINTAINED_TREE_MISSING,
    StartupRefusal,
)
from app.spine.paths import (
    PROGRAM_OPTIONS_DIR,
    SAFETY_DATA_DIR,
    SpinePaths,
)
from app.spine.store import RecordStore
from app.spine.version import SPINE_VERSION


@dataclass(frozen=True)
class SpineContext:
    """Everything the running service owns, built once at startup —
    the first place every real object meets every other (§G)."""

    paths: SpinePaths
    catalog: Catalog
    safety: SafetyFilter
    audit: AuditLog
    store: RecordStore
    token: str
    version: str


def build_context(
    data_root: Path | str,
    *,
    options_dirs: list[Path] | None = None,
    safety_data_dir: Path | str | None = None,
) -> SpineContext:
    paths = SpinePaths.under(data_root)
    failures: list[str] = []

    # First run creates the root and layout; creation failures are
    # startup refusals (§D).
    try:
        for directory in paths.created_dirs():
            directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise StartupRefusal(
            [
                f"[{DATA_ROOT_UNWRITABLE}] cannot create the data-root "
                f"layout under {paths.data_root}: {exc}"
            ]
        )

    # Catalog (§E): maintained tree required, drop-in optional. The
    # loader silently skips missing directories, so the maintained
    # tree's existence is asserted explicitly.
    if options_dirs is None:
        options_dirs = [PROGRAM_OPTIONS_DIR, paths.dropin_dir]
    maintained = Path(options_dirs[0])
    catalog: Catalog | None = None
    if not maintained.is_dir():
        failures.append(
            f"[{MAINTAINED_TREE_MISSING}] maintained option tree missing: "
            f"{maintained}"
        )
    else:
        present = [d for d in options_dirs if Path(d).is_dir()]
        catalog = load_catalog(present, strict=False)
        for record in catalog.errors:
            where = record.file + (f" {record.subject}" if record.subject else "")
            failures.append(f"[{record.code}] {where}: {record.message}")
        if not catalog.errors and len(catalog) == 0:
            failures.append(
                f"[{CATALOG_EMPTY}] the option catalog loaded no groups "
                f"from {', '.join(str(d) for d in options_dirs)}"
            )

    # Audit + safety (§G/§H): the real AuditLog is the filter's sink.
    audit = AuditLog(paths.audit_dir)
    safety: SafetyFilter | None = None
    try:
        safety = SafetyFilter(
            safety_data_dir if safety_data_dir is not None else SAFETY_DATA_DIR,
            audit_sink=audit,
        )
    except SafetyDataError as exc:
        failures.append(f"[{exc.code}] safety word data: {exc}")

    if failures:
        raise StartupRefusal(failures)
    assert catalog is not None and safety is not None

    token = secrets.token_urlsafe(32)
    store = RecordStore(paths.records_dir, paths.db_path, catalog)
    return SpineContext(
        paths=paths,
        catalog=catalog,
        safety=safety,
        audit=audit,
        store=store,
        token=token,
        version=SPINE_VERSION,
    )
