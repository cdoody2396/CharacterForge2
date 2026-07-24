# CharacterForge2

Stages O1–O5 of CharacterForge v2. This repository currently contains:

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
- **Character record model** (`app/record/`, stage O3 per
  [O3_INPUTS.md](O3_INPUTS.md)) — one JSON file per character: header,
  append-only immutable identity versions with an active pointer, at most
  one draft, an always-editable persona block. Atomic writes; strict load
  (no nulls, no unknown keys). Every mutation runs the **construction
  gate** (N4: age law 20–10000, unknown ids, rating admissibility and
  monotonicity, retired-option asymmetry, hidden-group refusal, kind
  shapes, session-home refusal); **finalization** (N5) re-checks the whole
  character plus required-when-visible across both layers, then commits
  the draft as v(n+1) with a deterministically drafted appearance
  paragraph (N7). The **safety seam** (N6) — OPENED at O4 per
  [O4_INPUTS.md](O4_INPUTS.md) §F: with a `SafetyFilter` passed in, the
  free-text slots write (cap 240, filtered), user paragraph edits target
  the draft (committed verbatim with a `paragraph_author` marker; every
  later finalization re-drafts), and names store `name_safety: "clear"`
  (finalization auto-revalidates a pending name). With no filter supplied,
  every O3 `SafetyNotInstalledError` refusal stands unchanged. Refusal,
  never redaction (§G). The **orphan report** (N9) lists unknown ids at
  load; the record still loads and orphaned picks stay written but inert.
- **Safety filter** (`app/safety/`, stage O4 per
  [O4_INPUTS.md](O4_INPUTS.md)) — the v1 Layer-1 deterministic word filter
  transplanted from v1 commit `a9519863`: pure blocklist/regex gating on
  normalized, obfuscation-folded text (homoglyphs, leetspeak, separators,
  stretching; no model, no network). Word files under `app/safety/data/`
  are the tuning surface and **self-declare** their scope in-file
  (`#! category / mode / enforcement` — §C); loading is fail-loud with
  distinct `SAFETY_*` codes and `minors`/`slurs` are floor-locked **in
  code**. Enforcement is rating-aware (§D/§E: everything floor except
  `drugs`, unlocked at `mature`). Contexts `freetext`/`chat`/`prompt`/
  `name` carry v1 semantics (contextual lists proximity-gate in free text,
  block outright in prompts, never gate names). An injected,
  vocabulary-blind audit sink (§H) logs refusals only — category and
  surface, never the matched term. The filter is passed where used, never
  a module global.
- **Ledger skeleton** (`app/ledger/`) — sidecar receipt JSON per rendered
  artifact as the source of truth; a rebuildable SQLite index (stdlib,
  WAL, injected path, one table only — N10); identity-staleness derived
  at query time, variable-staleness as a cached marker where **receipts
  win**; the R5 hook marks exactly what a persona edit touched;
  `derive_grade` rolls the G0/G1/G2 ladder up from ledger contents
  ([O3_INPUTS_N8_LADDER.md](O3_INPUTS_N8_LADDER.md): exactly
  (has-canonical-set, has-active-LoRA); G0 is every character's floor;
  grade is never stored) through the injected ring provider — the Null
  provider makes G1 honestly undeterminable until the image section
  supplies the ring-derivation rule. No artifacts render at this stage;
  synthetic sidecar fixtures test everything.
- **Service spine** (`app/spine/`, stage O5 per
  [O5_INPUTS.md](O5_INPUTS.md)) — one local process owning all of the
  above at runtime behind an authenticated, **loopback-only**,
  server-authoritative API. The spine is the **single evaluator** (§B):
  visibility, rating admissibility, required flags, retired handling,
  widget derivation, and gate refusals are computed spine-side and
  served as facts; no client re-implements catalog or gate logic.
  Fail-loud startup (catalog + drop-in through the full validator rule
  set, safety word data, writable data root — any error refuses start
  with every error named); single instance per data root with
  crash-natural stale-lock recovery; per-run token auth on every
  surface; atomic `runtime.json` discovery; per-character serialized
  mutations; the real `AuditLog` as the filter's sink plus
  `spine_start`/`spine_stop` lifecycle lines. Every refusal arrives as
  `{code, subject, message}` with the library's code verbatim. The
  endpoint inventory lives in
  [SESSION_REPORT_O5.md](SESSION_REPORT_O5.md).
- **Tests** (`tests/`) — 782 tests covering every format law with refusing
  tests, the harvest transformation rules, override consumption,
  refusals, the validator gate, byte-identical idempotence, every
  record-layer refusal individually, the ported v1 obfuscation/
  false-positive vector tables over the real word data, every §C
  declaration law, the opened seam both directions (filtered writes
  and the no-filter refusals), and the spine end to end over HTTP
  (startup refusals, auth, creator view, the full record lifecycle,
  every refusal code structured and unrenamed, audit, real-server
  loopback/discovery, concurrent-mutation serialization).
  `tests/fixtures/` is the only home for illustrative data.

## Running the tests

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). Runtime
dependencies (since O5, per O5_INPUTS §C) are exactly `fastapi`,
`uvicorn`, and `httpx`, pinned in [requirements.txt](requirements.txt)
and mirrored in pyproject/uv.lock.

```
uv sync
uv run pytest
```

## Running the validator

```
uv run python -m app.options.validate app/data/options
```

Exit 0 clean / 1 errors; `--json` emits a machine-readable summary.

## Running the spine

```
uv run python -m app.spine [--data-root PATH]
```

One process, bound to `127.0.0.1` on a random free port. The data root
(all mutable state) defaults to `%LOCALAPPDATA%/CharacterForge2`;
`--data-root` wins over the `CHARACTERFORGE2_DATA_ROOT` environment
variable. On a clean start the spine writes `runtime.json` (host, port,
per-run token, pid, version) atomically under the data root — clients
read it and send the token in the `X-Spine-Token` header on every
request; there is no unauthenticated surface. User option add-ons load
from `options_dropin/` under the data root, after the maintained tree,
through the full validator rule set; any error in either source refuses
startup with every error named. A second start against the same data
root refuses distinctly; a crashed run's lock recovers on the next
start. Stop with Ctrl+C — a clean stop logs `spine_stop` to the audit
trail and removes `runtime.json`.

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
eight O1 NOT_DECIDED items answered) **and [O3_INPUTS.md](O3_INPUTS.md)**
(§4 gains `required`, N3; the record layer's contract is its §B). The
safety stage's contract is [O4_INPUTS.md](O4_INPUTS.md) and the spine
stage's is [O5_INPUTS.md](O5_INPUTS.md) (neither changes the option
format). The §0 marking convention is binding:
**DECIDED** items are implemented exactly as written, and **ILLUSTRATIVE**
items (every identifier beginning `example_`) may never appear in committed
data — the loader refuses them outside `tests/fixtures/`
(`EXAMPLE_ID_IN_DATA`). See [SESSION_REPORT_O1.md](SESSION_REPORT_O1.md),
[SESSION_REPORT_O2.md](SESSION_REPORT_O2.md),
[SESSION_REPORT_O2B.md](SESSION_REPORT_O2B.md),
[SESSION_REPORT_O3.md](SESSION_REPORT_O3.md),
[SESSION_REPORT_O4.md](SESSION_REPORT_O4.md), and
[SESSION_REPORT_O5.md](SESSION_REPORT_O5.md) for what each stage decided,
found ambiguous, and left open.
