# NEXT_SESSION_PROMPT — stage O5 — DRAFT

Status: DRAFT. Stage O4 landed 2026-07-23 (safety transplant: `app/safety/`
word filter, N6 seam opened — see SESSION_REPORT_O4.md); this prompt is
not a kickoff until the planning chat picks the next stage and answers its
input list. The builder does not choose its own scope.

---

## Open items O4 leaves on the table

1. **The candidate O4_INPUTS §J names: the service spine**, "carrying the
   recorded creator-UX input" (that input lives in the planning chat's
   records, not this repo — deliver it with the kickoff). O3's record +
   ledger and O4's filter are pure library code with injected paths and
   filters; the spine decides processes, lifecycles, storage roots
   (records dir, sidecar dirs, DB path, audit log dir, the word-data
   dir), catalog reload semantics vs the frozen maintained tree, and the
   app-side write sites §H deferred (where the real `AuditLog` is
   constructed and which surfaces pass which codes).
2. **`misc` enforcement migration** (O4_INPUTS §D): `misc` stays floor
   until its contents are inventoried — the inventory now exists
   (SESSION_REPORT_O4 §B: 9 terms, 1 regex — incest, necrophilia, snuff,
   pipe-bomb instructions et al.). If any of it should unlock at a
   rating, that is a one-line data edit under §C; a ruling either way
   closes the item.
3. **Catalog-declared `free_text` groups remain unwritable** (noted
   consequence, SESSION_REPORT_O4): the record slots opened; a `free_text`
   group in the catalog still refuses at the gate. The maintained tree
   has zero such groups, so nothing is reachable — but the seam exists
   and some later contract owns it.
4. **Out-stages named by O4_INPUTS §A**, each still owned elsewhere:
   chat/image use-time filtering, Layer-2 model gating, the
   rating-downgrade residue rule.
5. **Still owed to the image-identity section** (unchanged from O3): the
   ring-derivation rule, the reference-core "LoRA seeds" disambiguation,
   the G0 exotic-anatomy carve-out, the ring-skip-to-LoRA execution call.
6. **POLISH_FLAGS** — still OPEN as its own track (unchanged since O2b).
7. **Personal drop-in pass** — catalog-side, frozen tool, nothing blocks
   on it (unchanged since O3).

## What the chosen stage needs from the planning chat (at minimum)

- **Service spine:** the recorded creator-UX input (§J's phrase) ·
  process model · storage roots for every injected path (records,
  sidecars, DB, audit logs, word data) · catalog reload semantics vs the
  frozen maintained tree · which existing seams it may wrap (ledger
  attach, orphan surfacing, filter construction + audit sink wiring) ·
  what, if anything, of the §H write-site placement lands now.

## Ground rules to carry forward (unchanged)

1. Build only what the prompt scopes. Invent nothing; ambiguity →
   SESSION_REPORT `NOT_DECIDED`, build nothing for it.
2. `python -m app.options.validate` stays the gatekeeper for any data
   change; all tests green before any push.
3. OPTION_FORMAT_SPEC.md as amended by O2_INPUTS.md and O3_INPUTS.md is
   the contract (O4_INPUTS.md added no format change); §0 marking
   convention binding. N7's sentence wording, the paragraph cap value
   (1200), and all fixture content remain ILLUSTRATIVE.
4. The §C hard law is code, not data: `minors`/`slurs` load only at
   floor. No stage may soften it by data edit.
