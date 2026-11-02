# CallMissed Platform for SmartNutri

**Date:** 2026-11-02 · Sources: public docs (docs.callmissed.com, callmissed.com/pricing), checked against the **live model catalogue** through the CallMissed tools on 2026-11-02.

**Key takeaways**
- One OpenAI-compatible gateway (`https://api.callmissed.com/v1`) gives us vision LLMs with JSON schemas, Indian-language STT (`saaras:v4`) and TTS (`bulbul`). It replaces direct Gemini, Groq and Sarvam.
- Several vision models are **processed in India** (`glm-5.3-flash`, `gemma-4-31b`, `deepseek-v4.1-flash-1017`), which helps with DPDP.
- **WhatsApp OTP authentication templates** (with zero-tap autofill on Android) can replace SMS OTP and avoid DLT registration.
- Gaps:
  - No SMS/DLT product was found.
  - No Flutter SDK; use REST or WebSocket through our backend.
  - Monthly call caps (Pro: 50k LLM calls) mean we must cache.
- Pricing: 1 credit = ₹1. 1,000 free credits on signup. $1,000 startup credits, and 50% off for DPIIT-registered startups.

## Basics

- **Inference base:** `https://api.callmissed.com/v1`. Covers chat, responses, messages, embeddings, audio, images, search and models.
- **Resource base:** `https://api.callmissed.com/api/v1`. Covers WhatsApp, email, telephony, knowledge, bots, conversations and webhooks.
- **Auth:** `Authorization: Bearer cm_...`. Keys are scoped by service and resource, never expire, and can be revoked. **Keep them on the server only.**
- **SDKs:** use the official OpenAI or Anthropic SDK with a different `base_url`. There is no CallMissed or Flutter SDK.
- **Errors:** OpenAI-style. `402 insufficient_credits`, `429 rate_limit_exceeded`. Supports an `Idempotency-Key` header.
- **Data residency:**
  - Per request: `provider: {"data_residency": "in"}`.
  - Zero-data-retention routes: `provider.zdr`.
  - Each model in the catalogue has a `processing` field: `india`, `india_preferred` or `outside_india`.

## LLM and vision models (live catalogue, per 1M tokens, USD)

| Model | Vision | Processing | In / Out | Notes |
|---|---|---|---|---|
| `gpt-6-luna` | yes | india_preferred | 0.1042 / 0.5208 | Cheapest vision model; extraction candidate |
| `glm-5.3-flash` | yes | **india** | 0.2292 / 0.7604 | Extraction candidate |
| `gemini-3.5-flash-lite` | yes | outside_india | 0.3125 / 2.604 | Strong at Indic OCR; extraction candidate |
| `gemma-4-31b` | yes | **india** | 0.3646 / 0.9375 | 131k context |
| `deepseek-v4.1-flash-1017` | yes | **india** | 0.4271 / 1.771 | — |
| `kimi-k2.5` / `kimi-k2.6` | yes | india_preferred | 0.84 / 4.22 · 1.33 / 5.63 | Free-plan models |
| `gemini-3.8-flash` | yes | outside_india | 1.563 / 7.813 | Higher quality |
| `claude-haiku-5-5` / `claude-sonnet-5-5` | yes | outside_india | 0.10 / 0.52 · 2.08 / 10.42 | Requires Pro plan |
| `gpt-6-sol` | yes | india_preferred | 2.083 / 10.42 | — |
| `sarvam-105b` | no | **india** | 0.1563 / 0.625 | Free plan; Indic-native; **explanation and coach candidate** |
| `gpt-oss-120b` | no | india_preferred | 1.042 / 4.167 | Free plan |

**Features:**
- `response_format` accepts `json_object` or `json_schema`. Requests that use tools or `response_format` never silently fall back to another model.
- SSE streaming.
- Up to 128 tools.
- `image_url` accepts a URL or base64.
- Gemini models also accept audio and PDF.
- `bot_id` + `knowledge_top_k` gives grounding (RAG).

## Speech (live catalogue)

**STT:** `POST /v1/audio/transcriptions` (multipart, 25 MB max).

| Model | Processing | Price | Notes |
|---|---|---|---|
| `saaras:v4` | **india** | $0.3125/hr | Free plan; 22 Indian languages + English; transcribe, translate, verbatim, translit and codemix (Hinglish) modes; **30 s per request**; no streaming |
| `gnani-prisma-v3.0` | india | $0.2813/hr | 10 languages, streaming |
| `whisper` | india | $0.4167/hr | 99 languages |
| `gpt-4o-mini-transcribe` | india_preferred | $0.25/hr | Streaming |
| `microsoft-speech-stt` | india | $1.042/hr | 12 Indian languages; voice sessions only |

**TTS:** `POST /v1/audio/speech`. Output formats: mp3, wav, pcm, aac, flac.

| Model | Processing | Price per 10k chars | Notes |
|---|---|---|---|
| `bulbul:v3` | **india** | $0.3125 | Free plan; 37 voices, 11 Indic languages incl. hi-IN and mr-IN; 2,500-char limit |
| `bulbul:v4-flash` | **india** | $0.2083 | Free plan; 222 persona voices, 9 Indic languages + Hinglish |
| `microsoft-neural-tts` | india | $0.1563 | 57 voices, 12 Indian languages |
| `gnani-timbre-v3.0` | india | $0.2813 | English + Hindi + 8 others |

## Voice agents (v2)

