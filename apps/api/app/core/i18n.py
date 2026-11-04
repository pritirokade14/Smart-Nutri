"""Server-side lookup of packages/i18n messages (for spoken and fallback text only).

The API normally returns codes and lets the clients localise them. The one exception is voice:
the spoken answer is synthesised on the server, so its fallback text is built here from the
SAME strings the clients use (Plan 7). Messages are ICU; this module implements the subset
the message files use (plain `{arg}`, `select` and `plural` with `#`), and fails loudly
(KeyError / ValueError) on anything else rather than speaking a broken sentence.

The directory comes from settings (`I18N_MESSAGES_DIR`): the repo's packages/i18n/messages in
development, `/app/i18n` in the Docker image.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, Literal

Language = Literal["en", "hi", "mr"]
LANGUAGES: tuple[Language, ...] = ("en", "hi", "mr")
FALLBACK_LANGUAGE: Language = "en"


def repo_messages_dir() -> Path:
    """packages/i18n/messages of the source checkout (apps/api/app/core -> repo root)."""
    parents = Path(__file__).resolve().parents
    if len(parents) > 4:
        return parents[4] / "packages" / "i18n" / "messages"
    return Path("i18n")


def _flatten(node: dict[str, Any], prefix: str, out: dict[str, str]) -> None:
    for key, value in node.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            _flatten(value, f"{name}.", out)
        elif isinstance(value, str):
            out[name] = value


# --- ICU subset ------------------------------------------------------------------------------

# Node kinds: str (text), ("arg", name), ("select", name, {case: nodes}),
# ("plural", name, {case: nodes}), ("hash",) inside a plural case.
type _Node = str | tuple[Any, ...]


class _Parser:
    def __init__(self, text: str) -> None:
        self.s = text
        self.i = 0

    def parse(self) -> list[_Node]:
        nodes = self._nodes(in_plural=False)
        if self.i != len(self.s):
            raise ValueError(f"unbalanced braces in message: {self.s!r}")
        return nodes

    def _nodes(self, *, in_plural: bool) -> list[_Node]:
        out: list[_Node] = []
        buf: list[str] = []
        while self.i < len(self.s):
            c = self.s[self.i]
            if c == "}":
                break
            if c == "{":
                if buf:
                    out.append("".join(buf))
                    buf = []
                out.append(self._arg())
                continue
            if c == "#" and in_plural:
                if buf:
                    out.append("".join(buf))
                    buf = []
                out.append(("hash",))
                self.i += 1
                continue
            if c == "'" and self.s[self.i : self.i + 2] == "''":
                buf.append("'")
                self.i += 2
                continue
            buf.append(c)
            self.i += 1
        if buf:
            out.append("".join(buf))
        return out

    def _token(self) -> str:
        start = self.i
        while self.i < len(self.s) and self.s[self.i] not in ",}{":
            self.i += 1
        return self.s[start : self.i].strip()

    def _expect(self, ch: str) -> None:
        if self.i >= len(self.s) or self.s[self.i] != ch:
            raise ValueError(f"expected {ch!r} at {self.i} in {self.s!r}")
        self.i += 1

    def _arg(self) -> _Node:
        self._expect("{")
        name = self._token()
        if self.s[self.i] == "}":
            self.i += 1
            return ("arg", name)
        self._expect(",")
        kind = self._token()
        if kind not in ("select", "plural"):
            raise ValueError(f"unsupported ICU argument type {kind!r}")
        self._expect(",")
        cases: dict[str, list[_Node]] = {}
        while True:
            while self.i < len(self.s) and self.s[self.i].isspace():
                self.i += 1
            if self.s[self.i] == "}":
                self.i += 1
                break
            key = self._token()
            self._expect("{")
            cases[key] = self._nodes(in_plural=kind == "plural")
            self._expect("}")
        if "other" not in cases:
            raise ValueError(f"{kind} without an other case: {self.s!r}")
        return (kind, name, cases)


def format_number(value: float) -> str:
    """Latin digits, at most 3 decimals, no trailing zeros (packages/test-fixtures rule)."""
    if isinstance(value, bool):
        raise TypeError("not a number")
    if isinstance(value, int) or float(value).is_integer():
        return str(int(value))
    return f"{round(float(value), 3):.3f}".rstrip("0").rstrip(".")


def _plural_category(n: float, language: str) -> str:
    # CLDR cardinal "one": hi = i is 0 or n is 1; en/mr = n is 1 (integers only here).
    if language == "hi" and n in (0, 1):
        return "one"
    return "one" if n == 1 else "other"


def _render(nodes: list[_Node], params: dict[str, Any], language: str, n: float | None) -> str:
    out: list[str] = []
    for node in nodes:
        if isinstance(node, str):
            out.append(node)
            continue
        kind = node[0]
        if kind == "hash":
            if n is None:
                raise ValueError("# outside plural")
            out.append(format_number(n))
        elif kind == "arg":
            value = params[node[1]]
            out.append(format_number(value) if isinstance(value, int | float) else str(value))
        elif kind == "select":
            cases = node[2]
            chosen = cases.get(str(params[node[1]]), cases["other"])
            out.append(_render(chosen, params, language, n))
        else:  # plural
            count = params[node[1]]
            if isinstance(count, str):
                count = float(count)
            cases = node[2]
            exact = f"={format_number(count)}"
            chosen = cases.get(exact) or cases.get(_plural_category(count, language))
            out.append(_render(chosen or cases["other"], params, language, count))
    return "".join(out)


def format_icu(message: str, language: str, **params: Any) -> str:
    """Format one ICU message. KeyError if a used param is missing."""
    return _render(_Parser(message).parse(), params, language, None)


# --- catalog ---------------------------------------------------------------------------------


@dataclass(frozen=True)
class Catalog:
    messages: dict[str, dict[str, str]]  # language -> flat key -> message

    def has(self, key: str, language: str) -> bool:
        return key in self.messages.get(language, {})

    def raw(self, key: str, language: str) -> str | None:
        """The message in `language`, else English, else None."""
        found = self.messages.get(language, {}).get(key)
        if found is None:
            found = self.messages.get(FALLBACK_LANGUAGE, {}).get(key)
        return found

    def t(self, key: str, language: str, **params: Any) -> str:
        """Formatted message; falls back to English, then to the key itself."""
        message = self.raw(key, language)
        if message is None:
            return key
        return format_icu(message, language, **params)


@cache
def catalog(directory: Path | None = None) -> Catalog:
    """Load (once per directory) every `<language>.json` in `directory`."""
    base = directory or repo_messages_dir()
    messages: dict[str, dict[str, str]] = {}
    for language in LANGUAGES:
        path = base / f"{language}.json"
        flat: dict[str, str] = {}
        _flatten(json.loads(path.read_text(encoding="utf-8")), "", flat)
        messages[language] = flat
    return Catalog(messages)


def t(key: str, language: str, **params: Any) -> str:
    """`catalog().t(...)` with the repo messages (tests and scripts)."""
    return catalog().t(key, language, **params)
