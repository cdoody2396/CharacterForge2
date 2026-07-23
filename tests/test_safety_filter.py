"""The transplanted filter over the REAL maintained word data.

The BLOCKED and ALLOWED tables are v1 obfuscation/false-positive vectors,
ported (O4_INPUTS SB) from CharacterForge@a9519863:tests/test_layer1.py
verbatim; only the import path and fixture changed. They also lock the
bypasses and false positives the v1 adversarial workflow found.
v2 additions at the bottom: SD/SE rating gating, SB transplant fidelity,
SH audit events, multi-hit severity order."""

import pytest

from app.safety.filter import CONTEXTS, FilterResult

# --- known-bad inputs: (context, text, expected category) --------------------

BLOCKED = [
    # minors — always terms + obfuscations
    ("freetext", "loli", "minors"),
    ("freetext", "L0li", "minors"),
    ("freetext", "l.o.l.i", "minors"),
    ("freetext", "looooli", "minors"),
    ("freetext", "lоli", "minors"),          # Cyrillic 'о'
    ("freetext", "ӏoli", "minors"),          # U+04CF confusable 'l'
    ("prompt", "lᴏli", "minors"),            # small-capital O (name-fold)
    ("prompt", "shoᴛa", "minors"),           # small-capital T
    ("freetext", "ᴘedo", "minors"),          # small-capital P
    ("freetext", "looli", "minors"),         # doubled letter
    ("freetext", "lolli", "minors"),
    ("freetext", "l.0.l.i", "minors"),       # leet + separators combined
    ("freetext", "l0000li", "minors"),       # digit-stretched leet
    ("freetext", "l*li", "minors"),          # masked vowel
    ("freetext", "shota", "minors"),
    ("freetext", "sh0ta", "minors"),
    ("freetext", "underage", "minors"),
    ("freetext", "under-age", "minors"),
    ("freetext", "jailbait", "minors"),
    ("freetext", "she looks barely legal", "minors"),
    ("freetext", "pedophile", "minors"),
    ("freetext", "p3do stuff", "minors"),
    ("freetext", "peԁo", "minors"),          # U+0501 confusable 'd'
    ("freetext", "lolicons gallery", "minors"),   # plural
    ("freetext", "paedophiles", "minors"),
    ("freetext", "paedos", "minors"),
    ("chat", "let's do some ageplay", "minors"),
    ("chat", "age-regression play", "minors"),
    ("name", "Loli", "minors"),
    # minors — age assertions (all contexts, 20+ line)
    ("freetext", "she is 15 years old", "minors"),
    ("freetext", "a 19-year-old elf", "minors"),
    ("freetext", "15yo", "minors"),
    ("freetext", "15 y.o.", "minors"),
    ("freetext", "15 y/o", "minors"),
    ("freetext", "15 yrs", "minors"),
    ("freetext", "9 yr old", "minors"),
    ("freetext", "aged 16", "minors"),
    ("freetext", "age: 14", "minors"),
    ("freetext", "age:15", "minors"),
    ("freetext", "she just turned 18", "minors"),
    ("freetext", "just turned eighteen", "minors"),   # written turned
    ("freetext", "turning sixteen", "minors"),
    ("freetext", "fifteen years old", "minors"),
    ("freetext", "a seventeen-year-old", "minors"),
    ("freetext", "twelve years old", "minors"),
    ("freetext", "twelve yo", "minors"),
    ("freetext", "fifteen y/o", "minors"),
    ("freetext", "she is under 18", "minors"),
    ("freetext", "under eighteen only", "minors"),    # written under
    ("freetext", "age fifteen", "minors"),
    ("freetext", "aged fifteen", "minors"),
    ("freetext", "her 16th birthday", "minors"),      # ordinal
    ("freetext", "18-25 years old", "minors"),        # range starting <20
    ("freetext", "19.0 years old", "minors"),         # decimal
    ("chat", "when she was 15", "minors"),            # R1 flagship example
    ("chat", "she is 17", "minors"),                  # copula
    ("chat", "im 17", "minors"),
    ("chat", "i'm 16 years old", "minors"),
    ("prompt", "girl, 17 years old, portrait", "minors"),
    # minors — contextual terms sexualized or in image prompts
    ("freetext", "naked teen on the bed", "minors"),
    ("freetext", "a schoolgirl undressing slowly", "minors"),
    ("chat", "naked school-girl", "minors"),
    ("prompt", "schoolgirl, blazer, classroom", "minors"),
    ("prompt", "high-school hallway", "minors"),
    ("prompt", "highschool classroom", "minors"),
    ("prompt", "teenaged girl at the beach", "minors"),
    ("prompt", "t.e.e.n at the beach", "minors"),     # spread contextual
    ("prompt", "cute child in a meadow", "minors"),
    ("prompt", "high schoolers", "minors"),           # plural of contextual term
    ("prompt", "school uniforms", "minors"),
    ("prompt", "baby girls", "minors"),
    ("freetext", "naked high schoolers", "minors"),
    # bestiality
    ("freetext", "bestiality", "bestiality"),
    ("freetext", "beastiality", "bestiality"),
    ("freetext", "zoophilia", "bestiality"),
    ("freetext", "zoosexuals forum", "bestiality"),
    ("freetext", "sex with a horse", "bestiality"),
    ("freetext", "sex with a feral wolf", "bestiality"),   # adjective insertion
    ("chat", "fucks the dog", "bestiality"),               # 3rd-person verb
    ("chat", "sex with a stallion", "bestiality"),
    # non-consent
    ("freetext", "he raped her", "noncon"),
    ("freetext", "r@pe", "noncon"),
    ("freetext", "r.a.p.e", "noncon"),
    ("freetext", "r*pe fantasy", "noncon"),               # masked vowel
    ("freetext", "molested", "noncon"),
    ("freetext", "molestations occurred", "noncon"),
    ("freetext", "nonconsensual scene", "noncon"),
    ("freetext", "took her nonconsensually", "noncon"),
    ("freetext", "a dubcon scenario", "noncon"),
    ("freetext", "dubious-consent scenario", "noncon"),   # hyphen multiword
    ("freetext", "somnophilia", "noncon"),
    ("freetext", "took her against her will", "noncon"),
    ("chat", "whether she wants it or not", "noncon"),
    ("freetext", "she was drugged and fucked", "noncon"),
    ("freetext", "forced her onto the bed and fucked her", "noncon"),
    ("chat", "coerces her into sex", "noncon"),           # inflection
    ("chat", "drugging her drink before sex", "noncon"),
    ("prompt", "unconscious woman on bed", "noncon"),
    ("prompt", "sexual-assault scene", "noncon"),         # hyphen multiword
    # self-harm
    ("chat", "how do i kill myself", "selfharm"),
    ("chat", "i want to die", "selfharm"),
    ("chat", "kys", "selfharm"),
    ("freetext", "she is suicidal", "selfharm"),
    ("freetext", "self-harm", "selfharm"),
    ("freetext", "self-harming", "selfharm"),             # inflection
    ("chat", "cut herself", "selfharm"),                  # 3rd-person reflexive
    ("chat", "starving herself", "selfharm"),
    ("chat", "takes her own life", "selfharm"),
    ("freetext", "cutting myself again", "selfharm"),
    ("freetext", "pro-ana blog", "selfharm"),
    ("chat", "tell me a good suicide method", "selfharm"),
    # slurs (including the name field — Stage 0 DoD)
    ("name", "nigger", "slurs"),
    ("name", "N1gger", "slurs"),
    ("name", "N*gger", "slurs"),                          # masked vowel
    ("name", "niɡger", "slurs"),                          # confusable 'g'
    ("name", "nɪgger", "slurs"),                          # small-capital I
    ("name", "ꜰaggot", "slurs"),                          # small-capital F
    ("name", "sandnigger", "slurs"),                      # concatenation
    ("name", "Faggot the Bold", "slurs"),
    ("name", "porch monkeys", "slurs"),                   # plural multiword
    ("name", "halfbreeds", "slurs"),
    ("freetext", "that tranny", "slurs"),
    ("chat", "you retard", "slurs"),
    # drugs
    ("freetext", "she deals cocaine", "drugs"),
    ("freetext", "crystal meth", "drugs"),
    ("freetext", "crystalmeth", "drugs"),                 # concatenation
    ("freetext", "angel-dust supply", "drugs"),           # hyphen multiword
    ("freetext", "m3th lab", "drugs"),
    ("chat", "how to cook meth", "drugs"),
    ("freetext", "fentanyl", "drugs"),
    ("freetext", "popping percocets", "drugs"),           # plural
    ("freetext", "smokes marijuana daily", "drugs"),
    # medical/legal advice extraction
    ("chat", "what dosage should I take", "advice"),
    ("chat", "is it legal to carry a knife in Ohio", "advice"),
    ("chat", "give me medical advice", "advice"),
    ("chat", "can i sue my landlord", "advice"),
    ("chat", "diagnose me, doc", "advice"),
    # misc prohibited
    ("freetext", "an incest storyline", "misc"),
    ("freetext", "necrophilia", "misc"),
    ("freetext", "he is a necrophiliac", "misc"),         # inflection
    ("freetext", "snuff-film idea", "misc"),              # hyphen multiword
    ("chat", "how to make a pipe bomb", "misc"),
]

