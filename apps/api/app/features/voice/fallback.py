"""Rule-based answer text when the LLM is unavailable, fails or is rejected (Plan 7, F7/F10).

Pure: no I/O apart from the cached message catalog, no LLM. The text is built only from the
engine's verdict and reason codes, with the same packages/i18n strings and the same param
rules the clients use (packages/i18n/README.md, "Rendering reasons"), so a spoken fallback
says exactly what the result screen shows. Also the verdict lock that every LLM answer must
pass before it is spoken.

Used by the voice answer now; the analyze explanation (Plan 5 F7) can use
`fallback_explanation` for its no-LLM case.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from app import scoring
from app.core.i18n import Catalog, catalog, format_number

logger = logging.getLogger(__name__)

MAX_FALLBACK_REASONS = 3
FALLBACK_TIP_KEYS = (
    "explanation.fallback_tip.1",
    "explanation.fallback_tip.2",
    "explanation.fallback_tip.3",
)
SAFE_WORD_KEY = "voice.word_safe"
# Always denied, in every language, whatever the status (as in the F7 guard).
_ALWAYS_DENIED = ("safe", "safely", "सेफ")  # "सेफ": Hinglish "safe" in Devanagari

# Params whose value is a code, mapped through a label namespace (lists item by item).
_CODE_PARAMS = {
    "diet": "diet",
    "claim": "claim",
    "nutrient": "nutrient",
    "high_in": "nutrient",
    "alert": "alert",
    "alerts": "alert",
}
_LIST_SEPARATOR = ", "


@dataclass(frozen=True)
class FallbackExplanation:
    text: str
    tips: tuple[str, str, str]
    source: Literal["fallback"] = "fallback"


def _cat(cat: Catalog | None) -> Catalog:
    return cat or catalog()


def verdict_sentence(status: scoring.Status, language: str, cat: Catalog | None = None) -> str:
    return _cat(cat).t(f"verdict.spoken.{status.value}", language)


def reason_key(code: str, params: Mapping[str, Any]) -> str:
    """The message key for a reason, including the README's `reason_variant.*` cases."""
    if code == "nutrient_missing" and params.get("reason") == "low_confidence":
        return "reason_variant.nutrient_missing_low_confidence"
    if code == "diet_violation" and not params.get("ingredients"):
        return "reason_variant.diet_violation_mark_only"
    if code == "custom_alert" and not params.get("ingredients"):
        return "reason_variant.custom_alert_flag_only"
    return f"reason.{code}"


def _label(cat: Catalog, namespace: str, code: Any, language: str) -> str:
    key = f"{namespace}.{code}"
    return cat.t(key, language) if cat.raw(key, language) is not None else str(code)


def _arg(cat: Catalog, name: str, value: Any, language: str) -> Any:
    if value is None:
        raise KeyError(name)
    namespace = _CODE_PARAMS.get(name)
    if name == "allergen":
        # A recognised allergen gets its label; anything else is the member's own wording.
        return _label(cat, "allergen", value, language)
    if namespace is not None:
        if isinstance(value, list | tuple):
            return _LIST_SEPARATOR.join(_label(cat, namespace, v, language) for v in value)
        return _label(cat, namespace, value, language)
    if isinstance(value, list | tuple):
        return _LIST_SEPARATOR.join(str(v) for v in value)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int | float):
        return format_number(value)
    return value


def reason_sentence(
    reason: scoring.Reason, language: str, cat: Catalog | None = None
) -> str | None:
    """The reason as the clients render it, or None if it can't be rendered completely."""
    c = _cat(cat)
    key = reason_key(reason.code, reason.params)
    message = c.raw(key, language)
    if message is None:
        logger.warning("fallback_reason_skipped code=%s why=no_message", reason.code)
        return None
    try:
        args = {k: _arg(c, k, v, language) for k, v in reason.params.items() if v is not None}
        return c.t(key, language, **args)
    except (KeyError, ValueError, TypeError):
        logger.warning("fallback_reason_skipped code=%s why=params", reason.code)
        return None


def _top_reasons(reasons: Sequence[scoring.Reason]) -> list[scoring.Reason]:
    # Most severe first; the engine's order breaks ties (sorted() is stable).
    return sorted(reasons, key=lambda r: -r.severity.rank)


def fallback_answer(
    verdict: scoring.MemberVerdict, language: str, cat: Catalog | None = None
) -> str:
    """verdict_sentence + up to MAX_FALLBACK_REASONS reason sentences, most severe first."""
    c = _cat(cat)
    parts = [verdict_sentence(verdict.status, language, c)]
    for reason in _top_reasons(verdict.reasons):
        if len(parts) > MAX_FALLBACK_REASONS:
            break
        sentence = reason_sentence(reason, language, c)
        if sentence and sentence not in parts:
            parts.append(sentence)
    return " ".join(parts)


def fallback_explanation(
    verdict: scoring.MemberVerdict, language: str, cat: Catalog | None = None
) -> FallbackExplanation:
    c = _cat(cat)
    tips = tuple(c.t(k, language) for k in FALLBACK_TIP_KEYS)
    return FallbackExplanation(text=fallback_answer(verdict, language, c), tips=tips)  # type: ignore[arg-type]


# --- verdict lock ------------------------------------------------------------------------------


def _normalise(text: str) -> str:
    """NFKC, drop invisible format characters (ZWJ, ZWNJ, zero-width space...), casefold."""
    text = unicodedata.normalize("NFKC", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return text.casefold()


def _contains(haystack: str, needle: str) -> bool:
    """Latin needles match whole words; other scripts match at a word start (case endings
    attach in Hindi and Marathi). A false positive only costs the LLM text."""
    if not needle:
        return False
    if needle.isascii():
        return re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack) is not None
    return re.search(rf"(?<!\w){re.escape(needle)}", haystack) is not None


def violates_verdict_lock(
    text: str, status: scoring.Status, language: str, cat: Catalog | None = None
) -> bool:
    """True if `text` names a status other than the engine's (its label in `language` or in
    English), or says "safe" in English or `language`, whatever the status."""
    c = _cat(cat)
    haystack = _normalise(text)
    needles: set[str] = set(_ALWAYS_DENIED)
    for lang in {language, "en"}:
        needles.add(_normalise(c.t(SAFE_WORD_KEY, lang)))
        for other in scoring.Status:
            if other is not status:
                needles.add(_normalise(c.t(f"status.{other.value}", lang)))
    needles.discard(_normalise(SAFE_WORD_KEY))  # a missing key never matches anything
    return any(_contains(haystack, n) for n in needles)
