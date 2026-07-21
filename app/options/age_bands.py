"""Age-band lookup loader (§8, Decision 10 pt 4).

Single file (``app/data/age_bands.json`` — ships empty-of-data; content
arrives at harvest). Laws: bands ordered, integer bounds, first ``min`` = 20,
contiguous (``min`` = previous ``max`` + 1), no overlaps or gaps, exactly one
final open band (no ``max``). Any violation: format error. ``image_text`` is
required on every band (kickoff-pinned decision, 2026-07-21). Bands are
system-selected by record age; no user-facing widget exists.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.options import errors as E
from app.options.errors import AgeBandFormatError

_FILE_KEYS = frozenset({"format", "bands"})
_BAND_KEYS = frozenset({"min", "max", "image_text"})

AGE_FLOOR = 20  # §8: first band's min, always


@dataclass(frozen=True)
class AgeBand:
    min: int
    max: int | None  # None = the single final open band
    image_text: str

    def contains(self, age: int) -> bool:
        return age >= self.min and (self.max is None or age <= self.max)


def select_band(bands: tuple[AgeBand, ...], age: int) -> AgeBand | None:
    """The band a record age falls in (system-selected, §8), or None below
    the floor."""
    for band in bands:
        if band.contains(age):
            return band
    return None


def _visible_keys(data: dict) -> list[str]:
    # §1.9 comment keys are legal and ignored anywhere.
    return [k for k in data if not (isinstance(k, str) and k.startswith("_"))]


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def load_age_bands(path: Path | str) -> tuple[AgeBand, ...]:
    """Load and validate the age-band file, raising
    :class:`AgeBandFormatError` on any §8 violation."""
    path = Path(path)
    file = path.name

    def err(code: str, message: str) -> AgeBandFormatError:
        return AgeBandFormatError(file, code, message)

    try:
        text = path.read_text(encoding="utf-8-sig")  # BOM tolerated
    except UnicodeDecodeError as exc:
        raise err(E.BAD_ENCODING, f"file is not UTF-8: {exc}") from exc
    except OSError as exc:
        raise err(E.BAND_FILE_MISSING, f"cannot read file: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise err(E.INVALID_JSON, f"invalid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise err(E.NOT_AN_OBJECT, "file must be one JSON object")
    for key in _visible_keys(data):
        if key not in _FILE_KEYS:
            raise err(E.UNKNOWN_KEY, f"file has unknown key {key!r}")
    if "format" not in data:
        raise err(E.MISSING_KEY, "file is missing 'format'")
    if not _is_int(data["format"]) or data["format"] != 1:
        raise err(E.BAD_FORMAT_VERSION, f"'format' must equal 1, got {data['format']!r}")
    if "bands" not in data or not isinstance(data["bands"], list):
        raise err(E.MISSING_KEY, "file must carry a 'bands' list")

    bands: list[AgeBand] = []
    for i, raw in enumerate(data["bands"]):
        label = f"band {i}"
        if not isinstance(raw, dict):
            raise err(E.BAD_KEY_TYPE, f"{label} must be an object")
        for key in _visible_keys(raw):
            if key not in _BAND_KEYS:
                raise err(E.UNKNOWN_KEY, f"{label} has unknown key {key!r}")
        if "min" not in raw or not _is_int(raw["min"]):
            raise err(E.BAND_BAD_BOUND, f"{label} 'min' must be an integer")
        lo = raw["min"]
        hi = None
        if "max" in raw:
            if not _is_int(raw["max"]):
                raise err(E.BAND_BAD_BOUND, f"{label} 'max' must be an integer")
            hi = raw["max"]
            if hi < lo:
                raise err(E.BAND_BAD_BOUND, f"{label} has max {hi} < min {lo}")
        image_text = raw.get("image_text")
        if not isinstance(image_text, str) or not image_text:
            raise err(
                E.BAND_MISSING_IMAGE_TEXT,
                f"{label} must carry a non-empty 'image_text'",
            )
        bands.append(AgeBand(min=lo, max=hi, image_text=image_text))

    # Structure laws (§8): floor, contiguity, exactly one final open band.
    if not bands or bands[-1].max is not None:
        raise err(
            E.BAND_NO_OPEN_BAND,
            "exactly one final open band (no 'max') is required",
        )
    if bands[0].min != AGE_FLOOR:
        raise err(
            E.BAND_WRONG_FLOOR,
            f"first band must start at min {AGE_FLOOR}, got {bands[0].min}",
        )
    for prev, band in zip(bands, bands[1:]):
        if prev.max is None:
            raise err(
                E.BAND_OPEN_NOT_LAST,
                f"band starting {prev.min} is open but not last; only the "
                f"final band may omit 'max'",
            )
        expected = prev.max + 1
        if band.min > expected:
            raise err(
                E.BAND_GAP,
                f"gap between max {prev.max} and min {band.min}; bands must "
                f"be contiguous (min = previous max + 1)",
            )
        if band.min < expected:
            raise err(
                E.BAND_OVERLAP,
                f"band starting {band.min} overlaps previous band ending "
                f"{prev.max}; bands must be contiguous (min = previous max + 1)",
            )
    return tuple(bands)
