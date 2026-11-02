import base64
import json
import logging

import httpx
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
        "confidence": 0.9, "unreadable_fields": [],
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


def make(responses) -> tuple[CallMissedClient, Mock]:
    mock = Mock(responses)
    http = httpx.AsyncClient(transport=httpx.MockTransport(mock.handler))
    return CallMissedClient(api_key=SECRET, base_url="https://cm.test/v1", http_client=http), mock


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    slept: list[float] = []

    async def fake_sleep(s):
        slept.append(s)

    monkeypatch.setattr(callmissed.asyncio, "sleep", fake_sleep)
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
