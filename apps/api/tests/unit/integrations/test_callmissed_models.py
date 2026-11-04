"""CallMissed model choices, India-only allow-list and fallback-on-failure (ADR 0021).

Request bodies follow https://docs.callmissed.com (chat-completion, speech-to-text,
text-to-speech, tts-voices, api-speed, gateway-controls), read 2026-11-04. Every call goes to
an httpx MockTransport; nothing reaches the real CallMissed API.
"""

import json
import logging

import httpx
import pytest
from pydantic import BaseModel

from app.core.config import Settings
from app.features.scans.schemas import NutritionExtraction
from app.integrations import callmissed
from app.integrations.callmissed import (
    INDIA_PROCESSED_MODELS,
    CallMissedClient,
    speech_config,
)
from app.integrations.providers import (
    CompletionFailed,
    ExtractionFailed,
    ProviderUnavailable,
    SpeechUnavailable,
)

SECRET = "cm_test_secret_key"
MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\xff\xfb\x90\x00" * 8
WAV = b"RIFF....WAVEfmt "


class Answer(BaseModel):
    text: str


def _chat_ok(content: str = '{"text": "fine"}') -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "x",
            "object": "chat.completion",
            "created": 0,
            "model": "m",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content},
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        },
    )


def _extract_ok() -> httpx.Response:
    empty = {
        "product_name": None, "brand": None, "basis_detected": "unknown", "per_100g": None,
        "per_serving": None, "serving_size_g": None, "ingredients": [], "allergen_statement": None,
        "may_contain_statement": None, "claims": [], "veg_mark": None, "category_guess": None,
        "confidence": 0.9, "unreadable_fields": [], "upper_bound_fields": [],
        "per_100_unit": None, "serving_size_unit": None,
    }  # fmt: skip
    return _chat_ok(NutritionExtraction(**empty).model_dump_json())


def _region_unavailable() -> httpx.Response:
    return httpx.Response(
        400,
        json={
            "error": {
                "message": "Model 'gpt-4o' is not available with India-only processing.",
                "type": "invalid_request_error",
                "code": "region_unavailable",
            }
        },
    )


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class Mock:
    def __init__(self, responses) -> None:
        self.responses = list(responses)
        self.requests: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        r = self.responses[min(len(self.requests) - 1, len(self.responses) - 1)]
        if isinstance(r, Exception):
            raise r
        return r

    def bodies(self) -> list[dict]:
        return [json.loads(r.content) for r in self.requests]


def make(responses, *, clock: Clock | None = None, **kw) -> tuple[CallMissedClient, Mock]:
    mock = Mock(responses)
    http = httpx.AsyncClient(transport=httpx.MockTransport(mock.handler))
    if clock is not None:
        kw["clock"] = clock
    client = CallMissedClient(api_key=SECRET, base_url="https://cm.test/v1", http_client=http, **kw)
    return client, mock


def make_speech(responses, settings: Settings | None = None) -> tuple[CallMissedClient, Mock]:
    return make(responses, **speech_config(settings or Settings(_env_file=None)))


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    slept: list[float] = []

    async def fake_sleep(s):
        slept.append(s)

    monkeypatch.setattr(callmissed, "_sleep", fake_sleep)
    return slept


async def _chat(client, *, model="gpt-4o", fallback_model="gemma-4-31b", **kw):
    return await client.chat_json(
        model=model,
        fallback_model=fallback_model,
        reasoning_effort=kw.pop("reasoning_effort", "none"),
        system="S",
        user="U",
        schema=Answer,
        prompt_version="explanation_v1",
        timeout_s=kw.pop("timeout_s", 8.0),
    )


async def _extract(client, *, model="gpt-4o", fallback_model="glm-5.3-flash"):
    return await client.extract_label(
        image=b"\xff\xd8\xff\xe0jpeg",
        mime="image/jpeg",
        prompt="P",
        prompt_version="extraction_v1",
        schema=NutritionExtraction,
        model=model,
        fallback_model=fallback_model,
        reasoning_effort="none",
    )


