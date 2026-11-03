"""CallMissedClient.transcribe / synthesize (Plan 7 Task 1).

Every call goes to an httpx MockTransport; nothing reaches the real CallMissed API.
"""

import json
import logging
from dataclasses import dataclass, field

import httpx
import pytest

from app.integrations import callmissed
from app.integrations.callmissed import CallMissedClient
from app.integrations.providers import SpeechProvider, SpeechUnavailable

SECRET = "cm_test_secret_key"
MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\xff\xfb\x90\x00" * 8


@dataclass
class MockCM:
    client: CallMissedClient
    responses: list
    requests: list[httpx.Request] = field(default_factory=list)

    @property
    def last_request(self) -> httpx.Request:
        return self.requests[-1]


def _make(responses) -> MockCM:
    mock: MockCM

    def handler(request: httpx.Request) -> httpx.Response:
        mock.requests.append(request)
        r = mock.responses[min(len(mock.requests) - 1, len(mock.responses) - 1)]
        if isinstance(r, Exception):
            raise r
        return r

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = CallMissedClient(
        api_key=SECRET,
        base_url="https://cm.test/v1",
        http_client=http,
        stt_model="saaras:v4",
        tts_model="bulbul:v3",
        tts_voice="anushka",
    )
    mock = MockCM(client=client, responses=list(responses))
    return mock


def _stt_ok(text: str = "chini kitni hai") -> httpx.Response:
    return httpx.Response(200, json={"text": text})


def _tts_ok() -> httpx.Response:
    return httpx.Response(200, content=MP3, headers={"content-type": "audio/mpeg"})


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    slept: list[float] = []

    async def fake_sleep(s):
        slept.append(s)

    monkeypatch.setattr(callmissed, "_sleep", fake_sleep)
    return slept


@pytest.fixture
def mock_cm():
    return _make([_stt_ok(), _tts_ok()])


@pytest.fixture
def mock_cm_402():
    return _make([httpx.Response(402, json={"error": {"code": "insufficient_credits"}})])


def test_client_satisfies_speech_provider():
    client = _make([_stt_ok()]).client
    provider: SpeechProvider = client  # static check; runtime: methods exist
    assert callable(provider.transcribe) and callable(provider.synthesize)


async def test_transcribe_sends_model_and_language_hint(mock_cm):
    text = await mock_cm.client.transcribe(b"RIFF....WAVE", "audio/wav", "hi")
    req = mock_cm.last_request
    assert req.url.path == "/v1/audio/transcriptions"
    assert b'name="model"' in req.content and b"saaras:v4" in req.content
    assert b"hi-IN" in req.content and text == "chini kitni hai"
    assert req.headers["authorization"] == f"Bearer {SECRET}"


@pytest.mark.parametrize(("language", "hint"), [("en", b"en-IN"), ("mr", b"mr-IN")])
async def test_transcribe_language_hints(language, hint):
    mock = _make([_stt_ok()])
    await mock.client.transcribe(b"RIFF....WAVE", "audio/wav", language)
    assert hint in mock.last_request.content


async def test_transcribe_rejects_unknown_language():
    mock = _make([_stt_ok()])
    with pytest.raises(ValueError):
        await mock.client.transcribe(b"RIFF....WAVE", "audio/wav", "fr")
    assert mock.requests == []


async def test_synthesize_rejects_text_over_2500_chars(mock_cm):
    with pytest.raises(ValueError):
        await mock_cm.client.synthesize("a" * 2501, "en")
    assert mock_cm.requests == []


async def test_synthesize_returns_mp3_bytes():
    mock = _make([_tts_ok()])
    audio = await mock.client.synthesize("Avoid.", "en")
    assert audio.startswith(b"ID3") or audio[:2] == b"\xff\xfb"
    body = json.loads(mock.last_request.content)
    assert body["model"] == "bulbul:v3"
    assert mock.last_request.url.path == "/v1/audio/speech"
    assert body["input"] == "Avoid."
    assert body["response_format"] == "mp3"
    assert body["language"] == "en-IN"
    assert body["voice"] == "anushka"


async def test_synthesize_rejects_non_audio_response():
    mock = _make([httpx.Response(200, content=b"<html>oops</html>")])
    with pytest.raises(SpeechUnavailable):
        await mock.client.synthesize("Avoid.", "en")


async def test_402_raises_speech_unavailable(mock_cm_402):
    with pytest.raises(SpeechUnavailable):
        await mock_cm_402.client.transcribe(b"RIFF....WAVE", "audio/wav", "en")
    assert len(mock_cm_402.requests) == 1  # never retried


async def test_402_on_tts_raises_speech_unavailable(mock_cm_402):
    with pytest.raises(SpeechUnavailable):
        await mock_cm_402.client.synthesize("Avoid.", "en")
    assert len(mock_cm_402.requests) == 1


async def test_429_retried_three_times_then_unavailable(no_sleep):
    mock = _make([httpx.Response(429, json={})])
    with pytest.raises(SpeechUnavailable):
        await mock.client.transcribe(b"RIFF....WAVE", "audio/wav", "en")
    assert len(mock.requests) == 3
    assert len(no_sleep) == 2


async def test_429_then_success():
    mock = _make([httpx.Response(429, json={}), _stt_ok("ok")])
    assert await mock.client.transcribe(b"RIFF....WAVE", "audio/wav", "en") == "ok"


async def test_5xx_retried_twice_then_unavailable():
    mock = _make([httpx.Response(503, json={})])
    with pytest.raises(SpeechUnavailable):
        await mock.client.synthesize("Avoid.", "en")
    assert len(mock.requests) == 3  # first try + 2 retries


async def test_timeout_retried_then_unavailable():
    mock = _make([httpx.ReadTimeout("slow")])
    with pytest.raises(SpeechUnavailable):
        await mock.client.transcribe(b"RIFF....WAVE", "audio/wav", "en")
    assert len(mock.requests) == 3


async def test_other_4xx_not_retried():
    mock = _make([httpx.Response(400, json={"error": "bad audio"})])
    with pytest.raises(SpeechUnavailable):
        await mock.client.transcribe(b"RIFF....WAVE", "audio/wav", "en")
    assert len(mock.requests) == 1


async def test_logs_metadata_only(caplog):
    caplog.set_level(logging.INFO, logger="app.integrations.callmissed")
    mock = _make([_stt_ok("chini kitni hai"), _tts_ok()])
    await mock.client.transcribe(b"RIFF....WAVE", "audio/wav", "hi")
    await mock.client.synthesize("Avoid this product.", "hi")
    assert "callmissed_stt" in caplog.text and "callmissed_tts" in caplog.text
    assert "saaras:v4" in caplog.text and "bulbul:v3" in caplog.text
    assert "chini" not in caplog.text
    assert "Avoid this product" not in caplog.text
    assert SECRET not in caplog.text


async def test_speech_without_configured_models_is_unavailable():
    http = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: _stt_ok()))
    client = CallMissedClient(api_key=SECRET, base_url="https://cm.test/v1", http_client=http)
    with pytest.raises(SpeechUnavailable):
        await client.transcribe(b"RIFF....WAVE", "audio/wav", "en")
