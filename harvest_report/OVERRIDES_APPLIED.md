# OVERRIDES APPLIED — planning-gate decisions consumed by this run

- overrides file: `tools/harvest/overrides.json`
- source `_note`, verbatim: Planning-gate overrides on the O2 harvest (2026-07-21). Reviewed against harvest_report/PRIORITY_REVIEW.md at CharacterForge2 e41e409. Applied by tools/harvest after the O2_INPUTS answer-7 table; 'why' strings are copied verbatim into OVERRIDES_APPLIED.md. 53 of 66 priority rows stand as defaulted; 13 override.

## `priority` — applied after the §1.6 default map

| group | default | override | why (verbatim) |
|---|---|---|---|
| hybrid_race | flavor | must | The second half of the subject's kind; a hybrid rendered as pure base race is a different subject. |
| apparent_age | should | must | Age class defines the subject, and the model's young-adult bias means a silent drop rewrites it; must survive every overflow. |
| lower_body | should | must | For split-anatomy species this IS the subject's body — a drop renders the wrong creature; the naga acceptance run is the precedent. |
| hair_color_2 | flavor | should | Two-tone hair is one strong feature with its pattern; the pair survives or drops together with the base hair block. |
| hair_color_pattern | flavor | should | Travels with hair_color_2 — pattern without the second color (or the reverse) makes an incoherent prompt. |
| facial_hair | flavor | should | A beard changes the face more than any flavor detail. |
| eye_color_2 | flavor | should | Heterochromia, when present, is the character's most-noticed feature; not safe to lose in framings that admit eye detail. |
| horns | flavor | should | Silhouette-level species feature. |
| wings | flavor | should | Silhouette-scale anatomy; dropping it visibly changes the creature. |
| fur_pattern | flavor | should | A beastfolk coat pattern is the hair-pattern equivalent; symmetric with hair_color_pattern. |
| chest_size | flavor | should | Figure-defining beyond body_type; the remaining proportion groups (waist, hips, rear) stay flavor to protect the window. |
| outfit | flavor | should | Decision 9 names the worn outfit as should-say explicitly; the default map under-placed it. |
| outfit_palette | flavor | should | Outfit color is part of the outfit's identity — 'red dress' is one fact; travels with outfit. |

## `home` — applied after the answer-7 table, superseding it wherever the group appears

| group | override | supersedes (answer-7 table) | why (verbatim) |
|---|---|---|---|
| race | identity | persona (10_identity.json) | Carries image text, defines the body, anchors every species-visibility rule — identity by every test; the answer-7 ellipsis misplaced it. |
| hybrid_race | identity | persona (10_identity.json) | Same tests as race. |
| piercings | identity | identity (38_marks.json), persona (92_piercings_intimate.json) | O2-gate ruling: v1 defined piercings among marks; the pierced look belongs to the trained likeness, with scene_overridable carrying the removability. Supersedes the answer-7 persona row for 92_piercings_intimate — the held fragment emits. |

## `scene_overridable` — identity homes only; value true emits the group key

| group | value | why (verbatim) |
|---|---|---|
| hair_style | true | The founding Decision 4a example: her own style is the trained default; an updo for the gala is a one-shot instruction on the receipt. |
| makeup | true | Identity-homed as her signature look, but inherently per-occasion; overridable keeps event looks off the training chain. |
| piercings | true | Ruled at the O2 gate: pierced look lives in the trained likeness; a scene can remove jewelry, training always renders with overrides off. |

## Comment records — recorded verbatim, never applied as keys

- `scene_overridable` / `_denied_apparent_age`: `{"value": false, "why": "Recorded refusal, not a key change: age presentation is never scene-overridable — a per-scene age-down is an abuse vector. The flag is simply absent, and merge-locking keeps drop-ins from adding it."}`

## Defaulted rows

- First-definition priority rows in this emission: 65; overridden: 13; standing as defaulted: 52.
- Fragment rows (inherit the defining group's priority, no default of their own): 2.
- The source `_note`'s own row arithmetic, where present, was counted at
  the gate against the review table as it then stood — before any held
  group returned; the counts above are recomputed from this emission.
