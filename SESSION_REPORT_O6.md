# SESSION_REPORT — stage O6 (2026-07-24)

Contract: [O6_INPUTS.md](O6_INPUTS.md) (committed verbatim as the first
commit of this stage, provenance header per the O5_INPUTS pattern) —
§A scope · §B single evaluator (carried verbatim) · §C process and
dependency law · §D client access · §E data flow · §F screens · §G
spine deltas · §H tests · §I rulings · §K deliverables. Base verified
before building: `main` at `f9e4038` == `origin/main`, `uv run pytest`
→ 782 passed, validator → 13 files / 135 groups / 2359 options, exit 0.

## What was built

1. **§G spine deltas** (`app/spine/creator_view.py`,
   `app/spine/discovery.py`) — held entries gain `tags` (resolved:
   `list(option.tags)`; orphaned: `[]`); `runtime.json` and its tmp
   chmod'd `0o600` best-effort after write/replace; the
   token-never-in-audit flow pinned. Three new creator-view tests, one
   POSIX permissions test, one audit-pinning test.
2. **`frontend/`** — React + Vite + TypeScript app: **Roster**
   (served-field cards; create runs the age gate as step zero) →
   **Session** (one served group per screen in served order, big-type
   register, per-section progress thread, post-creation Name screen,
   ends at the workbench only) ⇄ **Atelier** (station rail with
   trailing Unfiled and fixed Text stations · canvas with sticky
   mini-spine past 6 groups · record pane). Four widgets + fail-loud
   unknown-widget fault card; heavy picker kit at ≥ 24 served options;
   Ctrl+K jump palette over a hand-rolled fuzzy index; finalize
   ceremony with the display-only G0/G1/G2 explainer; rating raise
   with irreversibility copy; refusals as field-anchored stamps or
   toasts, codes verbatim; 401 full-screen fault. Forge iron/ember
   register token-deep in `frontend/src/register/tokens.css`.
3. **`scripts/dev.py`** — stdlib-only launcher: spine over `./.devroot`
   → reads `runtime.json` host-side → Vite with `VITE_SPINE_ORIGIN` /
   `VITE_SPINE_TOKEN` injected → both children terminated on exit.
4. **`frontend/scripts/capture-fixtures.mjs`** (§E.4) — captures every
   component-test payload from a real spine run; 15 fixtures committed.
5. **39 front-end tests** (§H): 29 jsdom component tests + 10
   node-environment integration tests over a real spawned spine.
6. Docs: README "Running the creator UI" + inventory to O1–O6; this
   report; NEXT_SESSION_PROMPT redrafted.

## Decisions taken at the planning gate during this session

1. **Empty-menu groups narrowed away.** The real tree serves
   `genitalia` and `grooming` (explicit-file groups, no
   `visible_when`) with an EMPTY options list at a standard-rating
   record. Ruled: a group with zero served options and no held value
   does not render — §B narrowing in the §I.4 no-teaser spirit. It
   appears by refetch after a rating raise. Pinned both ways in
   `recordpane.test.tsx`.
2. **Rating-raise targets mirrored in copy.** No endpoint serves the
   rating order (verified: `/catalog` serves option-level rating
   strings; the creator view serves the current rating only). Ruled:
   the client lists ratings above the served current rating in the
   fixed order standard → mature → explicit — the same mirrored-law
   status §F.6 grants the `RATING_DECREASE` copy. The spine still
   refuses any inadmissible pick.
3. **`@types/*` companions admitted.** React 19 ships no bundled
   TypeScript declarations, so the declared `typescript` cannot check
   JSX without `@types/react`/`@types/react-dom`; the node-environment
   test suite likewise needs `@types/node`. Ruled: declaration-only
   `@types/*` companions of the declared toolchain are admitted; the
   §C.2 set stays otherwise closed. Installed: `@types/react 19.2.17`,
   `@types/react-dom 19.2.3`, `@types/node` (pinned in the lockfile).

## Builder details (every naming/spelling choice, recorded)

- **npm pins** (§C.2, exact): `react 19.2.8` · `react-dom 19.2.8` ·
  `@tanstack/react-virtual 3.14.8`; dev `vite 8.1.5` ·
  `@vitejs/plugin-react 6.0.4` · `typescript 7.0.2` · `vitest 4.1.10` ·
  `jsdom 29.1.1` · `@testing-library/react 16.3.2` ·
  `@testing-library/user-event 14.6.1` ·
  `@testing-library/jest-dom 6.9.1` (+ the ruled `@types/*`).
