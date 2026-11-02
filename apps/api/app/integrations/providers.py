"""Provider protocols. Services depend on these, never on the SDK."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class ExtractionFailed(Exception):
    """Invalid output twice, timeout, or 5xx after retries. No draft may be produced."""


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
    ) -> BaseModel: ...
