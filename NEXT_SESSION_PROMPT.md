# NEXT_SESSION_PROMPT — after O6 — DRAFT

Status: DRAFT. Stage O6 landed 2026-07-24 (creator UI: `frontend/` —
Roster · Session · Atelier over the spine, plus the §G spine deltas and
`scripts/dev.py`; see SESSION_REPORT_O6.md); this prompt is not a
kickoff until the planning chat picks the next stage and answers its
input list. The builder does not choose its own scope.

The candidates the planning chat expects (O6_INPUTS §K.6):
**image-identity section** · **library screens** (the four-axis filter
— Race, Sex, Genitalia, Kinks — is recorded for them, not built). §B
below carries verbatim to whichever runs.

---

## Carried verbatim — O5_INPUTS §B (binding on every UI stage)

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

O6's operational form carries with it: **the client may narrow or
reorder what the spine serves; it may never widen it.** After every
successful mutation the client refetches served state — it never
predicts.

## Open items O6 leaves on the table

1. **Image-identity candidate.** Still owed (unchanged from O3): the
   ring-derivation rule (the `NullRingProvider` seam in
   `app/ledger/grade.py` stands until then — G1 honestly
   undeterminable) · the reference-core "LoRA seeds" disambiguation ·
   the G0 exotic-anatomy carve-out · the ring-skip-to-LoRA execution
   call. New UI surface owed to it from O6: the finalize ceremony's
   G0/G1/G2 explainer renders display-only with the honest
   not-yet-available line (§I.9) — grade *building* controls belong to
   this section when it lands. `GET …/artifacts` is served and still
   unconsumed by any UI.
2. **Library screens candidate.** The four-axis filter (Race, Sex,
   Genitalia, Kinks) is recorded as their input, not built. The heavy
   kit (filter/facets/sort over served tags) and the roster cards are
   the O6 precedents to grow from; `GET /catalog` (the nothing-hidden
   listing) is served and unconsumed.
3. **Deferred by O6 §I.1 (polish track):** Session-create polish and
   the zone-navigator absorption.
4. **Out-stages named by O6_INPUTS §A**, each still owned elsewhere:
   image-identity surfaces beyond the grade affordance · chat ·
   desktop shell / packaging (the packaged shell later swaps
   `frontend/src/spine/config.ts` and reproduces the `/spine/*`
   mapping — §D) · options editor · register alternates · record
   deletion (no spine endpoint exists — do not add one UI-side) ·
   version-history viewer · rating-locked teaser mode · ghost slots ·
   `subsection` format key · Session quick-subset (no data marking
   exists for it).
5. **O5 NOT_DECIDED 2** (`httpx2`) — still parked; adding it would
   exceed §C's exact-three dependency law. (O5 NOT_DECIDED 1 was
   closed by O6 §I.3: the age gate is the Session's step zero; no
   record-less preview exists.)
6. **POLISH_FLAGS** — still OPEN as its own track (unchanged since
   O2b).
7. **Personal drop-in pass** — catalog-side, frozen tool; the landing
   zone exists (`options_dropin/` under the data root). Nothing blocks
   on it. (O6's capture script exercises the drop-in path end to end.)

## Ground rules to carry forward (unchanged unless noted)

1. Build only what the prompt scopes. Invent nothing; ambiguity →
   SESSION_REPORT `NOT_DECIDED`, build nothing for it — or put it to
   the owner mid-session when the gate is available, and record the
   ruling (the O6 pattern).
2. `python -m app.options.validate` stays the gatekeeper for any data
   change; validator counts unchanged at close (13 / 135 / 2359 at the
   O6 close).
3. OPTION_FORMAT_SPEC.md as amended by O2_INPUTS.md and O3_INPUTS.md is
   the contract (O4/O5/O6 added no format change); §0 marking
   convention binding.
4. The §C hard law is code, not data: `minors`/`slurs` load only at
   floor. No stage may soften it by data edit.
5. **Python dependencies**: exactly `fastapi`, `uvicorn`, `httpx`,
   pinned. **npm dependencies (new at O6, §C.2)**: the declared set is
   closed (`react`, `react-dom`, `@tanstack/react-virtual` + the dev
   eight, exact pins in `frontend/package.json`; declaration-only
   `@types/*` companions admitted by gate ruling). Anything further is
   a `NOT_DECIDED` for the planning gate.
6. The spine is the single evaluator (§B); clients narrow or reorder
   served facts, never widen; refetch after every mutation, never
   predict. Catalog changes take effect at restart only.
7. **Offline law**: built front-end output makes zero network requests
   at runtime; fonts stay vendored OFL files in-repo.
8. **Stage close (permanent from O6, §K.7)**: `uv run pytest`,
   `npm test`, `npm run build` all green at the pushed head on a clean
   tree (`git status --porcelain` empty), fresh checkout preferred;
   the observed tails recorded verbatim in the SESSION_REPORT.