- **WebRTC:** `POST /v1/voice/sessions` returns a `ws_url` and a 1-hour token, used with `livekit-client`. Whether LiveKit's Flutter SDK works with it is unverified.
- **Raw WebSocket:** `wss://api.callmissed.com/v2/voice/agent` (PCM s16le 16 kHz), or `/v1/agent/converse` (Deepgram-compatible).
  - Easiest fit for Flutter, **proxied through FastAPI** so the key never reaches the device.
  - Client-side tool calls only (`FunctionCallRequest` / `FunctionCallResponse`).
  - Sessions up to 2 hours; 25k-character prompt; 30 s tool timeout.
- **Web widget:** a `pk_` publishable key, an origin allow-list and backend-signed tokens.
- **Saved agents (`bot_id`):** custom REST tools that call our HTTPS endpoint, `mcp_servers`, a built-in `http_request`, and memory tools.
- **Price:** ₹4 (Standard), ₹5 (Expressive) or ₹6 (Best latency; docs say ₹8 from 30 Nov 2026) per minute, with a 30 s minimum. **Too expensive as a free consumer feature**, so treat it as a premium feature.

## WhatsApp, email, other

- **WhatsApp:**
  - Bring your own WABA via Embedded Signup.
  - Send endpoints: `POST /api/v1/whatsapp/messages` and `/messages/template`.
  - Templates, campaigns, Flows, catalog and orders, UPI payments.
  - Inbound `message.received` webhooks, signed with HMAC-SHA256. Custom webhooks need Pro.
- **WhatsApp OTP:** AUTHENTICATION templates with `copy_code`, `one_tap` or `zero_tap` buttons. Zero-tap needs our Android `package_name` and `signature_hash`, and the template needs WABA approval. Meta conversation fees are billed separately.
- **SMS / DLT:** **not found in the docs.** Confirm with sales@callmissed.com.
- **Email:** `POST /api/v1/email/send`, from our own verified domain.
- **Knowledge and RAG:** `POST /api/v1/knowledge/search`. Sources can be text, URL or PDF.
- **Embeddings:** up to 128 strings per call.
- **Also available:** batch API, web search (1 credit), images (flux-2-pro, 10 credits), and a usage summary at `GET /v1/usage/summary`.

## Plans and caps

| Plan | Price/mo | Credits/mo | Requests/min | LLM calls/mo | STT calls/mo | TTS calls/mo |
|---|---|---|---|---|---|---|
| Free | ₹0 | — | 60 | 100 | 50 | 50 |
| Starter | ₹999 | 500 | 500 | 5,000 | 2,500 | 2,500 |
| Pro | ₹4,999 | 5,000 | 3,000 | 50,000 | 25,000 | 25,000 |
| Enterprise | ₹20,000+ | 20,000 | 10,000 | uncapped | uncapped | uncapped |

- Credits are prepaid and never expire. Top-ups range from 10 to 50,000 credits.
- Call caps are limits, not included usage; credits are still spent.
- The free plan allows only free-tier models, 2 team members and 100 MB of storage.
- **For launch:** use Starter during development and testing, and Pro at launch.
- **At ~10k MAU × 20 scans** (200k potential calls) we need caching (barcode → product, image hash → extraction, product + profile hash → explanation), or Enterprise.

## How SmartNutri uses CallMissed

| Need | v1 | v2 |
|---|---|---|
| Label photo extraction | Vision model + `json_schema` (model chosen by our evaluation set) | Batch re-extraction for catalogue quality |
| Explanation and tips in en/hi/mr | `sarvam-105b`, India-processed, with `data_residency: "in"` | Coach chat grounded in ICMR-NIN guidelines via knowledge `bot_id` |
| Voice Q&A | Push-to-talk: `saaras:v4` → LLM → `bulbul` (through FastAPI) | Real-time voice agent via WebSocket proxy, as a premium feature |
| Phone login | Code written: Supabase Send-SMS hook → WhatsApp OTP template (switched off until the template is approved) | Switch on |
| Email OTP and magic link | Supabase built-in SMTP for development | Supabase Send-Email hook → CallMissed email from our domain |
| Family alerts and weekly report | — | WhatsApp templates to caregivers |
| WhatsApp bot (photo → verdict) | — | Inbound webhook → our pipeline |
| Product similarity and alternatives | Rules plus Open Food Facts | Embeddings over our products table |

**Models to confirm on the evaluation set (50–200 real Indian labels):**
- Extraction: `gpt-6-luna` vs `glm-5.3-flash` vs `gemma-4-31b` vs `gemini-3.5-flash-lite`.
- Explanation: `sarvam-105b` vs `gpt-6-luna`.
- Measure field accuracy, Devanagari handling, latency and cost.
- **Model IDs stay in config.**

## Sources

- **Developer pages:** https://www.callmissed.com/developers · https://docs.callmissed.com/docs/quickstart · https://docs.callmissed.com/docs/authentication
- **LLM:** https://docs.callmissed.com/docs/chat-completion
- **Speech:** STT https://docs.callmissed.com/docs/speech-to-text · TTS https://docs.callmissed.com/docs/text-to-speech
- **Voice agents:**
  - https://docs.callmissed.com/docs/voice-agent
  - https://docs.callmissed.com/docs/voice-sdk
  - https://docs.callmissed.com/docs/managed-voice-agent
  - https://docs.callmissed.com/docs/voice-widget
  - https://docs.callmissed.com/docs/voice-agent-tools
- **WhatsApp:** https://docs.callmissed.com/docs/whatsapp · https://docs.callmissed.com/docs/whatsapp-templates
- **Pricing and models:** https://www.callmissed.com/pricing · https://www.callmissed.com/models
- **Live catalogue:** CallMissed `list_models` (llm, stt, tts), 2026-11-02
