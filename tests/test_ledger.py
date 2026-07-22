"""N8/N10 ledger skeleton: sidecar receipt schema, the SQLite index and
rebuild(), R4 staleness (identity derived, variable cached with receipts
winning), the R5 exactly-touched hook, and the grade-derivation seam.

Synthetic sidecars only — this stage renders nothing (N8)."""

import json
import sqlite3

import pytest

from app.ledger import Ledger, NullRingProvider, derive_grade, load_receipt
from app.ledger.errors import ReceiptError
from tests.conftest import new_record, record_catalog


def sidecar(directory, name, **overrides):
    """Write one synthetic sidecar receipt and return its path."""
    data = {
        "format": 1,
        "character_id": "test_char",
        "kind": "portrait",
        "identity_version": 1,
        "method": "txt2img@1",
        "variables": {"traits": ["brave"]},
        "rating_at_render": "standard",
        "created": "2026-07-22T00:00:00+00:00",
        "artifact_path": f"art/{name}.png",
        "content_hash": "sha256:0000",
    }
    data.update(overrides)
    path = directory / f"{name}.receipt.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def refuse_receipt(path, code):
    with pytest.raises(ReceiptError) as excinfo:
        load_receipt(path)
    assert excinfo.value.code == code, excinfo.value


@pytest.fixture
def ledger(tmp_path):
    led = Ledger(tmp_path / "ledger.db")
    yield led
    led.close()


# --- sidecar receipt schema -------------------------------------------------


def test_receipt_loads(tmp_path):
    receipt = load_receipt(sidecar(tmp_path, "p1"))
    assert receipt.character_id == "test_char"
    assert receipt.identity_version == 1
    assert receipt.variables == {"traits": ["brave"]}
    assert receipt.sidecar_path.endswith("p1.receipt.json")


def test_explicit_empty_variables_legal(tmp_path):
    # §A6: an explicit-empty receipt states "no variables used" — legal,
    # and it can never go variable-stale.
    receipt = load_receipt(sidecar(tmp_path, "p1", variables={}))
    assert receipt.variables == {}


def test_missing_variables_refused(tmp_path):
    path = sidecar(tmp_path, "p1")
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["variables"]
    path.write_text(json.dumps(data), encoding="utf-8")
    refuse_receipt(path, "RECEIPT_MISSING_KEY")


def test_null_in_receipt_refused(tmp_path):
    refuse_receipt(sidecar(tmp_path, "p1", method=None), "RECEIPT_NULL")


def test_unknown_key_refused_comment_keys_legal(tmp_path):
    refuse_receipt(sidecar(tmp_path, "p1", extra="x"), "RECEIPT_UNKNOWN_KEY")
    receipt = load_receipt(sidecar(tmp_path, "p2", _note="synthetic fixture"))
    assert receipt.kind == "portrait"


@pytest.mark.parametrize("version", [0, "1", True, 1.5])
def test_bad_identity_version_refused(tmp_path, version):
    refuse_receipt(
        sidecar(tmp_path, "p1", identity_version=version), "RECEIPT_BAD_TYPE"
    )


def test_bad_rating_refused(tmp_path):
    refuse_receipt(
        sidecar(tmp_path, "p1", rating_at_render="ultra"), "RECEIPT_BAD_TYPE"
    )


def test_bad_variable_shape_refused(tmp_path):
    refuse_receipt(
        sidecar(tmp_path, "p1", variables={"traits": []}), "RECEIPT_BAD_TYPE"
    )


def test_wrong_format_refused(tmp_path):
    refuse_receipt(sidecar(tmp_path, "p1", format=2), "RECEIPT_BAD_TYPE")


def test_active_flag_loads_and_defaults_false(tmp_path):
    # The AR ledger-minimum active flag (O3_INPUTS_N8_LADDER.md): optional,
    # absent reads false.
    assert load_receipt(sidecar(tmp_path, "p1")).active is False
    assert load_receipt(sidecar(tmp_path, "p2", active=True)).active is True


