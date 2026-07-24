"""Record endpoints (O5_INPUTS §F.4): create · list · load · N4-gated
mutations · rating raise · finalize (N5) · the O4 filtered surfaces.

Every handler is thin: acquire the store's per-character serialization,
call the record layer, persist atomically, serve the saved file's JSON
(the record layer's declared on-disk shape) plus the N9 orphan report.
Refusals propagate as ``RecordError`` and reach the client with code and
subject verbatim via the service-level handlers. Filtered writes always
pass the real safety filter (§G) — ``SAFETY_NOT_INSTALLED`` cannot arise
through the spine.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.ledger.grade import NullRingProvider, derive_grade
from app.spine.bootstrap import SpineContext
from app.spine.creator_view import assemble
from app.spine.schemas import (
    AgeBody,
    CreateBody,
    NameBody,
    RatingBody,
    SelectionBody,
    TextBody,
)

router = APIRouter()


def _ctx(request: Request) -> SpineContext:
    return request.app.state.ctx


def _record_payload(raw: dict, orphans) -> dict:
    return {"record": raw, "orphans": [asdict(entry) for entry in orphans]}


@router.post("/records", status_code=201)
def create_record(body: CreateBody, request: Request):
    ctx = _ctx(request)
    character_id, raw = ctx.store.create(body.age)
    return JSONResponse(status_code=201, content=_record_payload(raw, []))


@router.get("/records")
def list_records(request: Request) -> dict:
    ctx = _ctx(request)
    entries = []
    for character_id in ctx.store.list_ids():
        record, orphans, _raw = ctx.store.load(character_id)
        with ctx.store.open_ledger() as ledger:
            grade = derive_grade(
                character_id,
                ledger=ledger,
                ring_provider=NullRingProvider(),
                active_version=record.active_version,
            )
        entries.append(
            {
                "character_id": record.character_id,
                "name": record.persona.name,
                "rating": record.rating,
                "active_version": record.active_version,
                "grade": {
                    "grade": grade.grade,
                    "determinable": grade.determinable,
                    "g1_determinable": grade.g1_determinable,
                },
                "orphan_count": len(orphans),
            }
        )
    return {"records": entries}


@router.get("/records/{character_id}")
def load_record(character_id: str, request: Request) -> dict:
    ctx = _ctx(request)
    _record, orphans, raw = ctx.store.load(character_id)
    return _record_payload(raw, orphans)


@router.get("/records/{character_id}/creator-view")
def creator_view(character_id: str, request: Request) -> dict:
    ctx = _ctx(request)
    record, _orphans, _raw = ctx.store.load(character_id)
    return {
        "character_id": record.character_id,
        "rating": record.rating,
        "groups": assemble(ctx.catalog, record),
    }


# -- header + selection mutations (N4) ---------------------------------------


@router.put("/records/{character_id}/age")
def set_age(character_id: str, body: AgeBody, request: Request) -> dict:
    ctx = _ctx(request)
    _record, orphans, raw = ctx.store.mutate(
        character_id, lambda record: record.set_age(body.age)
    )
    return _record_payload(raw, orphans)


@router.post("/records/{character_id}/rating")
def raise_rating(character_id: str, body: RatingBody, request: Request) -> dict:
    ctx = _ctx(request)
    _record, orphans, raw = ctx.store.mutate(
        character_id, lambda record: record.raise_rating(body.rating)
    )
    return _record_payload(raw, orphans)


@router.post("/records/{character_id}/selections")
def set_selection(character_id: str, body: SelectionBody, request: Request) -> dict:
    ctx = _ctx(request)
    _record, orphans, raw = ctx.store.mutate(
        character_id,
        lambda record: record.set_selection(ctx.catalog, body.group_id, body.value),
    )
    return _record_payload(raw, orphans)


@router.delete("/records/{character_id}/selections/{group_id}")
def clear_selection(character_id: str, group_id: str, request: Request) -> dict:
    ctx = _ctx(request)
    _record, orphans, raw = ctx.store.mutate(
        character_id,
        lambda record: record.clear_selection(ctx.catalog, group_id),
    )
    return _record_payload(raw, orphans)


# -- draft / finalization (N5) -----------------------------------------------


@router.post("/records/{character_id}/draft")
def open_draft(character_id: str, request: Request) -> dict:
    ctx = _ctx(request)
    _record, orphans, raw = ctx.store.mutate(
        character_id, lambda record: record.open_draft()
    )
    return _record_payload(raw, orphans)


@router.post("/records/{character_id}/finalize")
def finalize(character_id: str, request: Request) -> dict:
    ctx = _ctx(request)
    _record, orphans, raw = ctx.store.mutate(
        character_id,
        lambda record: record.finalize(ctx.catalog, safety=ctx.safety),
    )
    return _record_payload(raw, orphans)


# -- the O4 filtered surfaces (§F.4) -----------------------------------------


@router.put("/records/{character_id}/name")
def set_name(character_id: str, body: NameBody, request: Request) -> dict:
    ctx = _ctx(request)
    _record, orphans, raw = ctx.store.mutate(
        character_id,
        lambda record: record.set_name(body.name, safety=ctx.safety),
    )
    return _record_payload(raw, orphans)


@router.post("/records/{character_id}/name/revalidate")
def revalidate_name(character_id: str, request: Request) -> dict:
    ctx = _ctx(request)
    _record, orphans, raw = ctx.store.mutate(
        character_id, lambda record: record.revalidate_name(ctx.safety)
    )
    return _record_payload(raw, orphans)


@router.put("/records/{character_id}/looks-text")
def set_looks_text(character_id: str, body: TextBody, request: Request) -> dict:
    ctx = _ctx(request)
    _record, orphans, raw = ctx.store.mutate(
        character_id,
        lambda record: record.set_looks_text(body.text, safety=ctx.safety),
    )
    return _record_payload(raw, orphans)


@router.delete("/records/{character_id}/looks-text")
def clear_looks_text(character_id: str, request: Request) -> dict:
    ctx = _ctx(request)
    _record, orphans, raw = ctx.store.mutate(
        character_id, lambda record: record.clear_looks_text()
    )
    return _record_payload(raw, orphans)


@router.put("/records/{character_id}/story-text")
def set_story_text(character_id: str, body: TextBody, request: Request) -> dict:
    ctx = _ctx(request)
    _record, orphans, raw = ctx.store.mutate(
        character_id,
        lambda record: record.set_story_text(body.text, safety=ctx.safety),
    )
    return _record_payload(raw, orphans)


@router.delete("/records/{character_id}/story-text")
def clear_story_text(character_id: str, request: Request) -> dict:
    ctx = _ctx(request)
    _record, orphans, raw = ctx.store.mutate(
        character_id, lambda record: record.clear_story_text()
    )
    return _record_payload(raw, orphans)


@router.put("/records/{character_id}/appearance-paragraph")
def edit_appearance_paragraph(
    character_id: str, body: TextBody, request: Request
) -> dict:
    ctx = _ctx(request)
    _record, orphans, raw = ctx.store.mutate(
        character_id,
        lambda record: record.edit_appearance_paragraph(body.text, safety=ctx.safety),
    )
    return _record_payload(raw, orphans)
