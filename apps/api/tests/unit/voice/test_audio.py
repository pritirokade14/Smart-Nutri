"""Voice upload checks: byte sniffing, size and duration limits, silence, transcoding.

Audio is generated with ffmpeg (tests/audio.py); the tests skip when ffmpeg is missing.
"""

import io
import wave
from pathlib import Path

import anyio
import pytest

from app.features.voice import audio
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
        await prepare_for_stt(b"RIFF" + b"\0" * (MAX_AUDIO_BYTES + 1))
    assert e.value.code == "audio_too_large"


async def test_unsupported_bytes_rejected():
    with pytest.raises(AudioRejected) as e:
        await prepare_for_stt(b"<html>hello</html>")
    assert e.value.code == "audio_unsupported"


async def test_corrupt_audio_with_valid_magic_rejected():
    require_ffmpeg()
    with pytest.raises(AudioRejected) as e:
        await prepare_for_stt(b"OggS" + b"\x00garbage" * 64)
    assert e.value.code == "audio_unsupported"


async def test_too_long_rejected(wav31s):
    with pytest.raises(AudioRejected) as e:
        await prepare_for_stt(wav31s)
    assert e.value.code == "audio_too_long"


async def test_too_long_rejected_even_when_container_hides_duration():
    require_ffmpeg()
    # MediaRecorder WebM carries no duration header; the decoded length must still count.
    with pytest.raises(AudioRejected) as e:
        await prepare_for_stt(make_audio("webm", 31))
    assert e.value.code == "audio_too_long"


async def test_silence_rejected_as_not_understood(silent_wav3s):
    with pytest.raises(AudioRejected) as e:
        await prepare_for_stt(silent_wav3s)
    assert e.value.code == "voice_not_understood"


async def test_very_short_recording_rejected_as_not_understood():
    require_ffmpeg()
    with pytest.raises(AudioRejected) as e:
        await prepare_for_stt(make_audio("wav", 0.2))
    assert e.value.code == "voice_not_understood"


async def test_webm_transcoded_to_wav(webm3s):
    data, mime = await prepare_for_stt(webm3s)
    assert mime == "audio/wav" and data[:4] == b"RIFF"
    assert 2.8 < await probe_duration_seconds(data) < 3.2


@pytest.mark.parametrize("fmt", ["wav", "m4a", "webm", "ogg", "mp3"])
async def test_stt_always_gets_the_measured_wav_never_the_upload(fmt, monkeypatch):
    """Security review (parser differential): STT receives exactly the PCM that was decoded,
    measured and capped, re-wrapped as WAV, for every input type including WAV."""
    require_ffmpeg()
    upload = make_audio(fmt, 3)
    decoded: list[bytes] = []
    real = audio._decode_pcm

    async def spy(data: bytes, mime: str) -> bytes:
        pcm = await real(data, mime)
        decoded.append(pcm)
        return pcm

    monkeypatch.setattr(audio, "_decode_pcm", spy)
    data, mime = await prepare_for_stt(upload)
    assert mime == "audio/wav" and data != upload
    with wave.open(io.BytesIO(data)) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, 16000)
        assert w.readframes(w.getnframes()) == decoded[0]


# --- security review: disguised playlists must never make ffmpeg open anything else ---------


def _playlists(target: Path) -> dict[str, bytes]:
    hls = f"#EXTM3U\n#EXT-X-TARGETDURATION:10\n#EXTINF:3,\n{target}\n#EXT-X-ENDLIST\n"
    concat = f"ffconcat version 1.0\nfile {target}\n"
    id3 = b"ID3\x04\x00\x00\x00\x00\x00\x00"
    return {
        "id3_hls": id3 + hls.encode(),
        "id3_concat": id3 + concat.encode(),
        "ogg_hls": b"OggS" + hls.encode(),
        "ebml_hls": b"\x1a\x45\xdf\xa3" + hls.encode(),
        "riff_hls": b"RIFF\x00\x00\x00\x00WAVE" + hls.encode(),
        "ftyp_hls": b"\x00\x00\x00\x18ftypisom" + hls.encode(),
    }


@pytest.mark.parametrize(
    "name", ["id3_hls", "id3_concat", "ogg_hls", "ebml_hls", "riff_hls", "ftyp_hls"]
)
async def test_disguised_playlist_is_rejected(name, tmp_path):
    require_ffmpeg()
    canary = tmp_path / "canary.wav"
    canary.write_bytes(make_audio("wav", 3))  # would decode fine if ffmpeg followed the link
    with pytest.raises(AudioRejected) as e:
        await prepare_for_stt(_playlists(canary)[name])
    assert e.value.code == "audio_unsupported"


@pytest.mark.parametrize(
    ("fmt", "demuxer"),
    [("wav", "wav"), ("m4a", "mov"), ("webm", "matroska"), ("ogg", "ogg"), ("mp3", "mp3")],
)
async def test_ffmpeg_demuxer_is_forced_and_protocols_whitelisted(fmt, demuxer, monkeypatch):
    require_ffmpeg()
    calls: list[list[str]] = []
    real = anyio.run_process

    async def spy(cmd, **kwargs):
        calls.append(list(cmd))
        return await real(cmd, **kwargs)

    monkeypatch.setattr(audio.anyio, "run_process", spy)
    await prepare_for_stt(make_audio(fmt, 3))
    (cmd,) = calls
    i = cmd.index("-i")
    before = cmd[:i]
    assert before[before.index("-f") + 1] == demuxer
    assert before[before.index("-format_whitelist") + 1] == demuxer
    protocols = before[before.index("-protocol_whitelist") + 1]
    if fmt == "m4a":  # MP4 needs a seekable input: a private temp file, no external refs
        assert protocols == "file" and before[before.index("-enable_drefs") + 1] == "0"
    else:
        assert protocols == "pipe" and cmd[i + 1] == "pipe:0"


@pytest.mark.parametrize("fmt", ["wav", "m4a", "webm", "ogg", "mp3"])
async def test_duration_of_every_format(fmt):
    require_ffmpeg()
    assert 2.8 < await probe_duration_seconds(make_audio(fmt, 3)) < 3.2
