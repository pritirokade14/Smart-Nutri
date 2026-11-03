"""CallMissed (OpenAI-compatible) client. Only this module talks to the SDK.

Logs carry model, prompt version, latency, status and token counts. Never the image, the
prompt or messages, the API key or the response body (extracted label content, explanations).
"""

from __future__ import annotations

import asyncio
import base64
import copy
import logging
import math
import random
import time
from collections.abc import AsyncIterator, Callable
from typing import Annotated, Any

import httpx
import openai
from fastapi import Depends
from pydantic import BaseModel, SecretStr, ValidationError

from app.core.config import Settings, get_app_settings
from app.features.scans.schemas import (
    NutritionExtraction,
    _strictify,
    extraction_json_schema,
)
from app.integrations.providers import (
    CompletionFailed,
    ExtractionFailed,
    LLMProvider,
    ProviderUnavailable,
)

logger = logging.getLogger(__name__)

VISION_TIMEOUT_S = 30.0
CHAT_TIMEOUT_S = 15.0  # per attempt; chat_json's timeout_s bounds the whole call
MAX_429_TRIES = 3
MAX_UPSTREAM_RETRIES = 2
MAX_VALIDATION_ATTEMPTS = 2
_MAX_BACKOFF_S = 30.0
DEADLINE_S = 70.0
# Every chat_json request is processed in India (AGENTS rule 6, callmissed skill rule 3). A
# module constant, not a setting, so it can't be configured away. Deep-copied into each request.
CHAT_EXTRA_BODY: dict[str, Any] = {"provider": {"data_residency": "in"}}

_sleep = asyncio.sleep  # module alias so tests patch this, not asyncio.sleep globally


class CallMissedClient:
    def __init__(
        self,
        *,
        api_key: SecretStr | str | None,
        base_url: str,
        http_client: httpx.AsyncClient | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._clock = clock
        key = api_key.get_secret_value() if isinstance(api_key, SecretStr) else api_key
        if not key:
            raise ProviderUnavailable("not_configured")
        self._client = openai.AsyncOpenAI(
            api_key=key,
            base_url=base_url,
            http_client=http_client,
            max_retries=0,  # retries are ours, so they are counted and logged
            timeout=VISION_TIMEOUT_S,
        )

    def __repr__(self) -> str:
        return "CallMissedClient()"

    async def aclose(self) -> None:
        await self._client.close()

    async def extract_label(
        self,
        *,
        image: bytes,
        mime: str,
        prompt: str,
        prompt_version: str,
        schema: type[BaseModel],
        model: str,
    ) -> BaseModel:
        json_schema = (
            extraction_json_schema()
            if schema is NutritionExtraction
            else schema.model_json_schema()
        )
        data_url = f"data:{mime};base64,{base64.b64encode(image).decode('ascii')}"
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ]
        response_format = {
            "type": "json_schema",
            "json_schema": {"name": "nutrition_extraction", "strict": True, "schema": json_schema},
        }
        return await self._complete(
            event="callmissed_extract",
            model=model,
            prompt_version=prompt_version,
            messages=messages,
            response_format=response_format,
            schema=schema,
            budget_s=DEADLINE_S,
            attempt_timeout_s=VISION_TIMEOUT_S,
            failure=ExtractionFailed,
        )

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
        """Strict-JSON chat at temperature 0, always with data residency "in" (AGENTS rule 6).

        `timeout_s` is the whole budget: every attempt, retry and backoff fits inside it.
        Errors: 402 / 401 / 403 -> ProviderUnavailable; anything else -> CompletionFailed.
        """
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__,
                "strict": True,
                "schema": strict_json_schema(schema),
            },
        }
        return await self._complete(
            event="callmissed_chat",
            model=model,
            prompt_version=prompt_version,
            messages=messages,
            response_format=response_format,
            schema=schema,
            budget_s=timeout_s,
            attempt_timeout_s=CHAT_TIMEOUT_S,
            failure=CompletionFailed,
            extra_body=copy.deepcopy(CHAT_EXTRA_BODY),
        )

    async def _complete(
        self,
        *,
        event: str,
        model: str,
        prompt_version: str,
        messages: list[dict[str, Any]],
        response_format: dict[str, Any],
        schema: type[BaseModel],
        budget_s: float,
        attempt_timeout_s: float,
        failure: type[Exception],
        extra_body: dict[str, Any] | None = None,
    ) -> BaseModel:
        """One retrying, deadline-bound structured completion, validated with `schema`.

        429, 5xx, timeouts and connection errors are retried with backoff; 402 and 401/403
        raise ProviderUnavailable at once; everything else raises `failure`. Invalid output is
        retried once. Logs metadata only, never the messages or the response content.
        """
        start = self._clock()
        deadline = start + budget_s
        status = "error"
        tokens: tuple[int | None, int | None] = (None, None)
        try:
            validation_attempts = 0
            tries_429 = 0
            upstream_retries = 0
            while True:
                remaining = deadline - self._clock()
                if remaining <= 0:
                    status = "deadline"
                    raise failure("deadline exceeded")
                try:
                    completion = await self._client.chat.completions.create(
                        model=model,
                        messages=messages,  # type: ignore[arg-type]
                        response_format=response_format,  # type: ignore[arg-type]
                        temperature=0,
                        timeout=min(attempt_timeout_s, remaining),
                        extra_body=extra_body,
                    )
                except openai.APIStatusError as exc:
                    code = exc.status_code
                    if code == 402:
                        status = "insufficient_credits"
                        raise ProviderUnavailable("insufficient_credits") from None
                    if code in (401, 403):
                        status = "misconfigured"
                        raise ProviderUnavailable("misconfigured") from None
                    if code == 429:
                        tries_429 += 1
                        if tries_429 >= MAX_429_TRIES:
                            status = "rate_limited"
                            raise failure("rate limited") from None
                        await self._pause(_backoff(tries_429, exc.response), deadline, failure)
                        continue
                    if code >= 500:
                        upstream_retries += 1
                        if upstream_retries > MAX_UPSTREAM_RETRIES:
                            status = f"http_{code}"
                            raise failure("upstream error") from None
                        await self._pause(_backoff(upstream_retries, None), deadline, failure)
                        continue
                    status = f"http_{code}"
                    raise failure("upstream rejected request") from None
                except (openai.APITimeoutError, openai.APIConnectionError):
                    upstream_retries += 1
                    if upstream_retries > MAX_UPSTREAM_RETRIES:
                        status = "timeout"
                        raise failure("upstream timeout") from None
                    await self._pause(_backoff(upstream_retries, None), deadline, failure)
                    continue
                except openai.OpenAIError:
                    status = "sdk_error"
                    raise failure("upstream error") from None

                usage = completion.usage
                if usage is not None:
                    tokens = (usage.prompt_tokens, usage.completion_tokens)
                content = completion.choices[0].message.content if completion.choices else None
                try:
                    result = schema.model_validate_json(content or "")
                except ValidationError:
                    validation_attempts += 1
                    if validation_attempts >= MAX_VALIDATION_ATTEMPTS:
                        status = "invalid_output"
                        raise failure("invalid output") from None
                    continue
                status = "ok"
                return result
        finally:
            logger.info(
                "%s model=%s prompt_version=%s latency_ms=%d status=%s tokens_in=%s tokens_out=%s",
                event,
                model,
                prompt_version,
                (self._clock() - start) * 1000,
                status,
                tokens[0],
                tokens[1],
            )

    async def _pause(
        self, delay: float, deadline: float, failure: type[Exception] = ExtractionFailed
    ) -> None:
        if self._clock() + delay > deadline:
            raise failure("deadline exceeded")
        await _sleep(delay)


