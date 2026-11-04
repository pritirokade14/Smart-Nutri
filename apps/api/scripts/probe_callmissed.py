"""One end-to-end CallMissed probe for every AI job (ADR 0021).

    cd apps/api
    uv run python -m scripts.probe_callmissed              # dry run: plan + estimated cost, exit 2
    uv run python -m scripts.probe_callmissed --yes-spend  # the paid calls

For each job it calls the configured primary model AND its fallback, one by one (no fallback
inside a call, so a broken fallback shows up), through CallMissedClient, i.e. the exact
request shapes the API sends:

- chat: a strict-JSON chat (data residency "in", the explanation reasoning effort) within the
  8 s explanation budget, on CALLMISSED_EXPLANATION_MODEL and its fallback;
- vision: a label extraction (the configured prompt and schema) of a synthetic label image
  drawn here, on CALLMISSED_EXTRACTION_MODEL and its fallback;
- tts: en, hi and mr, each with its configured voice, on CALLMISSED_TTS_MODEL and its fallback;
- stt: a generated 3-second WAV in en, hi and mr, on CALLMISSED_STT_MODEL and its fallback.

It prints the estimated cost first, then one line per call: job, model, language, status and
latency. Never the key, prompts, transcripts, extracted values or audio. It refuses to spend
without --yes-spend, and refuses in CI.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import math
import os
import struct
import sys
import time
import wave
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

sys.path.insert(0, str(Path(__file__).parents[1]))

if TYPE_CHECKING:
    import httpx

    from app.core.config import Settings

# US$ prices from GET https://api.callmissed.com/api/v1/models, read 2026-11-04 (US$1 = Rs 96,
# per docs.callmissed.com/docs/models). (unit, input, output): tokens per 1M; hour; 10K chars.
PRICES: dict[str, tuple[str, float, float]] = {
    "gpt-4o": ("tokens", 2.604, 10.42),
    "gemma-4-31b": ("tokens", 0.3646, 0.9375),
    "glm-5.3-flash": ("tokens", 0.2292, 0.7604),
    "deepseek-v4.1-flash-1017": ("tokens", 0.4271, 1.771),
    "sarvam-105b": ("tokens", 0.1563, 0.625),
    "saaras:v4": ("hour", 0.3125, 0.0),
    "whisper": ("hour", 0.4167, 0.0),
    "bulbul:v3": ("10k_chars", 0.3125, 0.0),
    "bulbul:v4-flash": ("10k_chars", 0.2083, 0.0),
    "gnani-timbre-v3.0": ("10k_chars", 0.2813, 0.0),
}
INR_PER_USD = 96.0
# Generous size assumptions, so the estimate is an upper bound. Output allows for reasoning
# tokens (glm-5.3-flash cannot switch thinking off).
CHAT_TOKENS = (600, 1200)
VISION_TOKENS = (5000, 3000)
STT_SECONDS = 3.0
LANGUAGES = ("en", "hi", "mr")
# Probe-only phrases (not user-facing app copy), no health data.
TTS_TEXT = {
    "en": "This is a SmartNutri test.",
    "hi": "यह स्मार्टन्यूट्री की जाँच है।",
    "mr": "ही स्मार्टन्यूट्रीची चाचणी आहे.",
}


@dataclass(frozen=True)
class Call:
    job: str  # chat | vision | stt | tts
    model: str
    language: str = "-"


def plan(settings: Settings) -> list[Call]:
    """Every paid call the probe makes: primary then fallback per job."""

    def pair(primary: str, fallback: str | None) -> list[str]:
        return [primary] + ([fallback] if fallback and fallback != primary else [])

    calls = [
        Call("chat", m)
        for m in pair(
            settings.callmissed_explanation_model, settings.callmissed_explanation_fallback_model
        )
    ]
    calls += [
        Call("vision", m)
        for m in pair(
            settings.callmissed_extraction_model, settings.callmissed_extraction_fallback_model
        )
    ]
    calls += [
        Call("tts", m, lang)
        for m in pair(settings.callmissed_tts_model, settings.callmissed_tts_fallback_model)
        for lang in LANGUAGES
    ]
    calls += [
        Call("stt", m, lang)
        for m in pair(settings.callmissed_stt_model, settings.callmissed_stt_fallback_model)
        for lang in LANGUAGES
    ]
    return calls


def estimate_usd(call: Call) -> float | None:
    """Upper-bound cost of one call in US$, or None when the model's price is not known."""
    price = PRICES.get(call.model)
    if price is None:
        return None
    unit, a, b = price
    if unit == "tokens":
        tin, tout = VISION_TOKENS if call.job == "vision" else CHAT_TOKENS
        return (tin * a + tout * b) / 1_000_000
    if unit == "hour":
        return STT_SECONDS / 3600 * a
    return len(TTS_TEXT[call.language]) / 10_000 * a


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--yes-spend", action="store_true", help="actually call the paid API")
    return ap.parse_args(argv)


def synthetic_label_jpeg() -> bytes:
    """A drawn (not photographed) nutrition label: invented product, invented values."""
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.load_default(size=28)
    img = Image.new("RGB", (900, 700), (245, 243, 236))
    d = ImageDraw.Draw(img)
    d.text((40, 30), "PROBE TEST BISCUIT  (synthetic label)", fill=(20, 20, 20), font=font)
    d.rectangle((40, 90, 860, 560), outline=(0, 0, 0), width=3)
    rows = [
        ("NUTRITION INFORMATION", "per 100 g"),
        ("Energy (kcal)", "450"),
        ("Protein (g)", "7.0"),
        ("Carbohydrate (g)", "65.0"),
        ("Total Sugars (g)", "20.0"),
        ("Total Fat (g)", "18.0"),
        ("Saturated Fat (g)", "8.0"),
        ("Sodium (mg)", "300"),
    ]
    for i, (name, value) in enumerate(rows):
        y = 110 + i * 54
        d.text((60, y), name, fill=(0, 0, 0), font=font)
        d.text((640, y), value, fill=(0, 0, 0), font=font)
    d.text((40, 590), "Ingredients: wheat flour, sugar, palm oil, salt.", fill=(0, 0, 0), font=font)
    d.text((40, 640), "Contains: wheat (gluten).", fill=(0, 0, 0), font=font)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=90)
    return out.getvalue()


