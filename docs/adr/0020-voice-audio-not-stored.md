# ADR 0020: Voice audio is never stored; answers are returned inline

- **Status:** Accepted
- **Date:** 2026-11-04

## Context

Plan 7 built push-to-talk voice questions (F10). The API transcribed the question with CallMissed STT, built a guarded answer, spoke it with CallMissed TTS, uploaded the mp3 to a private `voice-answers` Supabase bucket (`voice/{account_id}/{uuid}.mp3`) and returned a 1-hour signed URL. Plan 8 added a 24-hour voice window to the retention job and a voice-bucket step to `DELETE /v1/me`.

That design kept voice audio on our servers for up to a day, needed a second bucket on every environment, made retention a precondition for turning voice on, and added a storage failure mode (503) to every answer. A spoken answer is useful only while the user is looking at it.

On 2026-11-04 the user decided (binding): voice answers are sent directly in the API response, and **no voice audio is ever stored**. CallMissed still does STT and TTS.

## Decision

`POST /v1/voice/ask` returns the mp3 inline, and nothing about a voice question is stored.

1. **Response.** `VoiceAnswer` has `audio_base64` (the mp3, base64, or `null`) and `audio_mime: "audio/mpeg"`, replacing `audio_url` and `audio_expires_in`. Everything else is unchanged: consent gates, the verdict lock and guard, the rule-based fallback, rate limits, the `VOICE_ENABLED` flag, and no logging of audio, transcript or answer.
2. **Size cap.** The mp3 is capped at 1 MiB (`MAX_ANSWER_AUDIO_BYTES`, about 1.4 MB as base64). Over the cap the answer is still returned, with `audio_base64: null`, and no further TTS chunk is paid for. Clients then show the text only.
3. **No storage.** The voice route has no storage dependency. The question audio is held in memory; an MP4/M4A upload passes through a private (0600) temporary file for ffmpeg, which needs a seekable input, and it is deleted in a `finally` straight after decoding. Tests prove no storage call, no leftover temp file, and no database change apart from the voice rate-limit counter.
4. **Removed:** the `voice-answers` bucket and `SUPABASE_VOICE_BUCKET`, the voice window in the retention job (`--voice-hours`, `voice_deleted`), the voice listing in `DELETE /v1/me`, the storage client's signed download URL (used only by voice), and the bucket in `supabase/config.toml` and the dev deploy env.
5. **Clients.** Android decodes the base64 and plays it through `just_audio`, staged in a private cache file only while the answer is open (an in-memory `StreamAudioSource` needs a cleartext localhost proxy the app does not allow); a new answer replaces it and closing the sheet deletes it. Web decodes it into a Blob and plays an object URL that is revoked when the panel closes. CSP `media-src` is now `'self' blob:` only.

## Consequences

- Voice can be turned on without a bucket or a retention job; the only remaining gate is the paid STT/TTS probe (data residency check).
- Responses are larger (an answer of a few sentences is tens of kB of mp3; at most about 1.4 MB). Replay re-uses the audio already on the device and makes no new request.
- The privacy policy and Play data-safety form now say voice recordings, transcripts and answers are never stored. CallMissed still processes the audio for STT and TTS as our processor.
- Dev has an empty `voice-answers` bucket (created 2026-11-04) that the user may delete. Prod never gets one.
- Supersedes the voice parts of Plan 7 (signed URLs) and Plan 8 Task 3 (24-hour voice retention) and the voice line in ADR 0018's retention note.
