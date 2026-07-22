# HARVEST LOG — v1 → v2 option data (stage O2)

- v1 source: https://github.com/cdoody2396/CharacterForge
- v1 commit: a9519863ff933709dc080bf6941f118853b05569
- emitted files: 13

## Inventory — per-file counts vs v1

| v1 file | rating | v1 groups | v1 options | emitted groups | emitted options | disposition |
|---|---|---|---|---|---|---|
| 00_age.json | standard | 1 | 0 | 0 | 0 | consumed |
| 10_identity.json | standard | 8 | 297 | 8 | 297 | emitted |
| 20_appearance.json | standard | 19 | 277 | 19 | 277 | emitted |
| 30_body.json | standard | 3 | 24 | 3 | 24 | emitted |
| 35_species.json | standard | 20 | 179 | 20 | 179 | emitted |
| 38_marks.json | standard | 4 | 65 | 4 | 65 | emitted |
| 40_anatomy.json | standard | 5 | 24 | 5 | 24 | emitted |
| 50_mind.json | standard | 20 | 471 | 20 | 471 | emitted |
| 55_speech.json | standard | 11 | 127 | 11 | 127 | emitted |
| 60_wardrobe.json | standard | 7 | 201 | 7 | 201 | emitted |
| 70_life.json | standard | 34 | 669 | 34 | 669 | emitted |
| 90_wardrobe_intimate.json | explicit | 1 | 4 | 1 | 4 | emitted |
| 91_anatomy_intimate.json | explicit | 4 | 19 | 4 | 19 | emitted |
| 92_piercings_intimate.json | explicit | 1 | 2 | 1 | 2 | emitted |

## Flags — groups held out of the emitted tree

(none)

## Consumed

- `00_age.json`: consumed whole (answer 6): groups ['age']

## Log-only keys (`render`, `tier`) — information lives in text presence and `priority`

