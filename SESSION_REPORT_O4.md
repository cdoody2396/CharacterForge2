# SESSION_REPORT — stage O4 (2026-07-23)

Builder session for the safety transplant. Contract: the O4 kickoff
prompt + O4_INPUTS.md (§A scope, §B transplant source, §C declaration
laws, §D enforcement, §E filter API, §F record wiring, §G refusal-never-
redaction, §H audit, §I tests, §J deliverables), delivered in-chat and
committed verbatim (first commit) with a provenance header.

## What was built

1. **O4_INPUTS.md committed** (first commit, verbatim as delivered).
2. **`app/safety/`** (§B–§E, §H): `normalize.py` byte-identical to the
   pin; `filter.py` carrying the v1 matching machinery with the
   `_CATEGORY_FILES` registry deleted and v1's module-global convenience
   (`get_filter`/`filter_text`/`filter_name`, the `DATA_DIR` default)
   dropped (§F: passed in, never a module global); `errors.py`
   (`SAFETY_*` taxonomy); `audit.py` (v1's Layer-4 `AuditLog` class body
   unchanged, plus `NullAuditSink`); `data/` — all 11 word files, content
   byte-identical to the pin below the prepended `#!` declarations
   (verified by diff during the build).
3. **The N6 seam opened in `app/record/`** (§F/§G): slot setters +
   explicit clears, filtered name writes and `revalidate_name`, draft
   paragraph edits with the author marker, N5 auto-revalidation, load-law
   amendments. With no filter supplied every O3 refusal stands — proven
   by test_safety_seam.py passing untouched from O3.
4. **Tests**: 633 passed (O3's 328 + 305 new; §I coverage inventory in
   the test commit message). Validator: exit 0, counts unchanged
   (13 / 135 / 2359) — **no option-tree change was made**, as §J expects.
5. This report; README, spec changelog, pyproject updated;
   NEXT_SESSION_PROMPT.md redrafted for the planning chat.

## Decisions taken at the planning gate during this session

1. **§H "surface code"** (planning phase, via the question UI): the
   **caller passes it** — `check()` gained an optional `surface`
   argument; record wiring passes the slot name; the filter emits the
   event on block; with no surface given the event carries the context
   only. (The filter alone cannot know which record surface invoked it.)

## Transplant inventory (§B; the "nine lists" verification)

Source verified: local v1 clone, HEAD == pinned `a9519863ff93…` ("5.7o");
every file read via `git show a9519863:<path>` because the v1 working
tree had doc-only drift. **The checkpoint's "nine lists" count is WRONG
against the pin: reality is 11 `.txt` files — 10 blocklist files over 8
categories, plus the proximity vocabulary.** Locked in
`tests/test_safety_filter.py::test_transplanted_file_set_and_term_counts`.

| file | v1 lines | terms | regexes | category / scope |
|---|---|---|---|---|
| minors_always.txt | 84 | 42 | 16 | minors · always · floor |
| minors_contextual.txt | 65 | 59 | 0 | minors · contextual · floor |
| bestiality_always.txt | 21 | 9 | 2 | bestiality · always · floor |
| noncon_always.txt | 47 | 38 | 4 | noncon · always · floor |
| noncon_contextual.txt | 50 | 44 | 0 | noncon · contextual · floor |
| selfharm_always.txt | 39 | 17 | 11 | selfharm · always · floor |
| slurs.txt | 81 | 69 | 4 | slurs · always · floor |
| drugs_always.txt | 39 | 28 | 3 | drugs · always · **unlocked_at: mature** (§D) |
| advice_always.txt | 16 | 2 | 10 | advice · always · floor |
| misc_always.txt | 16 | 9 | 1 | misc · always · floor |
| sexual_context.txt | 105 | 95 | 0 | proximity vocabulary (no category) |

Code: `layer1.py` 318 lines consumed into `filter.py`; `normalize.py`
218 lines verbatim; `app/audit/audit.py` `AuditLog` transplanted whole.
Test vectors ported: `test_normalize.py` 16 verbatim; `test_layer1.py`'s
BLOCKED (~140 vectors) and ALLOWED (~50 vectors) tables verbatim — **all
197 ported tests pass unchanged over the self-declared data**, the
strongest available proof the registry→declaration change preserved
behavior.

## NOT_DECIDED

**Nothing was left undecided.** (The one candidate — where the §H surface
code originates — was put to the gate during planning and ruled; see
above.)

## Consequences noted (not softened)

