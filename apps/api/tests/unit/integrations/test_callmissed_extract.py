import base64
import json
import logging

import httpx
import openai
import pytest

from app.features.scans.schemas import NutritionExtraction
from app.integrations import callmissed
from app.integrations.callmissed import CallMissedClient
from app.integrations.providers import ExtractionFailed, ProviderUnavailable

IMAGE = b"\xff\xd8\xff\xe0" + b"fakejpegbytes" * 20
B64 = base64.b64encode(IMAGE).decode()
SECRET = "cm_test_secret_key"


def _extraction(**over) -> NutritionExtraction:
    base = {
        "product_name": None, "brand": None, "basis_detected": "unknown", "per_100g": None,
        "per_serving": None, "serving_size_g": None, "ingredients": [], "allergen_statement": None,
        "may_contain_statement": None, "claims": [], "veg_mark": None, "category_guess": None,
        "confidence": 0.9, "unreadable_fields": [], "upper_bound_fields": [],
        "per_100_unit": None, "serving_size_unit": None,
    }  # fmt: skip
    return NutritionExtraction(**{**base, **over})


def _valid_content() -> str:
    return _extraction().model_dump_json()


def _ok(content: str | None = None) -> httpx.Response:
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
                    "message": {"role": "assistant", "content": content or _valid_content()},
                }
            ],
            "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
        },
    )


class Mock:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        r = self.responses[min(len(self.requests) - 1, len(self.responses) - 1)]
        if isinstance(r, Exception):
            raise r
        return r

    @property
    def calls(self) -> int:
        return len(self.requests)

    def last_json(self) -> dict:
        return json.loads(self.requests[-1].content)


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def make(responses, clock=None) -> tuple[CallMissedClient, Mock]:
    mock = Mock(responses)
    http = httpx.AsyncClient(transport=httpx.MockTransport(mock.handler))
    kw = {"clock": clock} if clock else {}
    return (
        CallMissedClient(api_key=SECRET, base_url="https://cm.test/v1", http_client=http, **kw),
        mock,
    )


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    slept: list[float] = []

    async def fake_sleep(s):
        slept.append(s)

    monkeypatch.setattr(callmissed, "_sleep", fake_sleep)
    return slept


async def _call(client):
    return await client.extract_label(
        image=IMAGE,
        mime="image/jpeg",
        prompt="P",
        prompt_version="extraction_v1",
        schema=NutritionExtraction,
        model="m",
    )


