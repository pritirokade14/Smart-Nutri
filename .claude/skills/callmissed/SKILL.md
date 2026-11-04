---
name: callmissed
description: Use when apps/api calls the CallMissed API — LLM chat or explanations, vision label extraction, speech-to-text, text-to-speech, WhatsApp messages or OTP templates, email, or knowledge/RAG — or when debugging CallMissed errors (402, 429), cost or latency.
---

# Using CallMissed from `apps/api`

CallMissed is our AI and voice provider. It is OpenAI-compatible, so use the official `openai` Python SDK with a different `base_url`.

## Endpoints and auth

| Purpose | Base URL |
|---|---|
| Inference: chat, embeddings, audio, images, models | `https://api.callmissed.com/v1` |
| Resources: WhatsApp, email, telephony, knowledge, webhooks | `https://api.callmissed.com/api/v1` |

- Auth: `Authorization: Bearer cm_...`, read from env `CALLMISSED_API_KEY`. The key lives **only on the server.**
  - Never put it in the Android app, the Next.js web app (including its server code and any `NEXT_PUBLIC_*` variable), logs, Sentry events or error responses. Both clients reach CallMissed only through `apps/api`.
- Send an `Idempotency-Key` header on retried writes, such as WhatsApp sends and email.
- Docs: https://docs.callmissed.com. The model catalogue is `GET /v1/models`, which is authoritative over anything written here.

## Rules

1. **Go through the interfaces.**
   - All calls go through `app/integrations/callmissed.py`, behind `LLMProvider` and `SpeechProvider` protocols.
   - Services depend on the protocol, never on the SDK. Tests use fakes.
2. **Model IDs come from config, never literals in code.** Use `settings.models.extraction`, `.explanation`, `.stt`, `.tts`.
   - Each job also has a `*_fallback_model`, tried once on a 5xx, timeout or `region_unavailable`.
   - Current choices and why: ADR 0021 and `docs/SETUP_ACCOUNTS.md` ("CallMissed AI setup").
     - Extraction: `gpt-4o`, falling back to `glm-5.3-flash`. Compare the India vision models with the `label-eval` skill.
     - Explanation and voice answers: `gpt-4o`, falling back to `gemma-4-31b`, with `reasoning_effort: "none"`.
     - STT: `saaras:v4`, falling back to `whisper`.
     - TTS: `bulbul:v3` with a voice per language, falling back to `gnani-timbre-v3.0`.
   - `gpt-4o` sunsets on 2026-11-16.
   - Health-data calls refuse models outside `INDIA_PROCESSED_MODELS`.
3. **Health data stays in India.**
   - Any prompt that contains a member's conditions, allergies, diet or logs must pass `provider={"data_residency": "in"}` (via `extra_body`).
   - It must also use a model whose catalogue `processing` is `india`.
4. **Strip personal data from prompts.** No names, emails, phone numbers, or account or member IDs. Use "the member" and their age band.
5. **Structured output only.** Use `response_format={"type": "json_schema", "json_schema": {...}}` with a Pydantic-generated schema.
   - Validate the response with the same Pydantic model.
   - If validation fails, retry once, then return an error. **Never fall back to invented values.**
6. **Version every prompt.** Prompts live in `app/prompts/<name>_v<N>.md`. Log the prompt version with each call.

## Calls

- **Vision extraction:** a user message with a text part plus `{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}`.
  - Only use models with `supports_vision: true`. Limit images to 8 MB.
- **STT:** `POST /v1/audio/transcriptions` (multipart).
  - `saaras:v4` takes **at most 30 s of audio** and 25 MB per file.
  - Pass the language when known (`hi-IN`, `mr-IN`, `en-IN`).
- **TTS:** `POST /v1/audio/speech` with `bulbul:*`.
  - **At most 2,500 characters** per call; split longer text on sentence boundaries.
  - Return mp3, which plays on both the Android app and in browsers.
- **Voice input formats differ by client:** Android `record` (AAC or WAV) and web `MediaRecorder` (usually WebM/Opus). Check which formats `saaras:v4` accepts. If needed, transcode server-side before the STT call, and test both clients' recordings.
- **WhatsApp and email:** use the resource API (`/api/v1/whatsapp/messages`, `/messages/template`, `/api/v1/email/send`).
  - WhatsApp needs approved templates and opted-in users.

## Errors and resilience

| Status | Meaning | Action |
|---|---|---|
| 402 `insufficient_credits` | Credit balance is zero | Do not retry. Alert ops (Sentry error) and return 503 with a friendly code. |
| 429 `rate_limit_exceeded` | Plan request cap hit | Retry with exponential backoff and jitter (max 3), honouring `Retry-After`. |
| 5xx or timeout | Upstream issue | Retry up to 2 times. Explanation endpoints degrade to engine reason codes without LLM text. |

- Timeouts: 30 s for vision, 15 s for chat, 20 s for STT and TTS.
- Log every call with: model id, prompt version, latency in ms, input and output tokens or credits, status. Never log the prompt body when it contains health data.

## Unverified, so check before relying on it

- A real-time voice-agent client (`/v1/voice/sessions` with `livekit-client`, or `wss://api.callmissed.com/v2/voice/agent`):
  - The web could use `livekit-client`. A Flutter client is not documented.
  - v1 uses push-to-talk via our API on both clients, for parity.
- SMS / DLT OTP. Not found in the docs. Phone OTP is planned via a **WhatsApp AUTHENTICATION template** through the Supabase Send-SMS hook.
- Exact Claude-model pricing, and per-plan call caps (Free: 100 LLM calls/month). Check `/v1/models` and the console.
