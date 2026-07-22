"""Error taxonomy for the ledger (N8). Spellings builder's, coverage
decided: every sidecar-schema law fails distinctly, naming the file."""

from __future__ import annotations

RECEIPT_INVALID_JSON = "RECEIPT_INVALID_JSON"
RECEIPT_NULL = "RECEIPT_NULL"
RECEIPT_UNKNOWN_KEY = "RECEIPT_UNKNOWN_KEY"
RECEIPT_MISSING_KEY = "RECEIPT_MISSING_KEY"
RECEIPT_BAD_TYPE = "RECEIPT_BAD_TYPE"


class ReceiptError(ValueError):
    """A sidecar receipt file does not conform to the N8 schema."""

    def __init__(self, file: str, code: str, subject: str | None, message: str):
        self.file = file
        self.code = code
        self.subject = subject
        super().__init__(f"{file}: [{code}] {message}")
