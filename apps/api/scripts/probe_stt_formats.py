"""One-off probe: which audio formats does the CallMissed STT model accept? (Plan 7 Task 1)

    cd apps/api
    uv run python -m scripts.probe_stt_formats              # dry run: prints the plan, exits 2
    uv run python -m scripts.probe_stt_formats --yes-spend  # 5 paid STT calls + 1 paid TTS call

It generates a 3-second 440 Hz tone with ffmpeg in wav, m4a (AAC), webm (Opus), ogg (Opus) and
mp3, posts each one to `/v1/audio/transcriptions` with CALLMISSED_STT_MODEL, and prints
`<format>: <http status>`. Then it makes one TTS call with CALLMISSED_TTS_MODEL and
CALLMISSED_TTS_VOICE and prints its status, so a wrong default voice shows up here.

Record the table in docs/research/2026-11-03-callmissed-stt-formats.md and set the default of
VOICE_TRANSCODE_MIMES (app/core/config.py) to every rejected MIME type.

The key is read from settings (apps/api/.env) and never printed. Transcripts and response
bodies are never printed either: only HTTP status codes.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

# format -> (ffmpeg codec args, MIME type)
FORMATS: dict[str, tuple[list[str], str]] = {
    "wav": (["-c:a", "pcm_s16le"], "audio/wav"),
    "m4a": (["-c:a", "aac", "-f", "mp4"], "audio/mp4"),
    "webm": (["-c:a", "libopus", "-f", "webm"], "audio/webm"),
    "ogg": (["-c:a", "libopus", "-f", "ogg"], "audio/ogg"),
    "mp3": (["-c:a", "libmp3lame", "-f", "mp3"], "audio/mpeg"),
}
TIMEOUT_S = 30.0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--yes-spend", action="store_true", help="actually call the paid API")
    return ap.parse_args(argv)


def generate(fmt: str, out_dir: Path) -> Path:
    codec, _ = FORMATS[fmt]
    path = out_dir / f"tone.{fmt}"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=3",
            "-ac",
            "1",
            "-ar",
            "16000",
            *codec,
            "-y",
            str(path),
        ],
        check=True,
    )
    return path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(f"Plan: {len(FORMATS)} paid STT calls ({', '.join(FORMATS)}) + 1 paid TTS call.")
    if not args.yes_spend:
        print("Not running: pass --yes-spend to spend credits.")
        return 2
    if os.environ.get("CI"):
        print("Refusing to run paid probes in CI.")
        return 2
    if shutil.which("ffmpeg") is None:
        print("ffmpeg is not installed (macOS: brew install ffmpeg).")
        return 1

    import httpx

    from app.core.config import get_settings

    settings = get_settings()
    if settings.callmissed_api_key is None:
        print("CALLMISSED_API_KEY is not set.")
        return 1
    key = settings.callmissed_api_key.get_secret_value()
    base = settings.callmissed_base_url.rstrip("/")
    headers = {"Authorization": f"Bearer {key}"}

    with tempfile.TemporaryDirectory() as tmp, httpx.Client(timeout=TIMEOUT_S) as http:
        print(f"STT model: {settings.callmissed_stt_model}")
        for fmt, (_, mime) in FORMATS.items():
            path = generate(fmt, Path(tmp))
            response = http.post(
                f"{base}/audio/transcriptions",
                headers=headers,
                data={"model": settings.callmissed_stt_model, "language": "en-IN"},
                files={"file": (path.name, path.read_bytes(), mime)},
            )
            print(f"{fmt} ({mime}): {response.status_code}")
        response = http.post(
            f"{base}/audio/speech",
            headers=headers,
            json={
                "model": settings.callmissed_tts_model,
                "input": "For this member, avoid this product.",
                "voice": settings.callmissed_tts_voice,
                "response_format": "mp3",
                "language": "en-IN",
            },
        )
        ctype = response.headers.get("content-type", "")
        print(
            f"tts ({settings.callmissed_tts_model}, voice {settings.callmissed_tts_voice}): "
            f"{response.status_code} {ctype}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