| file | group | key | value |
|---|---|---|---|
| 10_identity.json | race | tier | `"P0"` |
| 10_identity.json | hybrid_race | tier | `"P2"` |
| 10_identity.json | gender_presentation | render | `false` |
| 10_identity.json | gender_identity | render | `false` |
| 10_identity.json | pronouns | render | `false` |
| 10_identity.json | apparent_age | tier | `"P1"` |
| 10_identity.json | age_reality | render | `false` |
| 10_identity.json | archetype | render | `false` |
| 20_appearance.json | skin_type | tier | `"P1"` |
| 20_appearance.json | skin_tone | tier | `"P1"` |
| 20_appearance.json | complexion | tier | `"P3"` |
| 20_appearance.json | hair_color | tier | `"P1"` |
| 20_appearance.json | hair_color_2 | tier | `"P2"` |
| 20_appearance.json | hair_color_pattern | tier | `"P2"` |
| 20_appearance.json | hair_length | tier | `"P1"` |
| 20_appearance.json | hair_style | tier | `"P1"` |
| 20_appearance.json | bangs | tier | `"P2"` |
| 20_appearance.json | facial_hair | tier | `"P2"` |
| 20_appearance.json | eye_color | tier | `"P1"` |
| 20_appearance.json | eye_color_2 | tier | `"P2"` |
| 20_appearance.json | eye_shape | tier | `"P2"` |
| 20_appearance.json | eye_features | tier | `"P2"` |
| 20_appearance.json | face_shape | tier | `"P3"` |
| 20_appearance.json | lips | tier | `"P3"` |
| 20_appearance.json | nose | tier | `"P3"` |
| 20_appearance.json | eyebrows | tier | `"P3"` |
| 20_appearance.json | makeup | tier | `"P2"` |
| 30_body.json | body_type | tier | `"P1"` |
| 30_body.json | height_band | tier | `"P2"` |
| 30_body.json | muscle_def | tier | `"P2"` |
| 35_species.json | ears | tier | `"P1"` |
| 35_species.json | horns | tier | `"P2"` |
| 35_species.json | tail | tier | `"P1"` |
| 35_species.json | wings | tier | `"P2"` |
| 35_species.json | fur_color | tier | `"P1"` |
| 35_species.json | fur_condition | tier | `"P3"` |
| 35_species.json | fur_pattern | tier | `"P2"` |
| 35_species.json | scale_color | tier | `"P1"` |
| 35_species.json | scale_sheen | tier | `"P2"` |
| 35_species.json | feather_color | tier | `"P1"` |
| 35_species.json | feather_condition | tier | `"P3"` |
| 35_species.json | chassis_finish | tier | `"P1"` |
| 35_species.json | chassis_seams | tier | `"P2"` |
| 35_species.json | faceplate | tier | `"P2"` |
| 35_species.json | ethereal_opacity | tier | `"P1"` |
| 35_species.json | glow_color | tier | `"P2"` |
| 35_species.json | lower_body | tier | `"P1"` |
| 35_species.json | elemental_marks | tier | `"P2"` |
| 35_species.json | undead_state | tier | `"P1"` |
| 35_species.json | other_features | tier | `"P2"` |
| 38_marks.json | marks | tier | `"P2"` |
| 38_marks.json | tattoo_placement | tier | `"P2"` |
| 38_marks.json | tattoo_motif | tier | `"P2"` |
| 38_marks.json | piercings | tier | `"P3"` |
| 40_anatomy.json | chest_size | tier | `"P2"` |
| 40_anatomy.json | waist | tier | `"P2"` |
| 40_anatomy.json | hips | tier | `"P2"` |
| 40_anatomy.json | rear | tier | `"P3"` |
| 40_anatomy.json | body_hair | tier | `"P3"` |
| 50_mind.json | personality_archetype | render | `false` |
| 50_mind.json | warmth | render | `false` |
| 50_mind.json | energy | render | `false` |
| 50_mind.json | assertiveness | render | `false` |
| 50_mind.json | candor | render | `false` |
| 50_mind.json | impulse | render | `false` |
| 50_mind.json | default_mood | render | `false` |
| 50_mind.json | traits | render | `false` |
| 50_mind.json | flaws | render | `false` |
| 50_mind.json | quirks | render | `false` |
| 50_mind.json | vices | render | `false` |
| 50_mind.json | values | render | `false` |
| 50_mind.json | moral_compass | render | `false` |
| 50_mind.json | fears | render | `false` |
| 50_mind.json | near_goal | render | `false` |
| 50_mind.json | life_dream | render | `false` |
| 50_mind.json | lines_never_cross | render | `false` |
| 50_mind.json | intellect_style | render | `false` |
| 50_mind.json | skills | render | `false` |
| 50_mind.json | signature_skill | render | `false` |
| 55_speech.json | voice_timbre | render | `false` |
| 55_speech.json | speech_pace | render | `false` |
| 55_speech.json | speech_register | render | `false` |
| 55_speech.json | speech_patterns | render | `false` |
| 55_speech.json | verbal_tic | render | `false` |
| 55_speech.json | accent_flavor | render | `false` |
| 55_speech.json | laugh | render | `false` |
| 55_speech.json | expressiveness | render | `false` |
| 55_speech.json | temper_fuse | render | `false` |
| 55_speech.json | affection_style | render | `false` |
| 55_speech.json | comfort_ritual | render | `false` |
| 60_wardrobe.json | outfit | tier | `"P2"` |
| 60_wardrobe.json | outfit_palette | tier | `"P2"` |
| 60_wardrobe.json | outfit_fit | tier | `"P3"` |
| 60_wardrobe.json | outfit_condition | tier | `"P3"` |
| 60_wardrobe.json | neckline | tier | `"P3"` |
| 60_wardrobe.json | accessories | tier | `"P2"` |
| 60_wardrobe.json | aesthetic | tier | `"P3"` |
| 70_life.json | setting | render | `false` |
| 70_life.json | roots | render | `false` |
| 70_life.json | locale | render | `false` |
| 70_life.json | social_standing | render | `false` |
| 70_life.json | reputation | render | `false` |
| 70_life.json | legal_status | render | `false` |
| 70_life.json | occupation | render | `false` |
| 70_life.json | workplace | render | `false` |
| 70_life.json | job_feeling | render | `false` |
| 70_life.json | origin_story | render | `false` |
| 70_life.json | family_now | render | `false` |
| 70_life.json | siblings | render | `false` |
| 70_life.json | defining_events | render | `false` |
| 70_life.json | secrets | render | `false` |
| 70_life.json | turning_point | render | `false` |
| 70_life.json | living_situation | render | `false` |
| 70_life.json | finances | render | `false` |
| 70_life.json | companion | render | `false` |
| 70_life.json | hobbies | render | `false` |
| 70_life.json | fav_food | render | `false` |
| 70_life.json | disliked_food | render | `false` |
| 70_life.json | music_taste | render | `false` |
| 70_life.json | pet_peeves | render | `false` |
| 70_life.json | with_strangers | render | `false` |
| 70_life.json | warming_pace | render | `false` |
| 70_life.json | with_friends | render | `false` |
| 70_life.json | toward_authority | render | `false` |
| 70_life.json | in_conflict | render | `false` |
| 70_life.json | trust | render | `false` |
| 70_life.json | when_interested | render | `false` |
| 70_life.json | attachment_behavior | render | `false` |
| 70_life.json | jealousy | render | `false` |
| 70_life.json | address_habits | render | `false` |
| 70_life.json | avoided_topics | render | `false` |
| 91_anatomy_intimate.json | chest_shape | tier | `"P2"` |
| 91_anatomy_intimate.json | genitalia | tier | `"P3"` |
| 91_anatomy_intimate.json | genitalia_size | tier | `"P3"` |
| 91_anatomy_intimate.json | grooming | tier | `"P3"` |

