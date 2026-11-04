"""Test audio generated with ffmpeg (a 440 Hz tone or silence). Never real recordings."""

from __future__ import annotations

import shutil
import subprocess
from functools import cache
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

_CODECS: dict[str, list[str]] = {
    "wav": ["-c:a", "pcm_s16le", "-f", "wav"],
    "m4a": ["-c:a", "aac", "-f", "mp4"],
    "webm": ["-c:a", "libopus", "-f", "webm"],
    "ogg": ["-c:a", "libopus", "-f", "ogg"],
    "mp3": ["-c:a", "libmp3lame", "-f", "mp3"],
}


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg is not installed (CI installs it; macOS: brew install ffmpeg)")


@cache
def make_audio(fmt: str, seconds: float, *, silent: bool = False) -> bytes:
    source = (
        f"anullsrc=r=16000:cl=mono:d={seconds}"
        if silent
        else f"sine=frequency=440:duration={seconds}"
    )
    with TemporaryDirectory() as tmp:
        out = Path(tmp) / f"a.{fmt}"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                source,
                "-t",
                str(seconds),
                "-ac",
                "1",
                "-ar",
                "16000",
                *_CODECS[fmt],
                "-y",
                str(out),
            ],
            check=True,
        )
        return out.read_bytes()
