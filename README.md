# CharacterForge2

Stages O1–O2 of CharacterForge v2. This repository currently contains:

- **Option-format loader and catalog** (`app/options/loader.py`,
  `app/options/catalog.py`) — parses and merges option JSON files
  (extension/merge semantics, atomic per-file apply, resilient and strict
  modes), evaluates visibility conditions, and enforces the catalog-level
  laws. Amended in O2 per [O2_INPUTS.md](O2_INPUTS.md): rating is an
  option-level fact only; an empty pick group after merge is a catalog
  error; `kind`/`home`/`feeds`/`scene_overridable` are merge-locked; group
  ids obey the option-id hygiene rule; the age-band subsystem is deleted
  whole (spec §8 struck).
- **Validator CLI** (`app/options/validate.py`) —
  `python -m app.options.validate <dir> [<dir> ...] [--json]`; prints every
  error plus a summary, exit 0 clean / 1 errors. The gatekeeper for all
  data.
- **Harvest tool** (`tools/harvest/`) — converts v1 option data to the v2
  format (see below).
- **Harvested data** (`app/data/options/`) — 12 files, 135 merged groups,
  2357 options, from v1 commit `a9519863` (see
  [harvest_report/HARVEST_LOG.md](harvest_report/HARVEST_LOG.md)).
- **Harvest artifacts** (`harvest_report/`) — the harvest log, the priority
  review table (overrides are decided there, not in the tool), and
  POLISH_FLAGS (groups whose wording v1 marked provisional).
- **Tests** (`tests/`) — 168 tests covering every format law with refusing
  tests, plus the harvest transformation rules, refusals, the validator
  gate, and byte-identical idempotence. `tests/fixtures/` is the only home
  for illustrative data.

## Running the tests

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). No runtime
dependencies.

```
uv venv --python 3.12
uv pip install pytest
uv run pytest
```

## Running the validator

```
uv run python -m app.options.validate app/data/options
```

Exit 0 clean / 1 errors; `--json` emits a machine-readable summary.

## Running the harvest

```
git clone https://github.com/cdoody2396/CharacterForge <v1_root>
uv run python -m tools.harvest <v1_root>
```

Emits to `app/data/options/` and writes `harvest_report/`; nothing is
written unless the staged emission set passes the full validator rule set.
Re-running over the same v1 commit is byte-identical. Exit codes: 0 clean ·
1 emission failed validation · 2 the tool refused the source.

## The spec

[OPTION_FORMAT_SPEC.md](OPTION_FORMAT_SPEC.md) is the build contract, **as
amended by [O2_INPUTS.md](O2_INPUTS.md)** (spec §8 age bands struck; the
eight O1 NOT_DECIDED items answered). The §0 marking convention is binding:
**DECIDED** items are implemented exactly as written, and **ILLUSTRATIVE**
items (every identifier beginning `example_`) may never appear in committed
data — the loader refuses them outside `tests/fixtures/`
(`EXAMPLE_ID_IN_DATA`). See [SESSION_REPORT_O1.md](SESSION_REPORT_O1.md)
and [SESSION_REPORT_O2.md](SESSION_REPORT_O2.md) for what each stage
decided, found ambiguous, and left open.