async def test_request_shape():
    client, mock = make([_ok()])
    result = await _call(client)
    assert isinstance(result, NutritionExtraction)
    body = mock.last_json()
    assert body["model"] == "m"
    assert body["temperature"] == 0
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["strict"] is True
    assert body["response_format"]["json_schema"]["schema"]["additionalProperties"] is False
    content = body["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "P"}
    assert content[1]["image_url"]["url"] == f"data:image/jpeg;base64,{B64}"
    assert mock.requests[0].headers["authorization"] == f"Bearer {SECRET}"


async def test_retry_once_then_fail_on_invalid_json():
    client, mock = make([_ok("not json")])
    with pytest.raises(ExtractionFailed):
        await _call(client)
    assert mock.calls == 2


async def test_invalid_then_valid_succeeds():
    client, mock = make([_ok("{}"), _ok()])
    assert isinstance(await _call(client), NutritionExtraction)
    assert mock.calls == 2


async def test_402_raises_unavailable_without_retry():
    client, mock = make([httpx.Response(402, json={"error": {"code": "insufficient_credits"}})])
    with pytest.raises(ProviderUnavailable) as ei:
        await _call(client)
    assert ei.value.reason == "insufficient_credits"
    assert mock.calls == 1


async def test_429_backoff_then_success(no_sleep):
    client, mock = make([httpx.Response(429, headers={"Retry-After": "2"}, json={}), _ok()])
    await _call(client)
    assert mock.calls == 2
    assert no_sleep == [2.0]


async def test_429_gives_up_after_three_tries():
    client, mock = make([httpx.Response(429, json={})])
    with pytest.raises(ExtractionFailed):
        await _call(client)
    assert mock.calls == 3


async def test_5xx_retried_twice_then_failed():
    client, mock = make([httpx.Response(503, json={})])
    with pytest.raises(ExtractionFailed):
        await _call(client)
    assert mock.calls == 3


async def test_timeout_retried_then_failed():
    client, mock = make([httpx.ReadTimeout("slow")])
    with pytest.raises(ExtractionFailed):
        await _call(client)
    assert mock.calls == 3


async def test_5xx_then_success():
    client, mock = make([httpx.Response(500, json={}), _ok()])
    await _call(client)
    assert mock.calls == 2


async def test_log_has_no_body_image_or_key(caplog):
    caplog.set_level(logging.DEBUG)
    client, _ = make([_ok(_extraction(ingredients=["sugar, milk"]).model_dump_json())])
    await _call(client)
    text = "\n".join(r.getMessage() for r in caplog.records)
    assert "callmissed_extract" in text and "prompt_version=extraction_v1" in text
    assert "model=m" in text and "status=ok" in text
    for forbidden in (B64, SECRET, "sugar, milk", "per_100g"):
        assert forbidden not in text


async def test_secret_not_in_repr_or_errors():
    client, _ = make([httpx.Response(500, json={})])
    assert SECRET not in repr(client)
    with pytest.raises(ExtractionFailed) as ei:
        await _call(client)
    assert SECRET not in repr(ei.value)


async def test_400_fails_without_retry():
    client, mock = make([httpx.Response(400, json={})])
    with pytest.raises(ExtractionFailed):
        await _call(client)
    assert mock.calls == 1


@pytest.mark.parametrize("code", [401, 403])
async def test_auth_errors_are_misconfigured_no_retry(code):
    client, mock = make([httpx.Response(code, json={})])
    with pytest.raises(ProviderUnavailable) as ei:
        await _call(client)
    assert ei.value.reason == "misconfigured"
    assert mock.calls == 1


async def test_connection_error_retried_then_failed():
    client, mock = make([httpx.ConnectError("down")])
    with pytest.raises(ExtractionFailed):
        await _call(client)
    assert mock.calls == 3


def test_missing_key_is_not_configured():
    for key in (None, ""):
        with pytest.raises(ProviderUnavailable) as ei:
            CallMissedClient(api_key=key, base_url="https://cm.test/v1")
        assert ei.value.reason == "not_configured"


async def test_retry_after_capped_at_30(no_sleep):
    client, _ = make([httpx.Response(429, headers={"Retry-After": "999"}, json={}), _ok()])
    await _call(client)
    assert no_sleep == [30.0]


async def test_retry_after_nan_uses_normal_backoff(no_sleep):
    client, _ = make([httpx.Response(429, headers={"Retry-After": "nan"}, json={}), _ok()])
    await _call(client)
    assert len(no_sleep) == 1 and 1.0 <= no_sleep[0] <= 2.0


async def test_malformed_200_body_maps_to_extraction_failed():
    client, _ = make([httpx.Response(200, json={"unexpected": True})])
    with pytest.raises(ExtractionFailed) as ei:
        await _call(client)
    assert str(ei.value) in ("upstream error", "invalid output")
    assert "unexpected" not in str(ei.value)


async def test_sdk_error_fallback_hides_sdk_text(monkeypatch):
    client, _ = make([_ok()])

    async def boom(**_):
        raise openai.OpenAIError("sdk internals cm_leak")

    monkeypatch.setattr(client._client.chat.completions, "create", boom)
    with pytest.raises(ExtractionFailed) as ei:
        await _call(client)
    assert str(ei.value) == "upstream error"
    assert "cm_leak" not in str(ei.value)
    assert ei.value.__cause__ is None


async def test_aclose_closes_http_client():
    client, _ = make([_ok()])
    await client.aclose()
    assert client._client.is_closed()


async def test_deadline_stops_mixed_failures(monkeypatch):
    clock = Clock()

    async def fake_sleep(s):
        clock.now += s

    monkeypatch.setattr(callmissed, "_sleep", fake_sleep)
    # each attempt burns 25 s on the fake clock: 429, 503, then invalid output
    seq = [httpx.Response(429, headers={"Retry-After": "20"}, json={}), httpx.Response(503, json={}),
           _ok("{}"), _ok("{}")]  # fmt: skip
    client, mock = make(seq, clock=clock)
    orig = mock.handler

    def handler(request):
        clock.now += 25
        return orig(request)

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = CallMissedClient(
        api_key=SECRET, base_url="https://cm.test/v1", http_client=http, clock=clock
    )
    start = clock.now
    with pytest.raises(ExtractionFailed):
        await _call(client)
    assert clock.now - start <= callmissed.DEADLINE_S
    assert mock.calls < 4


async def test_per_attempt_timeout_is_min_of_30_and_remaining():
    clock = Clock()
    client, _ = make([httpx.Response(503, json={}), _ok()], clock=clock)
    seen: list[float] = []
    real = client._client.chat.completions.create

    async def spy(**kw):
        seen.append(kw["timeout"])
        clock.now += 50  # first attempt eats 50 s
        return await real(**kw)

    client._client.chat.completions.create = spy  # type: ignore[method-assign]
    await _call(client)
    assert seen[0] == 30.0
    assert seen[1] <= 20.0


async def test_log_includes_token_counts(caplog):
    caplog.set_level(logging.INFO)
    client, _ = make([_ok()])
    await _call(client)
    text = "\n".join(r.getMessage() for r in caplog.records)
    assert "tokens_in=11" in text and "tokens_out=7" in text
