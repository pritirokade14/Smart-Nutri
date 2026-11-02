# ADR 0004: CallMissed API for LLM, vision, speech and WhatsApp

- **Status:** Accepted
- **Date:** 2026-11-02

## Context

We need several AI services:
- Vision extraction of nutrition labels
- Explanations in English, Hindi and Marathi
- Speech-to-text and text-to-speech in Indian languages
- Later, WhatsApp messaging (an OTP template, caregiver alerts, a bot)

The prototype used Groq, an end-of-life Gemini SDK, a Google Translate scraper and device TTS fixed to an English voice. Health data must be able to stay in India.

## Decision

Use the **CallMissed API** as the single AI and messaging gateway:
- **Inference:** `https://api.callmissed.com/v1`, OpenAI-compatible. `chat/completions` with vision and `response_format: json_schema`, `audio/transcriptions` (`saaras:v4`, 22 Indian languages) and `audio/speech` (`bulbul:v3` / `v4-flash`, including Hindi and Marathi).
- **Resources:** `https://api.callmissed.com/api/v1` for WhatsApp templates and messages, and email.
- **Data residency:**
  - Models carry a `processing` flag (`india` / `india_preferred` / `outside_india`).
  - Requests can force `provider.data_residency = "in"`.
  - Health-data prompts must use India-processed models.
- **Client:** the official `openai` Python SDK with `base_url` overridden, behind our own `LLMProvider` and `SpeechProvider` interfaces.
- **Model choice:** model IDs live in config. Defaults are chosen by the label eval set. See `docs/ARCHITECTURE.md`.

## Consequences

- **One vendor and one bill (credits, ₹).** There are many models (Sarvam, GPT, Gemini, GLM, Gemma and others) to compare without new integrations, plus Indic speech and WhatsApp in the same account.
- **Startup perks:** $1,000 in credits on application, and 50% off for DPIIT startups.
- **Risks:**
  - The vendor is young (founded 2026), and the catalogue and prices change.
  - Plan caps apply: Free allows 100 LLM calls a month, so launch needs Starter or higher.
  - No SMS/DLT product was found in the docs.
  - Real-time voice in Flutter needs either a LiveKit client or a raw-WebSocket proxy (v2).
- **Mitigations:**
  - Provider interfaces mean OpenAI-compatible vendors can be swapped by config.
  - Model IDs are pinned in config.
  - Explanations are cached.
  - `402 insufficient_credits` and `429` are handled explicitly, with credit-balance alerts.
  - Device STT and TTS remain a fallback.
- **The `cm_` key must never leave the backend.** The browser voice widget (publishable `pk_` key and signed tokens) is a v2 option.
