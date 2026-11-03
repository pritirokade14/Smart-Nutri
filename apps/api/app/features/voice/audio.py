"""Voice upload checks before any paid call: size, byte-sniffed format, duration, silence, and
transcoding to 16 kHz mono WAV with ffmpeg (Plan 7 Task 2).

The declared content type is never trusted. Every upload is decoded once with ffmpeg (as
16 kHz mono PCM, capped just past the limit), which gives a duration even for containers
without one (MediaRecorder WebM) and lets silent or very short recordings be refused before
STT spends credits. The audio goes to a private temporary file only for the decode (MP4 needs
a seekable input) and is deleted straight after. Nothing here logs audio or its content.
"""

from __future__ import annotations

import os
import tempfile
import wave
from array import array
from io import BytesIO
from typing import Literal

import anyio

MAX_AUDIO_BYTES = 5 * 1024 * 1024
MAX_AUDIO_SECONDS = 30.0
# Encoders pad a little: a client that stops at exactly 30 s may send 30.05 s.
_DURATION_TOLERANCE_S = 0.25
_DECODE_CAP_S = MAX_AUDIO_SECONDS + 0.5
# Shorter than this, or quieter than this peak (16-bit, about -40 dBFS), is not a question.
MIN_SPEECH_SECONDS = 0.5
SILENCE_PEAK = 300
FFMPEG_TIMEOUT_S = 20.0
SAMPLE_RATE = 16_000
_BYTES_PER_SECOND = SAMPLE_RATE * 2  # mono, 16-bit

RejectCode = Literal[
    "audio_unsupported", "audio_too_long", "audio_too_large", "voice_not_understood"
]


class AudioRejected(Exception):
    def __init__(self, code: RejectCode) -> None:
        super().__init__(code)
        self.code: RejectCode = code


def sniff_audio_mime(data: bytes) -> str | None:
    """The audio type from the leading bytes, or None if it is not an accepted type."""
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "audio/wav"
    if len(data) >= 8 and data[4:8] == b"ftyp":
        return "audio/mp4"
    if data[:4] == b"OggS":
        return "audio/ogg"
    if data[:4] == b"\x1a\x45\xdf\xa3":  # EBML: WebM (MediaRecorder) / Matroska
        return "audio/webm"
    if data[:3] == b"ID3":
        return "audio/mpeg"
    # MPEG audio frame: 11 sync bits, then layer III (bits 01). ADTS AAC (layer 00) is not mp3.
    if len(data) >= 2 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0 and data[1] & 0x06 == 0x02:
        return "audio/mpeg"
    return None


def _write_temp(data: bytes) -> str:
    fd, path = tempfile.mkstemp(prefix="voice-", suffix=".bin")  # mode 0600
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return path


async def _decode_pcm(data: bytes) -> bytes:
    """16 kHz mono s16le PCM of at most _DECODE_CAP_S seconds. AudioRejected on failure."""
    path = await anyio.to_thread.run_sync(_write_temp, data)
    try:
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-i",
            path,
            "-t",
            str(_DECODE_CAP_S),
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            "-f",
            "s16le",
            "pipe:1",
        ]
        try:
            with anyio.fail_after(FFMPEG_TIMEOUT_S):
                result = await anyio.run_process(cmd, check=False)
        except TimeoutError:
            raise AudioRejected("audio_unsupported") from None
        if result.returncode != 0 or not result.stdout:
            raise AudioRejected("audio_unsupported")
        return result.stdout
    finally:
        await anyio.to_thread.run_sync(_unlink, path)


def _unlink(path: str) -> None:
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def _peak(pcm: bytes) -> int:
    samples = array("h")
    samples.frombytes(pcm[: len(pcm) - len(pcm) % 2])
    return max((abs(s) for s in samples), default=0)


def _wav(pcm: bytes) -> bytes:
    out = BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)
    return out.getvalue()


async def probe_duration_seconds(data: bytes) -> float:
    """Decoded duration in seconds (capped just past MAX_AUDIO_SECONDS)."""
    return len(await _decode_pcm(data)) / _BYTES_PER_SECOND


async def prepare_for_stt(data: bytes, transcode_mimes: frozenset[str]) -> tuple[bytes, str]:
    """Validate an upload and return (audio, mime) to send to STT.

    Order: size, sniffed type, decode, duration, silence. Types in `transcode_mimes` are
    sent as 16 kHz mono WAV; others pass through unchanged.
    """
    if len(data) > MAX_AUDIO_BYTES:
        raise AudioRejected("audio_too_large")
    mime = sniff_audio_mime(data)
    if mime is None:
        raise AudioRejected("audio_unsupported")
    pcm = await _decode_pcm(data)
    seconds = len(pcm) / _BYTES_PER_SECOND
    if seconds > MAX_AUDIO_SECONDS + _DURATION_TOLERANCE_S:
        raise AudioRejected("audio_too_long")
    if seconds < MIN_SPEECH_SECONDS:
        raise AudioRejected("voice_not_understood")
    if await anyio.to_thread.run_sync(_peak, pcm) < SILENCE_PEAK:
        raise AudioRejected("voice_not_understood")
    if mime in transcode_mimes:
        return _wav(pcm), "audio/wav"
    return data, mime
