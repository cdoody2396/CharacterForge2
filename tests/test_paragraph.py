"""N7 appearance-paragraph drafter: deterministic over the identity
selections' labels. The MECHANISM is contract; the sentence wording is
ILLUSTRATIVE (asserted only through labels appearing, never exact prose)."""

import pytest

from app.record.paragraph import draft_appearance_paragraph
from tests.conftest import record_catalog


@pytest.fixture
def catalog(tmp_path):
    return record_catalog(tmp_path)


def test_deterministic_same_selections_same_paragraph(catalog):
    selections = {"species": "cat", "mane": "long_mane", "fur_color": "red"}
    first = draft_appearance_paragraph(catalog, selections)
    second = draft_appearance_paragraph(catalog, dict(selections))
    assert first == second
    assert first  # non-empty for real selections


def test_selection_order_does_not_matter_catalog_order_does(catalog):
    a = {"species": "cat", "fur_color": "red"}
    b = {"fur_color": "red", "species": "cat"}  # same facts, other insert order
    assert draft_appearance_paragraph(catalog, a) == draft_appearance_paragraph(
        catalog, b
    )


def test_labels_not_ids_are_spoken(catalog):
    text = draft_appearance_paragraph(catalog, {"mane": "long_mane"})
    assert "Long Mane" in text
    assert "long_mane" not in text


def test_changing_a_selection_changes_the_paragraph(catalog):
    red = draft_appearance_paragraph(catalog, {"species": "cat", "fur_color": "red"})
    blue = draft_appearance_paragraph(catalog, {"species": "cat", "fur_color": "blue"})
    assert red != blue


def test_persona_selections_do_not_appear(catalog):
    text = draft_appearance_paragraph(
        catalog, {"species": "cat", "callname": "soft", "traits": ["brave"]}
    )
    # identity labels in, persona labels out — N7 is looks only
    assert "Cat" in text
    assert "Soft" not in text and "Brave" not in text


def test_pick_many_labels_keep_pick_order(catalog):
    ab = draft_appearance_paragraph(catalog, {"old_look": ["current", "extra"]})
    ba = draft_appearance_paragraph(catalog, {"old_look": ["extra", "current"]})
    assert ab != ba  # order-as-picked is meaning (N2)
    assert ab.index("Current") < ab.index("Extra")


def test_retired_options_still_speak(catalog):
    # Decision 6: retired options stay functional for existing characters.
    text = draft_appearance_paragraph(catalog, {"old_look": ["legacy"]})
    assert "Legacy" in text


def test_empty_selections_empty_paragraph(catalog):
    assert draft_appearance_paragraph(catalog, {}) == ""
