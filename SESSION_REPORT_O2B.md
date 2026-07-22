# SESSION_REPORT — stage O2b (2026-07-22)

Builder session applying the O2 planning gate's overrides to the harvest,
re-emitting the data tree, and freezing the tool. Contract: the O2b kickoff
prompt + `tools/harvest/overrides.json` (its `why` strings authoritative),
under OPTION_FORMAT_SPEC.md as amended by O2_INPUTS.md.

## What was built

1. **`tools/harvest/overrides.json` committed** — the gate's decision
   record, verbatim as delivered: 13 `priority` overrides, 3 `home`
   overrides, 3 `scene_overridable` flags, 1 comment record
   (`_denied_apparent_age`). Every entry carries a `why` (checked before
   any work; the stop condition did not fire).
2. **Tool extension** (`tools/harvest/`): the harvest consumes an
   overrides file.
   - Load order as decided: O2_INPUTS answer-7 home table, THEN `home`
     overrides by group id (superseding the table wherever the group
     appears), then contradiction flagging on whatever remains. The
     92_piercings hold thereby clears itself: both sources say identity.
   - `priority` overrides apply after the §1.6 default map.
   - `scene_overridable` entries with value true emit the group key on
     the first definition (after `home`, spec §4 key order); value false
     emits nothing (absence = default). The validator's format error for
     a non-identity flag stays live as the safety net (tested end-to-end:
     such an emission fails the gate, nothing written).
   - Underscore-prefixed entries are comment records, not keys — carried
     into OVERRIDES_APPLIED.md, never applied.
   - Tool errors (refusal, exit 2): missing/blank `why` — an override
     without a reason is a tool error; bad `to`/`value`; unknown section
     or entry key; wrong `format`; and an override that never lands on an
     emitted group (see decision 2 below).
   - New artifact `harvest_report/OVERRIDES_APPLIED.md`: every override
     with its `why` verbatim, the superseded table homes per occurrence,
     comment records, and the mechanical defaulted-row counts.
     `PRIORITY_REVIEW.md` regenerates with a final column marking
     overridden rows (`… — OVERRIDE`).
   - CLI: `--overrides PATH`, defaulting to the committed
     `tools/harvest/overrides.json` (decision 1 below).
   - Determinism holds WITH overrides: byte-identical re-run, tested on
     synthetic fixtures and verified on the real run via SHA-256.
3. **The real re-run** — fresh full clone of
   `github.com/cdoody2396/CharacterForge`, checkout pinned
   `a9519863ff933709dc080bf6941f118853b05569`, HEAD verified equal before
   harvesting. Validator strict over the full tree: **exit 0, clean.**
4. **Freeze** — README: `app/data/options/` is the MAINTAINED SOURCE;
   future content edits happen there directly under the validator;
   `tools/harvest` exists only for the personal drop-in pass (O2_INPUTS
   answer 1). Guard: `--out` resolving to the maintained tree refuses to
   run without `--i-know-this-overwrites-maintained-data`; a bare
   `python -m tools.harvest <v1_root>` now refuses by design (verified
   against the real clone; the tree stays untouched).
5. This report; NEXT_SESSION_PROMPT.md gate list updated.

## Verified deltas vs O2 — every expected delta matched, no differences

- **13 emitted files**: `92_piercings_intimate.json` returns — 1 fragment
  group (`piercings`), options `nipple` + `genital`, rating `explicit`,
  fragment keys `id` + `options` (+ its v1 `_note` carried verbatim per
  §1.9). Inventory row now `emitted (1 group, 2 options)`; HARVEST_LOG
  flags section: **(none)**.
- **Merged groups still 135** (137 emitted entries — the outfit and
  piercings fragments merge); **options 2359 = 2334 standard + 25
  explicit** (O2's 2357/23 + the two returning piercing options), 0
  mature, 0 retired, 0 free-text slots.
- **piercings** (38_marks.json): home `identity`, `scene_overridable:
  true`, priority `flavor` (unchanged — not among the 13).
- **race** and **hybrid_race** (10_identity.json): home `identity`.
- **hair_style** and **makeup** (20_appearance.json):
  `scene_overridable: true`.
- **3 must-promotions** (hybrid_race flavor→must, apparent_age
  should→must, lower_body should→must) and **10 should-promotions**
  (hair_color_2, hair_color_pattern, facial_hair, eye_color_2, horns,
  wings, fur_pattern, chest_size, outfit, outfit_palette — all
  flavor→should) present in the emitted priorities.
- The full data diff vs O2 is exactly the override set: 2 home lines
  changed, 13 priority lines changed, 3 `scene_overridable` lines added,
  1 file added — nothing else. Files 30_body, 50_mind, 55_speech,
  70_life, 90_wardrobe_intimate, 91_anatomy_intimate and
  POLISH_FLAGS.md are byte-identical to O2.
- PRIORITY_REVIEW.md: 67 rows (66 + the returning 92 fragment-inherit
  row), exactly 13 marked `OVERRIDE`.
- Determinism on the real tree: second run SHA-256 byte-identical, all
  13 data files and all 4 reports.

## Decisions taken at the planning gate during this session

Three tool-interface points the kickoff prompt did not pin were put to the
gate (Casey) before building; answers are DECIDED and built:

1. **CLI wiring** — `--overrides PATH` defaults to the committed
   `tools/harvest/overrides.json` (default-on). Tests and any future pass
   point the flag elsewhere; the four pre-existing synthetic CLI tests now
   pass an explicit empty overrides file (`{"format": 1}`).
2. **Unapplied override** — a non-comment override entry that never lands
   on an emitted group is a tool error (refusal, exit 2, nothing
   written). An override that targets nothing is a latent lie.
3. **Defaulted-row count** — OVERRIDES_APPLIED.md reports the mechanical
   counts from the final emission: 65 first-definition priority rows, 13
   overridden, **52 standing as defaulted**, 2 fragment-inherit rows
   (67-row table), plus a reconciliation line: the overrides `_note`'s
   "53 of 66" was counted at the gate against the pre-return O2 table
   (65 first-definitions + 1 fragment row, 66 − 13 = 53).

## Builder details (recorded, not softened)

- Overrides-file validation is strict: `"format": 1` required; unknown
  non-`_` top-level section, unknown entry key, non-object entry, or a
  value outside {must, should, flavor} / {identity, persona, session} /
  bool → tool error. Underscore keys inside an entry are tolerated as
  comments (§1.9's family).
- The guard compares resolved absolute paths, anchored at the repo root
  (`tools/harvest/../..`), so it fires regardless of CWD and only for the
  actual maintained tree.
- PRIORITY_REVIEW's overridden mark spelling (`must — OVERRIDE`) and the
  OVERRIDES_APPLIED layout are the builder's (spec §10 principle: exact
  spelling builder's, coverage decided).

## NOT_DECIDED

Nothing was left unbuilt for lack of a decision. Still open by design
(not this session's): the wording-polish pass (its own track, per the
gate), the personal drop-in pass (answer 1, deferred), and stage O3's
input sheet.

## Test count

185 passed, 0 failed, 0 skipped (`uv run pytest`, Python 3.12, zero
runtime dependencies). O2's 168 + 14 override tests + 3 freeze-guard
tests; the shipped-tree invariant test now asserts the O2b counts
(13 / 135 / 2359 / 2334+25).
