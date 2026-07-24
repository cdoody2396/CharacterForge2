# O5 INPUTS — the service spine contract

Delivered by the planning gate (Casey) in-chat on 2026-07-24, at the O5
kickoff. Committed here verbatim so the contract lives in the repo, the
O3_INPUTS_N8_LADDER.md pattern. Everything below the line is the
delivery, untouched.

---

# O5_INPUTS — service spine (planning chat, 2026-07-23)

Marking convention: everything here is DECIDED unless tagged ILLUSTRATIVE.
Anything this document does not define is not the builder's to invent:
unclear → SESSION_REPORT `NOT_DECIDED`, build nothing for it.

---

## A. Stage scope

O5 builds `app/spine/`: one local service process that owns the existing
libraries at runtime — options catalog, record store, safety filter,
audit log, ledger — behind an authenticated, loopback-only,
server-authoritative API. Nothing else.

OUT of this stage (each owned elsewhere): front-end and creator screens
(UI stage) · desktop shell (packaging) · job runner, worker supervisor,
GPU-slot law, image/chat/training workers, llama.cpp and embedder
processes (image and chat sections) · transcripts / memory / jobs tables
(their own stages, per N10) · prompt assemblers (consumer contracts) ·
Layer-2 model gating · the rating-downgrade residue rule.

## B. Recorded creator-UX input (gate, 2026-07-23) — carried per O4_INPUTS §J

The owner's verbatim findings on v1, recorded as a named input:

> Bad choices on screen, bad screen formatting, bad option selection
> methods, bad user experience in making a character. Image and chat were
> not being updated as we were working on what the format and options
> should actually be.

