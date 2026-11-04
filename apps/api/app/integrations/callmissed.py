"""CallMissed (OpenAI-compatible) client. Only this module talks to the SDK.

Request shapes follow https://docs.callmissed.com (chat-completion, speech-to-text,
text-to-speech, tts-voices, api-speed, gateway-controls), read 2026-11-04. Model choices and
fallbacks: ADR 0021.

Logs carry model, prompt version, latency, status, fallback and token counts. Never the image,
the prompt or messages, the API key or the response body (extracted label content,
explanations, transcripts, spoken text).
"""

from __future__ import annotations

import asyncio
import base64
import copy
import logging
import math
import random
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from typing import Annotated, Any

import httpx
import openai
from fastapi import Depends
from pydantic import BaseModel, SecretStr, ValidationError

from app.core.config import Settings, get_app_settings
from app.features.scans.schemas import (
    NutritionExtraction,
    NutritionExtractionV2,
    _strictify,
    extraction_json_schema,
)
from app.integrations.providers import (
    MAX_TTS_CHARS,
    SPEECH_LANGUAGE_CODES,
    CompletionFailed,
    ExtractionFailed,
    LLMProvider,
    ProviderUnavailable,
    SpeechProvider,
    SpeechUnavailable,
)

logger = logging.getLogger(__name__)

VISION_TIMEOUT_S = 30.0
CHAT_TIMEOUT_S = 15.0  # per attempt; chat_json's timeout_s bounds the whole call
MAX_429_TRIES = 3
MAX_UPSTREAM_RETRIES = 2
MAX_VALIDATION_ATTEMPTS = 2
_MAX_BACKOFF_S = 30.0
DEADLINE_S = 70.0
SPEECH_TIMEOUT_S = 20.0  # per attempt, STT and TTS (callmissed skill)
# With a fallback model, the primary may use this share of the budget; the rest is kept for
# the one fallback attempt, so a slow primary cannot eat the whole deadline.
PRIMARY_BUDGET_SHARE = 0.6
_AUDIO_EXTENSIONS = {
    "audio/wav": "wav",
    "audio/mp4": "m4a",
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/mpeg": "mp3",
}
# Every chat_json request is processed in India (AGENTS rule 6, callmissed skill rule 3). A
# module constant, not a setting, so it can't be configured away. Deep-copied into each request.
# STT and TTS send it too (Ruling V1 S1): a spoken question or answer can carry health data.
# The docs list `provider` for chat, messages, responses and embeddings only; on the audio
# routes India-only processing is guaranteed by INDIA_PROCESSED_MODELS (and by the API key's
# "India-only processing" switch in the console, see docs/SETUP_ACCOUNTS.md).
CHAT_EXTRA_BODY: dict[str, Any] = {"provider": {"data_residency": "in"}}

# Models whose catalogue `processing` is "india" (GET /api/v1/models, read 2026-11-04). Calls
# that can carry member health data (chat_json, transcribe, synthesize) refuse any other model,
# primary or fallback, before a request is sent. "india_preferred" models (kimi-k2.5, gpt-6-*,
# gpt-oss-120b, ...) may be moved outside India, so they are not here. Keep in sync with the
# catalogue; ADR 0021 says how to add one.
INDIA_PROCESSED_MODELS: frozenset[str] = frozenset(
    {
        # chat (text and vision)
        "gpt-4o",
        "gemma-4-31b",
        "glm-5.3-flash",
        "deepseek-v4.1-flash-1017",
        "sarvam-105b",
        # speech-to-text (file transcription)
        "saaras:v4",
        "whisper",
        # text-to-speech (valid on POST /v1/audio/speech)
        "bulbul:v3",
        "bulbul:v4-flash",
        "gnani-timbre-v3.0",
    }
)
NOT_INDIA = "model_not_india_processed"

_sleep = asyncio.sleep  # module alias so tests patch this, not asyncio.sleep globally


