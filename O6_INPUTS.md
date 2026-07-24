# O6 INPUTS — the creator UI contract

Delivered by the owner from the planning chat of 2026-07-24, at the O6
kickoff. Committed here verbatim so the contract lives in the repo, the
O5_INPUTS.md pattern. Everything below the line is the delivery,
untouched.

---

# O6_INPUTS — Creator UI (Roster · Session · Atelier)

Contract for the O6 builder session. Decided in the planning chat
2026-07-24 on the confirmed Atelier chassis (Session-create and the
zone-navigator absorption noted for later polish; zone navigator is NOT
in this stage's scope). Commit this file verbatim as the first commit
with a provenance header. Ambiguity → SESSION_REPORT `NOT_DECIDED`,
build nothing for it.

Base: `main` at the O5 close (782 passed; validator 13 files /
135 groups / 2359 options). This stage makes NO option-tree change —
validator counts must be unchanged at close.

---

## §A — Scope

Build:

1. **`frontend/`** — a React + Vite + TypeScript app (new top-level
   directory) implementing three surfaces over the spine:
   **Roster** (list, create, open) → **Session** (guided walk) ⇄
   **Atelier** (workbench). Nothing else renders.
2. **`scripts/dev.py`** — stdlib-only dev launcher (§C.4).
3. **Three spine deltas** (§G): `tags` in served menu entries ·
   owner-only permissions on `runtime.json` · token-never-in-audit
   pinning test.

Out-stages, named so nothing is invented for them: library screens
(the four-axis filter — Race, Sex, Genitalia, Kinks — is recorded for
them, not built now) · image-identity surfaces beyond §F.6's honest
grade affordance · chat · desktop shell / packaging · options editor ·
register alternates · record deletion (no spine endpoint exists — do
not add one) · version-history viewer · rating-locked teaser mode ·
ghost slots · `subsection` format key · Session quick-subset (no data
marking exists for it).

## §B — Single evaluator (carried verbatim from O5_INPUTS §B)

> The owner's verbatim findings on v1, recorded as a named input:
>
> > Bad choices on screen, bad screen formatting, bad option selection
> > methods, bad user experience in making a character. Image and chat
> > were not being updated as we were working on what the format and
> > options should actually be.
>
> Binding consequence …: **the spine is the single evaluator.**
> Visibility (`visible_when`), rating admissibility, `required` flags,
> retired-option handling, widget derivation, and gate refusals are all
> computed spine-side and served to the front-end as facts; no client
> ever re-implements catalog or gate logic (the v1 two-evaluator drift
> hazard, designed out per the amended checkpoint). The UI stage
> inherits this section verbatim.

Operational form for this stage: **the client may narrow or reorder
what the spine serves; it may never widen it.** Search, facets, and
sort are curation of an already-judged menu. After every successful
mutation the client refetches served state (§E) — it never predicts.

## §C — Process, toolchain, dependency law

1. **Python law unchanged**: exactly `fastapi==0.139.2`,
   `uvicorn==0.51.0`, `httpx==0.28.1`. §G adds no dependency.
2. **Front-end toolchain**: Node LTS (≥ 20) + npm. `frontend/package.json`
   with `package-lock.json` committed. Declared dependency set, pinned:
   `react`, `react-dom`, `@tanstack/react-virtual`; dev:
   `vite`, `@vitejs/plugin-react`, `typescript`, `vitest`, `jsdom`,
   `@testing-library/react`, `@testing-library/user-event`,
   `@testing-library/jest-dom`. Exact versions are builder detail,
   recorded in the report. Anything beyond this set is a `NOT_DECIDED`.
3. **Offline law applies to the artifact**: `npm run build` output makes
   zero network requests at runtime — no CDN scripts, no CDN fonts.
   Fonts are vendored OFL files in-repo (a display serif + a grotesk +
   a mono; families are builder detail within that trio, licenses
   recorded).
4. **Dev launcher (`scripts/dev.py`, stdlib only)**: starts the spine
   (`--data-root ./.devroot`, gitignored) as a subprocess, reads
   `runtime.json` (the launcher is host-side; §D.2 forbids only the
   React app from reading it), then launches Vite with
   `VITE_SPINE_ORIGIN` and `VITE_SPINE_TOKEN` in the environment.
   Spine terminates when the launcher exits, both platforms.

## §D — Client access contract

1. **Same-origin rule (refinement of the confirmed injection decision,
   reason: it eliminates CORS everywhere, forever).** The React app
   fetches only relative paths under `/spine/*` and never knows the
   spine's origin. The hosting layer maps `/spine/*` → the spine:
   in dev, the Vite proxy (target from `VITE_SPINE_ORIGIN`, config-side
   only); the packaged shell reproduces the same mapping later. The
   spine itself gains no CORS handling — no cross-origin surface exists.
2. **Injection boundary**: one module, `frontend/src/spine/config.ts`,
   resolves `{ token }` from `import.meta.env.VITE_SPINE_TOKEN`. The
   React app never reads `runtime.json`, never spawns processes, never
   sees a port. The packaged shell later swaps this module's source and
   nothing else.
3. Every request carries `X-Spine-Token`. 401 renders a full-screen
   fault state naming the code — it means the host wiring is broken,
   not a user error.

## §E — Data flow

1. Opening a record loads, in parallel: `GET /records/{id}` (the record
   file + orphans; draft-open state read from it),
   `GET /records/{id}/creator-view`, `GET /records/{id}/staleness`,
   `GET /records/{id}/grade`.
2. **Refetch law**: after every 2xx mutation, refetch the creator view
   and the record (staleness/grade when the mutation can move them).
   No optimistic updates. Hidden groups vanish, revealed groups appear,
   menus re-cut on rating raise — all by refetch, never by prediction.
3. **Refusal handling**: any non-2xx with a `{code, subject, message}`
   body renders per §F.7. FastAPI-shaped `{detail}` bodies and network
   failures render as a generic fault card. Codes and subjects display
   verbatim — never renamed, never softened.
4. Fixture payloads for component tests are captured from a real spine
   run by a checked-in script (`frontend/scripts/capture-fixtures.*`),
   not hand-written — fixtures cannot drift from the true shapes.

## §F — Screens and interaction contract

**F.1 Roster.** `GET /records` → cards: name (or "Unnamed"), rating,
active version, grade summary, orphan count — served fields only.
Actions: open (→ Atelier) · guided pass (→ Session) · create. Create
runs the age gate as step zero: an age input, `POST /records`;
`AGE_UNDER_FLOOR` stamps on the field; success opens the Session on
the new record. Copy states the 20+ floor plainly. No delete (§A).

**F.2 Session.** Walks the served creator view: sections in served
order, groups in `order`, one group per screen, the group's real widget
at large scale. Big-type register per the confirmed direction. Controls:
answer (mutation → refetch → advance), skip group, skip to workbench,
per-section progress thread. After creation, one Name screen (filtered
`PUT /records/{id}/name`; skippable). The Session ends at the workbench,
never at finalize — finalize lives in the Atelier only.

**F.3 Atelier.** Three panes.
- **Rail**: stations = served sections in order with set/total counts;
  a trailing **Unfiled** station collects section-less groups verbatim;
  a fixed **Text** station below it (F.5); the jump palette (F.8).
- **Canvas**: the active station's groups in `order` — group label,
  hint, widget per F.4; a sticky in-section mini-spine when the station
  has > 6 groups.
- **Record pane**: name · rating chip · version/draft chip · groups-set
  count · grade line (served value verbatim; when the Null ring
  provider answers, say so honestly — no invented grade) · staleness
  line · orphan list (served) · prose block: the committed appearance
  paragraph when the active version carries one, otherwise a pick
  summary assembled client-side from served labels and explicitly
  captioned as a preview, never presented as the paragraph.

**F.4 Widget contract** (render the four served kinds; an unserved or
unknown `widget` value renders a visible fault card for that group —
fail loud, never skip silently):
- `segmented` — exclusive horizontal buttons; re-pick replaces; a
  clear affordance calls `DELETE …/selections/{group_id}`.
- `chips` — multi-pick; each toggle sends the full new list; selected
  pinned first with a live count.
- `swatch` — circles from served `color`, label on focus/selection.
- `picker` — list/grid, virtualized. At ≥ 24 served options the heavy
  kit activates: type-to-filter on labels; facet chips with counts when
  served options carry `tags` (§G.1); sort modes catalog / A–Z
  (client-side, presentation only); current value pinned. Thumb grid
  when `thumb` is served.
- Everywhere: a held retired value renders with a `retired` badge and
  stays functional; groups absent from the view do not render.

**F.5 Text station.** Name (set / revalidate), looks text
(draft-scoped), story text, appearance-paragraph editor (draft-scoped)
— the existing endpoints only; §I.2 stays sealed, no catalog
`free_text` group is introduced. Draft-scoped editors render
disabled-with-reason when no draft is open, with an inline
open-draft affordance; a raced refusal (`IDENTITY_NO_DRAFT`) remains
the truth and stamps normally.

**F.6 Contract events.**
- Draft: chip states draft-open / no-draft; open-draft action
  (`POST …/draft`) offered wherever identity writes are blocked by its
  absence.
- **Finalize**: Atelier-only ceremony. `POST …/finalize`; on success
  refetch everything and show the served grade. Render the G0/G1/G2
  ladder as an explainer with the honest line that grade building
  belongs to the image section and is not yet available — display, not
  a control. `REQUIRED_GROUP_UNFILLED` refusals deep-link to the named
  group.
- **Rating raise**: header control listing served admissible targets;
  confirm dialog naming irreversibility (`RATING_DECREASE` is a served
  law, mirrored in copy only); success → full refetch; explicit
  families simply appear. Locked options stay invisible — no teaser.
- Versions: header chip only (active version + draft state).

**F.7 Refusal surfacing.** Field-anchored stamp for any refusal whose
`subject` matches a rendered group id or slot name: code verbatim in
mono, message beside it, anchored at that widget. Record-level or
unmatched subjects → a toast carrying the same shape. 401 → §D.3
fault state. Corrupt-record (`RecordFormatError` on load) → full-pane
fault naming the served code; no recovery UI is invented.

**F.8 Jump palette.** Ctrl+K overlay; client-side fuzzy index over
served group and option labels; selecting jumps to the station and
highlights the group. Index rebuilds on every view refetch.

**F.9 Register.** Forge iron and ember, app-wide, dark-first, expressed
solely through CSS custom properties in one token file
(`frontend/src/register/tokens.css`) — a register swap must touch that
file only. Seed values (tuning within the register is builder detail):
iron `#2C2C2A` / recess `#232322` / lines `#444441`,`#5F5E5A` · text
`#F1EFE8`,`#D3D1C7`,`#B4B2A9`,`#888780` · ember `#EF9F27`,`#FAC775`,
`#BA7517`,`#854F0B`,`#633806`,`#FAEEDA` · refusal `#501313`,`#791F1F`,
`#F7C1C1`,`#F09595` · confirm tick `#5DCAA5`. Type: display serif for
character voice (names, section titles, Session questions), grotesk for
controls, mono for codes. Full keyboard operability and visible focus
states on every widget. Single-window presentation: no popups, no new
windows, no external links.

## §G — Spine deltas (Python scope of this stage)

1. **Tags served**: `_menu_entry` (and the held entry) in
   `app/spine/creator_view.py` gains `"tags": option.tags` — the §F.3
   view shape's one addition, decided at the gate. Tests pin presence
   and shape.
2. **Discovery file permissions**: `runtime.json` (and its tmp) written
   owner-only — `0o600` best-effort via `os.chmod` after `os.replace`;
   POSIX asserted in tests, Windows best-effort recorded (the
   `%LOCALAPPDATA%` ACL already scopes it).
3. **Token pinning test**: drive a start → mutate → stop flow, then
   assert the token string appears nowhere under `audit/`.

No other Python file changes. Existing 782 tests stay green.

## §H — Tests

Python: the three §G items, plus the untouched 782.

Front-end (`vitest`, jsdom; `npm test` and `npm run build` both green):
- Per-widget component tests against captured fixtures (§E.4): render,
  select, clear, retired badge, unknown-widget fault card.
- Heavy-kit tests: filter, facet counts from served tags, sort modes,
  pinned current, ≥ 24 activation threshold.
- Refetch-law test: a mutation triggers a creator-view refetch; a
  revealed group appears with no client prediction.
- Refusal tests: field-anchored stamp for a group-subject 409/422;
  toast for an unmatched subject; 401 fault state; verbatim codes.
- Session flow: age-gate refusal and success; skip; end-at-workbench.
- Roster: served-field rendering; create → Session handoff.
- Record pane: committed paragraph vs captioned preview distinction.

Integration (vitest, node environment, real spine spawned via
`uv run python -m app.spine --data-root <tmpdir>`, token read
launcher-side): auth refusals · create with age gate both ways ·
selection set/clear over real HTTP · a real `visible_when` reveal from
the maintained tree (species pick reveals its dependents) · rating
raise revealing an explicit-file group · name write blocked by the real
filter, with the blocked term read from the safety data files at test
runtime, never hardcoded · finalize path. Coverage inventory one-for-one
in the test commit message.

## §I — Rulings

1. Chassis: Atelier confirmed; Session absorbed as guided create; zone
   navigator deferred (polish track).
2. Register: forge iron/ember app-wide (F.9); token-deep, swappable.
3. O5 NOT_DECIDED 1 **closed**: no record-less preview — the Session's
   step zero is the age gate, which creates the record; everything
   after runs on a real one.
4. Locked options invisible until a rating raise; no teaser mode.
5. Null-section groups → trailing Unfiled station (authoring track owns
   section assignments; the nine known section-less groups render there
   meanwhile).
6. No catalog `free_text` group introduced; §I.2 seal untouched.
7. Heavy-kit threshold: 24 served options (23 real groups exceed it) —
   guidance, presentation-side.
8. Same-origin refinement (§D.1) supersedes the injected-origin wording
   of the confirmed decision; the injected value moves to the host
   layer. Reason recorded: CORS elimination for dev and every future
   shell.
9. Grade choice at finalize is display-only this stage (the
   HERE/HARDWARE honesty pattern applied to UI).

## §K — Deliverables

1. `O6_INPUTS.md` committed verbatim, first commit, provenance header.
2. `frontend/` app + `scripts/dev.py` + vendored fonts + lockfile.
3. §G spine deltas with tests.
4. README section "Running the creator UI" (prerequisites: Node ≥ 20;
   `python scripts/dev.py`).
5. `SESSION_REPORT_O6.md`: every naming/spelling choice, the endpoint
   usage map as built, decisions taken at builder latitude,
   `NOT_DECIDED` list, observed test tails.
6. `NEXT_SESSION_PROMPT.md` redrafted — candidates: image-identity
   section · library screens (four-axis filter recorded above). §B
   carries verbatim again.
7. **Stage close**: `uv run pytest`, `npm test`, `npm run build` all
   green **at the pushed head on a clean tree (`git status --porcelain`
   empty), fresh checkout preferred**; the observed tails recorded in
   the report. This ground rule is permanent from O6 on.

## Endpoint usage map (spec — the report records it as built)

| Endpoint | Consumer |
|---|---|
| `GET /health` | launcher readiness check |
| `GET /records` | Roster |
| `POST /records` | Roster create (age gate) |
| `GET /records/{id}` | record load; draft state; orphans |
| `GET /records/{id}/creator-view` | Session + Atelier, every refetch |
| `PUT /records/{id}/age` | unused this stage (creation sets age) |
| `POST /records/{id}/rating` | rating raise |
| `POST /records/{id}/selections` · `DELETE …/selections/{group_id}` | all four widgets |
| `POST /records/{id}/draft` | open-draft affordances |
| `POST /records/{id}/finalize` | Atelier finalize |
| `PUT /records/{id}/name` · `POST …/name/revalidate` | Session name step · Text station |
| `PUT/DELETE …/looks-text` · `PUT/DELETE …/story-text` | Text station |
| `PUT …/appearance-paragraph` | Text station (draft-scoped) |
| `GET …/staleness` · `GET …/grade` | record pane |
| `GET /catalog` · `GET …/artifacts` | unused this stage — noted, not consumed |

Ground rules carried: build only what this contract scopes · ambiguity
→ `NOT_DECIDED`, build nothing · validator counts unchanged
(13 / 135 / 2359) · OPTION_FORMAT_SPEC as amended is the format
contract (no format change this stage) · §C hard law untouched ·
dependency laws per §C.1–C.2 · the spine is the single evaluator ·
clean-tree close per §K.7.
