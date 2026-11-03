"""Provider protocols. Services depend on these, never on the SDK."""

from __future__ import annotations

from typing import Protocol

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
    ) -> BaseModel: ...

    async def chat_json(
        self,
        *,
        model: str,
        system: str,
        user: str,
        schema: type[BaseModel],
        prompt_version: str,
        timeout_s: float,
    ) -> BaseModel:
        """Strict-JSON chat, validated with `schema`. Always processed in India (data residency
        "in"), so it may carry anonymised member health data. `timeout_s` is the total budget,
        retries included. Raises ProviderUnavailable or CompletionFailed."""
        ...