# --- clean inputs that MUST pass (permitted adult content + ordinary text) ---

ALLOWED = [
    # explicit adult content between adults is permitted (DECISIONS.md §11)
    ("freetext", "Two adults spend an explicit, passionate night together."),
    ("freetext", "She pushes him onto the bed and they fuck, slow and deep."),
    ("chat", "I want you naked, right now."),
    ("prompt", "woman, 25 years old, silver hair, nude, reclining on silk sheets"),
    ("prompt", "muscular man, shirtless, forge in background, dramatic lighting"),
    ("freetext", "A dominant woman who enjoys consensual rope play and teasing."),
    # ordinary character-writing that keyword-blunt filters often break on
    ("freetext", "She is 25 years old, a mercenary from the northern wastes."),
    ("freetext", "A 118-year-old elf who looks ageless."),
    ("freetext", "A 111-year-old vampire countess."),
    ("freetext", "twenty-two years old"),                  # compound adult age
    ("freetext", "a thirty-five year old knight"),
    ("freetext", "a twenty-one-year-old ranger"),
    ("freetext", "twenty years old"),
    ("freetext", "Her childhood friend, now grown, runs the tavern."),
    ("freetext", "She grew up poor and left home at twenty."),
    ("freetext", "He has two kids from a previous marriage and sees them on weekends."),
    ("freetext", "As a child she watched the fireworks over the harbor every year."),
    ("freetext", "Forced to flee her homeland, she swore revenge."),
    ("freetext", "The assassin drugged the guard and slipped past the gate."),
    ("freetext", "A suicide mission to save the kingdom."),
    ("freetext", "He drinks whiskey at the tavern and smokes a pipe."),
    ("freetext", "A stern teacher at the royal academy for young nobles."),
    ("freetext", "She mounted her horse and rode north."),   # equestrian, not bestiality
    ("freetext", "He mounts his horse at dawn."),
    ("freetext", "a virgin forest where the children of the village play"),
    ("freetext", "an intimate dinner while the kids slept upstairs"),
    ("freetext", "Seduced by power, he abandoned his old friends."),
    ("freetext", "There are 5 guards at the gate."),        # copula counting FP
    ("freetext", "This is 1 of many secrets she keeps."),
    ("freetext", "The tower is 15 meters tall."),
    ("freetext", "She is 5 foot 9 and built like a soldier."),
    ("chat", "lol i think you're really cute, wanna chat more?"),  # 'lol i' != loli
    ("freetext", "The hunter shot a deer at dawn."),        # 'shot a' != shota
    ("chat", "My day was long; pour me a glass of wine."),
    ("prompt", "adult woman warrior, 30 years old, plate armor, snowfield"),
    ("prompt", "a 22-year-old university student in a lecture hall"),
    ("name", "Alexandra Vex"),
    ("name", "Kid"),                                       # contextual terms don't gate names
    ("name", "Seraphina"),
    ("name", "Cummings"),
    ("name", "Dickens"),
    ("freetext", "under 20 minutes to reach the safehouse"),
    ("freetext", "She waited 15 years for his return."),   # duration, not age
    ("freetext", "The grapes ripen in the vineyard."),     # no 'rape' hit
    ("freetext", "The torpedo struck the hull."),          # no 'pedo' hit
    ("freetext", "A therapist who lost a brother years ago and carries it quietly."),
    ("freetext", "The committee met at the university."),  # doubles not over-folded
    ("freetext", "She schools him in swordplay."),         # 'schools' verb, no minor context
]