def strict_json_schema(schema: type[BaseModel]) -> dict[str, Any]:
    """`schema`'s JSON schema adapted for strict mode (used by chat_json).

    As for extraction: every object is closed (`additionalProperties: false`) and lists all
    its properties as required; defaults and numeric bounds are removed. Length and item-count
    bounds are removed too, because strict mode may reject them. Pydantic still enforces every
    bound when the response is parsed: an out-of-bounds answer is invalid output, never
    truncated.
    """
    node = copy.deepcopy(schema.model_json_schema())
    _strictify(node)
    _strip_size_bounds(node)
    return node


_SIZE_BOUNDS = ("minLength", "maxLength", "minItems", "maxItems")


def _strip_size_bounds(node: Any) -> None:
    if isinstance(node, list):
        for item in node:
            _strip_size_bounds(item)
        return
    if not isinstance(node, dict):
        return
    for key in _SIZE_BOUNDS:
        node.pop(key, None)
    for key, value in node.items():
        if key in ("properties", "$defs") and isinstance(value, dict):
            for sub in value.values():  # values are schema nodes; keys are names
                _strip_size_bounds(sub)
        else:
            _strip_size_bounds(value)


def _backoff(attempt: int, response: httpx.Response | None) -> float:
    if response is not None:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                value = float(retry_after)
                if math.isfinite(value):
                    return min(max(value, 0.0), _MAX_BACKOFF_S)
            except ValueError:
                pass
    return min(2.0**attempt, _MAX_BACKOFF_S) * random.uniform(0.5, 1.0)


class LazyCallMissed:
    """An `LLMProvider` that builds the CallMissedClient on first use (ruling R12).

    A request served from the extraction cache never needs a key or a connection; a missing
    key surfaces as ProviderUnavailable("not_configured") only when a paid call is attempted.
    """

    def __init__(self, *, api_key: SecretStr | None, base_url: str) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._client: CallMissedClient | None = None

    def __repr__(self) -> str:
        return "LazyCallMissed()"

    def _ensure(self) -> CallMissedClient:
        if self._client is None:
            self._client = CallMissedClient(api_key=self._api_key, base_url=self._base_url)
        return self._client

    async def extract_label(self, **kwargs: Any) -> BaseModel:
        return await self._ensure().extract_label(**kwargs)

    async def chat_json(self, **kwargs: Any) -> BaseModel:
        return await self._ensure().chat_json(**kwargs)

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


async def get_llm_provider(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AsyncIterator[LLMProvider]:
    """FastAPI dependency: a per-request, lazily built CallMissed provider, closed afterwards."""
    provider = LazyCallMissed(
        api_key=settings.callmissed_api_key, base_url=settings.callmissed_base_url
    )
    try:
        yield provider
    finally:
        await provider.aclose()