def test_non_bool_active_refused(tmp_path):
    refuse_receipt(sidecar(tmp_path, "p1", active="yes"), "RECEIPT_BAD_TYPE")


def test_invalid_json_refused(tmp_path):
    path = tmp_path / "bad.receipt.json"
    path.write_text("{not json", encoding="utf-8")
    refuse_receipt(path, "RECEIPT_INVALID_JSON")


# --- N10: database scope ----------------------------------------------------


def test_wal_pragma_and_schema_version(tmp_path, ledger):
    conn = sqlite3.connect(ledger.db_path)
    try:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
    finally:
        conn.close()


def test_only_the_ledger_index_table_exists(tmp_path, ledger):
    # N10: transcripts, memory, jobs tables belong to their own stages.
    names = [
        row[0]
        for row in ledger._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    ]
    assert names == ["ledger_index"]


# --- R4: identity staleness (derived, no marker) ----------------------------


def test_identity_stale_derived_from_active_pointer(tmp_path, ledger):
    p1 = sidecar(tmp_path, "v1_art", identity_version=1)
    p2 = sidecar(tmp_path, "v2_art", identity_version=2)
    ledger.index_receipt(load_receipt(p1))
    ledger.index_receipt(load_receipt(p2))
    # derived at query time: moving the pointer changes the answer with
    # zero writes — there is no marker to update (or to rot)
    assert ledger.identity_stale("test_char", 1) == [str(p2)]
    assert ledger.identity_stale("test_char", 2) == [str(p1)]


# --- R4: variable staleness (cached marker, receipts win) -------------------


def test_variable_stale_cache_primed_on_index(tmp_path, ledger):
    path = sidecar(tmp_path, "p1", variables={"traits": ["brave"]})
    ledger.index_receipt(load_receipt(path), {"traits": ["calm"]})
    assert ledger.variable_stale_marked("test_char") == [str(path)]


def test_marker_is_cache_receipts_win(tmp_path, ledger):
    path = sidecar(tmp_path, "p1", variables={"traits": ["brave"]})
    ledger.index_receipt(load_receipt(path), {"traits": ["brave"]})
    assert ledger.variable_stale_marked("test_char") == []
    # corrupt the CACHE behind the ledger's back
    ledger._conn.execute("UPDATE ledger_index SET variable_stale = 1")
    ledger._conn.commit()
    assert ledger.variable_stale_marked("test_char") == [str(path)]  # lies
    # recompute from the receipt copies: receipts win, the lie is corrected
    stale = ledger.recompute_variable_stale("test_char", {"traits": ["brave"]})
    assert stale == []
    assert ledger.variable_stale_marked("test_char") == []


def test_cleared_value_is_a_mismatch(tmp_path, ledger):
    path = sidecar(tmp_path, "p1", variables={"traits": ["brave"]})
    ledger.index_receipt(load_receipt(path), {"traits": ["brave"]})
    stale = ledger.recompute_variable_stale("test_char", {})  # value cleared
    assert stale == [str(path)]


# --- R5: edits mark exactly what they touched -------------------------------


def test_mark_persona_edit_touches_exactly(tmp_path, ledger):
    touched_path = sidecar(tmp_path, "a", variables={"traits": ["brave"]})
    other_path = sidecar(tmp_path, "b", variables={"callname": "soft"})
    ledger.index_receipt(
        load_receipt(touched_path), {"traits": ["brave"], "callname": "soft"}
    )
    ledger.index_receipt(
        load_receipt(other_path), {"traits": ["brave"], "callname": "soft"}
    )
    # corrupt b's marker: if the edit re-evaluated it, the corruption would
    # be corrected — its survival proves only touched receipts re-evaluate
    ledger._conn.execute(
        "UPDATE ledger_index SET variable_stale = 1 WHERE sidecar_path = ?",
        (str(other_path),),
    )
    ledger._conn.commit()
    ledger.mark_persona_edit(
        "test_char", ("traits",), {"traits": ["calm"], "callname": "soft"}
    )
    marked = ledger.variable_stale_marked("test_char")
    assert str(touched_path) in marked  # touched: re-evaluated, now stale
    assert str(other_path) in marked  # untouched: corruption survived (R5)


