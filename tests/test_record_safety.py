"""The opened N6 seam (O4_INPUTS §F/§G) against the REAL maintained word
data: slots accept/block/overlong/clear, name clearing + revalidation +
finalization interplay, draft paragraph edits with the author marker, the
load-law amendments, committed-version immutability, and §H audit wiring
through the record surfaces. The no-filter direction (every O3 refusal
stands) lives in test_safety_seam.py, untouched from O3."""

import json

import pytest

from app.record import load_record, save_record
from app.record.errors import (
    GateRefusal,
    RecordFormatError,
    SafetyNotInstalledError,
)
from app.record import errors as E
from app.record.model import (
    FREE_TEXT_MAX_CHARS,
    PARAGRAPH_MAX_CHARS,
)
from tests.conftest import new_record, record_catalog, refuse_gate

BLOCKED_TEXT = "rape fantasy"          # noncon, floor
BLOCKED_NAME = "Faggot the Bold"       # slur; charset-legal
CLEAN_TEXT = "tall, green-eyed, a scar over one brow"


def finalizable(catalog):
    r = new_record()
    r.set_selection(catalog, "species", "robot")
    r.set_selection(catalog, "callname", "soft")
    return r


# --- free-text slots: accept / block / overlong / clear ----------------------


def test_looks_text_accepts_and_stores_on_draft(tmp_path, content_filter):
    cat = record_catalog(tmp_path)
    r = finalizable(cat)
    r.set_looks_text(CLEAN_TEXT, content_filter)
    assert r.draft.looks_text == CLEAN_TEXT
    v = r.finalize(cat, content_filter)
    assert v.looks_text == CLEAN_TEXT


def test_story_text_accepts_and_stores_on_persona(content_filter):
    r = new_record()
    r.set_story_text("grew up dockside, quick with a joke", content_filter)
    assert r.persona.story_text == "grew up dockside, quick with a joke"


@pytest.mark.parametrize("setter", ["set_looks_text", "set_story_text"])
def test_slot_block_names_category_and_term(content_filter, setter):
    r = new_record()
    exc = refuse_gate(
        E.TEXT_BLOCKED, getattr(r, setter), BLOCKED_TEXT, content_filter
    )
    # §G: the refusal names the category and the matched term.
    assert "noncon" in str(exc) and "rape" in str(exc)
    # record unchanged — §G refuses the whole write, never redacts.
    assert r.draft.looks_text is None and r.persona.story_text is None


@pytest.mark.parametrize("setter", ["set_looks_text", "set_story_text"])
def test_slot_overlong_refuses(content_filter, setter):
    r = new_record()
    refuse_gate(
        E.FREE_TEXT_OVERLONG,
        getattr(r, setter),
        "x" * (FREE_TEXT_MAX_CHARS + 1),
        content_filter,
    )


def test_slot_at_cap_passes(content_filter):
    r = new_record()
    r.set_story_text("x" * FREE_TEXT_MAX_CHARS, content_filter)
    assert len(r.persona.story_text) == FREE_TEXT_MAX_CHARS


@pytest.mark.parametrize("setter", ["set_looks_text", "set_story_text"])
def test_slot_empty_string_refuses(content_filter, setter):
    # "" would be a second spelling of cleared (N2); clearing is its own API.
    r = new_record()
    refuse_gate(E.BAD_VALUE_TYPE, getattr(r, setter), "   ", content_filter)


def test_clear_paths_are_explicit_and_idempotent(content_filter):
    r = new_record()
    r.set_looks_text(CLEAN_TEXT, content_filter)
    r.set_story_text(CLEAN_TEXT, content_filter)
    r.clear_looks_text()
    r.clear_story_text()
    assert r.draft.looks_text is None and r.persona.story_text is None
    r.clear_looks_text()  # clearing the cleared is a no-op
    r.clear_story_text()


def test_looks_slot_is_draft_scoped(tmp_path, content_filter):
    cat = record_catalog(tmp_path)
    r = finalizable(cat)
    r.finalize(cat, content_filter)  # draft closes
    refuse_gate(
        E.IDENTITY_NO_DRAFT, r.set_looks_text, CLEAN_TEXT, content_filter
    )
    refuse_gate(E.IDENTITY_NO_DRAFT, r.clear_looks_text)


def test_slot_rating_gating_drugs_at_mature(content_filter):
    # §E/§F interplay: the drugs list is unlocked_at mature, so the same
    # story text refuses at 'standard' and stores at 'mature'.
    r = new_record()
    refuse_gate(
        E.TEXT_BLOCKED, r.set_story_text, "she deals cocaine", content_filter
    )
    r.raise_rating("mature")
    r.set_story_text("she deals cocaine", content_filter)
    assert r.persona.story_text == "she deals cocaine"


# --- name: clear on pass, blocked refusal, revalidation ----------------------