@pytest.mark.parametrize("context,text,category", BLOCKED)
def test_blocks_known_bad(content_filter, context, text, category):
    result = content_filter.check(text, context)
    assert not result.allowed, f"should block ({category}): {text!r}"
    assert result.category == category
    assert result.matched


@pytest.mark.parametrize("context,text", ALLOWED)
def test_passes_clean(content_filter, context, text):
    result = content_filter.check(text, context)
    assert result.allowed, (
        f"false positive ({result.category}: {result.matched!r}): {text!r}"
    )


def test_empty_and_none_allowed(content_filter):
    assert content_filter.check("", "freetext").allowed
    assert content_filter.check(None, "chat").allowed
    assert content_filter.check("   ", "name").allowed


def test_unknown_context_rejected(content_filter):
    with pytest.raises(ValueError):
        content_filter.check("hello", "bogus")


def test_contexts_constant():
    assert set(CONTEXTS) == {"freetext", "chat", "prompt", "name"}


def test_check_name_helper(content_filter):
    assert content_filter.check_name("Kaelith").allowed
    assert not content_filter.check_name("sp1c").allowed


def test_result_shape(content_filter):
    result = content_filter.check("loli", "freetext")
    assert isinstance(result, FilterResult)
    data = result.to_dict()
    assert data["allowed"] is False
    assert data["category"] == "minors"
    assert "content policy" in data["message"]