Binding consequence for THIS stage (the screens themselves are the UI
stage's): **the spine is the single evaluator.** Visibility
(`visible_when`), rating admissibility, `required` flags, retired-option
handling, widget derivation, and gate refusals are all computed
spine-side and served to the front-end as facts; no client ever
re-implements catalog or gate logic (the v1 two-evaluator drift hazard,
designed out per the amended checkpoint). The UI stage inherits this
section verbatim.

## C. Process model (DECIDED)

- One service process. Framework: FastAPI + uvicorn — the checkpoint's
  reviewed stack decision. The zero-runtime-dependency rule ends here BY
  DECISION: dependencies are exactly `fastapi`, `uvicorn`, and the test
  client dependency FastAPI's TestClient requires, pinned in
  `requirements.txt`. Anything further is a `NOT_DECIDED`.
- Bind `127.0.0.1` explicitly, never `0.0.0.0` (loopback-only avoids the
  Windows Firewall first-run prompt — one-window/no-popup posture). Port:
  random free port at startup.
- Auth: a random per-run token generated at startup; every endpoint
  requires it (header; spelling builder's). No unauthenticated surface.
- Discovery: port + token written atomically to a runtime file under the
  data root (§D) so a shell or front-end can find the spine. File name
  and shape are the builder's, recorded.
- Single instance per data root: a second spine start against the same
  root refuses with a distinct error. Stale-lock recovery (crashed prior
  run) must exist; mechanism is the builder's, recorded and tested.
- Startup is fail-loud: catalog load errors (§E), safety data errors
  (O4 §C), or an unwritable data root refuse to start with the errors
  named. A spine that starts is a spine whose data all validated.

## D. Storage roots (DECIDED; names ILLUSTRATIVE)

- **One data root** holds all mutable state. Default:
  `%LOCALAPPDATA%/CharacterForge2`. Overridable by environment variable
  and by a `--data-root` flag (flag wins; spellings builder's). Nothing
  mutable is ever written beside the program install (installer-safe).
- Layout under the root (directory names ILLUSTRATIVE, the split
  DECIDED): `records/` — one JSON file per character (record layer's
  existing shape; file naming scheme is the builder's, recorded) ·
  `artifacts/<character_id>/` — future rendered artifacts with their
  sidecar receipts beside them (created lazily; empty this stage) ·
  `db/` — the single SQLite database (N10; ledger-index table only so
  far) · `audit/` — Layer-4 JSONL logs · `runtime` discovery file (§C).
- Program-bundled, read-only at runtime: the maintained option tree
  (`app/data/options/`) and the safety word data (`app/safety/data/`).
  The spine never writes either. User word-data tuning on an installed
  build is a packaging-stage concern, recorded here as deferred, not
  designed now.
- First run creates the root and layout; creation failures are startup
  refusals (§C).

## E. Catalog load and reload semantics (DECIDED)

- At startup the spine strict-loads, in order: the bundled maintained
  tree, then an optional user drop-in directory under the data root
  (name ILLUSTRATIVE, e.g. `options_dropin/`), through the full validator
  rule set. Any error in either source: refuse to start, name every
  error (the validator's resilient reporting, strict acceptance).
- The maintained tree stays frozen program data — user additions live
  only in the drop-in directory (the personal drop-in pass emits there).
- No hot reload. Catalog changes take effect at restart only — one
  evaluator, one load, no mid-session catalog drift. A restart is cheap;
  a stale-evaluator class of bugs is not.

## F. API surface (semantics DECIDED; paths, verbs, payload spellings builder's)

Endpoint inventory to build, each thin over the existing libraries — the
spine adds orchestration, never re-implements law:

1. **Service**: health/version (token-gated like everything else).
2. **Catalog**: full group/option listing with ratings, tags, retired
   status — the raw facts a library or editor view needs.
3. **Creator view** (the §B consequence made concrete): for a given
   record (or a new draft), return the groups visible under its current
   state, each with — derived widget · admissible options at the
   record's rating (retired options excluded from menus but resolvable
   for held values, per the O1 law) · current value(s) · `required`
   flag · section/order/hint passthrough. Widget derivation is
   spine-side from declared semantics (kind, cardinality, tags), closed
   set seeded by DECISIONS §10 (`segmented` / `chips` / `swatch` /
   `picker`); the exact mapping table is the builder's, recorded in the
   report. No numeric `slider` exists in v2 data.
4. **Records**: create · list (id, name, rating, active version, grade
   derivation summary) · load (with orphan report surfaced, N9) ·
   mutation endpoints that pass through the N4 gate verbatim · rating
   raise · finalize (N5) · the O4 filtered surfaces: name, looks/story
   slots, paragraph edit, name revalidation. Every gate/filter refusal
   maps to a structured error response carrying the existing code and
   subject — codes pass through, never renamed, never softened.
5. **Ledger**: per-character artifact/staleness queries and
   `derive_grade` passthrough (honestly undeterminable G1 included).

Concurrency: the spine serializes record mutations per character
(mechanism builder's); the record layer's atomic-write law already
protects the file, the spine protects the read-modify-write.

## G. Seam wrapping (DECIDED)

The spine wraps, at the named points: `Ledger.attach` on every record
load it serves · orphan surfacing on load and list (§F.4) · safety
filter construction at startup over the bundled word data, wired to the
real audit sink (§H). Null implementations remain what tests inject; the
spine is the first place every real object meets every other.

## H. Audit write sites landing now (DECIDED)

O4 §H deferred placement to the spine; this stage lands: the real
`AuditLog` constructed at startup, writing JSONL under `audit/` (§D) ·
every safety-filter refusal event (already emitted by the filter — the
spine supplies the real sink) · spine lifecycle lines: start (version,
data root) and clean stop. Generation and conversation logging remain
with their sections. The audit path stays vocabulary-blind.

## I. Rulings carried into the repo this gate (DECIDED)

1. **`misc` enforcement — CLOSED: floor, permanent.** The O4 inventory
   (incest, necrophilia, snuff, pipe-bomb instructions et al.) is
   exactly what the floor exists for; the "until inventoried" qualifier
   is spent. No data change — the list stands as built. NEXT_SESSION
   open item 2 closes.
2. **Catalog-declared `free_text` groups stay sealed.** The record gate
   keeps refusing them. Ownership assigned: whichever content-authoring
   or creator-UI contract first introduces such a group must specify its
   filtered write path (the O4 slot pattern) in that same contract.
   NEXT_SESSION open item 3 closes as owned, not as built.

## J. Required tests (coverage DECIDED)

Startup: clean start writes discovery file; catalog error / safety-data
error / unwritable root each refuse distinctly; second instance refuses;
stale-lock recovery · auth: every endpoint refuses without the token ·
loopback bind asserted · creator view: visibility shifts with selections,
rating admissibility, retired options excluded-but-resolvable, required
flags, widget derivation table exercised per widget · records: full
lifecycle over HTTP (create → select → finalize → filtered writes →
rating raise), every N4/N5/O4 refusal code arriving structured and
unrenamed · orphan report surfaced on load/list · ledger queries and
grade passthrough (G1 honestly undeterminable) · audit: refusal events
and lifecycle lines land in JSONL; vocabulary-blindness holds · per-
character mutation serialization under concurrent requests · drop-in
directory loads after the maintained tree; error in either refuses
start.

## K. Deliverables

Code per above · `requirements.txt` pinned per §C · all tests green;
`python -m app.options.validate app/data/options` exit 0 (no data change
expected — the report says so explicitly) · `SESSION_REPORT_O5.md`
(decisions, spellings, endpoint inventory, NOT_DECIDED) · README section
for running the spine · `NEXT_SESSION_PROMPT.md` redrafted (candidates
the planning chat expects: creator UI · image-identity section; carry
§B forward verbatim to whichever runs) · this file committed verbatim at
repo root with a provenance header.