# --- defaults and the allow-list --------------------------------------------------------------


def test_defaults_are_the_documented_india_models():
    s = Settings(_env_file=None)
    assert s.callmissed_extraction_model == "gpt-4o"
    assert s.callmissed_extraction_fallback_model == "glm-5.3-flash"
    assert s.callmissed_explanation_model == "gpt-4o"
    assert s.callmissed_explanation_fallback_model == "gemma-4-31b"
    assert s.callmissed_stt_model == "saaras:v4"
    assert s.callmissed_stt_fallback_model == "whisper"
    assert s.callmissed_tts_model == "bulbul:v3"
    assert s.callmissed_tts_fallback_model == "gnani-timbre-v3.0"
    assert s.callmissed_extraction_reasoning_effort == "none"
    assert s.callmissed_explanation_reasoning_effort == "none"


def test_every_default_model_is_india_processed():
    s = Settings(_env_file=None)
    defaults = [
        s.callmissed_extraction_model,
        s.callmissed_extraction_fallback_model,
        s.callmissed_explanation_model,
        s.callmissed_explanation_fallback_model,
        s.callmissed_stt_model,
        s.callmissed_stt_fallback_model,
        s.callmissed_tts_model,
        s.callmissed_tts_fallback_model,
    ]
    for model in defaults:
        assert model in INDIA_PROCESSED_MODELS, model


def test_allow_list_has_only_catalogue_india_models():
    # GET /api/v1/models, 2026-11-04: each of these has processing "india". Models marked
    # "india_preferred" (kimi-k2.5, gpt-6-sol, ...) may leave India, so they are not here.
    assert INDIA_PROCESSED_MODELS == frozenset(
        {
            "gpt-4o",
            "gemma-4-31b",
            "glm-5.3-flash",
            "deepseek-v4.1-flash-1017",
            "sarvam-105b",
            "saaras:v4",
            "whisper",
            "bulbul:v3",
            "bulbul:v4-flash",
            "gnani-timbre-v3.0",
        }
    )
    assert "kimi-k2.5" not in INDIA_PROCESSED_MODELS


def test_default_voices_and_language_codes_come_from_the_docs():
    s = Settings(_env_file=None)
    # tts-voices: bulbul:v3's recommended voice is ratan for en-IN and mr-IN, shubh for hi-IN.
    assert s.callmissed_tts_voices == {"en": "ratan", "hi": "shubh", "mr": "ratan"}
    # Gnani Timbre v3: every voice speaks en-IN, hi-IN and mr-IN.
    assert s.callmissed_tts_fallback_voices == {"en": "Chetana", "hi": "Chetana", "mr": "Chetana"}
    assert s.callmissed_stt_languages == {"en": "en-IN", "hi": "hi-IN", "mr": "mr-IN"}
    # Whisper's language codes are not documented: send none and let it auto-detect.
    assert s.callmissed_stt_fallback_languages == {}


def test_env_example_matches_the_defaults():
    from pathlib import Path

    example = Path(__file__).parents[3] / ".env.example"
    parsed, default = Settings(_env_file=example), Settings(_env_file=None)
    names = [n for n in Settings.model_fields if n.startswith("callmissed_") and "model" in n]
    names += [n for n in Settings.model_fields if n.endswith(("_voices", "_languages", "_effort"))]
    assert len(names) >= 14
    for name in names:
        assert getattr(parsed, name) == getattr(default, name), name


def test_voice_maps_parse_from_json_env(monkeypatch):
    monkeypatch.setenv("CALLMISSED_TTS_VOICES", '{"en": "ritu", "hi": "priya", "mr": "ritu"}')
    monkeypatch.setenv("CALLMISSED_EXPLANATION_FALLBACK_MODEL", "")
    s = Settings(_env_file=None)
    assert s.callmissed_tts_voices == {"en": "ritu", "hi": "priya", "mr": "ritu"}
    assert s.callmissed_explanation_fallback_model is None


