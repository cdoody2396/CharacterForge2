"""Harvest CLI (stage O2).

    python -m tools.harvest <v1_root> [--out DIR] [--report DIR]

Reads a v1 CharacterForge checkout, emits the v2 option tree and the three
harvest artifacts (HARVEST_LOG.md, PRIORITY_REVIEW.md, POLISH_FLAGS.md).
The v2 validator is the gatekeeper: nothing is written unless the staged
emission set loads with zero errors.

Exit codes: 0 clean · 1 the emission set failed validation · 2 the tool
refused the source (unknown file, null, example_ id, unreadable input).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.harvest.harvest import HarvestError, harvest_tree, write_output


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
    args = parser.parse_args(argv)

    try:
        result = harvest_tree(args.v1_root)
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
