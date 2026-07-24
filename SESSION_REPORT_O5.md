# SESSION_REPORT — stage O5 (2026-07-24)

Builder session for the service spine. Contract: the O5 kickoff prompt +
O5_INPUTS.md (§A scope, §B single-evaluator consequence, §C process
model, §D storage roots, §E catalog load, §F API surface, §G seam
wrapping, §H audit write sites, §I rulings, §J tests, §K deliverables),
delivered in-chat and committed verbatim (first commit) with a
provenance header.

## What was built

1. **O5_INPUTS.md committed** (first commit, verbatim as delivered).
2. **Dependencies (§C)**: the zero-runtime-dependency rule ended BY
   DECISION. Exactly `fastapi==0.139.2`, `uvicorn==0.51.0`,
   `httpx==0.28.1` (the TestClient dependency), pinned in
   `requirements.txt` and mirrored in pyproject `[project] dependencies`
   + regenerated `uv.lock` (gate decision 1 below). Nothing else was
   added; transitive dependencies arrive only through these three.
3. **`app/spine/`** (§A–§H): `paths.py` (root resolution + layout) ·
   `bootstrap.py` (fail-loud startup, the §G seam wiring) ·
   `instance_lock.py` (single instance) · `discovery.py` (runtime file) ·
   `store.py` (records dir, per-character serialization, per-call
   ledger + attach) · `creator_view.py` (§B made concrete) ·
   `schemas.py` · `service.py` (app factory, auth middleware, refusal
   handlers, lifespan audit lines) · `routes_catalog.py` /
   `routes_records.py` / `routes_ledger.py` · `server.py` (socket,
   uvicorn, run) · `__main__.py` (CLI) · `errors.py` · `version.py`.
   No existing library file was modified; the spine only orchestrates.
4. **§I rulings carried**: no code or data change was needed — `misc`
   stays at floor as built (item closed), catalog-declared `free_text`
   groups stay sealed (the gate's `SAFETY_NOT_INSTALLED` refusal now
   reaches HTTP as a 409; ownership of the write path stays with the
   contract that first introduces such a group).
5. **Tests**: 782 passed (O4's 633 + 149 new; §J coverage inventory in
   the test commit message). Validator: exit 0, counts unchanged
   (13 / 135 / 2359) — **no option-tree change was made**, as §K expects.
6. This report; README gains "Running the spine"; NEXT_SESSION_PROMPT.md
   redrafted for the planning chat (creator UI · image-identity).

## Decisions taken at the planning gate during this session

1. **Dependency declaration layout**: the three §C pins live in
   `requirements.txt` (the contract-named artifact) AND pyproject
   `[project] dependencies` + `uv.lock`, same exact versions — because
   the repo's test runner is uv-managed and `uv sync` would drop
   pip-only installs. No top-level package beyond the three named.
2. **Catalog-declared `free_text` groups are excluded from the creator
   view** (they are sealed per §I.2, have no widget in the closed set,
   and zero exist in the maintained tree). The raw `/catalog` endpoint
   still serves them with full facts.

## Builder details (every naming/spelling choice, recorded)

- **Data root**: flag `--data-root` > env `CHARACTERFORGE2_DATA_ROOT` >
  default `%LOCALAPPDATA%/CharacterForge2` (POSIX test-environment
  fallback: `~/.local/share/CharacterForge2`). Layout under the root:
  `records/` · `artifacts/` · `db/ledger.sqlite` · `audit/` ·
  `options_dropin/` (user drop-in, §E) · `runtime.json` (discovery) ·
  `spine.lock`.
- **Auth**: per-run token `secrets.token_urlsafe(32)`, header
  `X-Spine-Token`, compared with `secrets.compare_digest` in pure ASGI
  middleware that runs BEFORE routing — unknown paths also refuse
  untokened. FastAPI's docs/redoc/openapi surfaces are disabled
  outright (no unauthenticated surface, no unnamed surface).
- **Discovery file**: `runtime.json` — `{host, port, token, pid,
  version, started}`, written same-directory-tmp + `os.replace`
  (atomic), removed on graceful stop, overwritten by the next start if
  a crash left it stale.