## Held keys — carried in each group's `_v1` comment object

| file | group | key | value |
|---|---|---|---|
| 10_identity.json | race | quick | `true` |
| 10_identity.json | race | required | `true` |
| 10_identity.json | gender_presentation | quick | `true` |
| 10_identity.json | gender_presentation | required | `true` |
| 10_identity.json | apparent_age | quick | `true` |
| 20_appearance.json | skin_type | quick | `true` |
| 20_appearance.json | skin_type | required | `true` |
| 20_appearance.json | skin_tone | quick | `true` |
| 20_appearance.json | skin_tone | required | `true` |
| 20_appearance.json | hair_color | quick | `true` |
| 20_appearance.json | hair_color | required | `true` |
| 20_appearance.json | hair_length | quick | `true` |
| 20_appearance.json | hair_style | quick | `true` |
| 20_appearance.json | hair_style | required | `true` |
| 20_appearance.json | eye_color | quick | `true` |
| 20_appearance.json | eye_color | required | `true` |
| 30_body.json | body_type | quick | `true` |
| 30_body.json | body_type | required | `true` |
| 40_anatomy.json | chest_size | region | `"Chest"` |
| 40_anatomy.json | chest_size | attribute | `"Size"` |
| 40_anatomy.json | waist | region | `"Hips & Rear"` |
| 40_anatomy.json | waist | attribute | `"Waist"` |
| 40_anatomy.json | hips | region | `"Hips & Rear"` |
| 40_anatomy.json | hips | attribute | `"Width"` |
| 40_anatomy.json | rear | region | `"Hips & Rear"` |
| 40_anatomy.json | rear | attribute | `"Size"` |
| 40_anatomy.json | body_hair | region | `"Features"` |
| 40_anatomy.json | body_hair | attribute | `"Body Hair"` |
| 50_mind.json | personality_archetype | quick | `true` |
| 91_anatomy_intimate.json | chest_shape | region | `"Chest"` |
| 91_anatomy_intimate.json | chest_shape | attribute | `"Shape"` |
| 91_anatomy_intimate.json | genitalia | region | `"Genitalia"` |
| 91_anatomy_intimate.json | genitalia | attribute | `"Configuration"` |
| 91_anatomy_intimate.json | genitalia_size | region | `"Genitalia"` |
| 91_anatomy_intimate.json | genitalia_size | attribute | `"Size"` |
| 91_anatomy_intimate.json | grooming | region | `"Genitalia"` |
| 91_anatomy_intimate.json | grooming | attribute | `"Grooming"` |

## Comment keys other than `_note` carried verbatim (§1.9)

- `10_identity.json` / `gender_presentation`: `_render_note`

## Option `image` → `thumb` renames (§1.12)

(none — v1 carries no option `image` keys)

## Notes

- `field` equal to the group id dropped per §1.10: 135 occurrence(s); zero differed (a differing `field` would be held in `_v1`).
- Empty v1 `prompt` strings preserved verbatim as empty text values (answer 2 — delete nothing silently): 28 option(s).