- **Catalog-declared `free_text` groups remain unwritable.** §F opens the
  two record *slots* (`looks_text`/`story_text`) and the paragraph path;
  a `free_text` group in the catalog still refuses at the gate
  (`resolve_group` → `SafetyNotInstalledError`, message unchanged from
  O3 under the stands-unchanged law). The maintained tree has zero such
  groups today (validator: identity 0 / persona 0), so nothing is
  reachable; the write path for catalog free-text groups belongs to a
  later contract.
- **A mature-rated record can store hard-drug vocabulary in free text**
  ("she deals cocaine" refuses at `standard`, stores at `mature`) — this
  is §D's decided intent, tested both directions. The `name` context is
  rating-gated the same way: a drugs term as a *name* passes on a
  mature-rated record (charset-legal words only); slurs and every other
  floor list still block names at every rating.
- **The v1 age-assertion line carries into the slots**: any text age
  assertion under 20 blocks in every context (minors always-list
  regexes), independent of the record's own N4 age law (20–10000).
- **Finalization can now mutate persona**: N5 with a filter writes
  `name_safety: "clear"` on a passing pending name before committing the
  version. A blocked pending name refuses the WHOLE finalization; the
  draft and the pending flag survive untouched.
- **`AuditLog` never raises and can silently drop events** (broken
  disk/dir) — v1's decided visibility-not-enforcement stance, carried
  as-is with its thread lock and `default=str` coercion.

## Builder details (every naming/spelling choice, recorded)

