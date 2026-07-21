# OPTION FORMAT SPEC — v2, build contract
Status: DECIDED on approval of the kickoff turn (planning chat, 2026-07-21).
Supersedes DECISIONS.md §15 and the §12 numeric reservation for the character record.
Consolidates planning Decisions 1–10 (incl. 4a, 7-amended, 8, 8a, 9, 9a) and the
kickoff turn's promotions (§1).

---

## 0. Marking convention — read first, binding on the builder

Two words carry force in this document:

- **DECIDED** — build exactly this. Deviation requires returning to the planning
  chat, not builder judgment.
- **ILLUSTRATIVE** — an example standing in for content that arrives later
  (harvest or a later design turn). Illustrative material MUST NOT appear in
  committed application data or as hardcoded values. It may appear only in
  `tests/fixtures/`.

Structural guards (DECIDED):
1. `app/data/options/` ships EMPTY of data files — a README only. Real data
   arrives via the harvest stage. No sample, seed, starter, or demo data files.
2. Every example identifier in this spec begins `example_`. The loader REFUSES
   any group or option id beginning `example_` outside test fixtures
   (validator error `EXAMPLE_ID_IN_DATA`). Illustrativeness is enforced by
   code, not vigilance.
3. Anything this spec does not define is NOT the builder's to invent. Unclear →
   record in SESSION_REPORT.md under `NOT_DECIDED`, build nothing for it.

---

## 1. Fixed at kickoff (promoted from illustrative to DECIDED this turn)

These were left open during design and had to be pinned for code to exist.
Each is now DECIDED unless struck at the kickoff gate.

