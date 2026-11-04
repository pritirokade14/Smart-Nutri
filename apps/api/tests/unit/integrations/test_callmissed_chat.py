"""CallMissedClient.chat_json: strict JSON chat with data residency "in" (Plan 5 T7a).

Every call goes to an httpx MockTransport; nothing reaches the real CallMissed API.
"""

import json
import logging
from typing import Literal

import httpx
import pytest
from pydantic import BaseModel, Field

from app.integrations import callmissed
from app.integrations.callmissed import CHAT_EXTRA_BODY, CallMissedClient
from app.integrations.providers import CompletionFailed, ProviderUnavailable

SECRET = "cm_test_secret_key"
SYSTEM = "SYSTEM PROMPT about member_1"
USER = '{"members": [{"ref": "member_1", "conditions_hint": "diabetes-secret"}]}'


class Echo(BaseModel):
    ref: str
    status: Literal["ok", "caution", "unknown", "avoid"]


class Out(BaseModel):
    text: str = Field(max_length=50)
    tips: list[str] = Field(max_length=3)
    members: list[Echo]


def _valid() -> str:
    return Out(
        text="fine", tips=["a"], members=[Echo(ref="member_1", status="ok")]
    ).model_dump_json()


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
                    "message": {"role": "assistant", "content": content or _valid()},
                }
            ],
            "usage": {"prompt_tokens": 21, "completion_tokens": 9, "total_tokens": 30},
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
    client = CallMissedClient(api_key=SECRET, base_url="https://cm.test/v1", http_client=http, **kw)
    return client, mock


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    slept: list[float] = []

    async def fake_sleep(s):
        slept.append(s)

    monkeypatch.setattr(callmissed, "_sleep", fake_sleep)
    return slept


async def _call(client, timeout_s: float = 8.0):
    return await client.chat_json(
        model="sarvam-105b",
        system=SYSTEM,
        user=USER,
        schema=Out,
        prompt_version="explanation_v1",
        timeout_s=timeout_s,
    )


async def test_data_residency_in_request_body():
    client, mock = make([_ok()])
    await _call(client)
    body = mock.last_json()
    assert body["provider"] == {"data_residency": "in"}
    assert CHAT_EXTRA_BODY == {"provider": {"data_residency": "in"}}


def _every_attempt_is_in(mock: Mock) -> None:
    bodies = [json.loads(r.content) for r in mock.requests]
    assert bodies, "no request was made"
    for i, body in enumerate(bodies):
        assert body["provider"] == {"data_residency": "in"}, f"attempt {i + 1}"


async def test_data_residency_on_every_attempt_including_retries(no_sleep):
    # 429, then 503, then invalid output, then success: four attempts, all residency "in".
    client, mock = make(
        [
            httpx.Response(429, json={}),
            httpx.Response(503, json={}),
            _ok('{"text": "x"}'),
            _ok(),
        ]
    )
    await _call(client)
    assert mock.calls >= 3
    _every_attempt_is_in(mock)


@pytest.mark.parametrize(
    "responses",
    [
        [httpx.Response(429, json={})],
        [httpx.Response(503, json={})],
        [_ok('{"text": "x"}')],
    ],
    ids=["429", "5xx", "invalid_output"],
)
async def test_data_residency_on_every_failed_retry(responses):
    client, mock = make(responses)
    with pytest.raises(CompletionFailed):
        await _call(client)
    assert mock.calls >= 2
    _every_attempt_is_in(mock)


async def test_request_shape_strict_schema_temperature_zero():
    client, mock = make([_ok()])
    result = await _call(client)
    assert isinstance(result, Out)
    body = mock.last_json()
    assert body["model"] == "sarvam-105b"
    assert body["temperature"] == 0
    assert body["messages"] == [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER},
    ]
    rf = body["response_format"]
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["strict"] is True
    schema = rf["json_schema"]["schema"]
    assert schema["additionalProperties"] is False
    assert sorted(schema["required"]) == ["members", "text", "tips"]
    echo = schema["$defs"]["Echo"]
    assert echo["additionalProperties"] is False and sorted(echo["required"]) == ["ref", "status"]
    assert mock.requests[0].headers["authorization"] == f"Bearer {SECRET}"


