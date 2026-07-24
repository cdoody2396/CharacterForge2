"""Service + catalog endpoints (O5_INPUTS §F.1/§F.2).

The catalog listing serves the raw facts a library or editor view
needs — every group (free_text and session included) with ratings,
tags, retired status, and provenance. The creator view (§F.3) is the
curated surface; this one hides nothing.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.options.catalog import Group, Option
from app.spine.bootstrap import SpineContext

router = APIRouter()


def _ctx(request: Request) -> SpineContext:
    return request.app.state.ctx


def _option_facts(option: Option) -> dict:
    return {
        "id": option.id,
        "label": option.label,
        "rating": option.rating,
        "tags": list(option.tags),
        "status": option.status,
        "retired": option.retired,
        "color": option.color,
        "thumb": option.thumb,
        "image_text": option.image_text,
        "chat_text": option.chat_text,
        "source_file": option.source_file,
    }


def _group_facts(group: Group) -> dict:
    return {
        "id": group.id,
        "label": group.label,
        "kind": group.kind,
        "home": group.home,
        "scene_overridable": group.scene_overridable,
        "required": group.required,
        "priority": group.priority,
        "max_picks": group.max_picks,
        "feeds": group.feeds,
        "max_chars": group.max_chars,
        "visible_when": group.visible_when,
        "section": group.section,
        "order": group.order,
        "hint": group.hint,
        "tags": list(group.tags),
        "hidden": group.hidden,
        "sources": list(group.sources),
        "options": [_option_facts(option) for option in group.options],
    }


@router.get("/health")
def health(request: Request) -> dict:
    ctx = _ctx(request)
    return {
        "status": "ok",
        "version": ctx.version,
        "data_root": str(ctx.paths.data_root),
    }


@router.get("/catalog")
def catalog(request: Request) -> dict:
    ctx = _ctx(request)
    return {"groups": [_group_facts(group) for group in ctx.catalog.groups()]}
