"""The service spine (O5): one local process owning the libraries at
runtime — options catalog, record store, safety filter, audit log,
ledger — behind an authenticated, loopback-only, server-authoritative
API (O5_INPUTS §A).

The spine is the single evaluator (§B): visibility, rating
admissibility, required flags, retired-option handling, widget
derivation, and gate refusals are computed here and served as facts.
It adds orchestration only — law lives in the libraries it wraps.
"""

from app.spine.bootstrap import SpineContext, build_context
from app.spine.server import SpineServer, run
from app.spine.service import build_app
from app.spine.version import SPINE_VERSION

__all__ = [
    "SPINE_VERSION",
    "SpineContext",
    "SpineServer",
    "build_app",
    "build_context",
    "run",
]
