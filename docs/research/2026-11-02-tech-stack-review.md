# Tech Stack Review

**Date:** 2026-11-02 · Based on reading the full prototype on `main`, plus version and pricing checks.

> **Addendum (2026-11-02, later the same day). Decisions that supersede parts of this review:**
> - **Web is Next.js 16, not Flutter web** (ADR 0008). Flutter now targets Android only, and every v1 feature ships on both clients.
> - **Hosting:** the API and web both run on Cloud Run in Mumbai (ADR 0012). Firebase Hosting is no longer used.
> - **AI and speech:** CallMissed replaces direct Gemini, Groq and Sarvam calls (ADR 0004).
> - **State and structure:** Flutter uses Riverpod 3 (Provider and the singleton are dropped). The API is organised by feature (`app/features/*`), and Alembic owns the schema and RLS (ADR 0009).
> - **Shared packages:** `packages/api-contract` (generated Dart and TS clients), `i18n`, `design-tokens` and `test-fixtures` (ADR 0010).
> - **Delivery:** vertical slices M1–M6 across API, Android and web (ADR 0011).
> - Rows below that mention Flutter web, Firebase Hosting or direct Gemini or Sarvam are historical.

**Key takeaways**
- **Keep** Flutter, FastAPI and PostgreSQL. **Replace** almost everything inside them.
- `google-generativeai` reached end of life on 30 Nov 2025. The `translator` package is a scraper. Mock nutrition data was shown as real. The old prototype is a demo, not a foundation.
- Target stack:
  - Flutter with Riverpod, go_router, drift and mobile_scanner.
  - FastAPI on Cloud Run in Mumbai.
  - Supabase in Mumbai for auth, Postgres and storage.
  - **CallMissed** for the LLM, vision, STT and TTS.
- Read labels by sending the photo straight to a vision LLM with a JSON schema. Drop EasyOCR, Torch and OpenCV.
- Estimated cost at ~10k MAU is ~$400–1,300 a month. Voice is the largest optional line.

## Layer-by-layer

| Layer | Prototype | Recommendation | Why |
|---|---|---|---|
| Mobile framework | Flutter | **Keep** (3.44.x locally; latest 3.47.x) | One codebase for Android, web and iOS |
| State | Provider plus a 1,557-line screen | **Replace:** `flutter_riverpod` 3.x with `riverpod_generator`, `go_router`, `dio`, `freezed` | Testable async state. Bloc has had no release since May 2025 |
| Local data | One JSON blob in shared_preferences | **Replace:** `drift` (offline log) plus `flutter_secure_storage` | Queries, persistence, sync. Isar is unmaintained |
| Barcode | None | **Add** `mobile_scanner` 7.x | On-device, fast, works offline |
| Label reading | OpenCV + EasyOCR (English only) → Groq | **Replace:** label photo → vision LLM via CallMissed with a JSON schema. Optional on-device ML Kit OCR preview | EasyOCR loses table layout and Devanagari, and needs Torch (GBs) |
| LLM SDK | `google-generativeai` 0.4.1 (end of life) | **Replace:** OpenAI SDK pointed at the CallMissed gateway | Structured output; swappable providers |
| UI translation | `translator` (scraper) | **Replace:** ARB files for app text; the LLM writes answers directly in the user's language | The scraper is "educational" and "may break anytime" |
| STT / TTS | Device STT, `flutter_tts` en-US | **Upgrade:** CallMissed `saaras:v4` / `bulbul`; device as free fallback | Correct Indian-language recognition and voices |
| Backend | FastAPI 0.110; sync calls inside async handlers | **Upgrade:** current FastAPI, Pydantic 2, async clients, `pydantic-settings`, `uv`, Python 3.13 | Old pins (numpy 1.26.4) can't install on 3.13 |
| Database | `create_all`, no migrations | **Keep Postgres** on Supabase Pro (Mumbai); SQLAlchemy 2 + Alembic | Relational data (families, logs); row-level security |
| Auth | None | **Supabase Auth:** Google OAuth, email OTP/magic link; phone OTP later (WhatsApp OTP via CallMissed + Send-SMS hook) | Simplest secure option |
| Files | Local `uploads/` folder, never cleaned | Supabase Storage private bucket, signed URLs, 30-day retention | Privacy |
| Cache / jobs | None | Postgres cache tables first (barcode → product, image hash → extraction); Redis plus a task queue later | Fewer LLM calls; fits CallMissed caps |
| Hosting | localhost | Cloud Run asia-south1 (Mumbai) | Data stays in India; scales to zero |
| Observability | `print` | Sentry (Flutter + Python), structured logs, LLM call log with prompt version; PostHog later | Debugging and quality |
| Tests / CI | One stale widget test | pytest + httpx, **label evaluation set of 100–200 Indian labels**, Flutter widget and integration tests, GitHub Actions | Accuracy is the product |

### CallMissed replaces direct vendors

The tech review first recommended Gemini directly, plus Sarvam for speech. The founder chose **CallMissed**. Its OpenAI-compatible gateway serves Gemini, GPT-6, GLM, Gemma, Kimi, Sarvam and others, along with Sarvam's speech models. So:

| Earlier plan | Now |
|---|---|
| Gemini Flash-Lite via `google-genai` | A vision model via CallMissed `/v1/chat/completions` with `json_schema` |
| Groq gpt-oss-120b | Not needed |
| Sarvam Saaras / Bulbul directly | `saaras:v4` / `bulbul:v3` via CallMissed `/v1/audio/*` |
| `translator` scraper | LLM writes in the user's language; ARB files for UI text |

