"""Provider protocols. Services depend on these, never on the SDK."""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel


class ExtractionFailed(Exception):
    """Invalid output twice, timeout, or 5xx after retries. No draft may be produced."""


class CompletionFailed(Exception):
    """Chat completion failed: invalid output twice, timeout, 429/5xx after retries, the
    deadline, or another upstream rejection. No explanation may be produced."""


class ProviderUnavailable(Exception):
    """The provider refuses to serve (e.g. reason="insufficient_credits"). Not retried."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class LLMProvider(Protocol):
    async def extract_label(
        self,
        *,
        image: bytes,
        mime: str,
        prompt: str,
        prompt_version: str,
        schema: type[BaseModel],
        model: str,
        fallback_model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> BaseModel:
        """Vision extraction, validated with `schema`. `fallback_model` is tried once if
        `model` fails upstream. Raises ProviderUnavailable or ExtractionFailed."""
        ...

    async def chat_json(
        self,
        *,
        model: str,
        system: str,
        user: str,
        schema: type[BaseModel],
        prompt_version: str,
        timeout_s: float,
        fallback_model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> BaseModel:
        """Strict-JSON chat, validated with `schema`. Always processed in India (data residency
        "in", India-processed models only), so it may carry anonymised member health data.
        `timeout_s` is the total budget, retries and the one `fallback_model` try included.
        Raises ProviderUnavailable or CompletionFailed."""
        ...


SpeechLanguage = Literal["en", "hi", "mr"]
# BCP-47 hints the CallMissed (Sarvam) speech models take.
SPEECH_LANGUAGE_CODES: dict[str, str] = {"en": "en-IN", "hi": "hi-IN", "mr": "mr-IN"}
MAX_TTS_CHARS = 2500


class SpeechUnavailable(Exception):
    """Speech-to-text or text-to-speech cannot be served: 402 (credits), 401/403, another
    upstream rejection, a malformed response, or retries exhausted. Never carries audio or
    text, only a short machine reason."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class SpeechProvider(Protocol):
    async def transcribe(self, audio: bytes, mime: str, language: str) -> str:
        """The transcript of `audio`. `language` ("en" | "hi" | "mr") is sent as a hint.
        Raises SpeechUnavailable."""
        ...

    async def synthesize(self, text: str, language: str) -> bytes:
        """mp3 bytes for `text`. ValueError if `text` is longer than MAX_TTS_CHARS.
        Raises SpeechUnavailable."""
        ...