async def test_strict_schema_is_valid_for_strict_mode_everywhere():
    client, mock = make([_ok()])
    await _call(client)
    schema = mock.last_json()["response_format"]["json_schema"]["schema"]

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "object" or "properties" in node:
                assert node["additionalProperties"] is False
                assert set(node["required"]) == set(node["properties"])
            for key in ("default", "minimum", "maximum"):
                assert key not in node
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(schema)


async def test_constant_is_not_mutated_by_a_call():
    client, _ = make([_ok(), _ok()])
    await _call(client)
    await _call(client)
    assert CHAT_EXTRA_BODY == {"provider": {"data_residency": "in"}}


async def test_402_is_unavailable_without_retry():
    client, mock = make([httpx.Response(402, json={"error": {"code": "insufficient_credits"}})])
    with pytest.raises(ProviderUnavailable) as ei:
        await _call(client)
    assert ei.value.reason == "insufficient_credits"
    assert mock.calls == 1


@pytest.mark.parametrize("code", [401, 403])
async def test_auth_errors_are_misconfigured(code):
    client, mock = make([httpx.Response(code, json={})])
    with pytest.raises(ProviderUnavailable) as ei:
        await _call(client)
    assert ei.value.reason == "misconfigured"
    assert mock.calls == 1


async def test_429_retried_then_success(no_sleep):
    client, mock = make([httpx.Response(429, headers={"Retry-After": "1"}, json={}), _ok()])
    await _call(client)
    assert mock.calls == 2 and no_sleep == [1.0]


async def test_429_gives_up_as_completion_failed():
    client, mock = make([httpx.Response(429, json={})])
    with pytest.raises(CompletionFailed):
        await _call(client)
    assert mock.calls == 3


async def test_5xx_retried_twice_then_completion_failed():
    client, mock = make([httpx.Response(503, json={})])
    with pytest.raises(CompletionFailed):
        await _call(client)
    assert mock.calls == 3


async def test_timeout_is_completion_failed():
    client, _ = make([httpx.ReadTimeout("slow")])
    with pytest.raises(CompletionFailed):
        await _call(client)


async def test_400_is_completion_failed_without_retry():
    client, mock = make([httpx.Response(400, json={})])
    with pytest.raises(CompletionFailed):
        await _call(client)
    assert mock.calls == 1


async def test_invalid_output_retried_once_then_failed():
    client, mock = make([_ok('{"text": "x"}')])
    with pytest.raises(CompletionFailed):
        await _call(client)
    assert mock.calls == 2


async def test_over_long_text_is_invalid_output_never_truncated():
    too_long = Out.model_construct(text="x" * 51, tips=[], members=[]).model_dump_json()
    client, mock = make([_ok(too_long)])
    with pytest.raises(CompletionFailed):
        await _call(client)
    assert mock.calls == 2


async def test_deadline_is_the_timeout_budget():
    clock = Clock()
    client, _ = make([httpx.Response(503, json={}), _ok()], clock=clock)
    seen: list[float] = []
    real = client._client.chat.completions.create

    async def spy(**kw):
        seen.append(kw["timeout"])
        clock.now += 7.5  # the first attempt eats most of an 8 s budget
        return await real(**kw)

    client._client.chat.completions.create = spy  # type: ignore[method-assign]
    with pytest.raises(CompletionFailed):
        await _call(client, timeout_s=8.0)
    assert seen[0] == 8.0
    assert all(t <= 8.0 for t in seen)


async def test_log_has_metadata_but_no_prompt_or_output(caplog):
    caplog.set_level(logging.DEBUG)
    client, _ = make([_ok()])
    await _call(client)
    text = "\n".join(r.getMessage() for r in caplog.records)
    assert "callmissed_chat" in text and "prompt_version=explanation_v1" in text
    assert "model=sarvam-105b" in text and "status=ok" in text
    assert "tokens_in=21" in text and "tokens_out=9" in text
    for forbidden in (SYSTEM, "diabetes-secret", "member_1", SECRET, '"fine"'):
        assert forbidden not in text


async def test_lazy_provider_has_chat_json_and_needs_a_key():
    lazy = callmissed.LazyCallMissed(api_key=None, base_url="https://cm.test/v1")
    with pytest.raises(ProviderUnavailable) as ei:
        await lazy.chat_json(
            model="m", system="s", user="u", schema=Out, prompt_version="v", timeout_s=1.0
        )
    assert ei.value.reason == "not_configured"
