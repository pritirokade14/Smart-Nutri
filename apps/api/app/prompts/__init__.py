"""Versioned prompt files (`<name>_v<N>.md`). Never edit a released version."""

from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent
EXTRACTION_PROMPT_VERSION = "extraction_v1"
# Label accuracy v2: raw cell text, parsed in code (app/features/scans/cells.py).
EXTRACTION_V2_PROMPT_VERSION = "extraction_v2"
EXTRACTION_PROMPT_VERSIONS = (EXTRACTION_PROMPT_VERSION, EXTRACTION_V2_PROMPT_VERSION)
EXPLANATION_PROMPT_VERSION = "explanation_v3"
VOICE_PROMPT_VERSION = "voice_v3"


def load_prompt(name: str) -> tuple[str, str]:
    """Return (prompt text, version) for e.g. `extraction_v1`; log the version per call."""
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8"), name


def load_extraction_prompt(version: str = EXTRACTION_PROMPT_VERSION) -> tuple[str, str]:
    """The label-extraction prompt of `version` (the API picks it with the
    `EXTRACTION_PROMPT_VERSION` setting; v1 stays selectable so the eval can compare)."""
    if version not in EXTRACTION_PROMPT_VERSIONS:
        raise ValueError(f"unknown extraction prompt version: {version}")
    return load_prompt(version)


def load_explanation_prompt() -> tuple[str, str]:
    return load_prompt(EXPLANATION_PROMPT_VERSION)
