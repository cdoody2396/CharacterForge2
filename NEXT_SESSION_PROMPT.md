# NEXT_SESSION_PROMPT — stage O3 — DRAFT

Status: DRAFT. Do not paste until the planning chat has closed the
"Gates before O3" list below and this prompt has been updated with those
answers (including what stage O3 actually is — the builder does not choose
its own scope).

---

## Gates before O3 — planning-side decisions owed on O2's artifacts

These come back for decisions first; they are review items O2 explicitly
emitted for the gate and may change committed data:

1. **Priority review** — `harvest_report/PRIORITY_REVIEW.md` (66 rows,
   §1.6 default map applied, zero overrides). Decide every override, noting
   why (§1.6). Also decide HOW overrides land: hand-edit of the emitted
   files, or an override table consumed by a re-run of
   `python -m tools.harvest` (the tool currently applies the default map
   only — an override input would be a small, decided extension).
2. **POLISH_FLAGS** — `harvest_report/POLISH_FLAGS.md` (66 groups whose v1
   `_note` marks wording provisional; detection rule stated in the file).
   Decide the polish pass: who re-cuts the text, against what style rules,
   and whether it is its own stage or folds into another.
3. **Flag 1: `92_piercings_intimate`** (SESSION_REPORT_O2.md) — the held
   piercings fragment: rule whether `piercings` is `identity` (fragment
   emits, file home row struck) or worn-jewelry `persona` (then the
   38_marks group moves and the record semantics change). Until ruled, the
   two gated piercing placements are not in the tree.
4. **Merge-lock wording** (SESSION_REPORT_O2 discrepancy 1) — confirm
   "touching = error" as built, or relax to answer 8.3's literal
   "mismatch = error".
5. **Name stage O3.** Spec §2's out-of-stage list is the menu; the
   character record model + construction gate is the natural next
   dependency (the orphaned-selection report and every future gate need
   records), but that choice is the planning chat's.

## What O3 will likely need from the planning chat (once scoped)

If O3 is the record model + construction gate, at minimum:

- The record shape: values keyed by group id (§1.10) — storage format,
  one-vs-many per kind, free-text slots, provenance/versioning against
  catalog changes (retired options resolve per Decision 6 — what else?).
- The typed age number and the 20+ construction gate mechanics (answer 6
  kept age on the record; chat speaks digits).
- `home` semantics at the record layer: identity locked at finalization,
  persona editable, `scene_overridable` behavior (Decision 4/4a).
- What "construction gate" refuses vs warns (missing `must` groups?
  hidden-group values? rating admissibility per option — answer 8.4).
- Whether the personal runtime drop-in pass (answer 1: same harvest tool,
  separate pass) happens before, with, or after O3.

## Ground rules to carry forward (unchanged)

1. Build only what the prompt scopes. Invent nothing; ambiguity →
   SESSION_REPORT_O3.md `NOT_DECIDED`, build nothing for it.
2. `python -m app.options.validate` stays the gatekeeper for any data
   change; all tests green before any push.
3. OPTION_FORMAT_SPEC.md as amended by O2_INPUTS.md (and any O3 input
   sheet) is the contract; §0 marking convention binding.
