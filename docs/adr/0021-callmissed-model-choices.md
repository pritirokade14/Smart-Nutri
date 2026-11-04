# ADR 0021: CallMissed model choices, India-only allow-list and fallbacks

- **Status:** Accepted
- **Date:** 2026-11-04

## Context

SmartNutri sends four kinds of AI work to CallMissed (ADR 0004): label extraction (vision), explanations and voice answers (text), speech-to-text and text-to-speech. Explanations, voice answers and the spoken question and answer can carry anonymised member health data, which must be processed in India (AGENTS rule 6).

What we had before this ADR:

- Extraction defaulted to `kimi-k2.5`, which the catalogue marks `india_preferred`. That means it may be processed outside India.
- The explanation default `sarvam-105b` timed out at the 8 s budget.
- The TTS voice `anushka` is not a `bulbul:v3` voice, so CallMissed silently replaced it with a default voice.
- Nothing retried a different model when one failed.

What the official docs say (docs.callmissed.com, read 2026-11-04, plus the public catalogue `GET /api/v1/models`):

- **Processing.** Each model has `processing`: `india`, `india_preferred` or `outside_india`.
- **India-only mode.** `provider: {"data_residency": "in"}` serves a request only on `india` models, otherwise it returns `400 region_unavailable`. The field is documented for chat, messages, responses and embeddings. India-only mode set on an API key or workspace also covers STT and TTS.
- **Server-side fallback.** `models` is a fallback list, but it never applies to requests that send `response_format`. All of our LLM calls send it.
- **Reasoning.** `reasoning_effort` controls thinking, with a per-model matrix:
  - `"none"` switches thinking off on `gemma-4-31b`, `sarvam-105b` and `deepseek-v4.1-flash-1017`.
  - `glm-5.3-flash` cannot switch it off; it runs at `"low"`.
  - `gpt-4o` ignores the field.
- **India vision models.** `gpt-4o`, `gemma-4-31b`, `glm-5.3-flash` and `deepseek-v4.1-flash-1017`. Of these, only `glm-5.3-flash` documents JSON-schema structured output explicitly.
- **STT.**
  - `saaras:v4` takes locale codes (`hi-IN`) and at most 30 s of audio.
  - `whisper` is also India-processed, but its language codes are not documented.
- **TTS.**
  - `bulbul:v3` takes a `voice` and a `language`. Its recommended voices are `ratan` for en-IN and mr-IN, and `shubh` otherwise. It honours `mp3` and takes at most 2,500 characters.
  - `microsoft-neural-tts` (India) serves voice sessions only, so it returns 400 on `/v1/audio/speech`.
  - `gnani-timbre-v3.0` (India) is valid on `/v1/audio/speech`. Every one of its voices speaks en-IN, hi-IN and mr-IN.
- **`gpt-4o` is deprecated, with sunset 2026-11-16.** After that date it is answered by `gpt-6-sol`, which is `india_preferred`.

## Decision

Use India-processed models only, with one fallback per job. All values are config (`Settings`, `.env.example`):

| Job | Primary | Fallback | Notes |
|---|---|---|---|
| Extraction | `gemma-4-31b` | `glm-5.3-flash` | `reasoning_effort: "none"` (glm runs "low"); 70 s budget |
| Explanation and voice answer | `gemma-4-31b` | `deepseek-v4.1-flash-1017` | `reasoning_effort: "none"`; 8 s budget; `sarvam-105b` stays selectable |
| STT | `saaras:v4`, `language` en-IN / hi-IN / mr-IN | `whisper`, no `language` (auto-detect) | multipart `file`, `model`, `language` |
| TTS | `bulbul:v3`, voices en `ratan`, hi `shubh`, mr `ratan` | `gnani-timbre-v3.0`, voice `Chetana` | `response_format: "mp3"` |

- **Allow-list.** `INDIA_PROCESSED_MODELS` in `app/integrations/callmissed.py` lists the catalogue's `india` models we may use. `chat_json`, `transcribe` and `synthesize` refuse any other model, primary or fallback, before sending a request. Label extraction carries no health data, so it is not restricted, and the label eval can still compare any vision model.
- **Fallback on failure.**
  - A 5xx, a timeout or a `400 region_unavailable` from the primary switches to the fallback **once**, inside the same deadline. When a fallback is set, the primary may use 60% of the budget.
  - 402, 401, 403 and other 4xx never fall back.
  - Without a fallback, the old retry policy applies.
- **Residency.** Chat keeps sending `provider.data_residency = "in"`. STT and TTS keep sending it too, although it is undocumented there (dropping it could only weaken residency). The real guarantee for audio is the allow-list plus the API key's India-only setting.
- **Probe.** `scripts/probe_callmissed.py --yes-spend` checks every primary and fallback with the API's own request shapes. It costs at most about US$0.019 (Rs 1.80).

## Consequences

- **Plan.** Health data and label photos stay on India-processed models. The defaults now need a paid CallMissed plan (Starter or higher); only `saaras:v4`, `bulbul:v3` and `sarvam-105b` are free-tier.
- **`gpt-4o` sunset.** `gpt-4o` must be replaced as primary before 2026-11-16. Until then the `region_unavailable` fallback rule keeps explanations working on `gemma-4-31b`. The label eval should pick the extraction primary from the four India vision models, and the probe should confirm that `gemma-4-31b` honours strict JSON schema, because the docs do not say so.
- **Fallback provenance.** When the fallback answers an extraction, the scan still records and caches the primary model id. The `fallback_from=` log field shows the switch. A follow-up could store the answering model.
- **Adding a model.** Check its catalogue `processing` is `india`, add it to `INDIA_PROCESSED_MODELS` with a test, update this ADR and `docs/SETUP_ACCOUNTS.md`, and rerun the probe.

## Addendum 2026-11-04: no deprecated model (Ruling CM1)

`gpt-4o` (catalogue `deprecated: true`, `sunset_date` 2026-11-16) is no longer a default or a fallback. After the sunset it is rerouted to `gpt-6-sol`, which is `india_preferred`, so it is not guaranteed to be India-processed.

| Job | Primary | Fallback |
|---|---|---|
| Extraction (vision) | `gemma-4-31b` | `glm-5.3-flash` (documents JSON-schema output; always reasons, runs "low") |
| Explanation and voice answer | `gemma-4-31b`, `reasoning_effort: "none"` | `deepseek-v4.1-flash-1017`, `reasoning_effort: "none"` (documented to switch thinking off; India-processed, not deprecated) |

- `DEPRECATED_MODELS = {"gpt-4o"}` (sunset dates in `DEPRECATED_MODEL_SUNSETS`) in `app/integrations/callmissed.py`. `gpt-4o` is removed from `INDIA_PROCESSED_MODELS`, and the allow-list refuses any deprecated model, primary or fallback, before a request is sent.
- A test fails if any default or fallback model is deprecated.
- `glm-5.3-flash` is not used as an explanation fallback because it cannot turn reasoning off; `sarvam-105b` stays selectable but timed out at 8 s.
- Strict JSON on `gemma-4-31b` and `deepseek-v4.1-flash-1017` is undocumented; pydantic validation still rejects invalid output. Confirm with the probe.
- The probe now calls gemma and deepseek (chat), gemma and glm (vision), plus STT and TTS: 16 calls, upper-bound estimate about US$0.0188 (about Rs 1.80).
- This supersedes the Decision table's `gpt-4o` rows and the "`gpt-4o` sunset" consequence above.