See [callmissed-platform](2026-11-02-callmissed-platform.md).

## Scanning options compared

| Option | Strengths | Weaknesses |
|---|---|---|
| **Barcode → database** | Exact match | Open Food Facts India ~25K products, so it often misses |
| **On-device ML Kit OCR** | Free and fast | Latin and Devanagari only; loses the table; still needs an LLM |
| **Server EasyOCR** | — | Slow on CPU, heavy, loses layout |
| **Vision LLM** | Reads layout and Indian scripts; ~2–6 s; ~$0.001 per scan or less | Can invent numbers |

No published head-to-head comparison exists. An older study favoured OCR + LLM over GPT-4V-era models, and IndicVisionBench ranked Gemini 2.5 Flash top for Indian-language OCR. **Measure on our own evaluation set.**

Guarding against invented values:
- A confidence score and the per-100 g basis in the schema.
- An energy check: kcal ≈ 4P + 4C + 9F.
- A confirmation screen before saving.
- Never fill in missing values.

## Cost estimate (~10k MAU, ~20 scans per user per month)

| Item | Estimate |
|---|---|
| Label extraction (200k scans, minus barcode and cache hits) | ~$60–240 a month, depending on model (gpt-6-luna ~$0.10/$0.52 per 1M tokens; gemini-3.5-flash-lite $0.31/$2.60) |
| Explanation and coach | ~$100–300 a month |
| STT (5 min per user at saaras:v4, $0.3125/hr) | ~$260 a month |
| TTS (3k chars per user at bulbul:v3, $0.3125 per 10k chars) | ~$95 a month |
| Supabase Pro | $25 plus compute |
| Cloud Run | $0–30 |
| Sentry | free or ~$26–29 [unverified] |
| CallMissed plan | Starter ₹999 or Pro ₹4,999 a month (call caps; see the CallMissed doc) |
| **Total** | **~$400–1,300 a month (₹35k–1.1 lakh)** |

## Defects in the old prototype (fixed by the rebuild)

1. **Profile fields mismatched.** `models.py` uses `name`/`preference`, `main.py` reads `full_name`/`preferences`, so the vegetarian check never ran.
2. **One global profile.** Every scan used the most recently saved profile, whoever saved it.
3. **The app never sent `goal`**, then overwrote its own goal with the server's.
4. **Fake nutrition.** `fallback_mock_parser` returned invented values (380 kcal, 32 g sugar) on any error, shown as real.
5. **More invented values.** `normalize_nutrition_data` made up macros from calories and guessed mg-vs-g for salt.
6. **Incomplete extraction.** The prompt never asked for carbs, fibre, sodium, serving size or per-100 g basis, so carbs were always 0. The score was a heuristic labelled "Nutri-Score".
7. **Indian text destroyed.** `string_sanitize` stripped all non-ASCII text, deleting Devanagari. EasyOCR ran English only.
8. **Blocking calls** in async endpoints, and the OCR model loaded at import time.
9. **Unsafe uploads.** Files saved under client filenames in a shared folder, never deleted, with no limits. Product name taken from the filename.
10. **Security.**
    - No auth.
    - CORS allowed `*` with credentials.
    - `str(e)` leaked to clients.
    - `/health` lied about the database.
    - Prompt injection via voice questions; no rate limits.
11. **No migrations.** `get_db` was defined twice. JSON was parsed with a regex on an end-of-life SDK.
12. **numpy 1.26.4 can't install on Python 3.13.** Five dependencies were unused.
13. **Desktop-only.**
    - Hardcoded `127.0.0.1`.
    - No Android INTERNET/CAMERA/RECORD_AUDIO permissions; no iOS usage strings; macOS lacked `network.client`.
    - No camera support.
14. **"Weekly" totals summed every scan ever.** The history blob grew without limit.
15. **Voice.** TTS fixed to en-US; STT used the default locale.
16. **Open Food Facts misuse.** Legacy `cgi/search.pl` called with no User-Agent; alternatives searched by the first word only.
17. **Allergen matching was an English substring check.**
18. **The only test was stale**, there was no CI, and the 1,557-line screen mixed UI, HTTP and logic.

## Migration risks

- **Invented numbers become dangerous once medical conditions are involved.** Mitigate with the confirmation screen, sanity checks, rule-based verdicts and a disclaimer.
- **DPDP compliance.** Core obligations apply from ~May 2027. Build consent and deletion now.
- **Vendor and model churn.** Pin model IDs in config and keep providers swappable.
- **Open Food Facts India has only ~25K products, under ODbL.** Use crowdsourcing into our own table.
- **Phone OTP over SMS needs DLT registration.** Use WhatsApp OTP instead (see the CallMissed doc).

## Sources

- **Gemini SDK end of life:** https://github.com/google-gemini/deprecated-generative-ai-python
- **Gemini docs:** pricing https://ai.google.dev/gemini-api/docs/pricing · deprecations https://ai.google.dev/gemini-api/docs/deprecations
- **IndicVisionBench:** https://arxiv.org/pdf/2511.04727
- **OCR studies:** https://arxiv.org/abs/2510.03570 · https://arodes.hes-so.ch/record/15159
- **`translator` package:** https://pub.dev/packages/translator
- **Supabase:** pricing https://supabase.com/pricing · regions https://supabase.com/docs/guides/platform/regions
- **Cloud Run:** https://cloud.google.com/run/pricing
- **Open Food Facts API:** https://openfoodfacts.github.io/openfoodfacts-server/api/
- **Package versions:** pub.dev and PyPI pages for each package named above.
