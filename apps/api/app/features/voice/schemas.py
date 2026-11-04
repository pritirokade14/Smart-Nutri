from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from app.features.analyze.schemas import VerdictStatus

ANSWER_AUDIO_MIME = "audio/mpeg"


class VoiceLanguage(StrEnum):
    """Language of the question and of the spoken answer (a named schema, so the generated
    clients get a real enum type for the multipart field)."""

    EN = "en"
    HI = "hi"
    MR = "mr"


class VoiceAnswer(BaseModel):
    """A spoken answer. `answer` always starts with the engine's verdict sentence for
    `verdict_status`; clients show it with the "not medical advice" disclaimer and never
    derive a verdict from the text."""

    question: str = Field(description="The transcribed question (never stored or logged).")
    answer: str = Field(description="Engine verdict sentence, then the explanation.")
    audio_base64: str | None = Field(
        description=(
            "The spoken answer, base64-encoded (`audio_mime`), sent only in this response and "
            "never stored. null when the audio would be over about 1 MB: show `answer` as text."
        )
    )
    audio_mime: Literal["audio/mpeg"] = Field(
        default=ANSWER_AUDIO_MIME, description="Media type of audio_base64 (mp3)."
    )
    verdict_status: VerdictStatus
    source: Literal["llm", "fallback"] = Field(
        description="llm: AI explanation that passed every check; fallback: rule-based text."
    )
