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
    r"(?<![a-z0-9])(?:ins[\s.:-]*|e[\s-]?)(\d{3,4})[a-z]?"
    r"(?:\s*\((?:i{1,3}|iv|v|vi{1,3}|ix|x)\))?(?![a-z0-9])(?!\s*(?:iu|mg|mcg|g|ml|%))"
)
# A parenthesised list made only of 3-4 digit codes, e.g. "(220, 223)" or "(322 & 471)".
_CODE_LIST = re.compile(r"\(\s*\d{3,4}(?:\s*(?:[,;&]|and)\s*\d{3,4})*\s*\)")
_DIGITS = re.compile(r"\d{3,4}")
_SEPARATORS = re.compile(r"[,;:()\[\]/|।॥\n\r]+")
_ZERO_WIDTH = re.compile("[\u200c\u200d\u093c]")  # ZWNJ, ZWJ, nukta


def _ins_sub(t: str) -> str:
    def repl(m: re.Match[str]) -> str:
        if m.group(0).startswith("e") and t[: m.start()].rstrip(" -").endswith(("vitamin", "vit", "vit.")):
            return m.group(0)
        return f" ins{m.group(1)} "

    return _INS.sub(repl, t)


def _prep(text: str) -> str:
    """NFKC, lowercase and rewrite INS/E codes. Separators are left in place."""
    t = _ZERO_WIDTH.sub("", unicodedata.normalize("NFKC", text)).lower()
    t = _CODE_LIST.sub(lambda m: " " + " ".join(f"ins{d}" for d in _DIGITS.findall(m.group(0))) + " ", t)
    return _ins_sub(t)


def normalize(text: str) -> str:
    return _NOT_WC.sub(" ", _prep(text)).strip()


def _segments(texts: Iterable[str]) -> list[str]:
    """Normalised segments split on item boundaries and , ; : ( ) [ ] / | danda."""
    out: list[str] = []
    for text in texts:
        for part in _SEPARATORS.split(_prep(text)):
            n = _NOT_WC.sub(" ", part).strip()
            if n:
                out.append(f" {n} ")
    return out


def _pattern(term: str) -> re.Pattern[str]:
    body = rf"{re.escape(term)}(?:es|s)?"
    if term.endswith("y"):
        body = rf"(?:{body}|{re.escape(term[:-1])}ies)"
    return re.compile(rf"(?<![{_WC}]){body}(?![{_WC}])")


def _blank(text: str, pattern: re.Pattern[str]) -> tuple[str, bool]:
    found = False

    def repl(m: re.Match[str]) -> str:
        nonlocal found
        found = True
        return " "

    return pattern.sub(repl, text), found


def find_terms(texts: Iterable[str], terms: Iterable[str], exclude: Iterable[str] = ()) -> list[str]:
    segments = _segments(texts)
    exclude_patterns = [_pattern(p) for p in (normalize(x) for x in exclude) if p]

    originals: dict[str, str] = {}
    for term in terms:
        n = normalize(term)
        if n:
            originals.setdefault(n, term)
    ordered = [(n, _pattern(n)) for n in sorted(originals, key=lambda s: (-len(s), s))]

    matched: set[str] = set()
    for work in segments:
        for pat in exclude_patterns:
            work, _ = _blank(work, pat)
        for n, pat in ordered:
            work, found = _blank(work, pat)
            if found:
                matched.add(originals[n])
    return sorted(matched)
