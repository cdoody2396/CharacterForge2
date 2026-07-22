# NEXT_SESSION_PROMPT — stage O4 — DRAFT

Status: DRAFT. Stage O3 landed 2026-07-22 (record model, gates, ledger
skeleton — see SESSION_REPORT_O3.md); this prompt is not a kickoff until
the planning chat picks the next stage and answers its input list. The
builder does not choose its own scope.

---

## Open items O3 leaves on the table

1. **The grade ladder (N8) — NOT_DECIDED, seam built.** The checkpoint's
   G0/G1/G2 definition never reached the O3 session (the gate chose to
   paste it; the text did not arrive). The rules land in exactly one
   place, `app/ledger/grade.py::_apply_ladder`; the calling surface will
   not move. Delivering the ladder text (paste it into the next kickoff,
   or commit it as an inputs amendment) turns this into a small,
   self-contained task for whichever session goes next.
2. **hybrid_race required-always** (O3 gate decision 2, built as ruled):
   every character must pick a second heritage — no "none" option exists.
   If that reads wrong in use, it is a content-authoring fix (a none-style
   option or a visible_when), not a code change.
3. **POLISH_FLAGS** — still OPEN as its own track (unchanged since O2b).
4. **Personal drop-in pass** — N11 recommends running it now that O3 has
   landed; catalog-side, frozen tool, nothing blocks on it.

## Candidate next stages (the planning chat chooses ONE)

Per the O3 kickoff, the two candidates are:

- **The safety transplant.** Unblocks N6's seam: the word-filter with
  scope-declared word files (Decision 8 design), the two free-text slot
  setters, user edits to the appearance paragraph, and `name_safety`
  revalidation (the "pending" flag's clearing states). The record layer
  already refuses honestly everywhere the filter is missing, so this
  stage is the one that makes characters fully authorable.
- **The service spine.** The app-side skeleton the creator UI and image/
  chat sections will hang off. O3's record + ledger layers are pure
  library code with injected paths — the spine decides processes,
  lifecycles, and where the catalog/records/ledger live at runtime.

## What the chosen stage needs from the planning chat (at minimum)

- **Safety transplant:** the word-file format and scope vocabulary
  (Decision 8, restated for one-document build); what "revalidation"
  writes (`name_safety` cleared states); whether the paragraph edit path
  opens fully or stays drafter-only; refusal vs redaction semantics.
- **Service spine:** process model, storage roots (records dir, sidecar
  dirs, DB path — all currently injected), catalog reload semantics
  vs the frozen maintained tree, and which O3 seams it may wrap (ledger
  attach, orphan surfacing).

## Ground rules to carry forward (unchanged)

1. Build only what the prompt scopes. Invent nothing; ambiguity →
   SESSION_REPORT `NOT_DECIDED`, build nothing for it.
2. `python -m app.options.validate` stays the gatekeeper for any data
   change; all tests green before any push.
3. OPTION_FORMAT_SPEC.md as amended by O2_INPUTS.md and O3_INPUTS.md is
   the contract; §0 marking convention binding. N7's sentence wording and
   all fixture content remain ILLUSTRATIVE.
