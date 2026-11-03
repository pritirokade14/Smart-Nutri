from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from app.features.analyze.schemas import VerdictStatus

AUDIO_URL_EXPIRES_IN_S = 3600


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
    audio_url: str = Field(description="Signed URL of the mp3 answer; expires.")
    audio_expires_in: int = Field(
        default=AUDIO_URL_EXPIRES_IN_S, description="Seconds until audio_url expires."
    )
    verdict_status: VerdictStatus
    source: Literal["llm", "fallback"] = Field(
        description="llm: AI explanation that passed every check; fallback: rule-based text."
    )
