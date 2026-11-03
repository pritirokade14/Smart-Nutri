"""Every draft warning code the normaliser can emit has `warning.<code>` in en, hi and mr."""

import json
from pathlib import Path

import pytest

from app.features.scans.normalize import WARNING_CODES

MESSAGES = Path(__file__).resolve().parents[5] / "packages" / "i18n" / "messages"


@pytest.mark.parametrize("locale", ["en", "hi", "mr"])
def test_every_warning_code_has_a_string(locale):
    warnings = json.loads((MESSAGES / f"{locale}.json").read_text(encoding="utf-8"))["warning"]
    missing = [code for code in WARNING_CODES if not warnings.get(code)]
    assert missing == []
