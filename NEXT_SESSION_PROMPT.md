# NEXT_SESSION_PROMPT — after O5 — DRAFT

Status: DRAFT. Stage O5 landed 2026-07-24 (service spine: `app/spine/`,
one authenticated loopback process owning catalog + records + safety +
audit + ledger — see SESSION_REPORT_O5.md); this prompt is not a kickoff
until the planning chat picks the next stage and answers its input
list. The builder does not choose its own scope.

The candidates the planning chat expects (O5_INPUTS §K): **creator UI**
· **image-identity section**. §B below carries verbatim to whichever
runs.

---

## Carried verbatim — O5_INPUTS §B (binding on the UI stage)

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

## Open items O5 leaves on the table

1. **Creator UI candidate.** The spine serves everything a screen
   needs (creator view with derived widgets `segmented`/`chips`/
   `swatch`/`picker`, structured refusal codes, discovery via
   `runtime.json` + `X-Spine-Token`). The UI consumes the spine ONLY
   (§B above). Needed from the planning chat: shell/framework decision
   (and how it starts/finds/stops the spine) · screen inventory and
   section layout (the catalog's `section`/`order`/`hint` are served,
   uninterpreted so far) · rendering contract per widget · how drafts,
   finalize, versions, rating raises, and refusal codes surface to the
   creator · whether any catalog `free_text` group is introduced (its
   filtered write path must be specified in that same contract — §I.2
   ownership) · a ruling on O5 NOT_DECIDED 1 (record-less creator-view
   preview) if the UI wants one.
2. **Image-identity candidate.** Still owed (unchanged from O3): the
   ring-derivation rule (the `NullRingProvider` seam in
   `app/ledger/grade.py` stands until then — G1 honestly
   undeterminable) · the reference-core "LoRA seeds" disambiguation ·
   the G0 exotic-anatomy carve-out · the ring-skip-to-LoRA execution
   call. The spine already serves `artifacts/` layout (lazy, empty),
   receipt-indexed artifact/staleness queries, and the grade
   passthrough; generation logging stays with this section (O5 §H).
3. **O5 NOT_DECIDED items** (SESSION_REPORT_O5): (1) a record-less
   creator-view preview — the view exists for any record including a
   fresh one; a preview before any record exists was not built ·
   (2) `httpx2` (a TestClient deprecation suggestion) — adding it would
   exceed §C's exact-three dependency law.
4. **Closed by O5 §I** (for the record): `misc` enforcement — floor,
   permanent, list stands as built · catalog-declared `free_text`
   groups — sealed; the contract that first introduces such a group
   owns its filtered write path.
5. **Out-stages named by O5_INPUTS §A**, each still owned elsewhere:
   desktop shell / packaging (incl. §D's deferred user word-data tuning
   on installed builds) · job runner, worker supervisor, GPU-slot law,
   image/chat/training workers, llama.cpp and embedder processes ·
   transcripts / memory / jobs tables (N10) · prompt assemblers ·
   Layer-2 model gating · chat/image use-time filtering · the
   rating-downgrade residue rule.
6. **POLISH_FLAGS** — still OPEN as its own track (unchanged since O2b).
7. **Personal drop-in pass** — catalog-side, frozen tool; the landing
   zone now exists (`options_dropin/` under the data root loads after
   the maintained tree, full validator rule set, restart to take
   effect). Nothing blocks on it.

## Ground rules to carry forward (unchanged unless noted)

1. Build only what the prompt scopes. Invent nothing; ambiguity →
   SESSION_REPORT `NOT_DECIDED`, build nothing for it.
2. `python -m app.options.validate` stays the gatekeeper for any data
   change; all tests green before any push.
3. OPTION_FORMAT_SPEC.md as amended by O2_INPUTS.md and O3_INPUTS.md is
   the contract (O4/O5 added no format change); §0 marking convention
   binding.
4. The §C hard law is code, not data: `minors`/`slurs` load only at
   floor. No stage may soften it by data edit.
5. **Dependencies (new at O5)**: exactly `fastapi`, `uvicorn`, `httpx`,
   pinned (requirements.txt + pyproject/uv.lock). Anything further is a
   `NOT_DECIDED` for the planning gate.
6. **The spine is the single evaluator (new at O5, §B)**: no client
   re-implements catalog or gate logic; catalog changes take effect at
   restart only.
