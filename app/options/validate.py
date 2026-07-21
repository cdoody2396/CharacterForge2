"""Validator CLI (§9) — the harvest's gatekeeper.

    python -m app.options.validate <dir> [<dir> ...] [--json]

Loads the given directories in order with the full strict rule set, prints
EVERY error with file name and group/option id (the resilient machinery is
used so validation does not stop at the first error; acceptance is strict:
any error -> exit 1), then a summary: files, groups, options, retired count,
per-rating counts, free-text slots found. ``--json`` emits one
machine-readable object for harvest tooling instead. Exit 0 clean / 1 errors.

Unlike the library loader (which skips missing directories, v1 carryover), a
named directory that does not exist is itself an error — a gatekeeper must
not silently skip a typo'd path.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.options.catalog import Catalog
from app.options.errors import FormatErrorRecord
from app.options.loader import VALID_RATINGS, load_catalog

MISSING_DIRECTORY = "MISSING_DIRECTORY"


def _summarize(catalog: Catalog, files: int) -> dict:
    groups = catalog.groups()
    options = [o for g in groups for o in g.options]
    return {
        "files": files,
        "groups": len(groups),
        "options": len(options),
        "retired": sum(1 for o in options if o.retired),
        # Per-rating counts at option granularity — every option carries its
        # source file's rating (Decision 5).
        "ratings": {
            rating: sum(1 for o in options if o.rating == rating)
            for rating in VALID_RATINGS
        },
        "free_text_slots": {
            home: sum(
                1 for g in groups if g.is_free_text and g.home == home
            )
            for home in ("identity", "persona")
        },
    }


def _count_files(dirs: list[Path]) -> int:
    return sum(
        1
        for d in dirs
        if d.is_dir()
        for p in sorted(d.glob("*.json"))
        if p.is_file()
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.options.validate",
        description="Validate option data directories (OPTION_FORMAT_SPEC.md §9).",
    )
    parser.add_argument("dirs", nargs="+", metavar="dir", type=Path)
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit one machine-readable JSON object (for harvest tooling)",
    )
    args = parser.parse_args(argv)

    errors: list[FormatErrorRecord] = []
    for directory in args.dirs:
        if not directory.is_dir():
            errors.append(
                FormatErrorRecord(
                    str(directory),
                    MISSING_DIRECTORY,
                    None,
                    f"{directory}: [{MISSING_DIRECTORY}] not a directory",
                )
            )
    catalog = load_catalog(args.dirs)  # resilient: collects every error
    errors.extend(catalog.errors)
    summary = _summarize(catalog, _count_files(list(args.dirs)))

    if args.json:
        payload = dict(
            summary,
            errors=[
                {"file": e.file, "code": e.code, "id": e.subject, "message": e.message}
                for e in errors
            ],
        )
        print(json.dumps(payload, indent=2))
    else:
        for e in errors:
            print(f"ERROR {e.message}")
        print(
            f"files: {summary['files']}  groups: {summary['groups']}  "
            f"options: {summary['options']}  retired: {summary['retired']}"
        )
        ratings = "  ".join(f"{k}: {v}" for k, v in summary["ratings"].items())
        slots = "  ".join(
            f"{k}: {v}" for k, v in summary["free_text_slots"].items()
        )
        print(f"per-rating option counts: {ratings}")
        print(f"free-text slots: {slots}")
        print("errors: " + (f"{len(errors)}" if errors else "0 — clean"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
