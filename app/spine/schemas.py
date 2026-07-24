"""Request bodies (spellings builder's, recorded).

Deliberately permissive typing: the N4 gate is the validator. A wrong-
typed age, value, rating, name, or text must REACH the gate and refuse
with the gate's own code, verbatim — not be intercepted by a framework
422. Addressing fields (``group_id``) stay typed: they name a thing
like a URL path does; the gate still owns unknown-id refusals.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CreateBody(BaseModel):
    age: Any = None


class AgeBody(BaseModel):
    age: Any = None


class RatingBody(BaseModel):
    rating: Any = None


class SelectionBody(BaseModel):
    group_id: str
    value: Any = None


class NameBody(BaseModel):
    name: Any = None


class TextBody(BaseModel):
    text: Any = None
