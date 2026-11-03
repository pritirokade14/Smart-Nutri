"""Supabase Send-SMS hook: verify the Standard Webhooks signature, then send the OTP through
a CallMissed WhatsApp AUTHENTICATION template (Plan 8 Task 5).

Never log or echo the OTP, the phone number or the user id.
"""

from __future__ import annotations

import hashlib
import logging
import re

from pydantic import BaseModel, Field, SecretStr, ValidationError
from standardwebhooks import Webhook

from app.core.errors import ApiError
from app.integrations.callmissed_whatsapp import OtpSender, WhatsAppUnavailable

logger = logging.getLogger(__name__)

# Supabase shows the secret as "v1,whsec_<base64>"; Webhook() wants "whsec_<base64>".
_SUPABASE_PREFIX = "v1,"
MAX_BODY_BYTES = 16 * 1024


class _HookUser(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    phone: str = Field(min_length=6, max_length=20)


class _HookSms(BaseModel):
    otp: str = Field(min_length=4, max_length=10)


class SendSmsPayload(BaseModel):
    user: _HookUser
    sms: _HookSms


def verify(secret: SecretStr, body: bytes, headers: dict[str, str]) -> SendSmsPayload:
    """401 `auth_invalid` unless signed with `secret` within the 5-minute tolerance."""
    raw = secret.get_secret_value().strip()
    raw = raw.removeprefix(_SUPABASE_PREFIX)
    try:
        Webhook(raw).verify(body, headers, json_parse=False)
    except Exception:  # noqa: BLE001 - every verification failure (incl. malformed) is a 401
        logger.warning("send_sms_hook status=bad_signature")
        raise ApiError("auth_invalid", 401) from None
    try:
        return SendSmsPayload.model_validate_json(body)
    except ValidationError:
        logger.warning("send_sms_hook status=bad_payload")
        raise ApiError("validation_error", 422) from None


def to_e164(phone: str) -> str:
    """Supabase sends digits with the country code (e.g. 9198...); WhatsApp wants +E.164."""
    digits = re.sub(r"\D", "", phone)
    if not 8 <= len(digits) <= 15:
        raise ApiError("validation_error", 422)
    return f"+{digits}"


async def send_otp(payload: SendSmsPayload, sender: OtpSender) -> None:
    # Same user + same code -> same key, so a Supabase retry never sends a second message.
    key = hashlib.sha256(f"{payload.user.id}{payload.sms.otp}".encode()).hexdigest()
    try:
        await sender.send_otp(to_e164(payload.user.phone), payload.sms.otp, key)
    except WhatsAppUnavailable:
        logger.error("send_sms_hook status=send_failed")
        raise ApiError("internal_error", 500) from None
    logger.info("send_sms_hook status=sent")
