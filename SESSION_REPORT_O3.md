# SESSION_REPORT — stage O3 (2026-07-22)

Builder session for the character record model, its gates, and the ledger
skeleton. Contract: the O3 kickoff prompt + O3_INPUTS.md (§A verified
base, §B rulings N1–N11), under OPTION_FORMAT_SPEC.md as amended by
O2_INPUTS.md and this stage's §D spec touch.

## What was built

1. **O3_INPUTS.md committed** (first commit, verbatim as delivered).
2. **`required` returns to the format (N3, §D).** Loader accepts the
   group key (bool, default false); value-based laws mirroring the
   existing `scene_overridable` pattern: `required: true` on free_text →
   `REQUIRED_ON_FREE_TEXT`, on a session home → `REQUIRED_ON_SESSION_HOME`;
   non-bool → `BAD_KEY_TYPE`. Not merge-locked (answer 8.3's list is
   fixed). Spec §4 gained the row + a changelog line, same session as the
   tree edit.
3. **Maintained-tree edit (direct, validator-gated).** `required: true`
   on the eleven N3 groups. The eight were VERIFIED against their `_v1`
   holdings before the edit — all eight match (race, gender_presentation
   @10_identity; skin_type, skin_tone, hair_color, hair_style, eye_color
   @20_appearance; body_type @30_body). The three additions
   (apparent_age, hybrid_race @10_identity; lower_body @35_species) cite
   N3 via an in-file `_required_note` comment key. Validator strict:
   exit 0, counts unchanged (13 / 135 / 2359 / 2334 standard + 25
   explicit).
4. **Record module `app/record/`** (N1–N7, N9): `model.py` (file shape,
   atomic writes, strict load, mutation surface, N6 seam), `gate.py`
   (N4/N5 pure checks), `paragraph.py` (N7 drafter, wording marked
   ILLUSTRATIVE in code), `orphans.py` (N9 report), `errors.py`
   (taxonomy: every refusal a distinct code).
5. **Ledger skeleton `app/ledger/`** (N8/N10): `receipts.py` (sidecar
   schema, source of truth), `index.py` (SQLite index, `rebuild()`, R4
   derivations, R5 hook + `attach()` wiring to persona mutations),
   `grade.py` (`derive_grade` seam, `NullRingProvider`), `errors.py`.
   Synthetic sidecars only; nothing renders.
6. This report; README + pyproject updated; NEXT_SESSION_PROMPT.md
   redrafted for the planning chat.

## Decisions taken at the planning gate during this session

Four points were put to Casey via in-session questions before building;
answers are DECIDED and built:

1. **N8 grade ladder** — Casey chose "paste the checkpoint's ladder
   definition" (twice), with the agreed fallback: seam only if the paste
   cannot be produced. **The pasted text never arrived through the
   question UI**, so the fallback is what was built — see NOT_DECIDED.
2. **N3 hybrid_race** — **build as ruled.** `required: true` stands even
   though hybrid_race is always-visible with no "none" option: every
   character must pick a second heritage to finalize. The data
   consequence is owned by a later content-authoring pass.
3. **N4 hidden-on-edit** — **allow, inert.** The mutation gate is
   per-write: writing TO a hidden group refuses (`HIDDEN_GROUP_VALUE`);
   a mutation that HIDES an already-set other group succeeds, the stale
   value sits inert, and finalization's full-state re-check refuses until
   it is cleared. Tested both halves.
4. **N8 receipts** — the sidecar schema gains an explicit `character_id`
   field. N8's field list had no character linkage, but R4's
   version-vs-active comparison must know whose pointer to read;
   a self-contained receipt beats a path convention.

## NOT_DECIDED