| # | Item | Value |
|---|------|-------|
| 1.1 | Machine rating ids | `standard`, `mature`, `explicit` — machine identifiers only; user-facing display names are chosen at content authoring and never appear in data files |
| 1.2 | Free-text ceiling | 240 characters (per Decision 7-amended; the format refuses any declared limit above this) |
| 1.3 | Kind values | `pick_one`, `pick_many`, `free_text` |
| 1.4 | Home values | `identity`, `persona`, `session` |
| 1.5 | Priority values | `must`, `should`, `flavor` |
| 1.6 | Old→new priority default map | P0→`must`, P1→`should`, P2→`flavor`, P3→`flavor`; harvest may override per group, noting why |
| 1.7 | Status values | `active` (default), `retired` — options only; no group-level status |
| 1.8 | Metadata unification | old `class` + `tags` merge into one `tags` list; visibility predicate `class` becomes `has_tag` |
| 1.9 | Unknown keys | format error (strict authoring); exception: keys beginning `_` are comment keys, ignored and legal anywhere (preserves harvest `_note` provenance) |
| 1.10 | Old `field` key | dropped; record values are keyed by group id |
| 1.11 | Schema version | every file carries `"format": 1` |
| 1.12 | Text key names | `image_text`, `chat_text` on options; old option key `image` (thumbnail) renames to `thumb` |
| 1.13 | Gated directories | retired; one data tree, rating declared in-file (Decision 5) |
| 1.14 | `visible_when` strictness | absent → always visible (unchanged); present-but-invalid → format error (tightened from v1's silent degrade) |
| 1.15 | Language/tooling | Python 3.12, `uv` venv, pytest; no other runtime dependencies for this stage |
| 1.16 | Repo name | `CharacterForge2` (assumption — a different name is a one-word swap in the kickoff prompt) |

---

## 2. Stage scope

This stage builds: the option file format loader, the catalog it produces, the
age-band lookup loader, a validator CLI, and tests. Nothing else.

Explicitly OUT of this stage (each has its own later turn): character record
model and construction gate; orphaned-selection report (needs records);
creator UI and its keys; safety-filter transplant and scope-declared word
files (designed in Decision 8, built with the safety stage); service spine;
harvest tooling; chat-memory budget; detail-scope vocabulary and the shot
table; builder (scene/event/scenario) formats and any kinds they may argue.

---

## 3. File model (DECIDED)

One JSON object per file, UTF-8 (BOM tolerated), in a directory scanned in
(directory order, then filename order):

```json
{
  "format": 1,
  "rating": "standard",
  "groups": [ ... ]
}
```

- `format` — required, must equal 1.
- `rating` — required, one of §1.1. Every group and option in the file carries
  this rating (Decision 5: the file is the mark; an option has no rating key
  of its own to forget).
- `groups` — required list.
- Any other non-`_` key: format error.

## 4. Group keys (DECIDED)

| Key | Required | Type / values | Semantics |
|-----|----------|---------------|-----------|
| `id` | yes | string | unique across the catalog; merge target for extension files |
| `label` | yes | string | menu heading |
| `kind` | yes | §1.3 | interaction shape |
| `home` | yes | §1.4 | identity = locked at finalization; persona = editable; session = app-side vocabulary, never on the record (Decision 4) |
| `scene_overridable` | no (default false) | bool | legal ONLY when `home` is `identity`; elsewhere format error (Decision 4a) |
| `priority` | conditional | §1.5 | REQUIRED if any option in the merged group carries `image_text`; FORBIDDEN otherwise (a priority with nothing to prioritize is a latent lie — Decision 3's principle) |
| `max_picks` | no | int ≥ 1 | `pick_many` only; absent = uncapped; on other kinds, format error |
| `feeds` | free_text only | `image` \| `chat` \| `both` | required on `free_text`, forbidden elsewhere (Decision 7 pt 1 — typed content can't declare its reader by presence) |
| `max_chars` | free_text only | int 1–240 | required on `free_text`; a value above 240 is a format error in the FORMAT itself (Decision 7-amended pt 2) |
| `visible_when` | no | object, §6 | conditional display |
| `section` | no | string | creator page grouping hint |
| `order` | no | number | sort hint within section |
| `hint` | no | string | plain-language help; display-only, never enters any prompt |
| `tags` | no | list of strings | content facts (species class etc.); read by visibility, shot derivation, and future readers |
| `options` | pick kinds | list, §5 | required for `pick_one`/`pick_many`; forbidden on `free_text` |

Merge/extension semantics carry over from v1 unchanged (DECIDED, proven):
a later file reusing a group `id` appends its options (deduped by option id)
and overrides scalar keys; files apply atomically (a malformed file has zero
effect); default load is resilient (bad file skipped, error recorded on the
catalog), `strict=True` raises for tests and authoring.

## 5. Option keys (DECIDED)

| Key | Required | Type | Semantics |
|-----|----------|------|-----------|
| `id` | yes | string | stable, chat-emittable: lowercase `a–z0–9_`, ≤ 40 chars (session-vocabulary ids double as chat tags) |
| `label` | yes | string | menu text; also the raw material for the appearance-paragraph draft (Decision 2) |
| `image_text` | no | string | picture-engine shorthand; presence = the picture engine reads this option (Decision 3 — no switch) |
| `chat_text` | no | string | natural-language sentence fragment; presence = the chat model reads it (Decision 3) |
| `tags` | no | list of strings | content facts |
| `color` | no | `#rrggbb` | swatch hint |
| `thumb` | no | relative path | picker thumbnail |
| `status` | no | §1.7 | `retired` = hidden from new selection, fully functional for existing characters (Decision 6); a group whose options are all retired derives hidden — no group-level status exists |

Neither text present = menu-only: fills the record, nothing downstream speaks
it (legal, Decision 3 pt 3).

## 6. Visibility conditions (DECIDED)

`visible_when` = `{"group": "<id>", <exactly one predicate>}` where the
predicate is one of: `"any": true` (referenced group has a value) ·
`"in": [ids]` · `"not_in": [ids]` (empty selection reads visible) ·
`"has_tag": "tag"` (a selected option in the referenced group carries the
tag). Absent → always visible. Present but malformed, unknown predicate, or
referencing a missing group id → format error (§1.14). Evaluation is one hop,
non-recursive, single implementation (no second front-end evaluator exists in
v2 — the drift hazard is designed out).

## 7. Catalog-level laws (DECIDED)

Checked after all files merge; violations are catalog errors (strict mode
raises, resilient mode records):

1. **Two-slot law:** at most one `free_text` group with `home: identity` and
   one with `home: persona`; `free_text` with `home: session` is illegal
   (Decision 7-amended pt 1).
2. **Example guard:** no id beginning `example_` (§0).
3. Duplicate option ids within a merged group: format error at merge time.

## 8. Age-band lookup (DECIDED — Decision 10 pt 4)

Single file `app/data/age_bands.json` (ships empty-of-data with a README;
content arrives at harvest):

```json
{ "format": 1,
  "bands": [ {"min": 20, "max": 29, "image_text": "example_young_adult_text"},
             {"min": 30, "image_text": "example_text"} ] }
```

Laws: bands ordered, integer bounds, first `min` = 20, contiguous (`min` =
previous `max` + 1), no overlaps or gaps, exactly one final open band (no
`max`). Any violation: format error. System-selected by record age; no
user-facing widget exists for it. (The example texts above are ILLUSTRATIVE.)

## 9. Validator CLI (behavior DECIDED, flag spelling ILLUSTRATIVE)

`python -m app.options.validate <dir> [<dir> ...]` — strict-loads the given
directories in order, prints every error with file name and group/option id,
then a summary (files, groups, options, retired count, per-rating counts,
free-text slots found). Exit 0 clean / 1 errors. A machine-readable JSON
output mode exists for harvest tooling. This CLI is the harvest's gatekeeper.

## 10. Error taxonomy (names ILLUSTRATIVE, coverage DECIDED)

Every law above fails with a distinct, testable error naming the file and the
offending id. The fail-loud principle (Decisions 3, 5, 7, 10) is the point;
exact error-string spelling is the builder's.

## 11. Harvest holding list (DECIDED as a list; action per item is the harvest's)

Old keys that do NOT map 1:1 and are HELD ASIDE — carried in `_`-prefixed
comment keys or the harvest log, never silently dropped: `field` where it
differed from the group id · `quick` · `required` · `widget` · `region` ·
`attribute` · `aliases` (deferred — no consumer; Decision RS2) ·
`prompt_ranges` (dies; age content pours into §8) · `render` (dies; presence
of `image_text` replaces it) · old `tier` (maps per §1.6) · old gated-dir
placement (becomes in-file `rating`). `_note` provenance survives verbatim
(§1.9).

## 12. Required test coverage (DECIDED)

Happy paths: minimal valid file; merge-extend across files (append + dedupe +
scalar override); retired option excluded from menu view, resolvable for an
existing value; resilient multi-file load records the bad file and keeps the
good; BOM file loads; comment keys ignored; free-text slots load with both
homes; age-band file valid case.

Refusals (each its own test): unknown top-level/group/option key · unknown
`kind`, `home`, `rating`, `priority`, `status`, `feeds` value · missing
`format` / wrong version · `scene_overridable` on non-identity ·
`priority` present without any `image_text` in the merged group ·
`priority` absent with `image_text` present · `max_picks` on `pick_one` ·
`max_chars` over 240 · `free_text` with `options` · `feeds` on a pick kind ·
malformed `visible_when` (bad predicate, missing group ref) · two identity
free-text slots · `free_text` home `session` · `example_` id outside fixtures ·
atomicity (second group malformed → first group absent) · age bands: gap,
overlap, wrong floor, two open bands · option id violating the hygiene rule.

## 13. Repo skeleton for this stage (layout DECIDED, internal module/file
naming within `app/options/` ILLUSTRATIVE)

```
CharacterForge2/
  README.md                  what exists so far + how to run tests
  OPTION_FORMAT_SPEC.md      this file, committed verbatim
  pyproject.toml             py3.12, pytest config, no runtime deps
  app/__init__.py
  app/options/               loader, catalog, validate CLI
  app/data/options/README.md     "ships empty by design — harvest populates"
  app/data/age_bands.README.md   same
  tests/                     per §12
  tests/fixtures/            the ONLY home for example data
```

No spine, no UI, no safety code, no record model in this stage — their
directories are created when their stages build them, not before.
