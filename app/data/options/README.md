# app/data/options — harvested v2 option data

Populated by the stage-O2 harvest from v1
(github.com/cdoody2396/CharacterForge, commit recorded in
`harvest_report/HARVEST_LOG.md`). Files keep their v1 filenames and numeric
prefixes (load order); gated files live here too, their rating declared
in-file (spec §1.13 — one data tree).

Do NOT hand-edit these files: re-running `python -m tools.harvest <v1_root>`
emits byte-identical output and would overwrite edits. Authoring changes are
their own later pass. Illustrative `example_` data lives only in
`tests/fixtures/` (spec §0); the loader refuses it here.

Every file must pass `python -m app.options.validate app/data/options`
(exit 0) — the harvest tool itself stages and validates before writing.
