# PRIORITY REVIEW — §1.6 default map, then the gate's overrides

Map: P0→must, P1→should, P2→flavor, P3→flavor (O2_INPUTS answer 4).
Overrides are the planning gate's, recorded in the overrides file and
OVERRIDES_APPLIED.md, applied after the default map; overridden rows
are marked in the final column. Overridden rows in this emission: 13.

| file | group | v1 tier | default priority | final |
|---|---|---|---|---|
| 10_identity.json | race | P0 | must | must |
| 10_identity.json | hybrid_race | P2 | flavor | must — OVERRIDE |
| 10_identity.json | apparent_age | P1 | should | must — OVERRIDE |
| 20_appearance.json | skin_type | P1 | should | should |
| 20_appearance.json | skin_tone | P1 | should | should |
| 20_appearance.json | complexion | P3 | flavor | flavor |
| 20_appearance.json | hair_color | P1 | should | should |
| 20_appearance.json | hair_color_2 | P2 | flavor | should — OVERRIDE |
| 20_appearance.json | hair_color_pattern | P2 | flavor | should — OVERRIDE |
| 20_appearance.json | hair_length | P1 | should | should |
| 20_appearance.json | hair_style | P1 | should | should |
| 20_appearance.json | bangs | P2 | flavor | flavor |
| 20_appearance.json | facial_hair | P2 | flavor | should — OVERRIDE |
| 20_appearance.json | eye_color | P1 | should | should |
| 20_appearance.json | eye_color_2 | P2 | flavor | should — OVERRIDE |
| 20_appearance.json | eye_shape | P2 | flavor | flavor |
| 20_appearance.json | eye_features | P2 | flavor | flavor |
| 20_appearance.json | face_shape | P3 | flavor | flavor |
| 20_appearance.json | lips | P3 | flavor | flavor |
| 20_appearance.json | nose | P3 | flavor | flavor |
| 20_appearance.json | eyebrows | P3 | flavor | flavor |
| 20_appearance.json | makeup | P2 | flavor | flavor |
| 30_body.json | body_type | P1 | should | should |
| 30_body.json | height_band | P2 | flavor | flavor |
| 30_body.json | muscle_def | P2 | flavor | flavor |
| 35_species.json | ears | P1 | should | should |
| 35_species.json | horns | P2 | flavor | should — OVERRIDE |
| 35_species.json | tail | P1 | should | should |
| 35_species.json | wings | P2 | flavor | should — OVERRIDE |
| 35_species.json | fur_color | P1 | should | should |
| 35_species.json | fur_condition | P3 | flavor | flavor |
| 35_species.json | fur_pattern | P2 | flavor | should — OVERRIDE |
| 35_species.json | scale_color | P1 | should | should |
| 35_species.json | scale_sheen | P2 | flavor | flavor |
| 35_species.json | feather_color | P1 | should | should |
| 35_species.json | feather_condition | P3 | flavor | flavor |
| 35_species.json | chassis_finish | P1 | should | should |
| 35_species.json | chassis_seams | P2 | flavor | flavor |
| 35_species.json | faceplate | P2 | flavor | flavor |
| 35_species.json | ethereal_opacity | P1 | should | should |
| 35_species.json | glow_color | P2 | flavor | flavor |
| 35_species.json | lower_body | P1 | should | must — OVERRIDE |
| 35_species.json | elemental_marks | P2 | flavor | flavor |
| 35_species.json | undead_state | P1 | should | should |
| 35_species.json | other_features | P2 | flavor | flavor |
| 38_marks.json | marks | P2 | flavor | flavor |
| 38_marks.json | tattoo_placement | P2 | flavor | flavor |
| 38_marks.json | tattoo_motif | P2 | flavor | flavor |
| 38_marks.json | piercings | P3 | flavor | flavor |
| 40_anatomy.json | chest_size | P2 | flavor | should — OVERRIDE |
| 40_anatomy.json | waist | P2 | flavor | flavor |
| 40_anatomy.json | hips | P2 | flavor | flavor |
| 40_anatomy.json | rear | P3 | flavor | flavor |
| 40_anatomy.json | body_hair | P3 | flavor | flavor |
| 60_wardrobe.json | outfit | P2 | flavor | should — OVERRIDE |
| 60_wardrobe.json | outfit_palette | P2 | flavor | should — OVERRIDE |
| 60_wardrobe.json | outfit_fit | P3 | flavor | flavor |
| 60_wardrobe.json | outfit_condition | P3 | flavor | flavor |
| 60_wardrobe.json | neckline | P3 | flavor | flavor |
| 60_wardrobe.json | accessories | P2 | flavor | flavor |
| 60_wardrobe.json | aesthetic | P3 | flavor | flavor |
| 90_wardrobe_intimate.json | outfit | — | (fragment — inherits from 60_wardrobe.json) | — |
| 91_anatomy_intimate.json | chest_shape | P2 | flavor | flavor |
| 91_anatomy_intimate.json | genitalia | P3 | flavor | flavor |
| 91_anatomy_intimate.json | genitalia_size | P3 | flavor | flavor |
| 91_anatomy_intimate.json | grooming | P3 | flavor | flavor |
| 92_piercings_intimate.json | piercings | — | (fragment — inherits from 38_marks.json) | — |
