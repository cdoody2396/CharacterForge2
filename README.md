# CharacterForge2

Stage O1 of CharacterForge v2. This repository currently contains:

- **Option-format loader and catalog** (`app/options/loader.py`,
  `app/options/catalog.py`) — parses and merges option JSON files
  (extension/merge semantics, atomic per-file apply, resilient and strict
  modes), evaluates visibility conditions, and enforces the catalog-level
  laws.
- **Age-band loader** (`app/options/age_bands.py`) — loads and validates the
  age-band lookup file.
- **Validator CLI** (`app/options/validate.py`) —
  `python -m app.options.validate <dir> [<dir> ...] [--json]`; prints every
  error plus a summary, exit 0 clean / 1 errors.
- **Tests** (`tests/`) — 138 tests covering every format law with refusing
  tests. `tests/fixtures/` is the only home for illustrative data.

`app/data/options/` and the age-band file ship **empty of data** by design —
content arrives via the harvest stage.

## Running the tests

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). No runtime
dependencies.

```
uv venv --python 3.12
uv pip install pytest
uv run pytest
```

## The spec

[OPTION_FORMAT_SPEC.md](OPTION_FORMAT_SPEC.md) is the build contract for the
option file format and everything in this stage. Its §0 marking convention is
binding: **DECIDED** items are implemented exactly as written, and
**ILLUSTRATIVE** items (every identifier beginning `example_`) may never
appear in committed data or hardcoded values — the loader refuses them
outside `tests/fixtures/` (`EXAMPLE_ID_IN_DATA`). See
[SESSION_REPORT.md](SESSION_REPORT.md) for what was decided, what remains
open, and where the spec was found ambiguous.
