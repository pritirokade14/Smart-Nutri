"""FakeLLM: an LLMProvider for tests. Never calls the network."""

from __future__ import annotations

from pydantic import BaseModel


class FakeLLM:
    def __init__(self, result: BaseModel | Exception) -> None:
        self._result = result
        self.calls = 0
        self.last_kwargs: dict[str, object] = {}

    async def extract_label(self, **kwargs: object) -> BaseModel:
        self.calls += 1
        self.last_kwargs = kwargs
        if isinstance(self._result, Exception):
            raise self._result
        return self._result
