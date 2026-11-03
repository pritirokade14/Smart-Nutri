"""POST /v1/voice/ask: push-to-talk question about one product for one member (F10).

Flow (after the rate limit, in the route): product reference -> ai_processing consent ->
member and product ownership -> release the DB connection -> audio checks (size, sniffed
type, duration, silence) -> STT -> the engine's verdict for this one member -> the guarded
answer (engine verdict sentence first) -> TTS -> private upload -> signed URL.

Everything that can be refused for free (bad input, consent, ownership, audio) is refused
before the first paid call. The transcript and the answer are never written to the database
or to logs; logs carry only sizes, lengths, the language, the answer source and latency.
The mp3 lives at `voice/{account_id}/{uuid}.mp3` in the private voice bucket; the M6
retention job deletes objects older than 24 h.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import date
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.core.i18n import catalog
from app.features.analyze import service as analyze_service
from app.features.consents import service as consents_service
from app.features.members import service as members_service
from app.features.products import service as products_service
from app.features.products.service import ProductLookup
from app.features.voice.answer import answer_question
from app.features.voice.audio import AudioRejected, prepare_for_stt
from app.features.voice.schemas import AUDIO_URL_EXPIRES_IN_S, VoiceAnswer
from app.integrations.openfoodfacts import InvalidBarcode, OffClient, OffUnavailable
from app.integrations.providers import (
    MAX_TTS_CHARS,
    LLMProvider,
    ProviderUnavailable,
    SpeechProvider,
    SpeechUnavailable,
)
from app.integrations.storage import StorageClient, StorageUnavailable

logger = logging.getLogger(__name__)

DISCLAIMER_KEY = "common.disclaimer"
_SENTENCE_END = re.compile(r"(?<=[.!?।])\s+")


def split_for_tts(text: str, limit: int = MAX_TTS_CHARS) -> list[str]:
    """Chunks of at most `limit` chars, split on sentence boundaries where possible."""
    text = text.strip()
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(text):
        while len(sentence) > limit:  # a single overlong sentence: hard split
            if current:
                chunks.append(current)
                current = ""
            chunks.append(sentence[:limit])
            sentence = sentence[limit:]
        candidate = f"{current} {sentence}" if current else sentence
        if len(candidate) <= limit:
            current = candidate
        else:
            chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks


def _audio_error(exc: AudioRejected) -> ApiError:
    # Literal codes, so tests/unit/test_error_codes_i18n.py can see them.
    if exc.code == "audio_too_long":
        return ApiError("audio_too_long", 413)
    if exc.code == "audio_too_large":
        return ApiError("audio_too_large", 413)
    if exc.code == "voice_not_understood":
        return ApiError("voice_not_understood", 422)
    return ApiError("audio_unsupported", 415)


async def _resolve_product(
    session: AsyncSession,
    off: OffClient,
    *,
    product_id: UUID | None,
    barcode: str | None,
    settings: Settings,
    account_id: UUID,
) -> ProductLookup:
    if product_id is not None:
        found = await products_service.lookup_by_id(session, product_id, account_id=account_id)
    else:
        try:
            found = await products_service.lookup_by_barcode(
                session, off, barcode or "", settings=settings, account_id=account_id
            )
        except InvalidBarcode as exc:
            raise ApiError("invalid_barcode", 422) from exc
        except OffUnavailable as exc:
            raise ApiError("off_unavailable", 503) from exc
    if found is None:
        raise ApiError("product_not_found", 404)
    return found


async def ask_voice(
    session: AsyncSession,
    *,
    account_id: UUID,
    email: str | None,
    audio: bytes,
    product_id: UUID | None,
    barcode: str | None,
    member_id: UUID,
    language: str,
    settings: Settings,
    speech: SpeechProvider,
    llm: LLMProvider,
    storage: StorageClient,
    off: OffClient,
    today: date,
) -> VoiceAnswer:
    start = time.monotonic()
    status = "error"
    source = "-"
    sizes = {"audio_bytes": len(audio), "question_chars": 0, "answer_chars": 0}
    try:
        if (product_id is None) == (barcode is None):
            raise ApiError("invalid_product_ref", 422)
        if not await consents_service.has_active_consent(session, account_id, "ai_processing"):
            raise ApiError("consent_required", 403, details={"purpose": "ai_processing"})
        member = await members_service.get_member(session, account_id, member_id)
        found = await _resolve_product(
            session,
            off,
            product_id=product_id,
            barcode=barcode,
            settings=settings,
            account_id=account_id,
        )
        # Release the connection (and keep an OFF cache write) before the slow paid calls.
        await session.commit()

        try:
            stt_audio, stt_mime = await prepare_for_stt(audio)
        except AudioRejected as exc:
            status = exc.code
            raise _audio_error(exc) from None
        try:
            question = (await speech.transcribe(stt_audio, stt_mime, language)).strip()
        except SpeechUnavailable as exc:
            status = f"stt_{exc.reason}"
            raise ApiError("ai_unavailable", 503) from None
        sizes["question_chars"] = len(question)
        if not question:
            status = "empty_transcript"
            raise ApiError("voice_not_understood", 422)

        result = analyze_service.evaluate(found, [member], today=today)
        cat = catalog(settings.i18n_messages_dir)
        try:
            spoken = await answer_question(
                llm,
                settings,
                result,
                member,
                language,
                question,
                emails=[email] if email else [],
                today=today,
                cat=cat,
            )
        except ProviderUnavailable as exc:
            status = f"llm_{exc.reason}"
            raise ApiError("ai_unavailable", 503) from None
        source = spoken.source
        sizes["answer_chars"] = len(spoken.text)

        tts_text = f"{spoken.text} {cat.t(DISCLAIMER_KEY, language)}"
        try:
            mp3 = b"".join(
                [await speech.synthesize(chunk, language) for chunk in split_for_tts(tts_text)]
            )
        except SpeechUnavailable as exc:
            status = f"tts_{exc.reason}"
            raise ApiError("ai_unavailable", 503) from None

        path = f"voice/{account_id}/{uuid4()}.mp3"
        try:
            await storage.upload(path, mp3, "audio/mpeg")
            url = await storage.create_signed_url(path, AUDIO_URL_EXPIRES_IN_S)
        except StorageUnavailable:
            # Same client message as the other voice outages; logs keep the real cause.
            status = "storage_unavailable"
            raise ApiError("ai_unavailable", 503) from None

        status = "ok"
        return VoiceAnswer(
            question=question,
            answer=spoken.text,
            audio_url=url,
            audio_expires_in=AUDIO_URL_EXPIRES_IN_S,
            verdict_status=spoken.status.value,
            source=spoken.source,
        )
    except ApiError as exc:
        if status == "error":
            status = exc.code
        raise
    finally:
        logger.info(
            "voice_ask language=%s status=%s source=%s audio_bytes=%d question_chars=%d "
            "answer_chars=%d latency_ms=%d",
            language,
            status,
            source,
            sizes["audio_bytes"],
            sizes["question_chars"],
            sizes["answer_chars"],
            (time.monotonic() - start) * 1000,
        )