def test_voice_map_must_cover_every_language(monkeypatch):
    monkeypatch.setenv("CALLMISSED_TTS_VOICES", '{"en": "ritu"}')
    with pytest.raises(ValueError):
        Settings(_env_file=None)


async def test_chat_refuses_a_model_that_is_not_india_processed():
    client, mock = make([_chat_ok()])
    with pytest.raises(ProviderUnavailable) as ei:
        await _chat(client, model="kimi-k2.5")
    assert ei.value.reason == "model_not_india_processed"
    assert mock.requests == []


async def test_chat_refuses_a_fallback_that_is_not_india_processed():
    client, mock = make([_chat_ok()])
    with pytest.raises(ProviderUnavailable) as ei:
        await _chat(client, fallback_model="gpt-6-sol")
    assert ei.value.reason == "model_not_india_processed"
    assert mock.requests == []


async def test_stt_refuses_a_model_that_is_not_india_processed():
    s = Settings(_env_file=None, callmissed_stt_model="deepgram-nova-3")
    client, mock = make_speech([httpx.Response(200, json={"text": "x"})], s)
    with pytest.raises(SpeechUnavailable) as ei:
        await client.transcribe(WAV, "audio/wav", "hi")
    assert ei.value.reason == "model_not_india_processed"
    assert mock.requests == []


async def test_tts_refuses_a_fallback_that_is_not_india_processed():
    s = Settings(_env_file=None, callmissed_tts_fallback_model="sonic-3.6")
    client, mock = make_speech([httpx.Response(200, content=MP3)], s)
    with pytest.raises(SpeechUnavailable) as ei:
        await client.synthesize("Avoid.", "en")
    assert ei.value.reason == "model_not_india_processed"
    assert mock.requests == []


async def test_extraction_is_not_health_data_so_any_vision_model_may_be_evaluated():
    client, mock = make([_extract_ok()])
    await _extract(client, model="kimi-k2.5", fallback_model=None)
    assert mock.bodies()[0]["model"] == "kimi-k2.5"


# --- chat request shape --------------------------------------------------------------------


async def test_chat_sends_reasoning_effort_and_residency_in_the_body():
    client, mock = make([_chat_ok()])
    await _chat(client, reasoning_effort="none")
    body = mock.bodies()[0]
    assert body["model"] == "gpt-4o"
    assert body["reasoning_effort"] == "none"
    assert body["provider"] == {"data_residency": "in"}
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["strict"] is True
    assert "models" not in body  # server-side fallback never applies to response_format


async def test_chat_omits_reasoning_effort_when_unset():
    client, mock = make([_chat_ok()])
    await _chat(client, reasoning_effort=None)
    assert "reasoning_effort" not in mock.bodies()[0]


async def test_extraction_sends_image_part_and_reasoning_effort():
    client, mock = make([_extract_ok()])
    await _extract(client)
    body = mock.bodies()[0]
    assert body["reasoning_effort"] == "none"
    part = body["messages"][0]["content"][1]
    assert part["type"] == "image_url"
    assert part["image_url"]["url"].startswith("data:image/jpeg;base64,")


# --- chat fallback -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "failure",
    [
        httpx.Response(503, json={"error": {"code": "provider_error"}}),
        httpx.Response(500, json={}),
        httpx.ReadTimeout("slow"),
        _region_unavailable(),
    ],
    ids=["503", "500", "timeout", "region_unavailable"],
)
async def test_chat_falls_back_once_on_upstream_failure(failure):
    client, mock = make([failure, _chat_ok()])
    out = await _chat(client)
    assert isinstance(out, Answer)
    models = [b["model"] for b in mock.bodies()]
    assert models == ["gpt-4o", "gemma-4-31b"]
    for body in mock.bodies():
        assert body["provider"] == {"data_residency": "in"}
        assert body["reasoning_effort"] == "none"


async def test_chat_fallback_is_tried_only_once():
    client, mock = make([httpx.Response(503, json={})])
    with pytest.raises(CompletionFailed):
        await _chat(client)
    assert [b["model"] for b in mock.bodies()] == ["gpt-4o", "gemma-4-31b"]


