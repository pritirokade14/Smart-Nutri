# CallMissed STT: accepted audio formats (Plan 7 Task 1)

**Status: NOT YET PROBED.** The probe (`scripts.probe_callmissed`, which replaced `probe_stt_formats`) makes paid calls, so it needs the
user's go-ahead.

**Decision (security review, 2026-11-03):** the API always sends STT the 16 kHz mono WAV it
decoded and measured itself, for every upload type, WAV included. It never forwards the raw
upload, so the STT service can't parse a file differently from our duration and silence
checks (a parser differential). So the plan's `VOICE_TRANSCODE_MIMES` setting is gone, and
only the `wav` row below decides whether voice works. The other rows are for information.

## How to run

```
cd apps/api
uv run python -m scripts.probe_callmissed              # dry run, no spend
uv run python -m scripts.probe_callmissed --yes-spend  # 16 calls: chat, vision, STT, TTS
```

The script reads `CALLMISSED_API_KEY` from `apps/api/.env` and never prints it, the
transcripts or the response bodies. It prints only job, model, language, status and latency. It sends the 16 kHz WAV only; the per-format rows below are no longer probed.

## Results

Model: `saaras:v4` (`CALLMISSED_STT_MODEL`). Date: _pending_.

| Format | Client that produces it | MIME (sniffed) | HTTP status |
|---|---|---|---|
| wav | (server transcode target) | `audio/wav` | _pending_ |
| m4a (AAC) | Android `record` (`AudioEncoder.aacLc`) | `audio/mp4` | _pending_ |
| webm (Opus) | Chrome / Firefox / Edge `MediaRecorder` | `audio/webm` | _pending_ |
| ogg (Opus) | Firefox `MediaRecorder` (fallback) | `audio/ogg` | _pending_ |
| mp3 | (accepted upload type) | `audio/mpeg` | _pending_ |

TTS (`bulbul:v3`, voice `CALLMISSED_TTS_VOICE`, default `anushka`): _pending_. If the voice
is rejected, set `CALLMISSED_TTS_VOICE` to a voice listed for the model in `GET /v1/models`.

## After the probe

- If `wav` is rejected, voice cannot work: check the STT model id and the request shape
  (`app/integrations/callmissed.py::transcribe`) before anything else.
- Also check that `saaras:v4` returns a transcript in the spoken language (not an English
  translation) for `hi-IN` and `mr-IN`. Some Sarvam "saaras" models translate to English;
  if this one does, the voice answer is still in the requested language (the answer language
  comes from the request, not the transcript), but the `question` echoed to the client will be
  English.