def test_glued_nonascii_letter_does_not_break_boundary(content_filter):
    # A pasted Cyrillic letter glued to a slur must not defeat the name block.
    assert not content_filter.check_name("жfag").allowed
    assert not content_filter.check("cncж", "freetext").allowed


def test_proximity_window_is_directional_both_ways(content_filter):
    # sexual term before the contextual term
    assert not content_filter.check("nude photos of a teen", "freetext").allowed
    # sexual term after the contextual term
    assert not content_filter.check("a teen posing nude", "freetext").allowed
    # far apart (> window) — passes as freetext even with sexual vocab present
    filler = "the caravan crossed the dunes for many days and nights " * 4
    text = "the kid waved goodbye. " + filler + " later, two adults undress."
    assert content_filter.check(text, "freetext").allowed


# --- §D/§E rating gating over the real data ---------------------------------
# drugs is the one unlocked_at list (mature); every other category is floor.

DRUGS_SAMPLE = "she deals cocaine"
FLOOR_SAMPLES = [
    ("minors", "loli"),
    ("bestiality", "zoophilia"),
    ("noncon", "somnophilia"),
    ("selfharm", "self-harm"),
    ("slurs", "tranny"),
    ("advice", "give me medical advice"),
    ("misc", "necrophilia"),
]


def test_drugs_blocks_at_standard(content_filter):
    result = content_filter.check(DRUGS_SAMPLE, "freetext", rating="standard")
    assert not result.allowed and result.category == "drugs"


@pytest.mark.parametrize("rating", ["mature", "explicit"])
def test_drugs_unlocked_at_mature_and_above(content_filter, rating):
    assert content_filter.check(DRUGS_SAMPLE, "freetext", rating=rating).allowed


@pytest.mark.parametrize("category,text", FLOOR_SAMPLES)
def test_every_floor_category_still_blocks_at_explicit(
    content_filter, category, text
):
    result = content_filter.check(text, "freetext", rating="explicit")
    assert not result.allowed, f"{category} must be floor-enforced"
    assert result.category == category


def test_default_rating_is_standard(content_filter):
    # §E: a surface with no record rating gets everything applied.
    assert not content_filter.check(DRUGS_SAMPLE, "freetext").allowed


def test_unknown_rating_rejected(content_filter):
    with pytest.raises(ValueError):
        content_filter.check("hello", "freetext", rating="bogus")


# --- §B transplant fidelity: the real file set and per-file counts ----------
# The checkpoint's "nine lists" claim is WRONG against the pin: reality is
# 10 blocklist files + the proximity vocabulary (SESSION_REPORT_O4 §B).
# Counts pinned from a9519863 — a drifted count means the transplant or a
# later edit changed list contents without touching this lock.