async def test_chat_without_fallback_keeps_retrying_the_primary():
    client, mock = make([httpx.Response(503, json={})])
    with pytest.raises(CompletionFailed):
        await _chat(client, fallback_model=None)
    assert [b["model"] for b in mock.bodies()] == ["gpt-4o"] * 3


@pytest.mark.parametrize(
    ("status", "reason"),
    [(402, "insufficient_credits"), (401, "misconfigured"), (403, "misconfigured")],
)
async def test_chat_never_falls_back_on_billing_or_auth_errors(status, reason):
    client, mock = make([httpx.Response(status, json={})])
    with pytest.raises(ProviderUnavailable) as ei:
        await _chat(client)
    assert ei.value.reason == reason
    assert len(mock.requests) == 1


async def test_chat_never_falls_back_on_other_400s():
    client, mock = make([httpx.Response(400, json={"error": {"code": "context_length_exceeded"}})])
    with pytest.raises(CompletionFailed):
        await _chat(client)
    assert len(mock.requests) == 1


async def test_chat_primary_leaves_time_for_the_fallback():
    clock = Clock()
    client, _ = make([httpx.ReadTimeout("slow"), _chat_ok()], clock=clock)
    seen: list[tuple[str, float]] = []
    real = client._client.chat.completions.create

    async def spy(**kw):
        seen.append((kw["model"], kw["timeout"]))
        if kw["model"] == "gpt-4o":
            clock.now += kw["timeout"]  # the primary times out after its whole share
        return await real(**kw)

    client._client.chat.completions.create = spy  # type: ignore[method-assign]
    await _chat(client, timeout_s=8.0)
    (primary, t1), (fallback, t2) = seen
    assert (primary, fallback) == ("gpt-4o", "gemma-4-31b")
    assert t1 < 8.0
    assert t2 > 0 and t1 + t2 <= 8.0


async def test_chat_no_fallback_when_the_deadline_has_passed():
    clock = Clock()
    client, mock = make([httpx.Response(503, json={}), _chat_ok()], clock=clock)
    real = client._client.chat.completions.create

    async def spy(**kw):
        clock.now += 9.0  # past the whole 8 s budget
        return await real(**kw)

    client._client.chat.completions.create = spy  # type: ignore[method-assign]
    with pytest.raises(CompletionFailed):
        await _chat(client, timeout_s=8.0)
    assert len(mock.requests) == 1


async def test_chat_fallback_is_logged_with_metadata_only(caplog):
    caplog.set_level(logging.INFO, logger="app.integrations.callmissed")
    client, _ = make([httpx.Response(503, json={}), _chat_ok()])
    await _chat(client)
    text = caplog.text
    assert "model=gemma-4-31b" in text and "fallback_from=gpt-4o" in text
    assert "status=ok" in text and "tokens_in=10 tokens_out=5" in text
    assert '"fine"' not in text and SECRET not in text


async def test_extraction_falls_back_on_5xx():
    client, mock = make([httpx.Response(503, json={}), _extract_ok()])
    out = await _extract(client)
    assert isinstance(out, NutritionExtraction)
    assert [b["model"] for b in mock.bodies()] == ["gpt-4o", "glm-5.3-flash"]


async def test_extraction_fallback_failure_is_extraction_failed():
    client, mock = make([httpx.Response(503, json={})])
    with pytest.raises(ExtractionFailed):
        await _extract(client)
    assert [b["model"] for b in mock.bodies()] == ["gpt-4o", "glm-5.3-flash"]


# --- speech request shapes and fallback ----------------------------------------------------


def _form(request: httpx.Request) -> dict[str, str]:
    """The non-file multipart fields of a request."""
    out: dict[str, str] = {}
    content_type = request.headers["content-type"]
    boundary = content_type.split("boundary=")[1].encode()
    for part in request.content.split(b"--" + boundary):
        head, _, value = part.partition(b"\r\n\r\n")
        if b'name="' not in head or b"filename=" in head:
            continue
        name = head.split(b'name="')[1].split(b'"')[0].decode()
        out[name] = value.rstrip(b"\r\n").decode()
    return out


