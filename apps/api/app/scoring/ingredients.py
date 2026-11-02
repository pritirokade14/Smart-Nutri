"""Ingredient text normalisation and term matching (English + Devanagari)."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

# Python's \w misses Devanagari combining signs (matras, anusvara), so word
# characters are \w plus the Devanagari block (excluding danda punctuation).
_WC = r"\wऀ-ॣ०-ॿ"
_NOT_WC = re.compile(rf"[^{_WC}]+")

_INS = re.compile(
    r"(?<![a-z0-9])(?:ins[\s-]?|e-?)(\d{3,4})[a-z]?(?:\s*\((?:i{1,3}|iv|v|vi{1,3}|ix|x)\))?(?![a-z0-9])"
)
_BARE = re.compile(r"\((\d{3,4})\)")


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFKC", text).lower()
    t = _INS.sub(lambda m: f" ins{m.group(1)} ", t)
    t = _BARE.sub(lambda m: f" ins{m.group(1)} ", t)
    return _NOT_WC.sub(" ", t).strip()


def _pattern(term: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![{_WC}]){re.escape(term)}(?:es|s)?(?![{_WC}])")


def _blank(text: str, pattern: re.Pattern[str]) -> tuple[str, bool]:
    found = False

    def repl(m: re.Match[str]) -> str:
        nonlocal found
        found = True
        return " "

    return pattern.sub(repl, text), found


def find_terms(texts: Iterable[str], terms: Iterable[str], exclude: Iterable[str] = ()) -> list[str]:
    work = " " + normalize(" , ".join(texts)) + " "
    for phrase in exclude:
        p = normalize(phrase)
        if p:
            work, _ = _blank(work, _pattern(p))

    originals: dict[str, str] = {}
    for term in terms:
        n = normalize(term)
        if n:
            originals.setdefault(n, term)

    matched: set[str] = set()
    for n in sorted(originals, key=lambda s: (-len(s), s)):
        work, found = _blank(work, _pattern(n))
        if found:
            matched.add(originals[n])
    return sorted(matched)
