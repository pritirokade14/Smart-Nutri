"""Versioned prompt files (`<name>_v<N>.md`). Never edit a released version."""

from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent
EXTRACTION_PROMPT_VERSION = "extraction_v1"
EXPLANATION_PROMPT_VERSION = "explanation_v2"
VOICE_PROMPT_VERSION = "voice_v2"


def load_prompt(name: str) -> tuple[str, str]:
    """Return (prompt text, version) for e.g. `extraction_v1`; log the version per call."""
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8"), name


def load_extraction_prompt() -> tuple[str, str]:
    return load_prompt(EXTRACTION_PROMPT_VERSION)


def load_explanation_prompt() -> tuple[str, str]:
    return load_prompt(EXPLANATION_PROMPT_VERSION)
