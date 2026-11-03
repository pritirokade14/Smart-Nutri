"""Voice upload checks before any paid call: size, byte-sniffed format, duration, silence, and
transcoding to 16 kHz mono WAV with ffmpeg (Plan 7 Task 2).

The declared content type is never trusted. Every upload is decoded once with ffmpeg (as
16 kHz mono PCM, capped just past the limit), which gives a duration even for containers
without one (MediaRecorder WebM) and lets silent or very short recordings be refused before
STT spends credits. STT always receives that decoded, measured PCM re-wrapped as WAV, never
the upload itself, so the STT service cannot parse the file differently from us.

ffmpeg is locked down (security review): the demuxer is forced to the one matching the
sniffed type (`-f`, `-format_whitelist`), so a playlist or concat script disguised behind a
valid magic prefix is never interpreted as one. Input comes from stdin
(`-protocol_whitelist pipe`), except MP4: its index may sit at the end of the file, which
needs a seekable input, so it goes through a private (0600) temporary file with
`-protocol_whitelist file` and external data references off (`-enable_drefs 0`), deleted
straight after. Nothing here logs audio or its content.
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


# sniffed type -> the only ffmpeg demuxer allowed to read it
DEMUXERS: dict[str, str] = {
    "audio/wav": "wav",
    "audio/mp4": "mov",
    "audio/webm": "matroska",
    "audio/ogg": "ogg",
    "audio/mpeg": "mp3",
}


def _write_temp(data: bytes) -> str:
    fd, path = tempfile.mkstemp(prefix="voice-", suffix=".bin")  # mode 0600
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return path


async def _decode_pcm(data: bytes, mime: str) -> bytes:
    """16 kHz mono s16le PCM of at most _DECODE_CAP_S seconds. AudioRejected on failure."""
    demuxer = DEMUXERS[mime]
    output = [
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
    base = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin"]
    locked = ["-format_whitelist", demuxer, "-f", demuxer]
    if mime != "audio/mp4":
        cmd = [*base, "-protocol_whitelist", "pipe", *locked, "-i", "pipe:0", *output]
        return await _run_ffmpeg(cmd, stdin=data)
    path = await anyio.to_thread.run_sync(_write_temp, data)
    try:
        cmd = [
            *base,
            "-protocol_whitelist",
            "file",
            "-enable_drefs",
            "0",
            *locked,
            "-i",
            path,
            *output,
        ]
        return await _run_ffmpeg(cmd, stdin=None)
    finally:
        await anyio.to_thread.run_sync(_unlink, path)


async def _run_ffmpeg(cmd: list[str], *, stdin: bytes | None) -> bytes:
    try:
        with anyio.fail_after(FFMPEG_TIMEOUT_S):
            result = await anyio.run_process(cmd, input=stdin, check=False)
    except TimeoutError:
        raise AudioRejected("audio_unsupported") from None
    if result.returncode != 0 or not result.stdout:
        raise AudioRejected("audio_unsupported")
    return result.stdout


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
    mime = sniff_audio_mime(data)
    if mime is None:
        raise AudioRejected("audio_unsupported")
    return len(await _decode_pcm(data, mime)) / _BYTES_PER_SECOND


async def prepare_for_stt(data: bytes) -> tuple[bytes, str]:
    """Validate an upload and return (audio, mime) to send to STT: always the decoded,
    measured, duration-capped PCM as 16 kHz mono WAV.

    Order: size, sniffed type, decode, duration, silence.
    """
    if len(data) > MAX_AUDIO_BYTES:
        raise AudioRejected("audio_too_large")
    mime = sniff_audio_mime(data)
    if mime is None:
        raise AudioRejected("audio_unsupported")
    pcm = await _decode_pcm(data, mime)
    seconds = len(pcm) / _BYTES_PER_SECOND
    if seconds > MAX_AUDIO_SECONDS + _DURATION_TOLERANCE_S:
        raise AudioRejected("audio_too_long")
    if seconds < MIN_SPEECH_SECONDS:
        raise AudioRejected("voice_not_understood")
    if await anyio.to_thread.run_sync(_peak, pcm) < SILENCE_PEAK:
        raise AudioRejected("voice_not_understood")
    return _wav(pcm), "audio/wav"
