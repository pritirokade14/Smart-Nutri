"""Plan 8 Task 5: Supabase Send-SMS hook -> CallMissed WhatsApp OTP (switched off by default)."""

import base64
import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from pydantic import SecretStr
from standardwebhooks import Webhook

from app.core.config import Settings
from app.integrations.callmissed_whatsapp import (
    CallMissedWhatsApp,
    WhatsAppUnavailable,
    get_otp_sender,
)
from app.main import create_app

RAW_SECRET = base64.b64encode(b"0123456789abcdef0123456789abcdef").decode()
HOOK_SECRET = f"v1,whsec_{RAW_SECRET}"
USER_ID = "8d1f7a2e-3c4b-4d5e-9f60-718293a4b5c6"
PHONE = "919812345678"
OTP = "482913"
URL = "/v1/auth/hooks/send-sms"


class FakeSender:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.sent: list[tuple[str, str, str]] = []

    async def send_otp(self, phone: str, otp: str, idempotency_key: str) -> None:
        if self.fail:
            raise WhatsAppUnavailable("status 502")
        self.sent.append((phone, otp, idempotency_key))


def _payload() -> str:
    return json.dumps({"user": {"id": USER_ID, "phone": PHONE}, "sms": {"otp": OTP}})


def _signed(body: str, *, at: datetime | None = None, secret: str = RAW_SECRET) -> dict:
    at = at or datetime.now(UTC)
    msg_id = "msg_2b1c"
    sig = Webhook(secret).sign(msg_id, at, body)
    return {
        "webhook-id": msg_id,
        "webhook-timestamp": str(int(at.timestamp())),
        "webhook-signature": sig,
        "content-type": "application/json",
    }


@pytest.fixture
def sender() -> FakeSender:
    return FakeSender()


def _client(sender: FakeSender, *, enabled: bool = True, secret: str | None = HOOK_SECRET):
    app = create_app(
        Settings(
            _env_file=None,
            environment="test",
            phone_otp_enabled=enabled,
            supabase_send_sms_hook_secret=SecretStr(secret) if secret else None,
        )
    )
    app.dependency_overrides[get_otp_sender] = lambda: sender
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t")


async def test_valid_signature_sends_template_once(sender):
    body = _payload()
    async with _client(sender) as c:
        r = await c.post(URL, content=body, headers=_signed(body))
    assert r.status_code == 200 and r.json() == {}
    key = hashlib.sha256(f"{USER_ID}{OTP}".encode()).hexdigest()
    assert sender.sent == [("+" + PHONE, OTP, key)]


async def test_bad_signature_401_no_send(sender):
    body = _payload()
    other = base64.b64encode(b"another-secret-another-secret-!!").decode()
    async with _client(sender) as c:
        r = await c.post(URL, content=body, headers=_signed(body, secret=other))
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "auth_invalid"
        r = await c.post(URL, content=body, headers={"content-type": "application/json"})
        assert r.status_code == 401
        headers = _signed(body) | {"webhook-signature": "garbage"}
        assert (await c.post(URL, content=body, headers=headers)).status_code == 401
        # A valid signature over a different body does not verify this one.
        tampered = body.replace(OTP, "000000")
        assert (await c.post(URL, content=tampered, headers=_signed(body))).status_code == 401
    assert sender.sent == []


async def test_replay_outside_tolerance_401(sender):
    body = _payload()
    old = datetime.now(UTC) - timedelta(minutes=6)
    async with _client(sender) as c:
        r = await c.post(URL, content=body, headers=_signed(body, at=old))
    assert r.status_code == 401 and sender.sent == []


async def test_disabled_flag_503(sender):
    body = _payload()
    async with _client(sender, enabled=False) as c:
        r = await c.post(URL, content=body, headers=_signed(body))
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "phone_otp_disabled"
    assert sender.sent == []