def tone_wav(seconds: float = STT_SECONDS, rate: int = 16_000) -> bytes:
    """A 16 kHz mono 16-bit WAV of a 440 Hz tone (the format the API sends to STT)."""
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = b"".join(
            struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * i / rate)))
            for i in range(int(seconds * rate))
        )
        w.writeframes(frames)
    return out.getvalue()


def _status(exc: BaseException) -> str:
    reason = getattr(exc, "reason", None)
    return f"{type(exc).__name__}:{reason}" if reason else type(exc).__name__


async def run(settings: Settings, http: httpx.AsyncClient | None = None) -> int:
    """Make every planned call and print one metadata line each. 0 = all ok, 1 = a failure."""
    from pydantic import BaseModel, Field

    from app.features.analyze.explain import EXPLANATION_BUDGET_S
    from app.features.scans.cells import extraction_schema
    from app.integrations.callmissed import CallMissedClient
    from app.prompts import load_extraction_prompt

    class ProbeReply(BaseModel):
        reply: str = Field(max_length=60)

    key = settings.callmissed_api_key
    base = settings.callmissed_base_url
    image = synthetic_label_jpeg()
    audio = tone_wav()
    prompt, prompt_version = load_extraction_prompt(settings.extraction_prompt_version)
    schema = extraction_schema(prompt_version)
    primary_voices = settings.callmissed_tts_voices
    fallback_voices = settings.callmissed_tts_fallback_voices
    failures = 0

    def client(**speech: Any) -> CallMissedClient:
        return CallMissedClient(api_key=key, base_url=base, http_client=http, **speech)

    async def one(call: Call, fn: Callable[[], Awaitable[Any]]) -> None:
        nonlocal failures
        start = time.monotonic()
        try:
            await fn()
            status = "ok"
        except Exception as exc:  # noqa: BLE001 - report and go on with the next call
            status, failures = _status(exc), failures + 1
        ms = (time.monotonic() - start) * 1000
        print(f"{call.job:<6} {call.model:<26} {call.language:<3} {status:<40} {ms:7.0f} ms")

    for call in plan(settings):
        if call.job == "chat":
            c = client()
            await one(
                call,
                lambda c=c, m=call.model: c.chat_json(
                    model=m,
                    system="Return JSON only. This is a connectivity test.",
                    user='Reply with {"reply": "hello"}.',
                    schema=ProbeReply,
                    prompt_version="probe",
                    timeout_s=EXPLANATION_BUDGET_S,
                    reasoning_effort=settings.callmissed_explanation_reasoning_effort,
                ),
            )
        elif call.job == "vision":
            c = client()
            await one(
                call,
                lambda c=c, m=call.model: c.extract_label(
                    image=image,
                    mime="image/jpeg",
                    prompt=prompt,
                    prompt_version=prompt_version,
                    schema=schema,
                    model=m,
                    reasoning_effort=settings.callmissed_extraction_reasoning_effort,
                ),
            )
        elif call.job == "tts":
            is_primary = call.model == settings.callmissed_tts_model
            voices = primary_voices if is_primary else fallback_voices
            c = client(tts_model=call.model, tts_voices=voices)
            await one(call, lambda c=c, lang=call.language: c.synthesize(TTS_TEXT[lang], lang))
        else:
            is_primary = call.model == settings.callmissed_stt_model
            languages = (
                settings.callmissed_stt_languages
                if is_primary
                else settings.callmissed_stt_fallback_languages
            )
            c = client(stt_model=call.model, stt_languages=languages)
            await one(call, lambda c=c, lang=call.language: c.transcribe(audio, "audio/wav", lang))
        if http is None:  # an injected client (tests) is shared, so it is not closed here
            await c.aclose()
    return 1 if failures else 0


def main(
    argv: list[str] | None = None,
    *,
    settings: Settings | None = None,
    http: httpx.AsyncClient | None = None,
) -> int:
    args = parse_args(argv)
    if settings is None:
        from app.core.config import get_settings

        settings = get_settings()
    calls = plan(settings)
    costs = [estimate_usd(c) for c in calls]
    known = sum(c for c in costs if c is not None)
    print(f"Plan: {len(calls)} paid calls (primary and fallback for every job):")
    for call, cost in zip(calls, costs, strict=True):
        price = f"${cost:.5f}" if cost is not None else "price unknown"
        print(f"  {call.job:<6} {call.model:<26} {call.language:<3} up to {price}")
    print(
        f"Estimated cost: up to US${known:.4f} (about Rs {known * INR_PER_USD:.2f})"
        + (" plus models with an unknown price" if None in costs else "")
    )
    if not args.yes_spend:
        print("Not running: pass --yes-spend to spend credits.")
        return 2
    if os.environ.get("CI"):
        print("Refusing to run paid probes in CI.")
        return 2
    if settings.callmissed_api_key is None:
        print("CALLMISSED_API_KEY is not set.")
        return 1
    return asyncio.run(run(settings, http))


if __name__ == "__main__":
    raise SystemExit(main())