def test_name_pass_stores_clear(content_filter):
    r = new_record()
    r.set_name("Mira", content_filter)
    assert r.persona.name == "Mira"
    assert r.persona.name_safety == "clear"


def test_name_block_refuses_record_unchanged(content_filter):
    r = new_record()
    exc = refuse_gate(E.NAME_BLOCKED, r.set_name, BLOCKED_NAME, content_filter)
    assert "slurs" in str(exc)
    assert r.persona.name is None and r.persona.name_safety is None


def test_name_charset_law_still_first(content_filter):
    r = new_record()
    refuse_gate(E.NAME_CHARSET, r.set_name, "M1ra", content_filter)


def test_filterless_name_write_still_pends():
    r = new_record()
    r.set_name("Mira")
    assert r.persona.name_safety == "pending"


def test_revalidate_clears_a_pending_name(content_filter):
    r = new_record()
    r.set_name("Mira")  # pending
    r.revalidate_name(content_filter)
    assert r.persona.name_safety == "clear"


def test_revalidate_blocked_pending_name_refuses(content_filter):
    r = new_record()
    r.set_name(BLOCKED_NAME)  # filterless write pends even a blockable name
    refuse_gate(E.NAME_BLOCKED, r.revalidate_name, content_filter)
    assert r.persona.name_safety == "pending"  # blocked is never stored


def test_revalidate_is_idempotent_when_nothing_pends(content_filter):
    r = new_record()
    r.revalidate_name(content_filter)  # no name at all — no-op
    r.set_name("Mira", content_filter)
    r.revalidate_name(content_filter)  # already clear — no-op
    assert r.persona.name_safety == "clear"


def test_revalidate_without_filter_refuses_honestly():
    with pytest.raises(SafetyNotInstalledError):
        new_record().revalidate_name()


# --- finalization runs revalidation (§F) -------------------------------------


def test_finalize_clears_pending_name(tmp_path, content_filter):
    cat = record_catalog(tmp_path)
    r = finalizable(cat)
    r.set_name("Mira")  # pending
    r.finalize(cat, content_filter)
    assert r.persona.name_safety == "clear"


def test_finalize_refuses_blocked_pending_name(tmp_path, content_filter):
    cat = record_catalog(tmp_path)
    r = finalizable(cat)
    r.set_name(BLOCKED_NAME)
    refuse_gate(E.NAME_BLOCKED, r.finalize, cat, content_filter)
    # nothing committed, the draft survives, the name still pends.
    assert r.identity_versions == [] and r.draft is not None
    assert r.persona.name_safety == "pending"


def test_finalize_without_filter_keeps_pending(tmp_path):
    # §F law: with no filter the O3 behavior stands — pending survives.
    cat = record_catalog(tmp_path)
    r = finalizable(cat)
    r.set_name("Mira")
    r.finalize(cat)
    assert r.persona.name_safety == "pending"


# --- the paragraph edit path (§F) --------------------------------------------


def test_paragraph_edit_commits_verbatim_with_user_author(
    tmp_path, content_filter
):
    cat = record_catalog(tmp_path)
    r = finalizable(cat)
    r.edit_appearance_paragraph("My own words about her look.", content_filter)
    v = r.finalize(cat, content_filter)
    assert v.appearance_paragraph == "My own words about her look."
    assert v.paragraph_author == "user"


def test_next_finalization_redrafts(tmp_path, content_filter):
    # user text never silently survives an identity change (§F).
    cat = record_catalog(tmp_path)
    r = finalizable(cat)
    r.edit_appearance_paragraph("My own words.", content_filter)
    r.finalize(cat, content_filter)
    r.open_draft()
    assert r.draft.paragraph_edit is None  # the edit did not carry over
    v2 = r.finalize(cat, content_filter)
    assert v2.paragraph_author == "drafter"
    assert v2.appearance_paragraph != "My own words."


def test_paragraph_edit_filtered(content_filter):
    r = new_record()
    exc = refuse_gate(
        E.TEXT_BLOCKED, r.edit_appearance_paragraph, BLOCKED_TEXT, content_filter
    )
    assert "noncon" in str(exc)
    assert r.draft.paragraph_edit is None


def test_paragraph_edit_overlong_refuses(content_filter):
    r = new_record()
    refuse_gate(
        E.PARAGRAPH_OVERLONG,
        r.edit_appearance_paragraph,
        "x" * (PARAGRAPH_MAX_CHARS + 1),
        content_filter,
    )


def test_paragraph_edit_needs_open_draft(tmp_path, content_filter):
    cat = record_catalog(tmp_path)
    r = finalizable(cat)
    r.finalize(cat, content_filter)
    refuse_gate(
        E.IDENTITY_NO_DRAFT,
        r.edit_appearance_paragraph,
        "words",
        content_filter,
    )