1. **The grade ladder (N8).** What G0/G1/G2 each mean, what evidence
   produces each, and how ring membership decides G1 live in
   CHECKPOINT_creation-scoping_S1, which is not in this repo, and the
   definition did not reach this session (see gate decision 1).
   Built instead, per the agreed fallback: the full seam —
   `derive_grade(character_id, ledger=, ring_provider=, active_version=)`
   returns a frozen `GradeDerivation` with `grade=None`,
   `determinable=False`, `ladder_decided=False`, the evidence it CAN
   gather (artifact count, kinds, staleness counts, ring membership when
   the provider knows), and an honest note. `NullRingProvider` returns
   `None` = "cannot know", never "no rings", so G1 is undeterminable and
   the result says so (N8's requirement). The ladder rules land in
   exactly one place, `app/ledger/grade.py::_apply_ladder`; the calling
   surface will not move. **Nothing else was left undecided.**

## Consequences noted (not softened)

- **hybrid_race is required-always** (gate decision 2): no visible_when,
  no "none" option among its 112 — a pure-single-heritage character
  cannot finalize without picking something here.
- **Orphans block identity re-finalization** while they exist: N5 runs
  all of N4 over the full state, and an unknown id refuses. This is
  Decision 6 pt 3 by design — restore the file and the character is
  whole; clearing an orphaned group is also refused (`UNKNOWN_GROUP`),
  so editing is never the resolution path. Unrelated mutations keep
  working (per-write gate).
- **A catalog rating change can strand a record**: if a drop-in re-rates
  an option above a record's rating, finalization refuses
  (`RATING_ABOVE_RECORD`) until the record's rating is raised. Fail-loud,
  consistent with §A7's never-lower law.

## Builder details (every naming/spelling choice, recorded)

- **Record file keys** (N1 said spellings are the builder's): `format`
  (=1, mirroring data files), `character_id`, `age`, `rating`, `created`,
  `active_version` (absent until v1 exists), `identity_versions` (list of
  `version`/`selections`/`appearance_paragraph`/`finalized`/`looks_text`),
  `draft_identity` (`selections`, `looks_text`), `persona` (`name`,
  `name_safety`, `selections`, `story_text`). Comment keys (`_`-prefixed)
  are legal at every level, §1.9's family. `looks_text`/`story_text` keys
  exist in the shape but are unwritable until the safety stage (N6); they
  serialize only when present.
- **Module naming**: `app/record/` (`model`, `gate`, `paragraph`,
  `orphans`, `errors`), `app/ledger/` (`receipts`, `index`, `grade`,
  `errors`).
- **Creation**: `CharacterRecord.create(character_id, age)`; rating
  starts at `"standard"` (the floor — it only moves up, so any start
  state is reachable by an explicit `raise_rating`). Equal-rating
  `raise_rating` is a legal no-op (not a decrease). File naming/placement
  is the caller's: `save_record(record, path)` / `load_record(path,
  catalog)` take explicit paths.
- **Timestamps**: `datetime.now(timezone.utc).isoformat(timespec=
  "seconds")`.
- **Visibility basis** for the per-write gate: draft mutations evaluate
  against draft+persona; persona mutations against the LIVE identity
  (active version) + persona — the draft only before v1 exists.
  Finalization evaluates draft+persona (the state being committed).
- **`required: false`** on free_text/session passes the loader (value-
  based law, the `scene_overridable` precedent); only `true` is the lie.
- **Empty pick_many list refused** (`EMPTY_PICK_LIST`): a written `[]`
  would be a second spelling of "unselected" (absent key, N2).
  `clear_selection` is the one clearing path and is idempotent.
- **No-op writes fire no R5 hook** (setting the already-stored value):
  marking staleness for a non-edit would lie.
- **Name law spelling**: Unicode categories L* and M* plus the four
  ASCII literals space/apostrophe/hyphen/period; 1–60 chars. Curly
  quotes, digits, underscores refuse (`NAME_CHARSET`; length violations
  `NAME_LENGTH`). Load accepts only `name_safety: "pending"` while the
  safety stage is not installed; a name without the flag (or the flag
  without a name) refuses.
- **No draft-discard API was built** — N1 rules "at most one draft", no
  ruling covers abandoning it; an open draft stays editable forever.
  `open_draft()` refuses when one exists (`DRAFT_ALREADY_OPEN`).
- **Error codes**: gate `AGE_MISSING`/`AGE_NOT_INTEGER`/`AGE_UNDER_FLOOR`/
  `AGE_OVER_CEILING`/`UNKNOWN_GROUP`/`UNKNOWN_OPTION`/`RATING_ABOVE_RECORD`/
  `RETIRED_NEW_PICK`/`HIDDEN_GROUP_VALUE`/`LIST_FOR_PICK_ONE`/
  `NOT_A_LIST_FOR_PICK_MANY`/`EMPTY_PICK_LIST`/`DUPLICATE_PICK`/
  `MAX_PICKS_EXCEEDED`/`BAD_VALUE_TYPE`/`SESSION_HOME_VALUE`/`NULL_VALUE`/
  `BAD_RATING`/`RATING_DECREASE`/`IDENTITY_NO_DRAFT`/`DRAFT_ALREADY_OPEN`/
  `NO_DRAFT`/`REQUIRED_GROUP_UNFILLED`; N6 `SAFETY_NOT_INSTALLED`/
  `NAME_CHARSET`/`NAME_LENGTH`; record-format `RECORD_NULL`/
  `RECORD_UNKNOWN_KEY`/`RECORD_MISSING_KEY`/`RECORD_BAD_TYPE`/
  `RECORD_BAD_VERSIONING`/`RECORD_INVALID_JSON`; loader
  `REQUIRED_ON_FREE_TEXT`/`REQUIRED_ON_SESSION_HOME`; receipts
  `RECEIPT_*` (five).
- **Tree-edit placement**: `required` sits after `home` (after
  `scene_overridable` on hair_style), before `priority` — §4 key order,
  O2b's emission-order precedent. `_required_note` is the comment-key
  spelling on the three N3 additions.
- **Sidecar convention**: `*.receipt.json`, scanned by `rebuild()` over
  injected directories. Index table `ledger_index`, PK `sidecar_path`,
  receipt fields verbatim + `variables` as sorted-key JSON +
  `variable_stale` cache column. `PRAGMA user_version = 1`, WAL.
- **R5 wiring mechanism**: `CharacterRecord.persona_edit_hooks` (list of
  callables, not serialized), invoked with `(record, touched_group_ids)`
  after a successful persona selection edit; `Ledger.attach(record)`
  registers the marking hook. Current variable values for comparison =
  persona selections over the ACTIVE version's selections (draft state
  never marks — it is not live).
- The N7 sentence template (`"Group label: Label, Label; …"`) is
  ILLUSTRATIVE and marked so in code; tests assert determinism and
  label-presence, never exact prose.

## Test count

**319 passed, 0 failed, 0 skipped** (`uv run pytest`, Python 3.12, zero
runtime dependencies). O2b's 185 + 134 new: required key 8, record model
15, construction gate 37 (every N4 refusal individually, incl. the
hidden-refusal against the REAL maintained catalog), finalization 14,
safety seam 21 (name law both directions), paragraph 8, orphans 5,
ledger 26. Validator over the maintained tree: exit 0, clean.
