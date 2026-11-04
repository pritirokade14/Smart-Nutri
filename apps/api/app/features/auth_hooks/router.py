"""Supabase Auth hooks (server-to-server, signed; not part of the client contract)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.config import Settings, get_app_settings
from app.core.errors import ApiError
from app.features.auth_hooks import service
from app.integrations.callmissed_whatsapp import OtpSender, get_otp_sender

router = APIRouter(prefix="/v1/auth/hooks", tags=["auth_hooks"])


@router.post("/send-sms", operation_id="auth_hooks_send_sms", include_in_schema=False)
async def send_sms(
    request: Request,
    settings: Annotated[Settings, Depends(get_app_settings)],
    sender: Annotated[OtpSender, Depends(get_otp_sender)],
) -> dict:
    """Supabase "Send SMS" hook: deliver the OTP as a WhatsApp AUTHENTICATION template.

    Authenticated by the Standard Webhooks signature (no user JWT). Responses: 200 `{}`;
    401 bad, missing or stale (> 5 min) signature; 503 `phone_otp_disabled`; 500 when
    CallMissed fails (Supabase then shows the user a generic error).
    """
    secret = settings.supabase_send_sms_hook_secret
    if not settings.phone_otp_enabled or secret is None:
        raise ApiError("phone_otp_disabled", 503)
    body = await request.body()
    if len(body) > service.MAX_BODY_BYTES:
        raise ApiError("validation_error", 422)
    payload = service.verify(secret, body, dict(request.headers))
    await service.send_otp(payload, sender)
    return {}