@pytest.mark.parametrize(("language", "code"), [("en", "en-IN"), ("hi", "hi-IN"), ("mr", "mr-IN")])
async def test_stt_multipart_fields_match_the_docs(language, code):
    client, mock = make_speech([httpx.Response(200, json={"text": "chini kitni hai"})])
    text = await client.transcribe(WAV, "audio/wav", language)
    assert text == "chini kitni hai"
    req = mock.requests[0]
    assert req.url.path == "/v1/audio/transcriptions"
    assert b'name="file"; filename="question.wav"' in req.content
    form = _form(req)
    assert form["model"] == "saaras:v4"
    assert form["language"] == code
    assert set(form) <= {"model", "language", "provider[data_residency]"}


async def test_stt_falls_back_to_whisper_without_a_language_code():
    client, mock = make_speech(
        [
            httpx.Response(503, json={"error": {"code": "upstream_timeout"}}),
            httpx.Response(200, json={"text": "ok"}),
        ]
    )
    assert await client.transcribe(WAV, "audio/wav", "mr") == "ok"
    first, second = (_form(r) for r in mock.requests)
    assert first["model"] == "saaras:v4" and first["language"] == "mr-IN"
    assert second["model"] == "whisper" and "language" not in second


async def test_stt_fallback_on_timeout_is_tried_once():
    client, mock = make_speech([httpx.ReadTimeout("slow")])
    with pytest.raises(SpeechUnavailable) as ei:
        await client.transcribe(WAV, "audio/wav", "en")
    assert ei.value.reason == "timeout"
    assert [_form(r)["model"] for r in mock.requests] == ["saaras:v4", "whisper"]


async def test_stt_never_falls_back_on_402():
    client, mock = make_speech([httpx.Response(402, json={})])
    with pytest.raises(SpeechUnavailable):
        await client.transcribe(WAV, "audio/wav", "en")
    assert len(mock.requests) == 1


@pytest.mark.parametrize(
    ("language", "code", "voice"),
    [("en", "en-IN", "ratan"), ("hi", "hi-IN", "shubh"), ("mr", "mr-IN", "ratan")],
)
async def test_tts_body_matches_the_docs(language, code, voice):
    client, mock = make_speech([httpx.Response(200, content=MP3)])
    assert await client.synthesize("Avoid.", language) == MP3
    req = mock.requests[0]
    assert req.url.path == "/v1/audio/speech"
    body = json.loads(req.content)
    assert body == {
        "model": "bulbul:v3",
        "input": "Avoid.",
        "voice": voice,
        "language": code,
        "response_format": "mp3",
        "provider": {"data_residency": "in"},
    }


async def test_tts_falls_back_to_gnani_with_its_own_voice():
    client, mock = make_speech([httpx.Response(503, json={}), httpx.Response(200, content=MP3)])
    assert await client.synthesize("Avoid.", "mr") == MP3
    first, second = (json.loads(r.content) for r in mock.requests)
    assert (first["model"], first["voice"]) == ("bulbul:v3", "ratan")
    assert (second["model"], second["voice"], second["language"]) == (
        "gnani-timbre-v3.0",
        "Chetana",
        "mr-IN",
    )
    assert second["response_format"] == "mp3"


async def test_tts_fallback_failure_is_unavailable_after_two_calls():
    client, mock = make_speech([httpx.Response(503, json={})])
    with pytest.raises(SpeechUnavailable) as ei:
        await client.synthesize("Avoid.", "hi")
    assert ei.value.reason == "upstream_error"
    assert len(mock.requests) == 2


async def test_speech_fallback_is_logged(caplog):
    caplog.set_level(logging.INFO, logger="app.integrations.callmissed")
    client, _ = make_speech([httpx.Response(503, json={}), httpx.Response(200, content=MP3)])
    await client.synthesize("Do not log me.", "en")
    assert "model=gnani-timbre-v3.0" in caplog.text and "fallback_from=bulbul:v3" in caplog.text
    assert "Do not log me" not in caplog.text
