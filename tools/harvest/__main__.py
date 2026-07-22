"""Harvest CLI (stages O2/O2b).

    python -m tools.harvest <v1_root> [--out DIR] [--report DIR] [--overrides FILE]

Reads a v1 CharacterForge checkout, applies the planning gate's overrides
(default: the committed tools/harvest/overrides.json), and emits the v2
option tree plus the harvest artifacts (HARVEST_LOG.md, PRIORITY_REVIEW.md,
POLISH_FLAGS.md, OVERRIDES_APPLIED.md). The v2 validator is the gatekeeper:
nothing is written unless the staged emission set loads with zero errors.

Exit codes: 0 clean · 1 the emission set failed validation · 2 the tool
refused the source (unknown file, null, example_ id, unreadable input, or
a bad/unapplied override).

FROZEN at O2b: the emitted tree in app/data/options/ is the MAINTAINED
SOURCE — content edits happen there directly, under the validator. This
tool remains only for the personal drop-in pass (O2_INPUTS answer 1);
targeting the maintained tree with --out requires the explicit
--i-know-this-overwrites-maintained-data flag.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.harvest.harvest import (
    HarvestError,
    harvest_tree,
    load_overrides,
    write_output,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.harvest",
        description="Harvest v1 option data into the v2 format (O2_INPUTS.md).",
    )
    parser.add_argument("v1_root", type=Path, help="path to a v1 CharacterForge checkout")
    parser.add_argument(
        "--out", type=Path, default=Path("app/data/options"),
        help="output data directory (default: app/data/options)",
    )
    parser.add_argument(
        "--report", type=Path, default=Path("harvest_report"),
        help="harvest artifact directory (default: harvest_report)",
    )
    parser.add_argument(
        "--overrides", type=Path,
        default=Path(__file__).resolve().parent / "overrides.json",
        help="planning-gate overrides file (default: the committed "
        "tools/harvest/overrides.json)",
    )
    parser.add_argument(
        "--i-know-this-overwrites-maintained-data", action="store_true",
        help="required when --out targets app/data/options/ — since O2b that "
        "tree is the maintained source, not a harvest product",
    )
    args = parser.parse_args(argv)

    # O2b freeze: app/data/options/ is the MAINTAINED SOURCE. Overwriting it
    # is never implicit — the flag is the operator saying so out loud.
    maintained = Path(__file__).resolve().parents[2] / "app" / "data" / "options"
    if (
        args.out.resolve() == maintained
        and not args.i_know_this_overwrites_maintained_data
    ):
        print(
            "REFUSED: --out targets app/data/options/, the MAINTAINED SOURCE "
            "(frozen at O2b — content edits happen there directly, under the "
            "validator). If you really mean to overwrite it, pass "
            "--i-know-this-overwrites-maintained-data."
        )
        return 2

    try:
        overrides = load_overrides(args.overrides)
        result = harvest_tree(args.v1_root, overrides)
        errors = write_output(result, args.out, args.report)
    except HarvestError as exc:
        print(f"REFUSED: {exc}")
        return 2
    if errors:
        print("emission set failed validation; nothing written:")
        for record in errors:
            print(f"ERROR {record.message}")
        return 1
    for i, flag in enumerate(result.flags, 1):
        print(f"FLAG {i}: {flag.file} / {flag.group}: {flag.reason}")
    groups = sum(row["groups"] for row in result.inventory)
    options = sum(row["options"] for row in result.inventory)
    print(
        f"harvested v1 commit {result.source['commit'] or '(unknown)'}: "
        f"{len(result.files)} files, {groups} groups, {options} options -> {args.out}"
    )
    print(f"reports -> {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
