"""Ingredient text normalisation and term matching (English + Devanagari)."""

from __future__ import annotations

import functools
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
# Item boundaries (R19): , ; : ( ) [ ] / | & + danda, newlines, "." followed by
# whitespace, and the standalone word "and".
_SEPARATORS = re.compile(rf"(?:[,;:()\[\]/|&+।॥\n\r]|\.(?=\s)|(?<![{_WC}])and(?![{_WC}]))+")
_ZERO_WIDTH = re.compile("[‌‍़]")  # ZWNJ, ZWJ, nukta
_CHANDRABINDU = str.maketrans({"ँ": "ं"})  # fold chandrabindu to anusvara

# Text that stands in for a missing ingredient list (R21), compared without spaces.
_PLACEHOLDERS = frozenset(
    p.replace(" ", "")
    for p in (
        "na",
        "nil",
        "none",
        "not available",
        "see pack",
        "see package",
        "ingredients",
        "ingredient",
    )
)


def _ins_sub(t: str) -> str:
    def repl(m: re.Match[str]) -> str:
        if m.group(0).startswith("e") and t[: m.start()].rstrip(" -").endswith(
            ("vitamin", "vit", "vit.")
        ):
            return m.group(0)
        return f" ins{m.group(1)} "

    return _INS.sub(repl, t)


def _prep(text: str) -> str:
    """NFKC, lowercase, fold Devanagari variants and rewrite INS/E codes. Separators are kept."""
    t = _ZERO_WIDTH.sub("", unicodedata.normalize("NFKC", text)).lower().translate(_CHANDRABINDU)
    t = _CODE_LIST.sub(
        lambda m: " " + " ".join(f"ins{d}" for d in _DIGITS.findall(m.group(0))) + " ", t
    )
    return _ins_sub(t)


def normalize(text: str) -> str:
    return _NOT_WC.sub(" ", _prep(text)).strip()


def _segments(texts: Iterable[str]) -> list[str]:
    """Normalised segments split on item boundaries (see _SEPARATORS)."""
    out: list[str] = []
    for text in texts:
        for part in _SEPARATORS.split(_prep(text)):
            n = _NOT_WC.sub(" ", part).strip()
            if n:
                out.append(f" {n} ")
    return out


def has_ingredient_content(texts: Iterable[str]) -> bool:
    """True if any segment has >= 2 word characters and is not a placeholder such as "N/A"."""
    for seg in _segments(texts):
        compact = seg.replace(" ", "")
        if len(compact) >= 2 and compact not in _PLACEHOLDERS:
            return True
    return False


@functools.lru_cache(maxsize=4096)
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


def _exclude_patterns(exclude: Iterable[str]) -> list[tuple[str, re.Pattern[str]]]:
    originals: dict[str, str] = {}
    for x in exclude:
        n = normalize(x)
        if n:
            originals.setdefault(n, x)
    return [(original, _pattern(n)) for n, original in originals.items()]


def find_terms(
    texts: Iterable[str], terms: Iterable[str], exclude: Iterable[str] = ()
) -> list[str]:
    segments = _segments(texts)
    exclude_patterns = [pat for _, pat in _exclude_patterns(exclude)]

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


def excluded_hits(texts: Iterable[str], exclude: Iterable[str]) -> list[str]:
    """Exclude phrases that matched inside a segment that is not exactly the phrase (R19).

    "almond milk chocolate" -> ["almond milk"]. A segment that is exactly "coconut milk"
    is a clean exclusion and is not reported.
    """
    patterns = _exclude_patterns(exclude)
    hits: set[str] = set()
    for seg in _segments(texts):
        core = seg.strip()
        for original, pat in patterns:
            if pat.search(seg) and not pat.fullmatch(core):
                hits.add(original)
    return sorted(hits)


def modifier_excludes(texts: Iterable[str], exclude: Iterable[str]) -> list[str]:
    """Exclude phrases followed by more words in their segment, i.e. used as a modifier.

    "almond milk chocolate" -> ["almond milk"] (the product is chocolate, which may
    contain milk). "roasted cashew nuts" or "may contain tree nuts" are not reported:
    there the exclude phrase is the head noun, so excluding it is correct (R19, R30).
    """
    patterns = _exclude_patterns(exclude)
    hits: set[str] = set()
    for seg in _segments(texts):
        for original, pat in patterns:
            if any(seg[m.end() :].strip() for m in pat.finditer(seg)):
                hits.add(original)
    return sorted(hits)
