"""Safety subsystem (O4_INPUTS) — the v1 Layer-1 filter, transplanted.

The deterministic word filter (:mod:`filter`), its normalization engine
(:mod:`normalize`), the §C data-load error taxonomy (:mod:`errors`), and
the vocabulary-blind audit sink (:mod:`audit`). The maintained word data
lives under ``app/safety/data/``.

Layer 2 (model gating) attaches at the chat/image sections; app-wide
write-site placement belongs to the service spine (O5). The filter is
passed where it is used — never a module global (§F).
"""

from app.safety.audit import AuditLog, NullAuditSink
from app.safety.errors import SafetyDataError
from app.safety.filter import CONTEXTS, PROXIMITY_WINDOW, FilterResult, SafetyFilter

__all__ = [
    "AuditLog",
    "CONTEXTS",
    "FilterResult",
    "NullAuditSink",
    "PROXIMITY_WINDOW",
    "SafetyDataError",
    "SafetyFilter",
]
