from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.errors import ERROR_RESPONSES, ErrorEnvelope
from app.core.ratelimit import limit
from app.db.session import get_session
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.voice import service
from app.features.voice.audio import MAX_AUDIO_BYTES
from app.features.voice.schemas import VoiceAnswer, VoiceLanguage
from app.integrations.callmissed import get_llm_provider, get_speech_provider
from app.integrations.openfoodfacts import OffClient, get_off_client
from app.integrations.providers import LLMProvider, SpeechProvider
from app.integrations.storage import StorageClient, get_voice_storage

router = APIRouter(prefix="/v1/voice", tags=["voice"])

_RESPONSES = {
    **ERROR_RESPONSES,
    403: {"model": ErrorEnvelope, "description": "ai_processing consent required"},
    413: {"model": ErrorEnvelope, "description": "Audio longer than 30 s or larger than 5 MB"},
    415: {"model": ErrorEnvelope, "description": "Not an accepted audio format"},
    503: {"model": ErrorEnvelope, "description": "Speech, AI, storage or OFF unavailable"},
}


@router.post(
    "/ask",
    operation_id="voice_ask",
    response_model=VoiceAnswer,
    responses=_RESPONSES,
    dependencies=[Depends(limit("voice"))],  # first: it commits the session
)
async def voice_ask(
    # format: binary so both generated clients send a file part (OpenAPI 3.1 alone gives
    # contentMediaType, which the Dart generator reads as a plain string).
    audio: Annotated[UploadFile, File(json_schema_extra={"format": "binary"})],
    member_id: Annotated[UUID, Form()],
    language: Annotated[VoiceLanguage, Form()],
    current: Annotated[CurrentAccount, Depends(current_account_row)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    speech: Annotated[SpeechProvider, Depends(get_speech_provider)],
    llm: Annotated[LLMProvider, Depends(get_llm_provider)],
    storage: Annotated[StorageClient, Depends(get_voice_storage)],
    off: Annotated[OffClient, Depends(get_off_client)],
    product_id: Annotated[UUID | None, Form()] = None,
    barcode: Annotated[str | None, Form(max_length=64)] = None,
) -> VoiceAnswer:
    """Answer a spoken question about one product for one family member.

    Send exactly one of `product_id` (our catalogue) or `barcode` (Open Food Facts). Audio:
    at most 30 s and 5 MB; m4a/AAC, WAV, WebM, Ogg or mp3, detected from the bytes. The
    verdict comes only from the rules engine; `answer` starts with it. Needs the
    `ai_processing` consent. Rate-limited per account per day (`rate_limited_voice`).
    """
    data = await audio.read(MAX_AUDIO_BYTES + 1)
    return await service.ask_voice(
        session,
        account_id=current.ctx.account_id,
        email=current.ctx.email,
        audio=data,
        product_id=product_id,
        barcode=barcode,
        member_id=member_id,
        language=language.value,
        settings=settings,
        speech=speech,
        llm=llm,
        storage=storage,
        off=off,
        today=datetime.now(UTC).date(),
    )