async def test_enabled_without_secret_refuses(sender):
    body = _payload()
    async with _client(sender, secret=None) as c:
        r = await c.post(URL, content=body, headers=_signed(body))
    assert r.status_code == 503 and r.json()["error"]["code"] == "phone_otp_disabled"
    assert sender.sent == []


async def test_signed_but_malformed_payload_422_no_send(sender):
    body = json.dumps({"user": {"id": USER_ID}, "sms": {}})
    async with _client(sender) as c:
        r = await c.post(URL, content=body, headers=_signed(body))
    assert r.status_code == 422 and sender.sent == []


async def test_otp_and_phone_never_logged(sender, capsys):
    body = _payload()
    async with _client(sender) as c:  # create_app sets JSON logging to stdout, DEBUG below
        logging.getLogger().setLevel(logging.DEBUG)
        await c.post(URL, content=body, headers=_signed(body))
        await c.post(URL, content=body, headers=_signed(body, secret=RAW_SECRET[::-1]))
    async with _client(FakeSender(fail=True)) as c:
        logging.getLogger().setLevel(logging.DEBUG)
        await c.post(URL, content=body, headers=_signed(body))
    out = capsys.readouterr().out
    assert "status=sent" in out and "status=bad_signature" in out and "status=send_failed" in out
    for secret in (OTP, PHONE, USER_ID):
        assert secret not in out


async def test_callmissed_failure_returns_500_without_details():
    body = _payload()
    async with _client(FakeSender(fail=True)) as c:
        r = await c.post(URL, content=body, headers=_signed(body))
    assert r.status_code == 500
    assert r.json() == {
        "error": {"code": "internal_error", "message_key": "error.internal_error", "details": {}}
    }


def test_hook_is_not_in_the_public_contract():
    app = create_app(Settings(_env_file=None, environment="test"))
    assert URL not in app.openapi()["paths"]


# --- the CallMissed WhatsApp client (httpx.MockTransport, never the real API) -----------


def _wa(handler) -> tuple[CallMissedWhatsApp, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def _h(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    http = httpx.AsyncClient(transport=httpx.MockTransport(_h))
    client = CallMissedWhatsApp(
        http,
        base_url="https://api.callmissed.test/api/v1/",
        api_key=SecretStr("cm_test_key"),
        template="smartnutri_otp",
        phone_number_id="pn_1",
    )
    return client, seen


async def test_whatsapp_template_request_shape():
    wa, seen = _wa(lambda r: httpx.Response(200, json={"id": "m1"}))
    await wa.send_otp("+" + PHONE, OTP, "k" * 64)
    [req] = seen
    assert str(req.url) == "https://api.callmissed.test/api/v1/whatsapp/messages/template"
    assert req.headers["authorization"] == "Bearer cm_test_key"
    assert req.headers["idempotency-key"] == "k" * 64
    body = json.loads(req.content)
    assert body["to"] == "+" + PHONE
    assert body["template"] == "smartnutri_otp" and body["language"] == "en"
    assert body["phone_number_id"] == "pn_1"
    assert {"type": "body", "parameters": [{"type": "text", "text": OTP}]} in body["components"]
    button = next(c for c in body["components"] if c["type"] == "button")
    assert button["parameters"] == [{"type": "text", "text": OTP}]


@pytest.mark.parametrize("status", [400, 402, 429, 500])
async def test_whatsapp_errors_raise_without_body(status, caplog):
    wa, _ = _wa(lambda r: httpx.Response(status, text=f"echo {OTP} {PHONE}"))
    with caplog.at_level(logging.DEBUG), pytest.raises(WhatsAppUnavailable) as exc:
        await wa.send_otp("+" + PHONE, OTP, "k")
    assert OTP not in str(exc.value) and OTP not in caplog.text and PHONE not in caplog.text


async def test_whatsapp_network_error_raises():
    def boom(request):
        raise httpx.ConnectError("down")

    wa, _ = _wa(boom)
    with pytest.raises(WhatsAppUnavailable):
        await wa.send_otp("+" + PHONE, OTP, "k")
