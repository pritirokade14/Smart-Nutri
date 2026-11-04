"""FakeLLM: an LLMProvider for tests. Never calls the network."""

from __future__ import annotations

from pydantic import BaseModel


class FakeLLM:
    """`result` answers extract_label (counted in `calls`); `chat_result` answers chat_json
    (each call's kwargs recorded in `chat_calls`). An Exception result is raised."""

    def __init__(
        self,
        result: BaseModel | Exception | None = None,
        *,
        chat_result: BaseModel | Exception | None = None,
    ) -> None:
        self._result = result
        self._chat_result = chat_result
        self.calls = 0
        self.last_kwargs: dict[str, object] = {}
        self.chat_calls: list[dict[str, object]] = []

    async def extract_label(self, **kwargs: object) -> BaseModel:
        self.calls += 1
        self.last_kwargs = kwargs
        return _answer(self._result, "extract_label")

    async def chat_json(self, **kwargs: object) -> BaseModel:
        self.chat_calls.append(dict(kwargs))
        return _answer(self._chat_result, "chat_json")


def _answer(result: BaseModel | Exception | None, method: str) -> BaseModel:
    if result is None:
        raise AssertionError(f"FakeLLM.{method} called but no result was configured")
    if isinstance(result, Exception):
        raise result
    return result
