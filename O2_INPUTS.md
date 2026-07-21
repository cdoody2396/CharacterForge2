# O2 INPUTS — answers to SESSION_REPORT questions (planning chat, 2026-07-21)
Marking convention: everything here is DECIDED unless tagged ILLUSTRATIVE.

## 1. Source inventory
Harvest exactly the 14 repo-bundled files: `app/data/options/*.json` (11) and
`app/data/options_gated/*.json` (3), from github.com/cdoody2396/CharacterForge
at main. `00_age.json` is CONSUMED (see answer 6), not emitted. Runtime
drop-in directories are NOT harvest sources — if personal drop-in files exist
on the machine, they run through the same harvest tool afterward as a
separate pass. `app/data/builders/` is out of scope until the builders' turn.

## 2. prompt → text mapping (mechanical, per group)
- v1 `render` true/absent → old `prompt` becomes `image_text`. No `chat_text`
  is authored at harvest; looks reach chat via the appearance paragraph.
- v1 `render: false` → old `prompt` becomes `chat_text`. No `image_text`.
- No option receives both texts at harvest. Both-carrying options are future
  authoring, never a harvest product.
- AMENDMENT to Decision 1's migration note: the chat-text wording polish is
  NOT done during harvest. O2 pours verbatim and emits a `POLISH_FLAGS` list
  of every group whose v1 `_note` marks wording provisional. Polish is its
  own later authoring pass.

## 3. Rating assignment
All 10 emitted ungated files → `standard`. The 3 gated files
(90_wardrobe_intimate, 91_anatomy_intimate, 92_piercings_intimate) →
`explicit`. Nothing maps to `mature` at harvest; `mature` first fills at
content authoring (Decision 8 vice vocabulary).

## 4. Priority overrides
None pre-declared. Apply the §1.6 default map and emit a review table
(group → v1 tier → assigned priority) as a harvest artifact. Overrides are
decided on that table at the O2 gate, not guessed now.

## 5. Per-key holding action
One comment object per group: `"_v1": { ... }` holding, where present:
`field` (only if ≠ group id), `quick`, `required`, `widget`, `region`,
`attribute`, `aliases`, plus any unexpected leftover key. `_note` keys are
carried verbatim at their original level, outside `_v1`. `render` and `tier`
are LOG-ONLY (their information already lives in text presence and
`priority`; restating them in-file invites drift).

## 6. Age bands — STRUCK (spec §8 amended by code-verified evidence)
v1 already removed age `prompt_ranges` (00_age.json `_note`, 5.6c): apparent
age is the user-picked identity group `apparent_age` in 10_identity.json
(8 options, image texts present), because in a fantasy vocabulary apparent
age is NOT derivable from the record number — an ageless 400-year-old must
not render "elderly". Therefore:
- `apparent_age` harvests as a normal `pick_one`, home `identity`.
- The record keeps the typed number for the 20+ gate; chat speaks digits.
- Spec §8's age-band file, its loader, its README stub, and its tests are
  REMOVED in O2. Dormant machinery caused exactly this confusion in v1; v2
  deletes instead.
- The structural "adult" prompt anchor from v1's assembler is noted for the
  image-section turn; it is not option data.

## 7. Home assignment — source of truth is this table
| v1 file | home |
|---|---|
| 20_appearance, 30_body, 35_species, 38_marks, 40_anatomy, 91_anatomy_intimate | `identity` |
| 50_mind, 55_speech, 70_life, 60_wardrobe, 90_wardrobe_intimate | `persona` |
| 92_piercings_intimate | `persona` — worn jewelry behaves like wardrobe and must not bake into training; strike at the gate if piercings should instead be permanent identity |
| 10_identity | per-group split: `apparent_age` → `identity`; all other groups (gender_presentation, gender_identity, pronouns, age_reality, archetype, …) → `persona` |
| 00_age | none — consumed per answer 6 |
Zero `session` groups exist in v1; session vocabulary (expressions, poses) is
new authoring for the image-section and chat turns. O2 emits none and should
not hunt for them. If O2 finds a group that contradicts its file's home, or
any numeric-kind group other than age, it FLAGS and holds — never improvises.

## 8. O1 NOT_DECIDED — all eight answered (numbering matches SESSION_REPORT)
1. Empty `options` on a pick kind → catalog error (recorded in resilient
   mode, raised in strict), replacing O1's derives-hidden behavior. Hidden
   would vanish a group silently. "Empty" means zero options DEFINED; a
   group whose options are merely filtered by rating or retired is not
   empty.
2. Group-id hygiene → same rule as option ids: lowercase `a–z0–9_`, ≤ 40.
   The validator enforces it against the real v1 ids mechanically at
   harvest.
3. `home` may NOT be overridden by an extension file. Merge-locked keys:
   `kind`, `home`, `feeds`, `scene_overridable` — a mismatch is a format
   error. All other scalars keep v1 override semantics.
4. Mixed-rating groups → rating is an OPTION-level fact only. Each option
   is stamped with its file's rating at load; the group model carries no
   rating of its own, and O2 removes the group-level rating field O1 added.
   Every future gate (creator, image, chat) filters per option; a group
   with no admissible active options derives hidden — the same derivation
   family as all-retired. A stored group rating is a second place for one
   fact to be written (Decision 3's lie hazard), and Decision 5's
   span-ratings merge design only works per-option anyway.
5. Explicit `null` → confirmed as built: a format error anywhere. v1's
   null-clears do not return; clearing is writing the explicit default.
   The harvest emits fresh files and writes no nulls.
6. Summary granularity → options per rating, as built, plus the per-file
   counts this sheet's artifact list already requires. No group-rating
   count can exist after answer 4.
7. Missing age-band file at runtime → mooted; the subsystem is deleted
   whole (answer 6 above).
8. Validator CLI coverage of age bands → mooted the same way.

## 9. Rating display names
Confirmed: O2 does not need them. Machine ids only in data; display names
arrive with front-end/content work.

## O2 additionally inherits from this sheet
- Delete the age-band code path (answer 6) with its tests, first commit.
- Remove the group-level rating field and its tests; option-level stamping
  stays (answer 8.4). Convert empty-pick-group from derives-hidden to
  catalog error (answer 8.1); lock the four merge-fixed keys (answer 8.3).
- Emit artifacts: priority review table (answer 4), POLISH_FLAGS (answer 2),
  harvest log of every held/log-only key occurrence, per-file counts vs v1.
- The example_ guard, two-slot law, and all §12 refusals apply to harvested
  output: the harvest is not exempt from the validator — it is its first
  real customer.
