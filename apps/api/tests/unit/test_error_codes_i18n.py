"""Every error code the API can return has an `error.<code>` string in packages/i18n.

Codes are collected by scanning apps/api/app for `ApiError("<code>", ...)` and
`_envelope(<status>, "<code>", ...)` calls, plus the code constants used by the generic
handlers (core/errors.py) and the rate limiter (core/ratelimit.py ERROR_CODES). A call whose
code is not a string literal is only allowed in those two modules, whose constants are
collected below; anywhere else, use a literal so this test can see it.
"""

import ast
import json
from pathlib import Path

from app.core import errors, ratelimit

API_DIR = Path(__file__).resolve().parents[2]
APP_DIR = API_DIR / "app"
MESSAGES = API_DIR.parents[1] / "packages" / "i18n" / "messages"

# Modules allowed to pass a non-literal code; their codes come from the constants below.
DYNAMIC_CODE_MODULES = {"app/core/errors.py", "app/core/ratelimit.py"}


def _callee(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _code_arg(node: ast.Call, position: int) -> ast.expr | None:
    for kw in node.keywords:
        if kw.arg == "code":
            return kw.value
    return node.args[position] if len(node.args) > position else None


def scan() -> tuple[set[str], list[str]]:
    literal: set[str] = set()
    dynamic: list[str] = []
    for path in sorted(APP_DIR.rglob("*.py")):
        rel = path.relative_to(API_DIR).as_posix()
        for node in ast.walk(ast.parse(path.read_text(), filename=rel)):
            if not isinstance(node, ast.Call):
                continue
            name = _callee(node)
            if name == "ApiError":
                arg = _code_arg(node, 0)
            elif name == "_envelope":
                arg = _code_arg(node, 1)
            else:
                continue
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                literal.add(arg.value)
            else:
                dynamic.append(f"{rel}:{node.lineno}")
    return literal, dynamic


def all_codes() -> set[str]:
    literal, _ = scan()
    handler_codes = {
        errors.VALIDATION_CODE,
        errors.INTERNAL_CODE,
        errors.HTTP_FALLBACK_CODE,
        *errors.HTTP_STATUS_CODES.values(),
    }
    ratelimit_codes = {ratelimit._DEFAULT_CODE, *ratelimit.ERROR_CODES.values()}
    return literal | handler_codes | ratelimit_codes


def test_scan_finds_known_codes():
    literal, _ = scan()
    assert {"auth_required", "auth_invalid"} <= literal
    assert {"method_not_allowed", "rate_limited_scans", "internal_error"} <= all_codes()


def test_dynamic_codes_only_in_known_modules():
    _, dynamic = scan()
    stray = [site for site in dynamic if site.split(":")[0] not in DYNAMIC_CODE_MODULES]
    assert not stray, f"use a string-literal error code (or extend this test): {stray}"


def test_every_error_code_has_a_message_in_every_locale():
    codes = all_codes()
    for locale in ("en", "hi", "mr"):
        messages = json.loads((MESSAGES / f"{locale}.json").read_text())["error"]
        missing = sorted(c for c in codes if not messages.get(c))
        assert not missing, f"{locale}.json is missing error.{missing}"
