"""CallMissed WhatsApp AUTHENTICATION-template sender for phone OTP (Plan 8 Task 5).

Kept beside `callmissed.py` (the LLM/speech client) as its own module so the resource API
(`/api/v1/whatsapp/...`) and the inference API stay separate. Same rules: the `cm_...` key
stays server-side, and logs and exceptions never carry the key, the phone number, the OTP or
a response body.

UNVERIFIED until Task 14 (no paid or live call has been made). Check the exact request
fields against docs.callmissed.com before `PHONE_OTP_ENABLED=true`:
- the template endpoint body (`to`, `template`, `language`, `components`, `phone_number_id`);
- whether `to` must be E.164 with `+`;
- the button sub-type for a `copy_code` or `one_tap` OTP button.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Annotated, Any, Protocol

import httpx
from fastapi import Depends
from pydantic import SecretStr

from app.core.config import Settings, get_app_settings

logger = logging.getLogger(__name__)

# Supabase waits a few seconds for a hook; fail fast and let it retry (Idempotency-Key).
WHATSAPP_TIMEOUT_S = 4.0


class WhatsAppUnavailable(Exception):
    """Not configured, unreachable, or CallMissed refused the send."""


class OtpSender(Protocol):
    async def send_otp(self, phone: str, otp: str, idempotency_key: str) -> None: ...


class CallMissedWhatsApp:
    def __init__(
        self,
        http: httpx.AsyncClient,
        *,
        base_url: str,
        api_key: SecretStr,
        template: str,
        phone_number_id: str = "",
    ) -> None:
        self._http = http
        self._url = f"{base_url.rstrip('/')}/whatsapp/messages/template"
        self._key = api_key
        self._template = template
        self._phone_number_id = phone_number_id

    def __repr__(self) -> str:
        return f"CallMissedWhatsApp(template={self._template!r})"

    def _body(self, phone: str, otp: str) -> dict[str, Any]:
        param = [{"type": "text", "text": otp}]
        body: dict[str, Any] = {
            "to": phone,
            "template": self._template,
            "language": "en",
            "components": [
                {"type": "body", "parameters": param},
                # Meta AUTHENTICATION templates repeat the code in the OTP button.
                {"type": "button", "sub_type": "url", "index": "0", "parameters": param},
            ],
        }
        if self._phone_number_id:
            body["phone_number_id"] = self._phone_number_id
        return body

    async def send_otp(self, phone: str, otp: str, idempotency_key: str) -> None:
        headers = {
            "Authorization": f"Bearer {self._key.get_secret_value()}",
            "Idempotency-Key": idempotency_key,
        }
        try:
            response = await self._http.post(
                self._url, headers=headers, json=self._body(phone, otp)
            )
        except httpx.HTTPError:
            logger.warning("whatsapp_otp status=network_error")
            raise WhatsAppUnavailable("network error") from None
        if not 200 <= response.status_code < 300:
            logger.warning("whatsapp_otp status=%d", response.status_code)
            raise WhatsAppUnavailable(f"status {response.status_code}")


class _UnconfiguredSender:
    async def send_otp(self, phone: str, otp: str, idempotency_key: str) -> None:
        raise WhatsAppUnavailable("not configured")


async def get_otp_sender(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AsyncIterator[OtpSender]:
    """FastAPI dependency: the WhatsApp OTP sender for this request."""
    if settings.callmissed_api_key is None:
        yield _UnconfiguredSender()
        return
    async with httpx.AsyncClient(timeout=WHATSAPP_TIMEOUT_S) as http:
        yield CallMissedWhatsApp(
            http,
            base_url=settings.callmissed_resource_url,
            api_key=settings.callmissed_api_key,
            template=settings.callmissed_whatsapp_otp_template,
            phone_number_id=settings.callmissed_whatsapp_phone_number_id,
        )