EXPECTED_FILES = {
    "advice_always.txt": (2, 10),
    "bestiality_always.txt": (9, 2),
    "drugs_always.txt": (28, 3),
    "minors_always.txt": (42, 16),
    "minors_contextual.txt": (59, 0),
    "misc_always.txt": (9, 1),
    "noncon_always.txt": (38, 4),
    "noncon_contextual.txt": (44, 0),
    "selfharm_always.txt": (17, 11),
    "sexual_context.txt": (95, 0),
    "slurs.txt": (69, 4),
}


def test_transplanted_file_set_and_term_counts():
    from app.safety.filter import _parse_file
    from tests.conftest import SAFETY_DATA_DIR

    files = sorted(p.name for p in SAFETY_DATA_DIR.glob("*.txt"))
    assert files == sorted(EXPECTED_FILES)
    for name, (terms, regexes) in EXPECTED_FILES.items():
        _, t, r = _parse_file(SAFETY_DATA_DIR / name)
        assert (len(t), len(r)) == (terms, regexes), name


def test_every_list_loads_with_declared_scope(content_filter):
    loaded = {
        w.file_name: (w.category, w.mode, w.unlocked_at)
        for w in content_filter._lists
    }
    assert loaded == {
        "minors_always.txt": ("minors", "always", None),
        "minors_contextual.txt": ("minors", "contextual", None),
        "bestiality_always.txt": ("bestiality", "always", None),
        "noncon_always.txt": ("noncon", "always", None),
        "noncon_contextual.txt": ("noncon", "contextual", None),
        "selfharm_always.txt": ("selfharm", "always", None),
        "slurs.txt": ("slurs", "always", None),
        "drugs_always.txt": ("drugs", "always", "mature"),
        "advice_always.txt": ("advice", "always", None),
        "misc_always.txt": ("misc", "always", None),
    }


def test_multi_hit_reports_most_severe_category(content_filter):
    # minors ranks above drugs in the severity order; a text hitting both
    # must report minors, stably (the v1 registry-order behavior).
    result = content_filter.check("loli on cocaine", "freetext")
    assert result.category == "minors"


# --- §H audit: refusals and only refusals, vocabulary-blind -----------------


class RecordingSink:
    def __init__(self):
        self.events = []

    def log(self, kind, **payload):
        self.events.append((kind, payload))


@pytest.fixture
def audited_filter():
    from app.safety import SafetyFilter
    from tests.conftest import SAFETY_DATA_DIR

    sink = RecordingSink()
    return SafetyFilter(SAFETY_DATA_DIR, audit_sink=sink), sink


def test_refusal_emits_one_vocabulary_blind_event(audited_filter):
    f, sink = audited_filter
    f.check("loli", "freetext", surface="story_text")
    assert sink.events == [
        ("filter_block", {"context": "freetext", "category": "minors",
                          "surface": "story_text"})
    ]
    # vocabulary-blind: neither the matched term nor the text appears.
    payload = sink.events[0][1]
    assert "loli" not in repr(payload)


def test_allowed_check_emits_nothing(audited_filter):
    f, sink = audited_filter
    f.check("a quiet evening by the fire", "freetext", surface="story_text")
    f.check("", "freetext")
    assert sink.events == []


def test_absent_surface_event_carries_context_only(audited_filter):
    # Gate ruling 2026-07-23: the caller passes the surface code; absent,
    # the event carries the context only.
    f, sink = audited_filter
    f.check("loli", "prompt")
    assert sink.events == [
        ("filter_block", {"context": "prompt", "category": "minors"})
    ]


def test_null_sink_is_silent_default(tmp_path):
    from app.safety import NullAuditSink, SafetyFilter
    from tests.conftest import SAFETY_DATA_DIR

    f = SafetyFilter(SAFETY_DATA_DIR)  # default sink
    assert isinstance(f._audit, NullAuditSink)
    assert f._audit.log("filter_block", context="freetext") is None


def test_audit_log_appends_jsonl(tmp_path):
    import json

    from app.safety import AuditLog

    log = AuditLog(tmp_path / "logs")
    log.log("filter_block", context="freetext", category="minors",
            surface="story_text")
    lines = log.path_for_today().read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["kind"] == "filter_block"
    assert event["category"] == "minors"
    assert "ts" in event


def test_audit_log_disabled_writes_nothing(tmp_path):
    from app.safety import AuditLog

    log = AuditLog(tmp_path / "logs", enabled=False)
    log.log("filter_block", context="freetext")
    assert not (tmp_path / "logs").exists()
