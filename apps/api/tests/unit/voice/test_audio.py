"""Voice upload checks: byte sniffing, size and duration limits, silence, transcoding.

Audio is generated with ffmpeg (tests/audio.py); the tests skip when ffmpeg is missing.
"""

import pytest

from app.features.voice.audio import (
    MAX_AUDIO_BYTES,
    AudioRejected,
    prepare_for_stt,
    probe_duration_seconds,
    sniff_audio_mime,
)
from tests.audio import make_audio, require_ffmpeg


def test_sniff_known_formats(wav3s, m4a3s, webm3s, ogg3s, mp3_3s):
    assert [sniff_audio_mime(b) for b in (wav3s, m4a3s, webm3s, ogg3s, mp3_3s)] == [
        "audio/wav",
        "audio/mp4",
        "audio/webm",
        "audio/ogg",
        "audio/mpeg",
    ]


def test_sniff_rejects_garbage():
    assert sniff_audio_mime(b"<html>hello") is None


@pytest.mark.parametrize(
    "data",
    [b"", b"RIFF", b"RIFF\0\0\0\0AVI ", b"\xff\xf1\x50\x80", b"\x89PNG\r\n\x1a\n", b"%PDF-1.7"],
    ids=["empty", "short_riff", "avi", "adts_aac", "png", "pdf"],
)
def test_sniff_rejects_lookalikes(data):
    assert sniff_audio_mime(data) is None


def test_sniff_mp3_frame_without_id3():
    assert sniff_audio_mime(b"\xff\xfb\x90\x00" + b"\0" * 32) == "audio/mpeg"
    assert sniff_audio_mime(b"\xff\xf3\x90\x00" + b"\0" * 32) == "audio/mpeg"


async def test_too_large_rejected():
    with pytest.raises(AudioRejected) as e:
        await prepare_for_stt(b"RIFF" + b"\0" * (MAX_AUDIO_BYTES + 1), frozenset())
    assert e.value.code == "audio_too_large"


async def test_unsupported_bytes_rejected():
    with pytest.raises(AudioRejected) as e:
        await prepare_for_stt(b"<html>hello</html>", frozenset())
    assert e.value.code == "audio_unsupported"


async def test_corrupt_audio_with_valid_magic_rejected():
    require_ffmpeg()
    with pytest.raises(AudioRejected) as e:
        await prepare_for_stt(b"OggS" + b"\x00garbage" * 64, frozenset())
    assert e.value.code == "audio_unsupported"


async def test_too_long_rejected(wav31s):
    with pytest.raises(AudioRejected) as e:
        await prepare_for_stt(wav31s, frozenset())
    assert e.value.code == "audio_too_long"


async def test_too_long_rejected_even_when_container_hides_duration():
    require_ffmpeg()
    # MediaRecorder WebM carries no duration header; the decoded length must still count.
    with pytest.raises(AudioRejected) as e:
        await prepare_for_stt(make_audio("webm", 31), frozenset({"audio/webm"}))
    assert e.value.code == "audio_too_long"


async def test_silence_rejected_as_not_understood(silent_wav3s):
    with pytest.raises(AudioRejected) as e:
        await prepare_for_stt(silent_wav3s, frozenset())
    assert e.value.code == "voice_not_understood"


async def test_very_short_recording_rejected_as_not_understood():
    require_ffmpeg()
    with pytest.raises(AudioRejected) as e:
        await prepare_for_stt(make_audio("wav", 0.2), frozenset())
    assert e.value.code == "voice_not_understood"


async def test_webm_transcoded_to_wav(webm3s):
    data, mime = await prepare_for_stt(webm3s, frozenset({"audio/webm"}))
    assert mime == "audio/wav" and data[:4] == b"RIFF"
    assert 2.8 < await probe_duration_seconds(data) < 3.2


async def test_accepted_format_passes_through(m4a3s):
    data, mime = await prepare_for_stt(m4a3s, frozenset({"audio/webm"}))
    assert (data, mime) == (m4a3s, "audio/mp4")


@pytest.mark.parametrize("fmt", ["wav", "m4a", "webm", "ogg", "mp3"])
async def test_duration_of_every_format(fmt):
    require_ffmpeg()
    assert 2.8 < await probe_duration_seconds(make_audio(fmt, 3)) < 3.2
