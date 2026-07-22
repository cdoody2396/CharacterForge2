# CharacterForge2

Stages O1–O2b of CharacterForge v2. This repository currently contains:

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
- **Harvest tool** (`tools/harvest/`) — converted v1 option data to the v2
  format; frozen at O2b (see below).
- **Option data** (`app/data/options/`) — **THE MAINTAINED SOURCE** since
  O2b: 13 files, 135 merged groups, 2359 options, harvested from v1 commit
  `a9519863` with the O2 planning-gate overrides applied (see
  [harvest_report/HARVEST_LOG.md](harvest_report/HARVEST_LOG.md) and
  [harvest_report/OVERRIDES_APPLIED.md](harvest_report/OVERRIDES_APPLIED.md)).
- **Harvest artifacts** (`harvest_report/`) — the harvest log, the priority
  review table (final column marks the gate's 13 overrides),
  OVERRIDES_APPLIED (every override with its `why` verbatim), and
  POLISH_FLAGS (groups whose wording v1 marked provisional).
- **Tests** (`tests/`) — 182 tests covering every format law with refusing
  tests, plus the harvest transformation rules, override consumption,
  refusals, the validator gate, and byte-identical idempotence.
  `tests/fixtures/` is the only home for illustrative data.

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

## The harvest tool — FROZEN at O2b

The emitted tree in `app/data/options/` is now the **MAINTAINED SOURCE**:
future content edits happen there directly, under the validator.
`tools/harvest` exists only for the personal drop-in pass (O2_INPUTS
answer 1) — it is never used to re-emit the bundled tree.

```
uv run python -m tools.harvest <v1_root> --out <DIR> --report <DIR>
```

Applies the committed planning-gate overrides
(`tools/harvest/overrides.json`; `--overrides` to substitute) and writes
nothing unless the staged emission set passes the full validator rule set.
Re-running over the same source is byte-identical. Exit codes: 0 clean ·
1 emission failed validation · 2 the tool refused the source or an
override. As a guard, `--out` targeting `app/data/options/` refuses to run
without the explicit `--i-know-this-overwrites-maintained-data` flag.

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
