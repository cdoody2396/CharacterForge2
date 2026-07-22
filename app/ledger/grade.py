"""Grade derivation (N8) — the ladder, decided.

The ladder arrived from the planning gate after the O3 push (verbatim in
O3_INPUTS_N8_LADDER.md, from CHECKPOINT_creation-scoping_S1 as amended;
AR markers carry decided force):

- **G0 — basic** is the FLOOR of every character (fully playable,
  imagery on-demand).
- **G1 — canonical** = G0 + the canonical shot set (reference core +
  presentation ring, one pass).
- **G2 — anchored** = G1 + identity LoRA(s) trained from the reference
  core, ONE active.

Grade is NEVER stored — it is a rollup derived from ledger contents,
exactly two inputs: **(has-canonical-set, has-active-LoRA)** (AR: a
stored per-entry grade could contradict the derived one).

The seams that remain owed to the image-identity section:

- The ring-membership derivation rule ("derives from record contents, not
  a fixed list") — behind the injected ring provider. The
  :class:`NullRingProvider` answers ``None`` = "cannot know", never "no
  rings", so ``has_canonical_set`` is undeterminable, G1 with it, and the
  derivation says so honestly, reporting G0/G2 evidence only (N8).
- The ring-skip-to-LoRA execution call: an active LoRA WITHOUT the
  canonical set derives G0 under the decided cumulative table, with the
  open call named in the notes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.ledger.index import Ledger

GRADES = ("G0", "G1", "G2")
GRADE_FLOOR = "G0"  # decided: the floor of every character

# The machine id this module recognizes as an identity-LoRA ledger entry
# (checkpoint: "identity LoRA(s)"). Spelling is the builder's, recorded in
# SESSION_REPORT_O3; only synthetic fixtures use it until the image section
# writes real receipts.
IDENTITY_LORA_KIND = "identity_lora"


class NullRingProvider:
    """The honest stand-in until the image section supplies the ring
    derivation rule: every answer is UNKNOWN, not empty — ``None`` says
    "I cannot know", never "no rings" / "no set"."""

    def ring_membership(self, character_id: str) -> frozenset[str] | None:
        return None

    def has_canonical_set(self, character_id: str, ledger: Ledger) -> bool | None:
        return None


@dataclass(frozen=True)
class GradeDerivation:
    """The derivation's honest result. ``grade`` is None only when the
    rollup is undeterminable — and then the character still holds the
    decided floor (``evidence["floor"]`` = G0)."""

    character_id: str
    grade: str | None
    determinable: bool
    g1_determinable: bool  # False under the Null provider (N8)
    ladder_decided: bool
    evidence: dict = field(default_factory=dict)
    notes: str = ""


def derive_grade(
    character_id: str,
    *,
    ledger: Ledger,
    ring_provider,
    active_version: int | None = None,
) -> GradeDerivation:
    """Roll the character's grade up from ledger contents: exactly
    (has-canonical-set, has-active-LoRA), per the decided ladder."""
    artifacts = ledger.artifacts_for(character_id)
    membership = ring_provider.ring_membership(character_id)
    has_set = ring_provider.has_canonical_set(character_id, ledger)
    active_loras = [
        row["sidecar_path"]
        for row in artifacts
        if row["kind"] == IDENTITY_LORA_KIND and row["active"]
    ]
    evidence: dict = {
        "floor": GRADE_FLOOR,
        "artifacts": len(artifacts),
        "kinds": sorted({row["kind"] for row in artifacts}),
        "active_loras": len(active_loras),
        "variable_stale_marked": len(ledger.variable_stale_marked(character_id)),
    }
    if active_version is not None:
        evidence["identity_stale"] = len(
            ledger.identity_stale(character_id, active_version)
        )
    if membership is not None:
        evidence["rings"] = sorted(membership)
    grade, determinable, notes = _apply_ladder(has_set, bool(active_loras))
    return GradeDerivation(
        character_id=character_id,
        grade=grade,
        determinable=determinable,
        g1_determinable=has_set is not None,
        ladder_decided=True,
        evidence=evidence,
        notes=notes,
    )


def _apply_ladder(
    has_canonical_set: bool | None, has_active_lora: bool
) -> tuple[str | None, bool, str]:
    """The decided rollup (O3_INPUTS_N8_LADDER.md): cumulative rungs over
    exactly two inputs. ``has_canonical_set`` is three-valued — ``None``
    means the ring provider cannot know (the derivation rule is owed)."""
    if has_canonical_set is None:
        note = (
            "grade undeterminable above the floor: G1 needs the canonical "
            "set, whose ring derivation is owed to the image-identity "
            "section (Null ring provider); character is at least G0"
        )
        if has_active_lora:
            note += "; an active identity LoRA exists (G2 evidence)"
        return None, False, note
    if not has_canonical_set:
        if has_active_lora:
            # Cumulative table: no canonical set, no G1, so no G2 — the
            # ring-skip-to-LoRA path is an image-section execution call
            # the ladder does not pre-empt.
            return (
                "G0",
                True,
                "G0: active identity LoRA present WITHOUT the canonical "
                "set — ring-skip-to-LoRA is an open image-section call; "
                "the decided cumulative ladder grades this the floor",
            )
        return "G0", True, "G0 (the floor): no canonical set"
    if has_active_lora:
        return "G2", True, "G2: canonical set + an active identity LoRA"
    return "G1", True, "G1: canonical set, no active identity LoRA"
