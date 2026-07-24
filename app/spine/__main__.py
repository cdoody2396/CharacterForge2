"""CLI entry: ``python -m app.spine [--data-root PATH]``.

Data root resolution (§D): the flag wins over the
``CHARACTERFORGE2_DATA_ROOT`` environment variable, which wins over the
default ``%LOCALAPPDATA%/CharacterForge2``.
"""

from __future__ import annotations

import argparse
import sys

from app.spine.paths import ENV_DATA_ROOT, resolve_data_root
from app.spine.server import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.spine",
        description="CharacterForge2 service spine (loopback-only).",
    )
    parser.add_argument(
        "--data-root",
        default=None,
        help=f"data root directory (default: %%LOCALAPPDATA%%/CharacterForge2; "
        f"env override: {ENV_DATA_ROOT})",
    )
    args = parser.parse_args(argv)
    return run(resolve_data_root(args.data_root))


if __name__ == "__main__":
    sys.exit(main())