- **Module naming**: `app/safety/` (`filter`, `normalize`, `errors`,
  `audit`, `data/`). The engine class is `SafetyFilter` (§E's name);
  `FilterResult` carries v1's exact shape and message spelling
  ("Blocked by content policy (<category>)."). v1's `check_name`
  convenience survives as `check_name(name, rating, surface)`.
- **`check` signature**: `check(text, context="freetext",
  rating="standard", surface=None)`. Unknown context AND unknown rating
  raise `ValueError` (programmer errors, the v1 unknown-context stance) —
  only DATA problems get `SAFETY_*` codes.
- **Declaration spellings (§C header spelling ILLUSTRATIVE)**:
  `#! category: <id>` · `#! mode: always|contextual` ·
  `#! enforcement: floor` / `#! enforcement: unlocked_at: mature` /
  `#! enforcement: unlocked_at: explicit` · sexual_context.txt carries
  `#! role: proximity_vocabulary` and nothing else. `#!` lines are legal
  anywhere in the file and are comments to the v1 term parser (so the v1
  line format survives byte-compatible). A `role` declaration on any
  other file refuses; the proximity file's NAME is contract-pinned.
- **Category ids**: `[a-z][a-z0-9_]*` (machine id, §C law 1); violations
  refuse `SAFETY_DECLARATION_UNKNOWN`.
- **`SAFETY_*` codes** (all load-surface, on `SafetyDataError`):
  `SAFETY_DATA_DIR_INVALID` (missing dir / no `.txt` files) ·
  `SAFETY_UNDECLARED_FILE` (zero declarations) ·
  `SAFETY_DECLARATION_MISSING` (some but not all; also the proximity
  file missing its role) · `SAFETY_DECLARATION_UNKNOWN` (unknown key,
  unknown value, malformed line, bad category id, role misuse) ·
  `SAFETY_DECLARATION_DUPLICATE` · `SAFETY_NO_PROXIMITY_VOCABULARY` ·
  `SAFETY_REGEX_IN_CONTEXTUAL` (contextual lists AND the proximity
  vocabulary — v1 refused both, as `ValueError`) ·
  `SAFETY_ENFORCEMENT_LOCKED` (the §C hard law; `_FLOOR_LOCKED_CATEGORIES
  = {"minors", "slurs"}` in code).
- **Enforcement is a per-LIST property** (§E gates "lists"), so two
  files sharing a category may declare different enforcement without a
  conflict law; the §C hard law binds by CATEGORY. `unlocked_at: R`
  skips the list when the passed rating ≥ R (`VALID_RATINGS` order from
  `app.options.loader` — the one canonical ratings source).
- **Scan order** (multi-hit category stability, the v1 registry-order
  behavior): fixed severity ranking `minors, bestiality, noncon,
  selfharm, slurs, drugs, advice, misc`; unknown categories after,
  alphabetically; `always` before `contextual` within a category;
  filename as the final tiebreak.
- **Non-`.txt` files in the data directory are ignored** (a README may
  sit there); an empty or missing directory refuses.
- **Audit**: sink protocol is duck-typed `.log(kind, **payload)`; the
  filter emits kind `"filter_block"` with `context`, `category`, and
  `surface` only when the caller passed one (gate decision 1). The
  timestamp is the sink's (`AuditLog` stamps `ts`). Vocabulary-blind:
  never the matched term, never the text. `NullAuditSink` is the
  default; refusals and only refusals emit (an allowed check, an empty
  check, a load error — nothing).
- **Record wiring (§F spelling)**: a trailing optional
  `safety=None` parameter on `set_looks_text`, `set_story_text`,
  `edit_appearance_paragraph`, `set_name`, `revalidate_name`, and
  `finalize`. The filter type is imported under `TYPE_CHECKING` only —
  no runtime `record → safety` import; the object is duck-typed.
- **Record codes**: `FREE_TEXT_OVERLONG` (both slots, subject names the
  slot) · `PARAGRAPH_OVERLONG` (its own code; different cap) ·
  `TEXT_BLOCKED` (filtered block on slots and the paragraph; message
  names category AND matched term per §G) · `NAME_BLOCKED` (name-family
  block, joining `NAME_CHARSET`/`NAME_LENGTH`). Reused codes:
  `IDENTITY_NO_DRAFT` for draft-scoped paths without a draft
  (`set_looks_text`, `clear_looks_text`, `edit_appearance_paragraph` —
  they are identity-layer writes, the `_layer_for` precedent);
  `BAD_VALUE_TYPE` for a non-string or empty/whitespace-only text (an
  empty write would be a second spelling of "cleared" — the
  `EMPTY_PICK_LIST` argument; clearing is its own API).
- **Caps**: `FREE_TEXT_MAX_CHARS = 240` (§F DECIDED, both slots).
  `PARAGRAPH_MAX_CHARS = 1200` — the cap's existence is DECIDED, the
  value is ILLUSTRATIVE and the builder's: roomy enough for every
  drafter output over the maintained tree, small enough to stay one
  paragraph.
- **Clear APIs are filter-free** (`clear_looks_text`, `clear_story_text`):
  clearing enters no text, so no filter is required; both idempotent
  (the `clear_selection` precedent). `clear_looks_text` needs an open
  draft (draft-scoped state).
- **Names are checked at the record's rating** — §E's "no record rating"
  default applies only to surfaces without one, and every record surface
  has one.
- **`revalidate_name`**: with no filter, `SafetyNotInstalledError` (the
  API's whole purpose is the filter); idempotent no-op when no name is
  set or the name is already `clear`; a blocked pending name refuses
  `NAME_BLOCKED` and stays `pending` — blocked is never a stored state.
- **Finalize order**: full-state check (N5) first, then name
  revalidation, then the commit — a refusal at any point leaves the
  record byte-identical.
- **Record-file keys**: `name_safety` values exactly
  `"pending" | "clear"` (`NAME_SAFETY_VALUES`); version key
  `paragraph_author` with values `"drafter" | "user"` — ALWAYS
  serialized on new saves, absent on load reads `"drafter"` (O3 files);
  draft key `paragraph_edit`, serialized only when present, never
  copied by `open_draft`.
- **No paragraph-edit discard API was built** (the O3 draft-discard
  precedent: no ruling covers abandoning one). A pending edit can be
  *replaced* by another `edit_appearance_paragraph` call; it dies with
  its draft's finalization (the next draft starts without it).
- **Test-file naming**: `test_normalize.py` (verbatim port),
  `test_safety_filter.py` (ported vector tables + §D/§E/§B/§H),
  `test_safety_data.py` (§C laws), `test_record_safety.py` (§F/§G).
  Session-scoped `content_filter` fixture over the REAL maintained data
  in `tests/conftest.py`; per-file term/regex counts pinned as a
  fidelity lock.

## Test count

**633 passed, 0 failed, 0 skipped** (`uv run pytest`, Python 3.12, zero
runtime dependencies). O3's 328 + 305 new: normalize vectors 16 (ported
verbatim), filter 218 (197 ported vectors + §D/§E rating gating +
fidelity locks + §H audit + severity order), §C declaration laws 32,
record seam 39. `test_safety_seam.py` (9) untouched from O3 and still
green — the §F stands-unchanged law's direct proof. Validator over the
maintained tree: exit 0, clean, counts unchanged.
