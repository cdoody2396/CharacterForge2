"""N6 safety seam: free-text and paragraph setters refuse honestly until
the safety stage lands; name alone is writable under the charset law, both
directions; every name write leaves name_safety pending."""

import pytest

from app.record.errors import SafetyNotInstalledError
from tests.conftest import new_record, refuse_gate


def test_looks_slot_refuses_until_safety_lands():
    with pytest.raises(SafetyNotInstalledError):
        new_record().set_looks_text("tall, green-eyed")


def test_story_slot_refuses_until_safety_lands():
    with pytest.raises(SafetyNotInstalledError):
        new_record().set_story_text("grew up dockside")


def test_paragraph_edit_refuses_until_safety_lands():
    with pytest.raises(SafetyNotInstalledError):
        new_record().edit_appearance_paragraph("my own words")


# --- the name law, legal direction ------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "Mara",
        "Anne-Marie O'Neil Jr.",
        "Zoë",
        "José del Río",
        "A",  # 1 char is the floor
        "N" * 60,  # 60 chars is the ceiling
        "Naḿe",  # combining mark (category Mn)
    ],
)
def test_legal_names_accepted(name):
    record = new_record()
    record.set_name(name)
    assert record.persona.name == name
    assert record.persona.name_safety == "pending"


# --- the name law, refusing direction ---------------------------------------


def test_empty_name_refused():
    refuse_gate("NAME_LENGTH", new_record().set_name, "")


def test_overlong_name_refused():
    refuse_gate("NAME_LENGTH", new_record().set_name, "N" * 61)


@pytest.mark.parametrize(
    "name",
    [
        "R2D2",  # digits are not letters
        "O’Neil",  # curly quote is not the apostrophe
        "Two\nLines",
        "semi;colon",
        "star*",
        "snake_case",
        "\U0001f431",  # emoji cat is not a letter
    ],
)
def test_illegal_names_refused(name):
    record = new_record()
    refuse_gate("NAME_CHARSET", record.set_name, name)
    assert record.persona.name is None  # unchanged on refusal


def test_non_string_name_refused():
    refuse_gate("BAD_VALUE_TYPE", new_record().set_name, 42)


def test_name_safety_pending_set_on_every_write():
    record = new_record()
    record.set_name("Mara")
    # simulate the future safety stage having cleared it, then a re-write
    record.persona.name_safety = "cleared_v1"
    record.set_name("Marra")
    assert record.persona.name_safety == "pending"
