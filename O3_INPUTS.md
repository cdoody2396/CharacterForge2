# O3 INPUTS — character record model + construction gate
Planning chat, 2026-07-22. Marking: DECIDED unless tagged ILLUSTRATIVE.
Checkpoint citations are to CHECKPOINT_creation-scoping_S1 (amended), re-read
this turn — not recalled.

## A. Verified base (already decided; restated for one-document build)

1. **Storage split (checkpoint §storage):** the character record is a JSON
   FILE per character (authored artifact; drop-in extensibility demands
   files). SQLite holds mutable state only. The library/artifact index is
   DERIVED — rebuildable from files (AR note).
2. **Identity versioning (checkpoint 1b/1c):** identity edits open v(n+1),
   active only through re-finalization; versions immutable (by convention
   inside the single file — acceptable single-user); every derived artifact
   records its identity version; the active pointer moves.
3. **Decided record minimum (checkpoint):** age, character id, schema
   version, active identity-version pointer. Everything beyond that is
   ruled in §B.
4. **Layers (Decision 4):** identity locked at finalization; persona
   editable any time; session vocabulary never on the record.
5. **Retired options (Decision 6):** existing picks keep working; only NEW
   selection is blocked. **Free-text slots (Decision 7-amended):** exactly
   two record slots, looks (identity) and story (persona), ≤ 240 chars.
6. **Receipts and staleness (R3–R5):** every rendered artifact records
   identity version, method, and its full variable receipt (explicit-empty
   legal); identity-stale = version ≠ active (derived, no marker);
   variable-stale = receipt mismatch (cached marker, receipts win); edits
   mark exactly what they touched. **Age floor:** 20+, typed number.
7. **Rating (this project’s ruling):** never lowered in use.

## B. New rulings — N1–N11, each strikeable at this gate

**N1 — Record file shape.** One JSON object per character: header (character
id, schema version `1`, age, rating, active identity-version pointer,
created stamp) · `identity_versions` — append-only list of immutable
committed versions, each holding its identity-layer selections, the looks
free-text slot, the appearance paragraph, and a finalized stamp · at most
one `draft_identity` working copy (uncommitted v(n+1)) · one `persona`
block (name, persona selections, story slot). No grade field anywhere —
grade is derived (§A6/N8). Exact key spellings: builder's. Writes are
atomic (temp file + rename). **Strong.**

**N2 — Selections representation.** Keyed by group id. Absent key =
unselected; `pick_one` = one option id; `pick_many` = list, order-as-picked,
no duplicates. No JSON null anywhere in a record (same law as data files).
Values for session-home groups are unstorable — refused. **Strong.**

**N3 — `required` returns to the format.** New group key `required`
(bool, default false), semantics required-when-visible; legal on pick kinds
only (meaningless on free_text and session homes → format error). Applied
by direct maintained-tree edit, validator-gated: restore the eight groups
v1 held in `_v1` (race, gender_presentation, skin_type, skin_tone,
hair_color, hair_style, eye_color, body_type — verified in the emitted tree
this turn) PLUS apparent_age, hybrid_race, lower_body, completing the
convention that every `must`-priority group is required-when-visible — a
subject-defining group may not sit empty when it applies. **Strong on the
eight (proven set); moderate-strong on the three additions (consistency
with their must rulings).**

**N4 — Construction gate (checked on every mutation).** REFUSES, always:
age missing, non-integer, < 20, or > 10000 · unknown group or option id ·
an option above the record's rating · a retired option NEWLY introduced ·
a value for a group hidden under current selections · kind violations
(list where single, cap exceeded) · session-home values · any null ·
free-text writes per N6 · any rating decrease (§A7 made enforceable —
rating moves up or not at all). **Strong.**

**N5 — Finalization gate (the identity commit).** All of N4, plus: every
`required` group that is visible under current selections has a value —
across BOTH layers (a character must be whole to finalize; persona stays
editable after). On success: draft becomes v(n+1) verbatim, appearance
paragraph drafts (N7), finalized stamp set, active pointer moves. First
finalization creates v1. **Strong.**

**N6 — Safety seam, honest refusal.** The word-filter is a later stage;
O3 does not stub it into silence. Setters for the two free-text slots and
for user edits to the appearance paragraph RAISE a
safety-not-installed error until the safety stage lands (the v1
NOT_CONFIGURED honesty pattern). `name` alone is writable now under a
charset law (letters, marks, spaces, apostrophe, hyphen, period; 1–60
chars), and the record carries a `name_safety: "pending"` field the safety
stage clears on revalidation. **Moderate — the name interim is the one
soft spot; strike it and name-setting waits for the safety stage too.**

**N7 — Appearance paragraph.** A field on each identity version. Drafted
at finalization by a deterministic assembler over the identity selections'
labels (mechanism DECIDED; sentence wording ILLUSTRATIVE and replaceable);
re-drafted at every re-finalization; user editing blocked per N6 for now.
**Strong on mechanism.**

**N8 — Ledger now, receipts as truth.** Sidecar receipt JSON per rendered
artifact is the source of truth (kind, identity version, method, variable
receipt, rating-at-render, created stamp, artifact path + content hash).
SQLite holds a rebuildable index of them plus the variable-stale cache
column; `rebuild()` reconstructs the index from sidecars (AR
derived-index note honored). R4 derivations and the R5 edit-marking hook
on persona mutations are implemented as record-layer functions. No real
artifacts exist yet — synthetic sidecars in fixtures test everything.
`derive_grade` implements the ladder with an injected ring-membership
provider; the Null provider makes G1 undeterminable and the derivation
says so honestly (G0/G2 evidence only) until the image section supplies
the real one. **Strong; the grade-provider seam is the deliberate
NOT-built piece.**

**N9 — Orphan report (closes O1's deferral).** At record load against the
catalog: unknown ids are listed per character, the record still loads,
orphaned picks stay written but inert — restore the file and the character
is whole (Decision 6 pt 3, now buildable). **Strong.**

**N10 — SQLite scope in O3.** One database file, stdlib `sqlite3` (the
zero-dependency rule holds), WAL mode, schema-version pragma, path
injected (tests use temp dirs). O3 creates ONLY the ledger-index table;
transcripts, memory, and jobs tables belong to their own stages.
**Strong.**

**N11 — Personal drop-in pass timing.** Independent of O3 (catalog-side,
frozen tool). Recommendation: run it after O3 lands to keep sessions
serial; nothing blocks on it. **Moderate — sequencing preference only.**

## C. Out of scope for O3 (each owned elsewhere)

Creator UI and flows · safety-filter internals (the seam is N6) · image
generation, ring derivation, shot table, real receipts · chat · service
spine · scenario/event builders · transcripts/memory/jobs storage ·
polish track (runs parallel) · display names for ratings.

## D. Spec touch

OPTION_FORMAT_SPEC.md gains the `required` key row in §4 (wording per N3)
with a changelog line; committed in the same session as the tree edit that
uses it. No other spec change.