def test_hook_wired_to_persona_mutations(tmp_path, ledger):
    catalog = record_catalog(tmp_path)
    record = new_record()
    record.set_selection(catalog, "species", "cat")
    record.set_selection(catalog, "mane", "long_mane")
    record.set_selection(catalog, "callname", "soft")
    record.set_selection(catalog, "traits", ["brave"])
    record.finalize(catalog)
    path = sidecar(tmp_path, "p1", variables={"traits": ["brave"]})
    ledger.index_receipt(load_receipt(path), {"traits": ["brave"]})
    ledger.attach(record)
    record.set_selection(catalog, "traits", ["calm"])  # persona edit
    assert ledger.variable_stale_marked("test_char") == [str(path)]
    record.set_selection(catalog, "traits", ["brave"])  # edited back
    assert ledger.variable_stale_marked("test_char") == []


# --- rebuild ----------------------------------------------------------------


def test_rebuild_reconstructs_equivalent_index(tmp_path):
    sidecars = tmp_path / "sidecars"
    sidecars.mkdir()
    sidecar(sidecars, "a", variables={"traits": ["brave"]})
    sidecar(sidecars, "b", variables={"callname": "soft"}, identity_version=2)
    sidecar(sidecars, "c", variables={}, character_id="other_char")
    current = {"traits": ["calm"], "callname": "soft"}  # traits edited since
    incremental = Ledger(tmp_path / "incremental.db")
    for name in ("a", "b", "c"):
        receipt = load_receipt(sidecars / f"{name}.receipt.json")
        values = current if receipt.character_id == "test_char" else {}
        incremental.index_receipt(receipt, values)
    rebuilt = Ledger(tmp_path / "rebuilt.db")
    count = rebuilt.rebuild([sidecars], {"test_char": current, "other_char": {}})
    assert count == 3
    assert rebuilt.rows() == incremental.rows()  # AR: the index is derived
    incremental.close()
    rebuilt.close()


def test_rebuild_replaces_stale_index_state(tmp_path, ledger):
    sidecars = tmp_path / "sidecars"
    sidecars.mkdir()
    ghost = sidecar(sidecars, "ghost")
    ledger.index_receipt(load_receipt(ghost))
    ghost.unlink()  # artifact receipt deleted on disk
    sidecar(sidecars, "real")
    assert ledger.rebuild([sidecars]) == 1
    assert [row[0] for row in ledger.rows()] == [
        str(sidecars / "real.receipt.json")
    ]


def test_rebuild_ignores_non_receipt_json(tmp_path, ledger):
    sidecars = tmp_path / "sidecars"
    sidecars.mkdir()
    (sidecars / "notes.json").write_text("{}", encoding="utf-8")
    sidecar(sidecars, "real")
    assert ledger.rebuild([sidecars]) == 1


# --- the grade ladder (O3_INPUTS_N8_LADDER.md) ------------------------------


class FakeRingProvider:
    """Test provider standing in for the owed ring-derivation rule."""

    def __init__(self, canonical_set, rings=frozenset({"portrait_ring"})):
        self._canonical_set = canonical_set
        self._rings = rings

    def ring_membership(self, character_id):
        return self._rings

    def has_canonical_set(self, character_id, ledger):
        return self._canonical_set


def lora_sidecar(directory, name, **overrides):
    overrides.setdefault("kind", "identity_lora")
    overrides.setdefault("variables", {})
    return sidecar(directory, name, **overrides)