- **Instance lock**: an OS advisory exclusive lock on byte 0 of
  `spine.lock` (`msvcrt.locking` on Windows, `fcntl.flock` elsewhere),
  held for the process lifetime. The OS releases a dead holder's lock,
  so a leftover file that locks cleanly WAS stale — recovery needs no
  PID bookkeeping. The file is never deleted (Windows cannot unlink a
  locked file). The lock, not the discovery file, is the authority on
  "is one running".
- **Startup order** (`run`): build_context (layout → catalog → audit +
  safety, ALL errors collected then refused together) → instance lock →
  bind `127.0.0.1:0` and read the real port → write discovery → hand
  the already-listening socket to uvicorn (`sockets=[...]`) — no window
  where discovery names a port nobody owns.
- **Spine-origin codes** (service facts, not library renames):
  `AUTH_MISSING`, `AUTH_INVALID`, `RECORD_NOT_FOUND`,
  `SPINE_ALREADY_RUNNING`, `DATA_ROOT_UNWRITABLE`,
  `MAINTAINED_TREE_MISSING`, `CATALOG_EMPTY`.
- **Record ids and files**: the spine mints ids (uuid4 hex); files are
  `records/<character_id>.json`. Path addressing accepts
  `[A-Za-z0-9_-]{1,64}`; anything else is `RECORD_NOT_FOUND` (nothing
  outside that set can name a file this store wrote).
- **Concurrency**: one `threading.Lock` per character (registry under
  its own lock) held across the whole load → mutate → atomic-save;
  reads take it too (a read never races a same-character
  `os.replace`). `Ledger` is constructed per call and closed — its
  sqlite3 connection is thread-bound and requests run on a thread pool.
- **Responses**: record-returning endpoints serve the SAVED FILE's
  parsed JSON (the record layer's declared on-disk shape — no second
  projection to drift) as `{"record": …, "orphans": […]}`.
- **Request bodies are deliberately permissively typed** (`age`,
  `value`, `rating`, `name`, `text` accept anything): the N4 gate is
  the validator and refuses with ITS codes (`AGE_NOT_INTEGER`,
  `BAD_VALUE_TYPE`, …), never a framework 422. Addressing fields
  (`group_id`) stay typed.
- **Creator view**: per-group visibility basis mirrors
  `CharacterRecord._current_values` exactly (identity-home groups →
  draft+persona; persona-home → live identity + persona; parity pinned
  by test). `session`-home groups are excluded (not record-storable)
  alongside the gate-decided `free_text` exclusion. Menus =
  non-retired options at admissible rating (`RATING_ORDER` from the
  gate — the law is imported, not re-implemented); held values resolve
  retired-inclusive and carry a `retired` flag; unknown held ids are
  served as `orphaned`. Groups arrive in catalog (load) order with
  `section`/`order`/`hint` passed through.
- **Widget mapping table** (closed set seeded by DECISIONS §10; derived
  over the non-retired option list, so a widget never shifts with a
  rating raise), first match wins:
  1. any option carries `thumb` → `picker`
  2. any option carries `color` → `swatch`
  3. kind `pick_many` → `chips`
  4. `pick_one` with ≤ 5 options → `segmented`
  5. `pick_one` otherwise → `picker`
- **Audit lifecycle kinds**: `spine_start` (version, data_root) /
  `spine_stop`, emitted by the app lifespan — a clean stop writes the
  stop line, a crash writes nothing, which is what makes the line mean
  something. Filter refusal events land through the same `AuditLog`
  (`audit/audit-YYYYMMDD.jsonl`) with the record layer's surface codes;
  the whole path stays vocabulary-blind.
- **Version**: `SPINE_VERSION = "0.1.0"` (`app/spine/version.py`),
  tracking pyproject.
- **uvicorn**: `log_level="warning"`, access log off, lifespan on.

## Endpoint inventory (§F; spellings builder's)