def _not_india(*models: str | None) -> bool:
    return any(m is not None and m not in INDIA_PROCESSED_MODELS for m in models)


def _error_code(exc: openai.APIStatusError) -> str | None:
    code = getattr(exc, "code", None)
    return code if isinstance(code, str) else None


def _switchable(exc: openai.APIStatusError) -> bool:
    """A primary failure that a different model may not have: 5xx, or a 400 refusal because
    the model is not processed in India (e.g. after a deprecated id starts being answered by
    a successor that is not; gpt-4o's sunset is 2026-11-16)."""
    return exc.status_code >= 500 or (
        exc.status_code == 400 and _error_code(exc) == "region_unavailable"
    )


def speech_config(settings: Settings) -> dict[str, Any]:
    """CallMissedClient speech keyword arguments from settings."""
    return {
        "stt_model": settings.callmissed_stt_model,
        "stt_fallback_model": settings.callmissed_stt_fallback_model,
        "stt_languages": dict(settings.callmissed_stt_languages),
        "stt_fallback_languages": dict(settings.callmissed_stt_fallback_languages),
        "tts_model": settings.callmissed_tts_model,
        "tts_voices": dict(settings.callmissed_tts_voices),
        "tts_fallback_model": settings.callmissed_tts_fallback_model,
        "tts_fallback_voices": dict(settings.callmissed_tts_fallback_voices),
    }