def test_committed_versions_stay_frozen(tmp_path, content_filter):
    # N1: nothing above rewrites history — the committed paragraph, author,
    # and looks text are untouched by later edits on a new draft.
    cat = record_catalog(tmp_path)
    r = finalizable(cat)
    r.set_looks_text(CLEAN_TEXT, content_filter)
    v1 = r.finalize(cat, content_filter)
    frozen = (v1.appearance_paragraph, v1.paragraph_author, v1.looks_text)
    r.open_draft()
    r.set_looks_text("a different look entirely", content_filter)
    r.edit_appearance_paragraph("New words.", content_filter)
    r.finalize(cat, content_filter)
    kept = r.identity_versions[0]
    assert (
        kept.appearance_paragraph,
        kept.paragraph_author,
        kept.looks_text,
    ) == frozen


# --- load laws (§F amendments) -----------------------------------------------


def roundtrip(tmp_path, record, catalog, mutate=None):
    path = tmp_path / "r.json"
    save_record(record, path)
    if mutate is not None:
        data = json.loads(path.read_text(encoding="utf-8"))
        mutate(data)
        path.write_text(json.dumps(data), encoding="utf-8")
    return load_record(path, catalog)


def test_load_accepts_pending_and_clear(tmp_path, content_filter):
    cat = record_catalog(tmp_path)
    r = new_record()
    r.set_name("Mira", content_filter)
    loaded, _ = roundtrip(tmp_path, r, cat)
    assert loaded.persona.name_safety == "clear"
    r2 = new_record()
    r2.set_name("Mira")
    loaded2, _ = roundtrip(tmp_path, r2, cat)
    assert loaded2.persona.name_safety == "pending"  # loads never mutate


@pytest.mark.parametrize("value", ["blocked", "cleared", "", 1])
def test_load_refuses_other_name_safety_values(tmp_path, value):
    cat = record_catalog(tmp_path)
    r = new_record()
    r.set_name("Mira")

    def mutate(data):
        data["persona"]["name_safety"] = value

    with pytest.raises(RecordFormatError) as excinfo:
        roundtrip(tmp_path, r, cat, mutate)
    assert excinfo.value.code in (E.RECORD_BAD_TYPE, E.RECORD_NULL)


def test_load_absent_author_reads_drafter(tmp_path, content_filter):
    cat = record_catalog(tmp_path)
    r = finalizable(cat)
    r.finalize(cat, content_filter)

    def mutate(data):
        del data["identity_versions"][0]["paragraph_author"]  # an O3 file

    loaded, _ = roundtrip(tmp_path, r, cat, mutate)
    assert loaded.identity_versions[0].paragraph_author == "drafter"


def test_load_roundtrips_user_author_and_draft_edit(tmp_path, content_filter):
    cat = record_catalog(tmp_path)
    r = finalizable(cat)
    r.edit_appearance_paragraph("My words.", content_filter)
    r.finalize(cat, content_filter)
    r.open_draft()
    r.edit_appearance_paragraph("Pending new words.", content_filter)
    loaded, _ = roundtrip(tmp_path, r, cat)
    assert loaded.identity_versions[0].paragraph_author == "user"
    assert loaded.draft.paragraph_edit == "Pending new words."


def test_load_refuses_unknown_author(tmp_path, content_filter):
    cat = record_catalog(tmp_path)
    r = finalizable(cat)
    r.finalize(cat, content_filter)

    def mutate(data):
        data["identity_versions"][0]["paragraph_author"] = "editor"

    with pytest.raises(RecordFormatError) as excinfo:
        roundtrip(tmp_path, r, cat, mutate)
    assert excinfo.value.code == E.RECORD_BAD_TYPE


def test_load_refuses_bad_paragraph_edit_type(tmp_path):
    cat = record_catalog(tmp_path)
    r = new_record()

    def mutate(data):
        data["draft_identity"]["paragraph_edit"] = 7

    with pytest.raises(RecordFormatError) as excinfo:
        roundtrip(tmp_path, r, cat, mutate)
    assert excinfo.value.code == E.RECORD_BAD_TYPE


# --- §H audit through the record surfaces ------------------------------------


class RecordingSink:
    def __init__(self):
        self.events = []

    def log(self, kind, **payload):
        self.events.append((kind, payload))


def test_record_refusals_emit_surface_coded_events(tmp_path):
    from app.safety import SafetyFilter
    from tests.conftest import SAFETY_DATA_DIR

    sink = RecordingSink()
    safety = SafetyFilter(SAFETY_DATA_DIR, audit_sink=sink)
    r = new_record()
    with pytest.raises(GateRefusal):
        r.set_story_text(BLOCKED_TEXT, safety)
    with pytest.raises(GateRefusal):
        r.set_name(BLOCKED_NAME, safety)
    r.set_story_text("a quiet dockside childhood", safety)  # no event
    surfaces = [payload["surface"] for _, payload in sink.events]
    assert surfaces == ["story_text", "name"]
    # vocabulary-blind: no matched term in any payload.
    assert "rape" not in repr(sink.events)
