"""FakeSpeech: a SpeechProvider for tests. Never calls CallMissed."""

from __future__ import annotations

from dataclasses import dataclass

from app.integrations.providers import MAX_TTS_CHARS, SpeechUnavailable

FAKE_MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\xff\xfb\x90\x00" * 4


@dataclass(frozen=True)
class SttCall:
    audio: bytes
    mime: str
    language: str


@dataclass(frozen=True)
class TtsCall:
    text: str
    language: str


class FakeSpeech:
    def __init__(self, transcript: str = "is this ok for me") -> None:
        self.transcript = transcript
        self.raise_unavailable = False
        self.stt_calls: list[SttCall] = []
        self.synth_calls: list[TtsCall] = []

    async def transcribe(self, audio: bytes, mime: str, language: str) -> str:
        self.stt_calls.append(SttCall(audio, mime, language))
        if self.raise_unavailable:
            raise SpeechUnavailable("insufficient_credits")
        return self.transcript

    async def synthesize(self, text: str, language: str) -> bytes:
        if len(text) > MAX_TTS_CHARS:
            raise ValueError("too long")
        self.synth_calls.append(TtsCall(text, language))
        if self.raise_unavailable:
            raise SpeechUnavailable("insufficient_credits")
        return FAKE_MP3