- **Fonts** (§C.3, OFL trio, builder choice): display serif **Playfair
  Display** (400, 400 italic, 700) · grotesk **Space Grotesk** (400,
  500, 700) · mono **JetBrains Mono** (400, 700); latin-subset woff2
  vendored under `frontend/public/fonts/` with the three OFL license
  texts beside them.
- **Layout**: `src/spine/` (config.ts = the §D.2 injection boundary,
  client.ts, types.ts) · `src/state/` (recordData.ts, fuzzy.ts) ·
  `src/register/` (tokens.css THE register file; base.css fonts/reset;
  app.css layout — both consume tokens only) · `src/widgets/`
  (WidgetHost + Segmented/Chips/Swatch/Picker/HeavyKit) · `src/parts/`
  (faults, Overlay, ToastHost, JumpPalette, DraftChip, RatingRaise,
  FinalizeCeremony, TextStation) · `src/surfaces/`
  (Roster/Session/Atelier).
- **Client errors**: `SpineRefusal` (the `{code, subject, message}`
  triple + status) and `SpineFault` (network / `{detail}`-shaped);
  `onAuthFault` listener drives the §D.3 full-screen fault.
- **Refusal anchoring**: `subjectMatches(subject, groupId)` — exact
  group id OR the compound `"group/option"` form the spine's selection
  refusals carry (observed: `"genitalia/vulva"`). Text-station slots
  anchor on `name` / `looks_text` / `story_text` /
  `appearance_paragraph`; `age` anchors on the Roster create field.
  Unmatched → toast, same shape. Toasts are dismiss-button only (no
  auto-dismiss).
- **Widgets**: heavy-kit threshold constant 24 (`HEAVY_KIT_THRESHOLD`);
  facet chips = tag → overall served count, AND-composed, toggleable;
  sort modes `catalog`/`A–Z`; current pinned above the virtualized
  list; thumb grid = 4-column virtualized rows. Clear affordance on
  every widget frame (the endpoint map names all four widgets as the
  DELETE consumer). Pick-many toggles send the full new list; the
  swatch and picker handle both kinds (spine-side derivation can make
  a pick_many a swatch/picker).
- **Session**: single-pick answers auto-advance after the refetch;
  multi-pick screens advance by an explicit **Continue** (builder
  latitude). Cursor is group-id-based; a vanished group falls back to
  the head of the recomputed walk. Name question copy: "What is their
  name?".
- **Atelier**: stations = sections in first-appearance served order;
  Unfiled key `__unfiled__`, Text key `__text__`; mini-spine appears
  past 6 groups (`MINI_SPINE_AT`); jump highlight auto-clears after
  2.5 s.
- **Narrowing rule** (ruling 1) as implemented:
  `options.length > 0 || current.length > 0` in
  `visibleGroups()` — a held value always renders, even menu-less.
- **`scripts/dev.py`**: prefers `.venv`'s python over `uv run` (a
  direct child is what exit-termination needs on both platforms);
  removes a stale `runtime.json` before start; refuses with a named
  hint when npm or `frontend/node_modules` is missing.
