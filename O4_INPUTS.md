# O4 INPUTS — the safety transplant contract

Delivered by the planning gate (Casey) in-chat on 2026-07-23, at the O4
kickoff (through the plan-phase question UI). Committed here verbatim so
the contract lives in the repo, the O3_INPUTS_N8_LADDER.md pattern.
Everything below the line is the delivery, untouched.

---

# O4_INPUTS — safety transplant (planning chat, 2026-07-23)

Marking convention: everything here is DECIDED unless tagged ILLUSTRATIVE.
Anything this document does not define is not the builder's to invent:
unclear → SESSION_REPORT `NOT_DECIDED`, build nothing for it.

---

## A. Stage scope

O4 builds `app/safety/` (filter engine, transplanted word data, audit sink)
and opens the N6 seam in `app/record/`. Nothing else.

OUT of this stage (each owned elsewhere): service spine and all app-side
write sites (O5) · chat/image use-time filtering (their sections) · Layer-2
model gating (chat/image sections) · creator UI · list-content authoring
beyond the verbatim transplant (polish track) · the rating-downgrade
residue rule (consumer contracts).

## B. Transplant source (DECIDED)

Source: v1 repo `github.com/cdoody2396/CharacterForge` at commit
`a9519863` — the same pinned commit the harvest consumed. Transplant:

- `app/safety/normalize.py` — verbatim; the obfuscation-folding engine
  under everything.
- `app/safety/layer1.py` — the matching machinery carries: term parsing
  (`#` comments, `re:` regex lines), the joiner / spread / doubled-letter /
  leetspeak / digit-safe match families, ASCII edge guards, plural
  tolerance, the proximity logic, `FilterResult`. The hardcoded
  `_CATEGORY_FILES` registry does NOT carry — v2 word files self-declare
  (§C) and the code-side dict is deleted.
- `app/safety/data/*` — every list file verbatim, comments and
  false-positive commentary included, then wrapped with §C declarations.
  The builder inventories the real file set and per-file line counts in the
  session report (the checkpoint's "nine lists" count is verified there,
  not assumed).
- v1's Layer-4 audit module (vocabulary-blind JSONL appender) — as library
  code only (§H).
- v1's normalization/obfuscation test vectors — ported.

The zero-runtime-dependency rule holds; everything above is stdlib.

## C. Scope-declared word files (laws DECIDED; header spelling ILLUSTRATIVE)

The v1 line format survives: one term per line, `#` comment lines, `re:`
regex lines, contextual lists literal-only. Each file additionally declares
its own scope in-file. Declaration laws:

1. Required declarations per list file: `category` (machine id) · `mode`
   (`always` | `contextual`) · `enforcement` (`floor` |
   `unlocked_at: mature` | `unlocked_at: explicit`).
2. Fail-loud load, distinct error codes: missing, unknown, or duplicate
   declarations · an undeclared file in the data directory · a `contextual`
   file when `sexual_context.txt` is absent · a regex line in a contextual
   file. The filter never starts over a bad data directory.
3. HARD LAW in code, not data: files carrying category `minors` or `slurs`
   load only with `enforcement: floor`; anything else refuses. A data edit
   cannot unlock these.
4. `sexual_context.txt` carries a declaration marking it the proximity
   vocabulary; it takes no category or enforcement of its own.

Header spelling (e.g. `#! category: drugs`) is the builder's, recorded in
the report.

## D. Category enforcement — the gate answer (DECIDED at the gate, 2026-07-23)

- `floor` — enforced at every rating: `minors` (both lists), `slurs`,
  `bestiality`, `noncon` (both lists), `selfharm`, `advice`, `misc`.
- `unlocked_at: mature`: `drugs`.

Reasons recorded: the `mature` tier is the planned home of vice vocabulary
(O2_INPUTS answer 3, Decision 8), so drug terms in free text become legal
exactly where that content becomes authorable. `misc` stays floor until its
contents are inventoried (§B report) — migrating it later is a one-line
data edit under §C. Nothing in the remaining floor lists is content any
rating should unlock.

## E. Filter API (semantics DECIDED; spellings builder's)

- A `SafetyFilter` constructed over a data directory, loading per §C.
  `check(text, context, rating)` → `FilterResult` (allowed, category,
  matched, context, message). Contexts are v1's set: `freetext`, `chat`,
  `prompt`, `name`.
