"""The deterministic word filter (O4_INPUTS §C/§D/§E) — v1's Layer 1,
transplanted.

Matching machinery carries from `CharacterForge@a9519863:app/safety/
layer1.py`: term parsing (``#`` comments, ``re:`` regex lines), the
joiner / spread / doubled-letter / leetspeak / digit-safe match families,
ASCII edge guards, plural tolerance, the proximity logic, ``FilterResult``.
No model, no network, no judgment calls — pure blocklist/regex gating on
normalized text.

What changed from v1 (§B):

- The hardcoded ``_CATEGORY_FILES`` registry is gone. Word files
  self-declare their scope in-file (§C): ``category`` (machine id),
  ``mode`` (``always`` | ``contextual``), ``enforcement`` (``floor`` |
  ``unlocked_at: mature`` | ``unlocked_at: explicit``). Declaration lines
  spell ``#! key: value`` (builder spelling, recorded) — they are ``#``
  comments to the v1 term parser, so the v1 line format survives intact.
- Rating-aware enforcement (§E): ``floor`` lists apply at every rating;
  an ``unlocked_at: R`` list is skipped when the passed rating is at or
  above R. Default rating is ``standard`` (everything applies).
- The filter is constructed over an explicit data directory and passed
  where it is used — v1's module-global convenience (``get_filter`` and
  friends) does not carry (§F: never a module global).
- An injected audit sink (§H): a blocked check emits one vocabulary-blind
  event — context, category, surface code; never the matched term or the
  text. Default sink is the no-op :class:`~app.safety.audit.NullAuditSink`.

Category semantics carry unchanged: ``always`` lists block in every
applied context; ``contextual`` lists block outright in image-``prompt``
context, block in ``freetext``/``chat`` contexts only when sexual
vocabulary (``sexual_context.txt``, the declared proximity list) occurs
within ``PROXIMITY_WINDOW`` characters, and are never applied to ``name``
context.

Layer 1 errs toward blocking: false positives are accepted by design and
the data files remain the tuning surface (§E). Loading is fail-loud (§C
law 2): the filter never starts over a bad data directory — see
:mod:`app.safety.errors`.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from app.options.loader import VALID_RATINGS
from app.safety import errors as E
from app.safety import normalize as norm
from app.safety.audit import NullAuditSink
from app.safety.errors import SafetyDataError

# Max characters between a contextual term and sexual vocabulary for a
# proximity block. Roughly one sentence.
PROXIMITY_WINDOW = 120

CONTEXTS = ("freetext", "chat", "prompt", "name")

_RATING_ORDER = {rating: i for i, rating in enumerate(VALID_RATINGS)}

# The proximity-vocabulary file (§C law 4): its NAME is contract-pinned.
PROXIMITY_FILE = "sexual_context.txt"

# §C declaration spellings (header spelling ILLUSTRATIVE, recorded):
#   #! category: drugs
#   #! mode: always
#   #! enforcement: unlocked_at: mature
#   #! role: proximity_vocabulary        (sexual_context.txt only)
_DECL_PREFIX = "#!"
_LIST_DECL_KEYS = ("category", "mode", "enforcement")
_MODES = ("always", "contextual")
_PROXIMITY_ROLE = "proximity_vocabulary"
_CATEGORY_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")

# §C law 3 — the HARD LAW in code, not data: these categories load only
# with `enforcement: floor`. A data edit cannot unlock them.
_FLOOR_LOCKED_CATEGORIES = frozenset({"minors", "slurs"})

# Multi-hit reporting order (builder detail, recorded): v1's registry
# order was the severity order, most severe first, so the reported
# category on multi-hit text was stable. Self-declared files keep that
# ranking for the eight known categories; unknown categories scan after,
# alphabetically.
_SEVERITY = ("minors", "bestiality", "noncon", "selfharm", "slurs",
             "drugs", "advice", "misc")

# Spread (every-letter-separated) matching only for single words this long or
# longer. 3 catches short listed terms ("cnc" -> "c.n.c") while staying rare
# enough on ordinary text to be an accepted err-toward-blocking tradeoff.
_SPREAD_MIN_LEN = 3

_ASCII_WORD = "[a-z0-9]"
_EDGE_L = r"(?<!" + _ASCII_WORD + r")"
_EDGE_R = r"(?!" + _ASCII_WORD + r")"
_SEP0 = r"[^a-z0-9]{0,2}"        # word-join separators (0 = concatenation)
_SEP_PUNCT = r"[^a-z0-9\s]{0,2}"  # intra-word punctuation (NOT whitespace)
_SEP1 = r"[^a-z0-9]{1,2}"        # full spread (>=1 sep, whitespace allowed)
_PLURAL = r"(?:e?s)?"            # tolerate a trailing plural on the whole term
_DIGIT_RE = re.compile(r"\\d|[0-9]")


@dataclass(frozen=True)
class FilterResult:
    allowed: bool
    category: str | None = None
    matched: str | None = None
    context: str = "freetext"
    message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# --- v1 matching machinery (carried) -----------------------------------------


def _chunks(term: str) -> list[str]:
    """Alphanumeric chunks of a normalized term ('self-harm' -> [self, harm])."""
    return [c for c in re.split(r"[^a-z0-9]+", term) if c]


def _joiner_core(term: str) -> str | None:
    """Regex core matching a term across separator/concatenation variants,
    with a trailing plural tolerated ('high school' -> 'high schools')."""
    parts = _chunks(term)
    if not parts:
        return None
    return _SEP0.join(re.escape(p) for p in parts) + _PLURAL


def _single_word(term: str) -> str | None:
    """The lone alphabetic chunk of a single-word term long enough to obfuscate,
    else None."""
    parts = _chunks(term)
    if len(parts) != 1:
        return None
    word = parts[0]
    if len(word) < _SPREAD_MIN_LEN or not word.isalpha():
        return None
    return word


def _punct_core(term: str) -> str | None:
    """Core tolerating 0-2 NON-whitespace separators between every letter of a
    single word. Catches punctuation obfuscation and a lone separator dropped
    inside a word ('under-age', 'l.o.l.i', 'school-girl') without folding two
    space-separated words into a term ('shot a' never becomes 'shota')."""
    word = _single_word(term)
    if word is None:
        return None
    return _SEP_PUNCT.join(re.escape(ch) for ch in word) + _PLURAL


def _spread_core(term: str) -> str | None:
    """Core requiring at least one separator (whitespace allowed) between every
    letter, catching fully space-spread obfuscation ('l o l i') that _punct_core
    deliberately rejects. Adjacent-word text cannot match: every pair must be
    separated, which 'shot a'/'lol i' are not."""
    word = _single_word(term)
    if word is None:
        return None
    return _SEP1.join(re.escape(ch) for ch in word)


def _alt(cores: list[str]) -> re.Pattern[str] | None:
    """Edge-guarded alternation of cores, longest-first for specific matches."""
    cores = [c for c in cores if c]
    if not cores:
        return None
    cores = sorted(set(cores), key=len, reverse=True)
    return re.compile(_EDGE_L + r"(?:" + "|".join(cores) + r")" + _EDGE_R)


class _TermSet:
    """Compiled matcher for one term list: joiner + spread families over both
    the plain and doubled-collapsed forms, plus raw regexes."""

    def __init__(self, terms: list[str], regexes: list[str]):
        self._plain = self._build(terms)
        self._doubled = self._build([norm.collapse_doubles(t) for t in terms])
        self.digit_res = [re.compile(rx) for rx in regexes if _DIGIT_RE.search(rx)]
        self.free_res = [re.compile(rx) for rx in regexes if not _DIGIT_RE.search(rx)]

    @staticmethod
    def _build(terms: list[str]) -> tuple[re.Pattern[str] | None, ...]:
        return (
            _alt([_joiner_core(t) for t in terms]),
            _alt([_punct_core(t) for t in terms]),
            _alt([_spread_core(t) for t in terms]),
        )

    def find(self, text: str) -> str | None:
        """First match across every family/variant, or None."""
        for variant in norm.scan_variants(text):      # base + leet
            for pat in self._plain:
                if pat is not None:
                    m = pat.search(variant)
                    if m:
                        return m.group(0)
        for variant in norm.double_variants(text):    # doubles collapsed
            for pat in self._doubled:
                if pat is not None:
                    m = pat.search(variant)
                    if m:
                        return m.group(0)
        # Raw regexes: digit-bearing on digit-safe variants only; digit-free
        # additionally on leet variants.
        if self.digit_res:
            for variant in norm.digit_safe_variants(text):
                for pat in self.digit_res:
                    m = pat.search(variant)
                    if m:
                        return m.group(0)
        if self.free_res:
            variants = norm.digit_safe_variants(text) + norm.leet_variants(text)
            for variant in variants:
                for pat in self.free_res:
                    m = pat.search(variant)
                    if m:
                        return m.group(0)
        return None

    def iter_spans(self, variant: str):
        """(start, end, text) matches of the literal families on one variant,
        for proximity checks on contextual lists."""
        for pat in self._plain:
            if pat is not None:
                for m in pat.finditer(variant):
                    yield m.start(), m.end(), m.group(0)


# --- §C data loading ---------------------------------------------------------


@dataclass(frozen=True)
class _WordList:
    """One loaded, declared word file. Enforcement is a per-list property
    (§E gates LISTS): `unlocked_at` is None for floor lists, else the
    rating at which the list stops applying."""

    file_name: str
    category: str
    mode: str            # "always" | "contextual"
    unlocked_at: str | None
    terms: _TermSet


def _parse_file(path: Path) -> tuple[dict[str, str], list[str], list[str]]:
    """One data file -> (declarations, literal terms, raw regex strings).

    Declaration lines (``#! key: value``) are # comments to the v1 term
    format, so everything else parses exactly as v1 did."""
    declarations: dict[str, str] = {}
    terms: list[str] = []
    regexes: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith(_DECL_PREFIX):
            body = line[len(_DECL_PREFIX):].strip()
            key, sep, value = body.partition(":")
            key, value = key.strip(), value.strip()
            if not sep or not key or not value:
                raise SafetyDataError(
                    E.SAFETY_DECLARATION_UNKNOWN,
                    path.name,
                    f"{path.name}: malformed declaration line {line!r}; "
                    f"declarations spell '#! key: value'",
                )
            if key in declarations:
                raise SafetyDataError(
                    E.SAFETY_DECLARATION_DUPLICATE,
                    path.name,
                    f"{path.name}: duplicate declaration {key!r}",
                )
            declarations[key] = value
            continue
        if not line or line.startswith("#"):
            continue
        if line.startswith("re:"):
            regexes.append(line[3:].strip())
        else:
            terms.append(norm.normalize(line))
    return declarations, terms, regexes


def _check_proximity_declarations(name: str, declarations: dict[str, str]) -> None:
    """§C law 4: the proximity file declares its role and nothing else."""
    role = declarations.get("role")
    if role is None:
        raise SafetyDataError(
            E.SAFETY_DECLARATION_MISSING,
            name,
            f"{name}: the proximity vocabulary must declare "
            f"'#! role: {_PROXIMITY_ROLE}'",
        )
    if role != _PROXIMITY_ROLE:
        raise SafetyDataError(
            E.SAFETY_DECLARATION_UNKNOWN,
            name,
            f"{name}: unknown role {role!r}; the one legal role is "
            f"{_PROXIMITY_ROLE!r}",
        )
    extras = set(declarations) - {"role"}
    if extras:
        raise SafetyDataError(
            E.SAFETY_DECLARATION_UNKNOWN,
            name,
            f"{name}: the proximity vocabulary takes no category or "
            f"enforcement of its own (§C); found {sorted(extras)}",
        )


def _parse_list_declarations(
    name: str, declarations: dict[str, str]
) -> tuple[str, str, str | None]:
    """§C laws 1-3 over one blocklist file -> (category, mode, unlocked_at)."""
    if not declarations:
        raise SafetyDataError(
            E.SAFETY_UNDECLARED_FILE,
            name,
            f"{name}: no scope declarations; every word file self-declares "
            f"category, mode, and enforcement (§C)",
        )
    unknown = set(declarations) - set(_LIST_DECL_KEYS)
    if unknown:
        raise SafetyDataError(
            E.SAFETY_DECLARATION_UNKNOWN,
            name,
            f"{name}: unknown declaration(s) {sorted(unknown)}; legal are "
            f"{list(_LIST_DECL_KEYS)}",
        )
    missing = [k for k in _LIST_DECL_KEYS if k not in declarations]
    if missing:
        raise SafetyDataError(
            E.SAFETY_DECLARATION_MISSING,
            name,
            f"{name}: missing required declaration(s) {missing}",
        )
    category = declarations["category"]
    if not _CATEGORY_ID_RE.match(category):
        raise SafetyDataError(
            E.SAFETY_DECLARATION_UNKNOWN,
            name,
            f"{name}: category {category!r} is not a machine id "
            f"([a-z][a-z0-9_]*)",
        )
    mode = declarations["mode"]
    if mode not in _MODES:
        raise SafetyDataError(
            E.SAFETY_DECLARATION_UNKNOWN,
            name,
            f"{name}: unknown mode {mode!r}; legal are {list(_MODES)}",
        )
    enforcement = declarations["enforcement"]
    if enforcement == "floor":
        unlocked_at = None
    else:
        head, sep, rating = enforcement.partition(":")
        rating = rating.strip()
        if head.strip() != "unlocked_at" or not sep or rating not in (
            "mature",
            "explicit",
        ):
            raise SafetyDataError(
                E.SAFETY_DECLARATION_UNKNOWN,
                name,
                f"{name}: unknown enforcement {enforcement!r}; legal are "
                f"'floor', 'unlocked_at: mature', 'unlocked_at: explicit'",
            )
        unlocked_at = rating
    if category in _FLOOR_LOCKED_CATEGORIES and unlocked_at is not None:
        raise SafetyDataError(
            E.SAFETY_ENFORCEMENT_LOCKED,
            name,
            f"{name}: category {category!r} loads only with "
            f"'enforcement: floor' (§C hard law); a data edit cannot "
            f"unlock it",
        )
    return category, mode, unlocked_at


def _severity_key(word_list: _WordList) -> tuple:
    try:
        rank, tail = _SEVERITY.index(word_list.category), ""
    except ValueError:
        rank, tail = len(_SEVERITY), word_list.category
    # always before contextual within a category — v1's per-category order.
    mode_rank = 0 if word_list.mode == "always" else 1
    return (rank, tail, mode_rank, word_list.file_name)


# --- the filter --------------------------------------------------------------


class SafetyFilter:
    """Deterministic content filter over a §C-declared word-file directory.

    Constructed over an explicit data directory (never a module global,
    §F) with an optional audit sink (§H). Loading is fail-loud: any §C
    violation raises :class:`SafetyDataError` and nothing loads.
    """

    def __init__(self, data_dir: Path | str, audit_sink=None):
        data_dir = Path(data_dir)
        self._audit = audit_sink if audit_sink is not None else NullAuditSink()
        if not data_dir.is_dir():
            raise SafetyDataError(
                E.SAFETY_DATA_DIR_INVALID,
                str(data_dir),
                f"word-file directory {data_dir} does not exist",
            )
        files = sorted(p for p in data_dir.iterdir() if p.suffix == ".txt")
        if not files:
            raise SafetyDataError(
                E.SAFETY_DATA_DIR_INVALID,
                str(data_dir),
                f"word-file directory {data_dir} holds no .txt files; the "
                f"filter never starts over a bad data directory (§C)",
            )
        lists: list[_WordList] = []
        self._sexual: _TermSet | None = None
        for path in files:
            declarations, terms, regexes = _parse_file(path)
            if path.name == PROXIMITY_FILE:
                _check_proximity_declarations(path.name, declarations)
                if regexes:
                    raise SafetyDataError(
                        E.SAFETY_REGEX_IN_CONTEXTUAL,
                        path.name,
                        f"{path.name}: the proximity vocabulary takes "
                        f"literal terms only",
                    )
                self._sexual = _TermSet(terms, [])
                continue
            if declarations.get("role") is not None:
                raise SafetyDataError(
                    E.SAFETY_DECLARATION_UNKNOWN,
                    path.name,
                    f"{path.name}: 'role' is legal only on "
                    f"{PROXIMITY_FILE} (§C law 4)",
                )
            category, mode, unlocked_at = _parse_list_declarations(
                path.name, declarations
            )
            if mode == "contextual" and regexes:
                raise SafetyDataError(
                    E.SAFETY_REGEX_IN_CONTEXTUAL,
                    path.name,
                    f"{path.name}: contextual lists take literal terms only",
                )
            lists.append(
                _WordList(
                    file_name=path.name,
                    category=category,
                    mode=mode,
                    unlocked_at=unlocked_at,
                    terms=_TermSet(terms, regexes),
                )
            )
        if self._sexual is None and any(w.mode == "contextual" for w in lists):
            raise SafetyDataError(
                E.SAFETY_NO_PROXIMITY_VOCABULARY,
                PROXIMITY_FILE,
                f"contextual lists need {PROXIMITY_FILE} in the data "
                f"directory; it is absent",
            )
        self._lists = sorted(lists, key=_severity_key)

    # -- public API ---------------------------------------------------------

    def check(
        self,
        text: str | None,
        context: str = "freetext",
        rating: str = "standard",
        surface: str | None = None,
    ) -> FilterResult:
        """Gate one string. Same call wraps inputs and model outputs.

        ``rating`` gates `unlocked_at` lists (§E); default `standard`
        applies everything. ``surface`` is the caller's surface code for
        the audit event (gate ruling 2026-07-23): absent, the event
        carries the context only."""
        if context not in CONTEXTS:
            raise ValueError(f"unknown filter context: {context!r}")
        if rating not in _RATING_ORDER:
            raise ValueError(f"unknown rating: {rating!r}")
        if not text or not text.strip():
            return FilterResult(True, context=context, message="ok")

        for word_list in self._lists:
            if (
                word_list.unlocked_at is not None
                and _RATING_ORDER[rating] >= _RATING_ORDER[word_list.unlocked_at]
            ):
                continue  # unlocked at this rating; the list is skipped (§E)
            if word_list.mode == "always":
                matched = word_list.terms.find(text)
                if matched:
                    return self._blocked(
                        word_list.category, matched, context, surface
                    )
                continue
            # contextual: never applied to names (v1 semantics, §E).
            if context == "name":
                continue
            hit = self._contextual_hit(word_list.terms, text, context)
            if hit:
                return self._blocked(word_list.category, hit, context, surface)
        return FilterResult(True, context=context, message="ok")

    def check_name(
        self,
        name: str | None,
        rating: str = "standard",
        surface: str | None = None,
    ) -> FilterResult:
        return self.check(name, context="name", rating=rating, surface=surface)

    # -- internals ----------------------------------------------------------

    def _contextual_hit(
        self, contextual: _TermSet, text: str, context: str
    ) -> str | None:
        if context == "prompt":
            # Strictest: any contextual match blocks outright.
            return contextual.find(text)
        # freetext / chat: block only near sexual vocabulary, checked in the
        # same variant so spans line up.
        for variant in norm.scan_variants(text):
            for start, end, hit in contextual.iter_spans(variant):
                if self._sexual_near(variant, start, end):
                    return hit
        return None

    def _sexual_near(self, variant: str, start: int, end: int) -> bool:
        assert self._sexual is not None  # load law: contextual needs proximity
        lo = max(0, start - PROXIMITY_WINDOW)
        hi = end + PROXIMITY_WINDOW
        for s, e, _ in self._sexual.iter_spans(variant):
            if e >= lo and s <= hi:
                return True
        return False

    def _blocked(
        self, category: str, matched: str, context: str, surface: str | None
    ) -> FilterResult:
        # §H: refusals — and only refusals — emit one vocabulary-blind
        # event. Never the matched term, never the text.
        payload = {"context": context, "category": category}
        if surface is not None:
            payload["surface"] = surface
        self._audit.log("filter_block", **payload)
        return FilterResult(
            False,
            category=category,
            matched=matched,
            context=context,
            message=f"Blocked by content policy ({category}).",
        )