- **Capture script**: drop-in group `capture_probe`
  (`probe_a`/`probe_b`) under `options_dropin/95_capture_probe.json`;
  phase 2 rewrites `probe_a` to `status: retired` and restarts the
  same data root. Finalize is reached honestly by answering each
  `REQUIRED_GROUP_UNFILLED` subject with its first admissible option
  (the same loop the integration test uses). 15 fixtures (the test
  commit message says 16 — this report's count is the correct one).
- **Unknown-widget case**: cannot be captured (the spine serves only
  four kinds) — the test mutates a captured group's `widget` to
  `"holo_dial"` in-test; everything else in that group stays captured.
- **Test scaffolding**: vitest split into `vitest.jsdom.config.ts`
  (components, `tests/setup.ts` stubs ResizeObserver +
  element sizes for the virtualizer) and `vitest.node.config.ts`
  (integration); `npm test` chains both.
- **§G spellings**: `_chmod_owner_only` helper in `discovery.py`
  (chmods tmp before `os.replace` and the final path after, each in
  `suppress(OSError)`); test `test_discovery_file_is_owner_only`
  (POSIX-only, skips on win32); `test_token_never_lands_in_audit`
  drives the real thread-server with a create + selection + a
  filter-blocked name write so a `filter_block` line lands, then walks
  every file under `audit/`.

## Endpoint usage map (as built)

| Endpoint | Consumer as built |
|---|---|
| `GET /health` | `scripts/dev.py` readiness · capture script · integration harness (all launcher-side) |
| `GET /records` | Roster |
| `POST /records` | Roster create (age gate step zero) |
| `GET /records/{id}` | `useRecordData` parallel load → record pane, draft chip, Text station |
| `GET /records/{id}/creator-view` | Session + Atelier, every refetch; jump-palette index |
| `PUT /records/{id}/age` | **unused this stage** (creation sets age) — noted, not consumed |
| `POST /records/{id}/rating` | RatingRaise (header control) |
| `POST …/selections` · `DELETE …/selections/{group_id}` | all four widgets via WidgetHost (Atelier canvas + Session screen) |
| `POST /records/{id}/draft` | open-draft affordances (record pane + draft-scoped Text editors) |
| `POST /records/{id}/finalize` | FinalizeCeremony — Atelier only |
| `PUT …/name` · `POST …/name/revalidate` | Session name step · Text station |
| `PUT/DELETE …/looks-text` · `PUT/DELETE …/story-text` | Text station |
| `PUT …/appearance-paragraph` | Text station (draft-scoped) |
| `GET …/staleness` · `GET …/grade` | record pane (roster cards read the nested grade from `GET /records`) |
| `GET /catalog` · `GET …/artifacts` | **not consumed** — noted |

## NOT_DECIDED (unclear in the contract; nothing built)

None left open. The two contract ambiguities found mid-build
(empty-menu rendering; the unserved rating-raise targets) and the
`@types/*` gap were put to the owner during the session and ruled
(§decisions above) rather than parked — the gate was available.

## Behavior notes (consequences, not decisions)

- **§G.1 base observation**: `_menu_entry` already served
  `"tags": list(option.tags)` at the O5 close (`creator_view.py:80` at
  `f9e4038`), as did group entries. The contract's "gains tags" was
  therefore already half-true at base; the delta reduced to the held
  entries plus pinning tests for both shapes.
- Selection refusals carry compound subjects (`"group/option"`), not
  bare group ids — hence `subjectMatches`. Display stays verbatim;
  only anchoring interprets.
- The maintained tree serves **115 groups** to a fresh
  standard-rating record; `genitalia` and `grooming` arrive
  empty-menued (the trigger for ruling 1). The validator reports
  **retired: 0** — no maintained-tree option is retired, which is why
  the retired-held fixture needs the two-phase drop-in capture.
- After a real finalize with an empty ledger the grade endpoint serves
  `grade: null`, `determinable: false`, `ladder_decided: true`, and
  the Null-ring-provider note — the record pane renders the note
  verbatim (no invented grade), and the integration test pins exactly
  that.
- `npm test` includes the integration suite → it needs the Python
  toolchain (`.venv` via `uv sync`, or `uv` on PATH) beside Node.
- On Windows the §G.2 POSIX assertion runs as **skipped** (the suite
  shows `786 passed, 1 skipped`); `os.chmod` is best-effort there and
  the `%LOCALAPPDATA%` ACL already scopes the file. On POSIX the test
  asserts `0o600`.
- The built artifact's only absolute URLs are XML namespace constants
  and React's error-doc strings — no external request exists; fonts
  resolve to `/fonts/*.woff2` relative paths.

## Test count and verification

Python: **787 tests** (782 untouched + 3 §G.1 + 1 §G.2 + 1 §G.3).
Front-end: **39 tests** (29 jsdom component + 10 integration).

Observed tails on the working tree at the docs commit (Windows 11,
Python 3.12, Node v20.19.0):

```
uv run pytest      → 786 passed, 1 skipped, 1 warning in 9.11s
npm test           → Test Files 7 passed (7) / Tests 29 passed (29)
                     Test Files 1 passed (1) / Tests 10 passed (10)
npm run build      → ✓ built in 127ms
validator          → files: 13  groups: 135  options: 2359  retired: 0
                     errors: 0 — clean   (exit 0)
```

## Stage close (§K.7) — observed at the pushed head

The close ran against a **fresh clone** of the pushed head `dc2c289`
(`git status --porcelain` empty before and after the runs; `uv sync`
then `npm ci` from the committed lockfiles). Observed tails, verbatim:

```
git rev-parse HEAD → dc2c289f88cf62a7e3bada0e167773b3744ab515
uv run pytest      → ================= 786 passed, 1 skipped, 1 warning in 12.54s ==================
npm test           → Test Files  7 passed (7)  /  Tests  29 passed (29)
                     Test Files  1 passed (1)  /  Tests  10 passed (10)
npm run build      → ✓ built in 150ms
validator          → files: 13  groups: 135  options: 2359  retired: 0
                     errors: 0 — clean   (exit 0)
```

(The 1 skip is the §G.2 POSIX permissions assertion on this Windows
host, as designed.) This tails-recording commit changes documentation
only; the suites' behavior is that of `dc2c289`.