def test_derive_grade_null_provider_is_honest(tmp_path, ledger):
    ledger.index_receipt(load_receipt(sidecar(tmp_path, "p1")))
    result = derive_grade(
        "test_char",
        ledger=ledger,
        ring_provider=NullRingProvider(),
        active_version=1,
    )
    assert result.grade is None  # no guess, ever
    assert result.determinable is False
    assert result.g1_determinable is False  # the Null provider cannot know
    assert result.ladder_decided is True
    assert result.evidence["floor"] == "G0"  # the decided floor still holds
    assert result.evidence["artifacts"] == 1
    assert result.evidence["identity_stale"] == 0
    assert "rings" not in result.evidence  # unknown is not "no rings"
    assert "at least G0" in result.notes and "owed" in result.notes


def test_null_provider_still_reports_g2_evidence(tmp_path, ledger):
    # N8: with G1 undeterminable the derivation reports G0/G2 evidence only.
    ledger.index_receipt(load_receipt(lora_sidecar(tmp_path, "l1", active=True)))
    result = derive_grade(
        "test_char", ledger=ledger, ring_provider=NullRingProvider()
    )
    assert result.grade is None and result.determinable is False
    assert result.evidence["active_loras"] == 1
    assert "G2 evidence" in result.notes


def test_grade_g0_no_canonical_set(tmp_path, ledger):
    result = derive_grade(
        "test_char", ledger=ledger, ring_provider=FakeRingProvider(False)
    )
    assert (result.grade, result.determinable) == ("G0", True)
    assert result.g1_determinable is True
    assert result.evidence["rings"] == ["portrait_ring"]


def test_grade_g1_canonical_set_without_lora(tmp_path, ledger):
    ledger.index_receipt(load_receipt(sidecar(tmp_path, "ring_frame")))
    result = derive_grade(
        "test_char", ledger=ledger, ring_provider=FakeRingProvider(True)
    )
    assert (result.grade, result.determinable) == ("G1", True)


def test_grade_g2_canonical_set_plus_active_lora(tmp_path, ledger):
    ledger.index_receipt(load_receipt(lora_sidecar(tmp_path, "l1", active=True)))
    result = derive_grade(
        "test_char", ledger=ledger, ring_provider=FakeRingProvider(True)
    )
    assert (result.grade, result.determinable) == ("G2", True)
    assert result.evidence["active_loras"] == 1


def test_inactive_lora_is_not_g2(tmp_path, ledger):
    # AR: multiple LoRAs per version, ONE active — inactive entries carry
    # no grade force.
    ledger.index_receipt(load_receipt(lora_sidecar(tmp_path, "l1")))
    result = derive_grade(
        "test_char", ledger=ledger, ring_provider=FakeRingProvider(True)
    )
    assert result.grade == "G1"
    assert result.evidence["active_loras"] == 0


def test_another_characters_lora_does_not_count(tmp_path, ledger):
    ledger.index_receipt(
        load_receipt(
            lora_sidecar(tmp_path, "l1", active=True, character_id="other_char")
        )
    )
    result = derive_grade(
        "test_char", ledger=ledger, ring_provider=FakeRingProvider(True)
    )
    assert result.grade == "G1"


def test_lora_without_canonical_set_is_the_floor_with_open_call_named(
    tmp_path, ledger
):
    # Cumulative ladder: no set, no G1, no G2 — ring-skip-to-LoRA is an
    # image-section execution call the derivation names, never pre-empts.
    ledger.index_receipt(load_receipt(lora_sidecar(tmp_path, "l1", active=True)))
    result = derive_grade(
        "test_char", ledger=ledger, ring_provider=FakeRingProvider(False)
    )
    assert (result.grade, result.determinable) == ("G0", True)
    assert "ring-skip" in result.notes


def test_grade_is_derived_never_stored(tmp_path):
    # AR: no stored per-entry grade exists to contradict the rollup — the
    # receipt schema refuses a grade key outright.
    refuse_receipt(sidecar(tmp_path, "p1", grade="G2"), "RECEIPT_UNKNOWN_KEY")
