"""CallMissed (OpenAI-compatible) client. Only this module talks to the SDK.

Logs carry model, prompt version, latency, status and token counts. Never the image, the
API key or the response body (extracted label content).
"""

from __future__ import annotations

import asyncio
import base64
import logging
import random
import time

import httpx
import openai
from pydantic import BaseModel, SecretStr, ValidationError

from app.features.scans.schemas import NutritionExtraction, extraction_json_schema
from app.integrations.providers import ExtractionFailed, ProviderUnavailable

logger = logging.getLogger(__name__)

VISION_TIMEOUT_S = 30.0
MAX_429_TRIES = 3
MAX_UPSTREAM_RETRIES = 2
MAX_VALIDATION_ATTEMPTS = 2
_MAX_BACKOFF_S = 30.0


class CallMissedClient:
    def __init__(
        self,
        *,
        api_key: SecretStr | str | None,
        base_url: str,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
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

        start = time.monotonic()
        status = "error"
        tokens: tuple[int | None, int | None] = (None, None)
        try:
            validation_attempts = 0
            tries_429 = 0
            upstream_retries = 0
            while True:
                try:
                    completion = await self._client.chat.completions.create(
                        model=model,
                        messages=messages,  # type: ignore[arg-type]
                        response_format=response_format,  # type: ignore[arg-type]
                        temperature=0,
                        timeout=VISION_TIMEOUT_S,
                    )
                except openai.APIStatusError as exc:
                    code = exc.status_code
                    if code == 402:
                        status = "insufficient_credits"
                        raise ProviderUnavailable("insufficient_credits") from None
                    if code == 429:
                        tries_429 += 1
                        if tries_429 >= MAX_429_TRIES:
                            status = "rate_limited"
                            raise ExtractionFailed("rate limited") from None
                        await asyncio.sleep(_backoff(tries_429, exc.response))
                        continue
                    if code >= 500:
                        upstream_retries += 1
                        if upstream_retries > MAX_UPSTREAM_RETRIES:
                            status = f"http_{code}"
                            raise ExtractionFailed("upstream error") from None
                        await asyncio.sleep(_backoff(upstream_retries, None))
                        continue
                    status = f"http_{code}"
                    raise ExtractionFailed("upstream rejected request") from None
                except (openai.APITimeoutError, openai.APIConnectionError):
                    upstream_retries += 1
                    if upstream_retries > MAX_UPSTREAM_RETRIES:
                        status = "timeout"
                        raise ExtractionFailed("upstream timeout") from None
                    await asyncio.sleep(_backoff(upstream_retries, None))
                    continue

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
                        raise ExtractionFailed("invalid output") from None
                    continue
                status = "ok"
                return result
        finally:
            logger.info(
                "callmissed_extract model=%s prompt_version=%s latency_ms=%d status=%s "
                "tokens_in=%s tokens_out=%s",
                model,
                prompt_version,
                (time.monotonic() - start) * 1000,
                status,
                tokens[0],
                tokens[1],
            )


def _backoff(attempt: int, response: httpx.Response | None) -> float:
    if response is not None:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return min(max(float(retry_after), 0.0), _MAX_BACKOFF_S)
            except ValueError:
                pass
    return min(2.0**attempt, _MAX_BACKOFF_S) * random.uniform(0.5, 1.0)
