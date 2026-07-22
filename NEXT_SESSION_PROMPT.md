# NEXT_SESSION_PROMPT — stage O3 — DRAFT

Status: DRAFT. The O2 gate list below is closed (O2b, 2026-07-22) except
polish, which runs as its own track; stage O3 is named: the character
record model + construction gate. Do not paste until the planning chat has
answered the O3 input list below and this prompt has been rewritten as a
real kickoff — the builder does not choose its own scope.

---

## Gates before O3 — status after O2b (see SESSION_REPORT_O2B.md)

1. **Priority review** — **CLOSED at O2b.** The gate's 13 overrides landed
   via `tools/harvest/overrides.json` (consumed by the tool, `why` strings
   verbatim in `harvest_report/OVERRIDES_APPLIED.md`); the other 52
   defaulted rows stand.
2. **POLISH_FLAGS** — **OPEN, as its own track.** The wording-polish pass
   is not part of O3; it gets its own scoping (who re-cuts the text,
   against what style rules) when the planning chat opens that track.
3. **Flag 1: `92_piercings_intimate`** — **CLOSED at O2b.** Ruled
   `identity` with `scene_overridable: true`; the fragment emits (13
   files, options 2359) and the answer-7 persona row is superseded by the
   committed override.
4. **Merge-lock wording** — **CLOSED as built.** "Touching = error"
   stands (SESSION_REPORT_O2 discrepancy 1, confirmed at the gate).
5. **Stage O3 = the character record model + construction gate**, per the
   planning chat. This prompt still awaits the O3 input sheet below.

## What O3 needs from the planning chat

For the record model + construction gate, at minimum:

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