class CallMissedClient:
    def __init__(
        self,
        *,
        api_key: SecretStr | str | None,
        base_url: str,
        http_client: httpx.AsyncClient | None = None,
        clock: Callable[[], float] = time.monotonic,
        stt_model: str | None = None,
        stt_fallback_model: str | None = None,
        stt_languages: Mapping[str, str] | None = None,
        stt_fallback_languages: Mapping[str, str] | None = None,
        tts_model: str | None = None,
        tts_voices: Mapping[str, str] | None = None,
        tts_fallback_model: str | None = None,
        tts_fallback_voices: Mapping[str, str] | None = None,
    ) -> None:
        self._clock = clock
        # Speech model ids come from settings (never literals); None = speech not configured.
        self._stt_model = stt_model
        self._stt_fallback_model = stt_fallback_model
        self._stt_languages = dict(
            SPEECH_LANGUAGE_CODES if stt_languages is None else stt_languages
        )
        self._stt_fallback_languages = dict(stt_fallback_languages or {})
        self._tts_model = tts_model
        self._tts_voices = dict(tts_voices or {})
        self._tts_fallback_model = tts_fallback_model
        self._tts_fallback_voices = dict(tts_fallback_voices or {})
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
        fallback_model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> BaseModel:
        """Vision extraction: a text part plus a base64 `image_url` part, strict JSON schema.

        A label photo carries no member health data, so any vision model may be used (the
        label eval compares models); the default is India-processed all the same.
        """
        json_schema = (
            extraction_json_schema(schema)
            if schema in (NutritionExtraction, NutritionExtractionV2)
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
        extra_body = {"reasoning_effort": reasoning_effort} if reasoning_effort else None
        return await self._complete(
            event="callmissed_extract",
            model=model,
            fallback_model=fallback_model,
            prompt_version=prompt_version,
            messages=messages,
            response_format=response_format,
            schema=schema,
            budget_s=DEADLINE_S,
            attempt_timeout_s=VISION_TIMEOUT_S,
            failure=ExtractionFailed,
            extra_body=extra_body,
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
        fallback_model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> BaseModel:
        """Strict-JSON chat at temperature 0, always with data residency "in" (AGENTS rule 6),
        and only on INDIA_PROCESSED_MODELS (primary and fallback).

        `timeout_s` is the whole budget: every attempt, retry, backoff and the one fallback
        attempt fit inside it. `reasoning_effort` is sent as is ("none" = thinking off where
        the model allows it).
        Errors: 402 / 401 / 403 / a non-India model -> ProviderUnavailable; anything else ->
        CompletionFailed.
        """
        if _not_india(model, fallback_model):
            logger.warning("callmissed_chat refused status=%s", NOT_INDIA)
            raise ProviderUnavailable(NOT_INDIA)
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
        extra_body = copy.deepcopy(CHAT_EXTRA_BODY)
        if reasoning_effort:
            extra_body["reasoning_effort"] = reasoning_effort
        return await self._complete(
            event="callmissed_chat",
            model=model,
            fallback_model=fallback_model,
            prompt_version=prompt_version,
            messages=messages,
            response_format=response_format,
            schema=schema,
            budget_s=timeout_s,
            attempt_timeout_s=CHAT_TIMEOUT_S,
            failure=CompletionFailed,
            extra_body=extra_body,
        )

    async def _complete(
        self,
        *,
        event: str,
        model: str,
        fallback_model: str | None,
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

        429 is retried with backoff. 5xx, timeouts, connection errors and a `region_unavailable`
        refusal switch to `fallback_model` once (it then gets a single try for those errors);
        without a fallback, 5xx and timeouts are retried on the same model. 402 and 401/403
        raise ProviderUnavailable at once; everything else raises `failure`. Invalid output is
        retried once. The server-side `models` fallback is not used: CallMissed never applies
        it to requests with `response_format`. Logs metadata only, never the content.
        """
        start = self._clock()
        deadline = start + budget_s
        fallback = fallback_model if fallback_model and fallback_model != model else None
        primary_end = start + budget_s * PRIMARY_BUDGET_SHARE if fallback else deadline
        current = model
        switched = False
        status = "error"
        tokens: tuple[int | None, int | None] = (None, None)
        validation_attempts = 0
        tries_429 = 0
        upstream_retries = 0

        def switch() -> None:
            nonlocal current, switched, upstream_retries
            current, switched = fallback, True  # type: ignore[assignment]
            upstream_retries = MAX_UPSTREAM_RETRIES  # the fallback is tried once

        try:
            while True:
                now = self._clock()
                if deadline - now <= 0:
                    status = "deadline"
                    raise failure("deadline exceeded")
                window = (deadline if switched else primary_end) - now
                if window <= 0:  # the primary used its share: hand the rest to the fallback
                    switch()
                    continue
                try:
                    completion = await self._client.chat.completions.create(
                        model=current,
                        messages=messages,  # type: ignore[arg-type]
                        response_format=response_format,  # type: ignore[arg-type]
                        temperature=0,
                        timeout=min(attempt_timeout_s, window),
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
                    if _switchable(exc) and fallback and not switched:
                        switch()
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
                    if fallback and not switched:
                        switch()
                        continue
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
                "%s model=%s prompt_version=%s latency_ms=%d status=%s fallback_from=%s "
                "tokens_in=%s tokens_out=%s",
                event,
                current,
                prompt_version,
                (self._clock() - start) * 1000,
                status,
                model if switched else "none",
                tokens[0],
                tokens[1],
            )

    # --- speech (SpeechProvider) -----------------------------------------------------------

    async def transcribe(self, audio: bytes, mime: str, language: str) -> str:
        """Speech-to-text (POST /v1/audio/transcriptions, multipart `file`, `model`,
        `language`) with the configured STT model, then once with the fallback on a 5xx or
        timeout. Only INDIA_PROCESSED_MODELS (Ruling V1 S1). The response field is `text`.

        Logs metadata only (model, latency, status, audio byte count), never the transcript.
        """
        _speech_language(language)  # en / hi / mr only
        model, fallback = self._stt_model, self._stt_fallback_model
        if not model:
            raise SpeechUnavailable("not_configured")
        if _not_india(model, fallback):
            logger.warning("callmissed_stt refused status=%s", NOT_INDIA)
            raise SpeechUnavailable(NOT_INDIA)
        ext = _AUDIO_EXTENSIONS.get(mime, "bin")

        def make(target: str) -> Callable[[float], Awaitable[str]]:
            languages = self._stt_languages if target == model else self._stt_fallback_languages
            hint = {"language": languages[language]} if languages.get(language) else {}

            async def call(timeout: float) -> str:
                result = await self._client.audio.transcriptions.create(
                    model=target,
                    file=(f"question.{ext}", audio, mime),
                    # Multipart: the SDK sends this as the form field provider[data_residency].
                    extra_body=copy.deepcopy(CHAT_EXTRA_BODY),
                    timeout=timeout,
                    **hint,  # type: ignore[arg-type]
                )
                text = getattr(result, "text", None)
                if not isinstance(text, str):
                    raise SpeechUnavailable("malformed_response")
                return text

            return call

        return await self._speech(
            "callmissed_stt", model, fallback, make, size=f"audio_bytes={len(audio)}"
        )

    async def synthesize(self, text: str, language: str) -> bytes:
        """Text-to-speech (POST /v1/audio/speech, JSON `model`, `input`, `voice`, `language`,
        `response_format: mp3`) with the configured model and the voice for `language`, then
        once with the fallback model and its voice on a 5xx or timeout. Only
        INDIA_PROCESSED_MODELS (Ruling V1 S1).

        `text` must be at most MAX_TTS_CHARS (bulbul's limit; callers split longer answers on
        sentence boundaries). Logs metadata only, never the text.
        """
        if len(text) > MAX_TTS_CHARS:
            raise ValueError(f"TTS input is limited to {MAX_TTS_CHARS} characters")
        code = _speech_language(language)
        model, voice = self._tts_model, self._tts_voices.get(language)
        if not model or not voice:
            raise SpeechUnavailable("not_configured")
        fallback_voice = self._tts_fallback_voices.get(language)
        fallback = self._tts_fallback_model if fallback_voice else None
        if _not_india(model, fallback):
            logger.warning("callmissed_tts refused status=%s", NOT_INDIA)
            raise SpeechUnavailable(NOT_INDIA)

        def make(target: str) -> Callable[[float], Awaitable[bytes]]:
            target_voice = voice if target == model else fallback_voice

            async def call(timeout: float) -> bytes:
                response = await self._client.audio.speech.create(
                    model=target,
                    input=text,
                    voice=target_voice,  # type: ignore[arg-type]  # CallMissed voices
                    response_format="mp3",
                    extra_body={**copy.deepcopy(CHAT_EXTRA_BODY), "language": code},
                    timeout=timeout,
                )
                audio = response.content
                if not is_mp3(audio):
                    raise SpeechUnavailable("malformed_response")
                return audio

            return call

        return await self._speech(
            "callmissed_tts", model, fallback, make, size=f"text_chars={len(text)}"
        )

    async def _speech[T](
        self,
        event: str,
        model: str,
        fallback: str | None,
        make: Callable[[str], Callable[[float], Awaitable[T]]],
        *,
        size: str,
    ) -> T:
        """Run one speech call with the skill's policy: 20 s per attempt; 429 -> backoff, at
        most 3 tries; 402 and other 4xx -> no retry. 5xx / timeout -> with a fallback model,
        one try on it; without one, at most 2 retries. So the worst case with a fallback (two
        attempts) is shorter than without (three). Every failure becomes
        SpeechUnavailable(reason)."""
        start = self._clock()
        status = "error"
        tries_429 = 0
        upstream_retries = 0
        current, switched = model, False
        call = make(model)

        def can_switch() -> bool:
            return fallback is not None and fallback != model and not switched

        def switch() -> None:
            nonlocal current, switched, call, upstream_retries
            current, switched = fallback, True  # type: ignore[assignment]
            call = make(current)
            upstream_retries = MAX_UPSTREAM_RETRIES  # the fallback is tried once

        try:
            while True:
                try:
                    result = await call(SPEECH_TIMEOUT_S)
                except SpeechUnavailable as exc:
                    status = exc.reason
                    raise
                except openai.APIStatusError as exc:
                    code = exc.status_code
                    if code == 402:
                        status = "insufficient_credits"
                        raise SpeechUnavailable("insufficient_credits") from None
                    if code in (401, 403):
                        status = "misconfigured"
                        raise SpeechUnavailable("misconfigured") from None
                    if code == 429:
                        tries_429 += 1
                        if tries_429 >= MAX_429_TRIES:
                            status = "rate_limited"
                            raise SpeechUnavailable("rate_limited") from None
                        await _sleep(_backoff(tries_429, exc.response))
                        continue
                    if _switchable(exc) and can_switch():
                        switch()
                        continue
                    if code >= 500:
                        upstream_retries += 1
                        if upstream_retries > MAX_UPSTREAM_RETRIES:
                            status = f"http_{code}"
                            raise SpeechUnavailable("upstream_error") from None
                        await _sleep(_backoff(upstream_retries, None))
                        continue
                    status = f"http_{code}"
                    raise SpeechUnavailable("rejected") from None
                except (openai.APITimeoutError, openai.APIConnectionError):
                    if can_switch():
                        switch()
                        continue
                    upstream_retries += 1
                    if upstream_retries > MAX_UPSTREAM_RETRIES:
                        status = "timeout"
                        raise SpeechUnavailable("timeout") from None
                    await _sleep(_backoff(upstream_retries, None))
                    continue
                except openai.OpenAIError:
                    status = "sdk_error"
                    raise SpeechUnavailable("sdk_error") from None
                status = "ok"
                return result
        finally:
            logger.info(
                "%s model=%s latency_ms=%d status=%s fallback_from=%s %s",
                event,
                current,
                (self._clock() - start) * 1000,
                status,
                model if switched else "none",
                size,
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


def _speech_language(language: str) -> str:
    try:
        return SPEECH_LANGUAGE_CODES[language]
    except KeyError:
        raise ValueError("language must be en, hi or mr") from None


def is_mp3(data: bytes) -> bool:
    """An ID3 tag or an MPEG audio frame sync (11 set bits) at the start."""
    if data.startswith(b"ID3"):
        return True
    return len(data) >= 2 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0


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
    `speech` takes CallMissedClient's speech keyword arguments (see `speech_config`).
    """

    def __init__(self, *, api_key: SecretStr | None, base_url: str, **speech: Any) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._speech = speech
        self._client: CallMissedClient | None = None

    def __repr__(self) -> str:
        return "LazyCallMissed()"

    def _ensure(self) -> CallMissedClient:
        if self._client is None:
            self._client = CallMissedClient(
                api_key=self._api_key, base_url=self._base_url, **self._speech
            )
        return self._client

    async def extract_label(self, **kwargs: Any) -> BaseModel:
        return await self._ensure().extract_label(**kwargs)

    async def chat_json(self, **kwargs: Any) -> BaseModel:
        return await self._ensure().chat_json(**kwargs)

    async def transcribe(self, audio: bytes, mime: str, language: str) -> str:
        return await self._speech_client().transcribe(audio, mime, language)

    async def synthesize(self, text: str, language: str) -> bytes:
        return await self._speech_client().synthesize(text, language)

    def _speech_client(self) -> CallMissedClient:
        try:
            return self._ensure()
        except ProviderUnavailable as exc:  # no key: speech is unavailable, not a crash
            raise SpeechUnavailable(exc.reason) from None

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


async def get_speech_provider(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AsyncIterator[SpeechProvider]:
    """FastAPI dependency: a per-request, lazily built CallMissed speech provider."""
    provider = LazyCallMissed(
        api_key=settings.callmissed_api_key,
        base_url=settings.callmissed_base_url,
        **speech_config(settings),
    )
    try:
        yield provider
    finally:
        await provider.aclose()
