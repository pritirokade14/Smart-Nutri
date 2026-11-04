"""scripts/probe_callmissed.py: one paid end-to-end probe, never run without --yes-spend.

The paid path runs here only against an httpx MockTransport.
"""

import json
import wave
from io import BytesIO

import httpx

from app.core.config import Settings
from scripts import probe_callmissed

SECRET = "cm_test_secret_key"
MP3 = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\xff\xfb\x90\x00" * 8
TRANSCRIPT = "transcript that must never be printed"
EXTRACTION = {
    "product_name": "PROBE TEST BISCUIT", "brand": None, "basis_detected": "per_100g",
    "per_100g": None, "per_serving": None, "serving_size_g": None, "ingredients": ["wheat flour"],
    "allergen_statement": "Contains: wheat", "may_contain_statement": None, "claims": [],
    "veg_mark": None, "category_guess": None, "confidence": 0.9, "unreadable_fields": [],
    "upper_bound_fields": [], "per_100_unit": None, "serving_size_unit": None,
}  # fmt: skip


def _settings(**over) -> Settings:
    return Settings(_env_file=None, callmissed_api_key=SECRET, **over)


def _no_network(monkeypatch):
    async def boom(*_a, **_k):
        raise AssertionError("the probe must not touch the network without --yes-spend")

    monkeypatch.setattr(httpx.AsyncClient, "send", boom)


def _completion(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "x",
            "object": "chat.completion",
            "created": 0,
            "model": "m",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content},
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        },
    )


class Fake:
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        if path == "/v1/audio/transcriptions":
            return httpx.Response(200, json={"text": TRANSCRIPT})
        if path == "/v1/audio/speech":
            return httpx.Response(200, content=MP3, headers={"content-type": "audio/mpeg"})
        body = json.loads(request.content)
        if isinstance(body["messages"][0]["content"], list):  # vision
            return _completion(json.dumps(EXTRACTION))
        return _completion('{"reply": "hello"}')


def test_dry_run_prints_the_plan_and_cost_and_refuses(monkeypatch, capsys):
    _no_network(monkeypatch)
    assert probe_callmissed.main([], settings=_settings()) == 2
    out = capsys.readouterr().out
    assert "--yes-spend" in out and "Estimated cost: up to US$" in out
    assert "Plan: 16 paid calls" in out
    for model in ("gpt-4o", "gemma-4-31b", "glm-5.3-flash", "saaras:v4", "whisper"):
        assert model in out
    assert "bulbul:v3" in out and "gnani-timbre-v3.0" in out
    assert SECRET not in out


def test_refuses_in_ci_even_with_yes_spend(monkeypatch, capsys):
    _no_network(monkeypatch)
    monkeypatch.setenv("CI", "true")
    assert probe_callmissed.main(["--yes-spend"], settings=_settings()) == 2
    assert "CI" in capsys.readouterr().out


def test_plan_covers_every_job_primary_and_fallback_in_every_language():
    calls = probe_callmissed.plan(_settings())
    jobs = {(c.job, c.model, c.language) for c in calls}
    assert ("chat", "gpt-4o", "-") in jobs and ("chat", "gemma-4-31b", "-") in jobs
    assert ("vision", "gpt-4o", "-") in jobs and ("vision", "glm-5.3-flash", "-") in jobs
    for lang in ("en", "hi", "mr"):
        assert {("stt", "saaras:v4", lang), ("stt", "whisper", lang)} <= jobs
        assert {("tts", "bulbul:v3", lang), ("tts", "gnani-timbre-v3.0", lang)} <= jobs
    assert len(calls) == 16


def test_plan_skips_a_disabled_fallback():
    calls = probe_callmissed.plan(_settings(callmissed_explanation_fallback_model=""))
    assert [c.model for c in calls if c.job == "chat"] == ["gpt-4o"]


def test_estimate_is_small_and_known_for_every_default():
    costs = [probe_callmissed.estimate_usd(c) for c in probe_callmissed.plan(_settings())]
    assert None not in costs
    assert 0 < sum(costs) < 0.10  # US$, an upper bound


def test_generated_wav_is_16k_mono_under_saaras_30s_limit():
    with wave.open(BytesIO(probe_callmissed.tone_wav())) as w:
        assert (w.getnchannels(), w.getframerate(), w.getsampwidth()) == (1, 16000, 2)
        assert w.getnframes() / w.getframerate() <= 30


def test_synthetic_label_is_a_jpeg():
    assert probe_callmissed.synthetic_label_jpeg()[:3] == b"\xff\xd8\xff"


def test_paid_path_prints_metadata_only(monkeypatch, capsys):
    monkeypatch.delenv("CI", raising=False)
    fake = Fake()
    http = httpx.AsyncClient(transport=httpx.MockTransport(fake.handler))
    assert probe_callmissed.main(["--yes-spend"], settings=_settings(), http=http) == 0
    out = capsys.readouterr().out
    result_lines = [line for line in out.splitlines() if line.endswith(" ms")]
    assert len(result_lines) == 16 and all(" ok " in line for line in result_lines)
    for forbidden in (TRANSCRIPT, SECRET, "PROBE TEST BISCUIT", "hello", "wheat"):
        assert forbidden not in out
    paths = [r.url.path for r in fake.requests]
    assert paths.count("/v1/chat/completions") == 4
    assert paths.count("/v1/audio/speech") == 6
    assert paths.count("/v1/audio/transcriptions") == 6
    tts = [json.loads(r.content) for r in fake.requests if r.url.path == "/v1/audio/speech"]
    assert {(b["model"], b["language"], b["voice"]) for b in tts} == {
        ("bulbul:v3", "en-IN", "ratan"),
        ("bulbul:v3", "hi-IN", "shubh"),
        ("bulbul:v3", "mr-IN", "ratan"),
        ("gnani-timbre-v3.0", "en-IN", "Chetana"),
        ("gnani-timbre-v3.0", "hi-IN", "Chetana"),
        ("gnani-timbre-v3.0", "mr-IN", "Chetana"),
    }
    chats = [json.loads(r.content) for r in fake.requests if r.url.path == "/v1/chat/completions"]
    text_chats = [b for b in chats if isinstance(b["messages"][0]["content"], str)]
    assert all(b["provider"] == {"data_residency": "in"} for b in text_chats)


def test_paid_path_reports_a_failure_with_exit_1(monkeypatch, capsys):
    monkeypatch.delenv("CI", raising=False)
    http = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(402, json={})))
    assert probe_callmissed.main(["--yes-spend"], settings=_settings(), http=http) == 1
    assert "insufficient_credits" in capsys.readouterr().out
