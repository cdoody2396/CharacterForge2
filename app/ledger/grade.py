"""Grade derivation seam (N8).

DECIDED here: grade is DERIVED, never stored (no grade field exists on the
record); the derivation takes an INJECTED ring-membership provider; the
Null provider makes G1 undeterminable and the derivation SAYS SO honestly
— it never guesses. The image section supplies the real provider.

NOT_DECIDED (recorded in SESSION_REPORT_O3): the ladder itself — what G0,
G1, and G2 each mean, and what evidence produces them. The planning gate
chose to paste the checkpoint's ladder definition into this session, but
the text never arrived through the question UI; per the agreed fallback
this module builds the SEAM ONLY. ``derive_grade`` therefore returns an
honestly-undeterminable result carrying the evidence it CAN see (artifact
counts and staleness from the ledger, ring membership from the provider)
and ``ladder_decided=False``. Filling in ``_apply_ladder`` when the
definition lands is the whole remaining work — the surface will not move.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.ledger.index import Ledger

GRADES = ("G0", "G1", "G2")


class NullRingProvider:
    """The honest stand-in until the image section supplies ring
    derivation: membership is UNKNOWN, not empty — ``None`` says "I cannot
    know", never "no rings"."""

    def ring_membership(self, character_id: str) -> frozenset[str] | None:
        return None


@dataclass(frozen=True)
class GradeDerivation:
    """The derivation's honest result. ``grade`` stays None whenever the
    ladder cannot be applied; ``notes`` says exactly why."""

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
    """Derive the character's grade from ledger evidence and ring
    membership. With the ladder NOT_DECIDED this returns the gathered
    evidence and an honest non-answer; see the module docstring."""
    artifacts = ledger.artifacts_for(character_id)
    membership = ring_provider.ring_membership(character_id)
    g1_determinable = membership is not None
    evidence: dict = {
        "artifacts": len(artifacts),
        "kinds": sorted({row["kind"] for row in artifacts}),
        "variable_stale_marked": len(ledger.variable_stale_marked(character_id)),
    }
    if active_version is not None:
        evidence["identity_stale"] = len(
            ledger.identity_stale(character_id, active_version)
        )
    if g1_determinable:
        evidence["rings"] = sorted(membership)
    grade, determinable, notes = _apply_ladder(evidence, g1_determinable)
    return GradeDerivation(
        character_id=character_id,
        grade=grade,
        determinable=determinable,
        g1_determinable=g1_determinable,
        ladder_decided=False,
        evidence=evidence,
        notes=notes,
    )


def _apply_ladder(
    evidence: dict, g1_determinable: bool
) -> tuple[str | None, bool, str]:
    """THE SEAM: the ladder's G0/G1/G2 rules land here when the planning
    chat supplies them (NOT_DECIDED at O3 — build nothing, guess nothing).
    Until then every derivation is honestly undeterminable."""
    note = (
        "ladder NOT_DECIDED at O3: G0/G2 evidence gathered, no rule maps it "
        "to a grade yet"
    )
    if not g1_determinable:
        note += "; G1 undeterminable (Null ring provider - N8)"
    return None, False, note