| Method · path | Does |
|---|---|
| `GET /health` | status, version, data root |
| `GET /catalog` | every group/option, full raw facts |
| `POST /records` | create (age gate) → 201 |
| `GET /records` | id, name, rating, active version, grade summary, orphan count |
| `GET /records/{id}` | the record file + orphan report |
| `GET /records/{id}/creator-view` | §F.3 assembled view |
| `PUT /records/{id}/age` | `set_age` |
| `POST /records/{id}/rating` | `raise_rating` |
| `POST /records/{id}/selections` | `set_selection` |
| `DELETE /records/{id}/selections/{group_id}` | `clear_selection` |
| `POST /records/{id}/draft` | `open_draft` |
| `POST /records/{id}/finalize` | `finalize` (real filter) |
| `PUT /records/{id}/name` | `set_name` (filtered) |
| `POST /records/{id}/name/revalidate` | `revalidate_name` |
| `PUT /records/{id}/looks-text` · `DELETE` | `set_looks_text` / `clear_looks_text` |
| `PUT /records/{id}/story-text` · `DELETE` | `set_story_text` / `clear_story_text` |
| `PUT /records/{id}/appearance-paragraph` | `edit_appearance_paragraph` |
| `GET /records/{id}/artifacts` | `Ledger.artifacts_for` |
| `GET /records/{id}/staleness` | `identity_stale` + `variable_stale_marked` |
| `GET /records/{id}/grade` | `derive_grade` passthrough (Null ring provider) |

No name-clearing endpoint exists — §F.4 names none and the record layer
has none; nothing was invented.

**Refusal → HTTP status** (the body's `code` is the truth; status is a
coarse secondary signal): 401 auth · 404 unknown record · **409** for
state/law-in-context refusals (`RATING_DECREASE`, `IDENTITY_NO_DRAFT`,
`DRAFT_ALREADY_OPEN`, `NO_DRAFT`, `REQUIRED_GROUP_UNFILLED`,
`RETIRED_NEW_PICK`, `HIDDEN_GROUP_VALUE`, `RATING_ABOVE_RECORD`, and
`SAFETY_NOT_INSTALLED` — reachable only as the sealed-free_text-group
refusal, §I.2) · **422** for payload/content refusals (everything else,
including `TEXT_BLOCKED`/`NAME_BLOCKED` and `RecordFormatError` on a
corrupt stored file). Codes and subjects pass through verbatim.

## NOT_DECIDED (unclear in the contract; nothing built)

1. **A record-less creator-view preview.** §F.3 says "for a given
   record (or a new draft)". Since `CharacterRecord.create` opens a
   draft, the view was built for any existing record including a fresh
   one; if "(or a new draft)" meant a preview BEFORE any record exists,
   that surface is not built — a ruling would size it.
2. **`httpx2`.** Starlette's TestClient import emits a deprecation
   warning suggesting `httpx2`. Adding it would exceed §C's exact-three
   law, so nothing was added; the warning is cosmetic today.

## Behavior notes (consequences, not decisions)

- `GET /records` loads every record; a corrupt record file fails the
  list loudly with that file's `RecordFormatError` code (fail-loud
  posture; delete or restore the file to recover — the record layer's
  own recovery story).
- With a valid token, an UNDEFINED path returns FastAPI's plain 404
  (`{"detail": …}`), not the structured refusal shape — no defined
  surface answers unstructured.
- A second spine start against a busy root refuses at the lock with
  `SPINE_ALREADY_RUNNING` AFTER its data validated (build_context runs
  first); a doomed second start with bad data reports the data errors
  instead. Either way it exits non-zero having claimed nothing.

## Test count and verification

- `uv run pytest`: **782 passed** (633 carried + 149 new), zero failed.
- `python -m app.options.validate app/data/options`: exit 0 —
  13 files / 135 groups / 2359 options, errors 0 (unchanged; no data
  edit this stage).
- The §J list is covered one-for-one; the real-server tests bind an
  actual loopback socket and read the discovery file back; the
  concurrency test drives 7 simultaneous mutations of one record over
  HTTP and proves none is lost.