- Enforcement: `floor` lists always apply. `unlocked_at: R` lists apply
  only when the passed rating is BELOW R; at or above R they are skipped.
  Where a surface has no record rating, the default is `standard`
  (everything applies).
- v1 context semantics carry unchanged: `always` files block in every
  applied context; `contextual` files block outright in `prompt` context,
  block in `freetext`/`chat` only within the proximity window of sexual
  vocabulary, and never apply to `name` context.
- Err-toward-blocking stands; the data files remain the tuning surface.

## F. Record wiring — the N6 seam opens (DECIDED)

Wiring spelling is the builder's (the catalog-argument precedent: the
filter is passed in, never a module global). Law: with no filter supplied,
every O3 `SafetyNotInstalledError` refusal stands unchanged — the seam's
honesty survives for tests and for any caller without the filter.

- **Free-text slots.** `set_looks_text` / `set_story_text` open. Cap 240
  characters (Decision 7-amended ceiling; overlong refuses with a distinct
  code). Checked in `freetext` context at the record's current rating.
  Pass → stored in the O3 shape (draft / persona). Block → refusal naming
  category and matched term; record unchanged. Clearing is an explicit
  clear API; no nulls (N2 law).
- **Name.** Charset law first (unchanged from O3), then the filter in
  `name` context. Pass → stored with `name_safety: "clear"`. Block →
  refusal, record unchanged. `name_safety` values are exactly `pending` |
  `clear`; the O3 load law amends to accept both and refuse anything else.
  Blocked is never a stored state. Revalidation of a `pending` name: an
  explicit revalidate API, plus N5 finalization runs it automatically when
  a name exists and is pending — pass writes `clear`, fail refuses
  finalization. Loads still never mutate.
- **Appearance paragraph.** User edits target the DRAFT only; committed
  versions stay frozen (N1 law untouched). No open draft → refusal. The
  edit runs the filter (`freetext`, record rating) and carries a length
  cap (value ILLUSTRATIVE — builder picks and records; the cap exists).
  At finalization, a draft carrying a user edit commits it verbatim and
  the version records its author (`user` vs `drafter`; key spelling
  builder's). Every later finalization re-drafts unless its own draft
  carries a new user edit — user text never silently survives an identity
  change it might misdescribe. On load, an absent author key reads as
  `drafter` (O3 fixtures).
- Every refusal above: distinct code, individually tested.

## G. Refusal, never redaction (DECIDED)

No surface rewrites, masks, or trims user text. A block refuses the whole
write and names the category and matched term so the user can rewrite.
Silent mutation of user input is the same lie as silent data repair.

## H. Audit sink (DECIDED, minimal)

The filter takes an injected audit sink; the default is a Null sink
(no-op). The real sink is v1's vocabulary-blind JSONL appender,
transplanted as library code. Refusals — and only refusals — emit an
event: timestamp, context, category, surface code. App-wide write-site
placement belongs to the spine (O5); O4 wires nothing beyond the filter
itself.

## I. Required tests (coverage DECIDED)

Transplant fidelity: every v1 list loads, per-file term counts reported ·
ported v1 obfuscation vectors green · each §C declaration law refuses
distinctly, incl. the minors/slurs hard law · context semantics:
contextual-proximity block in freetext, outright block in prompt, name
exemption · rating gating: `drugs` blocks at `standard` and passes at
`mature`/`explicit`; every floor category still blocks at `explicit` ·
both slots: accept, block (category + term surfaced), overlong, clear
path · name: `clear` on pass, blocked-name refusal, `pending` → `clear`
at finalization, finalization refusal on a blocked pending name, load
accepts `pending` + `clear` and refuses others · paragraph: filtered edit
on draft, verbatim commit with author marker, re-draft on the next
finalization, no-draft refusal · committed versions untouched by all of
the above · a record used with no filter keeps every O3 refusal · audit:
events on refusals only; Null sink silent.

## J. Deliverables

Code and data per above · all tests green; `python -m app.options.validate
app/data/options` exit 0 (no option-tree change is expected — the report
says so explicitly) · `SESSION_REPORT_O4.md` (decisions taken, every
naming/spelling choice, transplant inventory, NOT_DECIDED) · README and
spec changelog touches · `NEXT_SESSION_PROMPT.md` redrafted for O5
(candidate: service spine, carrying the recorded creator-UX input) · this
file committed verbatim at repo root with a provenance header.
