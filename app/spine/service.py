"""The spine app (O5_INPUTS §F): thin orchestration over the libraries.

Auth (builder detail, recorded): every request must carry the per-run
token in the ``X-Spine-Token`` header, enforced by pure ASGI middleware
BEFORE routing — so no surface answers untokened, including unknown
paths. FastAPI's docs/openapi endpoints are disabled outright: no
unauthenticated surface (§C) and no surface the contract didn't name.

Refusals: exception handlers turn every ``RecordError`` into the
structured body ``{code, subject, message}`` with the library's code and
subject verbatim (§F.4). Audit lifecycle lines (§H) are emitted by the
app's lifespan: ``spine_start`` (version, data root) on startup,
``spine_stop`` on clean shutdown only — a crash writes no stop line,
which is what makes the clean line mean something.
"""

from __future__ import annotations

import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.record.errors import RecordError
from app.spine.bootstrap import SpineContext
from app.spine.errors import (
    AUTH_INVALID,
    AUTH_MISSING,
    RECORD_NOT_FOUND,
    RecordNotFound,
    error_body,
    status_for,
)
from app.spine.routes_catalog import router as catalog_router
from app.spine.routes_ledger import router as ledger_router
from app.spine.routes_records import router as records_router

TOKEN_HEADER = "X-Spine-Token"
_TOKEN_HEADER_ASGI = TOKEN_HEADER.lower().encode()


class TokenAuthMiddleware:
    """Pure ASGI: the check runs before routing touches anything."""

    def __init__(self, app, token: str):
        self.app = app
        self._token = token.encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        supplied = None
        for name, value in scope.get("headers", ()):
            if name == _TOKEN_HEADER_ASGI:
                supplied = value
                break
        if supplied is None:
            refusal = JSONResponse(
                status_code=401,
                content={
                    "code": AUTH_MISSING,
                    "subject": TOKEN_HEADER,
                    "message": f"[{AUTH_MISSING}] the {TOKEN_HEADER} header "
                    f"is required on every request",
                },
            )
        elif not secrets.compare_digest(supplied, self._token):
            refusal = JSONResponse(
                status_code=401,
                content={
                    "code": AUTH_INVALID,
                    "subject": TOKEN_HEADER,
                    "message": f"[{AUTH_INVALID}] the supplied token does "
                    f"not match this run",
                },
            )
        else:
            await self.app(scope, receive, send)
            return
        await refusal(scope, receive, send)


def build_app(ctx: SpineContext) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        ctx.audit.log(
            "spine_start", version=ctx.version, data_root=str(ctx.paths.data_root)
        )
        yield
        ctx.audit.log("spine_stop")

    app = FastAPI(
        title="CharacterForge2 spine",
        version=ctx.version,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.ctx = ctx

    app.include_router(catalog_router)
    app.include_router(records_router)
    app.include_router(ledger_router)

    @app.exception_handler(RecordError)
    async def _record_error(request, exc: RecordError):
        return JSONResponse(status_code=status_for(exc), content=error_body(exc))

    @app.exception_handler(RecordNotFound)
    async def _record_not_found(request, exc: RecordNotFound):
        return JSONResponse(
            status_code=404,
            content={
                "code": RECORD_NOT_FOUND,
                "subject": exc.character_id,
                "message": str(exc),
            },
        )

    app.add_middleware(TokenAuthMiddleware, token=ctx.token)
    return app
