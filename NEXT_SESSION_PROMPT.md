# NEXT_SESSION_PROMPT — stage O2 (harvest tooling) — DRAFT

Status: DRAFT. Do not paste until the planning chat has answered the
"Needed before O2 can start" list below and this prompt has been updated
with those answers.

---

## Ready-to-paste prompt (fill the [BRACKETS] first)

You are the builder for stage O2 of CharacterForge v2: harvest tooling that
converts the v1 option data into the v2 option format, gated by the stage-O1
validator.

READ FIRST, FULLY: OPTION_FORMAT_SPEC.md (the contract, §0 marking
convention binding) and SESSION_REPORT.md (stage O1's decisions, ambiguity
findings, and NOT_DECIDED list) in the repo root.

Ground rules carried over from O1:
1. Build only harvest tooling and its tests. No creator UI, no record model,
   no safety code, no service spine.
2. Invent nothing. Spec-silent → SESSION_REPORT.md `NOT_DECIDED`, build
   nothing for it.
3. `python -m app.options.validate` (strict laws, exit 0/1, `--json`) is the
   gatekeeper: no harvested file lands in `app/data/options/` unless the
   validator exits 0 on the full data tree.
4. §11 holding list: old keys that do not map 1:1 are carried in
   `_`-prefixed comment keys or the harvest log, never silently dropped.
   `_note` provenance survives verbatim (§1.9).
5. All tests green before any commit is pushed.

Inputs:
- v1 repository at [PATH — c:\Projects\game\CharacterForge on the build
  machine], data in [CONFIRM: app/data/options, app/data/options_gated;
  builders are OUT of §2 scope for options — confirm whether any builder
  data harvests this stage].
- Key mappings (DECIDED in spec): old `tier` → priority per §1.6 default map
  (P0→must, P1→should, P2→flavor, P3→flavor) except the overrides listed
  below; old `class`+`tags` → one `tags` list (§1.8); `image` → `thumb`
  (§1.12); `prompt` → [CONFIRM: image_text? chat_text? both?]; gated-dir
  placement → in-file `rating` per the assignment below; `field`/`quick`/
  `required`/`widget`/`region`/`attribute`/`aliases`/`prompt_ranges`/
  `render` → held aside per §11.

## Needed from the planning chat before O2 can start

1. **Source inventory** — the exact v1 files/directories to harvest, and
   whether the runtime `data/options` drop-in dirs are included.
2. **`prompt` → text mapping** — v1 options carry one `prompt` string; v2
   has `image_text` and `chat_text` with presence-is-meaning (Decision 3).
   Which old prompts become which text(s), per group or per rule.
3. **Rating assignment** — which old gated-dir content becomes `mature` vs
   `explicit`; everything ungated presumably `standard` (confirm).
4. **Priority overrides** — any group where the §1.6 default map is wrong,
   "noting why" (§1.6).
5. **Per-key holding action** — for each §11 held key: carried as `_`-comment
   in the emitted file, or logged only.
6. **Age-band content** — the real bands and their image texts (old
   `prompt_ranges` age content pours into §8; floor is 20, one open band).
7. **Home assignment** — v1 groups have no `home`; every harvested group
   needs `identity`/`persona`/`session` assigned. Source of truth for that
   mapping.
8. **O1's NOT_DECIDED list** (SESSION_REPORT.md) — answers, or explicit
   deferrals, for the 8 recorded questions; at minimum: empty pick groups,
   group-id hygiene, whether `home` is extension-fixed, and null-clears.
9. **Rating display names** — user-facing names for
   `standard`/`mature`/`explicit` are chosen at content authoring (§1.1);
   confirm whether O2 needs them at all (likely no — they never appear in
   data files).

## What O2 will build (once the above is answered)

- A harvest script (`app/harvest/` or similar — planning chat names it)
  reading v1 files, emitting v2-format files, writing a harvest log of every
  held-aside key and every transformation.
- Validator-gated output: the emitted tree must pass
  `python -m app.options.validate` (exit 0) before it is committed.
- Tests: transformation rules (each §11 key), provenance survival, the §1.6
  map and its overrides, idempotence of re-harvest, refusal to emit
  `example_` ids.
