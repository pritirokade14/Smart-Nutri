# CallMissed STT: accepted audio formats (Plan 7 Task 1)

**Status: NOT YET PROBED.** The probe makes paid calls (5 STT + 1 TTS), so it needs the
user's go-ahead. Until it runs, the API transcodes every non-WAV upload to 16 kHz mono WAV
with ffmpeg before STT (`VOICE_TRANSCODE_MIMES=audio/mp4,audio/webm,audio/ogg,audio/mpeg`).
That is always correct, just slightly slower (one ffmpeg pass of at most 30 s of audio).

## How to run

```
cd apps/api
uv run python -m scripts.probe_stt_formats              # dry run, no spend
uv run python -m scripts.probe_stt_formats --yes-spend  # 5 STT calls + 1 TTS call
```

The script reads `CALLMISSED_API_KEY` from `apps/api/.env` and never prints it, the
transcripts or the response bodies. It prints only `<format>: <http status>`.

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

- Set the default of `voice_transcode_mimes` in `apps/api/app/core/config.py` and
  `VOICE_TRANSCODE_MIMES` in `apps/api/.env.example` to every **rejected** MIME type. If all
  are accepted, use `audio/webm,audio/ogg` as the safe choice (Plan 7).
- Also check that `saaras:v4` returns a transcript in the spoken language (not an English
  translation) for `hi-IN` and `mr-IN`. Some Sarvam "saaras" models translate to English;
  if this one does, the voice answer is still in the requested language (the answer language
  comes from the request, not the transcript), but the `question` echoed to the client will be
  English.
