"""Appearance-paragraph drafter (N7).

MECHANISM (DECIDED): a deterministic assembler over the identity-layer
selections' LABELS (Decision 2: labels are the raw material), walking the
catalog in load order — same selections, same catalog, same paragraph,
every time. Drafted at finalization, re-drafted at every re-finalization;
user editing is blocked per N6 until the safety stage lands.

SENTENCE WORDING (ILLUSTRATIVE): every literal string below — the joiners,
the punctuation, the sentence template — is placeholder prose standing in
for a later authoring pass. Do NOT treat the wording as final; only the
determinism and the labels-in, paragraph-out mechanism are contract.
"""

from __future__ import annotations

from app.options.catalog import Catalog


def draft_appearance_paragraph(catalog: Catalog, identity_selections: dict) -> str:
    """Deterministically assemble the appearance paragraph from the
    identity-layer selections' labels.

    Groups walk in catalog load order; pick_many labels keep pick order
    (N2: order-as-picked). Retired options resolve (Decision 6). Only
    identity-home pick groups contribute — persona is not looks, and the
    looks free-text slot is NOT an input (N7: labels only).
    """
    fragments: list[str] = []
    for group in catalog.groups():
        if group.home != "identity" or group.is_free_text:
            continue
        value = identity_selections.get(group.id)
        if not value:
            continue
        picked = [value] if isinstance(value, str) else list(value)
        labels = []
        for option_id in picked:
            option = group.resolve(option_id)
            if option is not None:  # unknown ids are inert (N9), never spoken
                labels.append(option.label)
        if not labels:
            continue
        # ILLUSTRATIVE wording: "<Group label>: <label>, <label>".
        fragments.append(f"{group.label}: {', '.join(labels)}")
    if not fragments:
        return ""
    # ILLUSTRATIVE wording: a single semicolon-joined sentence.
    return "; ".join(fragments) + "."
