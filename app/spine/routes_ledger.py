"""Ledger endpoints (O5_INPUTS §F.5): per-character artifact and
staleness queries, and the ``derive_grade`` passthrough — the honestly
undeterminable G1 included (the ring provider stays the null one until
the image-identity section delivers the ring-derivation rule).
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Request

from app.ledger.grade import NullRingProvider, derive_grade
from app.spine.bootstrap import SpineContext

router = APIRouter()


def _ctx(request: Request) -> SpineContext:
    return request.app.state.ctx


@router.get("/records/{character_id}/artifacts")
def artifacts(character_id: str, request: Request) -> dict:
    ctx = _ctx(request)
    ctx.store.ensure_exists(character_id)
    with ctx.store.open_ledger() as ledger:
        rows = ledger.artifacts_for(character_id)
    return {"artifacts": [dict(row) for row in rows]}


@router.get("/records/{character_id}/staleness")
def staleness(character_id: str, request: Request) -> dict:
    ctx = _ctx(request)
    record, _orphans, _raw = ctx.store.load(character_id)
    with ctx.store.open_ledger() as ledger:
        return {
            "identity_stale": ledger.identity_stale(
                character_id, record.active_version
            ),
            "variable_stale_marked": ledger.variable_stale_marked(character_id),
        }


@router.get("/records/{character_id}/grade")
def grade(character_id: str, request: Request) -> dict:
    ctx = _ctx(request)
    record, _orphans, _raw = ctx.store.load(character_id)
    with ctx.store.open_ledger() as ledger:
        derivation = derive_grade(
            character_id,
            ledger=ledger,
            ring_provider=NullRingProvider(),
            active_version=record.active_version,
        )
    return asdict(derivation)
