# Plan 4 (M2): Label Photo → Confirm → Verdict Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** On **Android or web** a user photographs a nutrition label (or lands here automatically when a barcode isn't found, F15). They then see a **draft** of the extracted values, correct it on an editable confirm screen, save it as a product (`verification_status='pending'`), and get the same verdict screen as M1. Extraction never invents a value, never runs twice for the same image, and never decides a verdict.

**Architecture:**
- **API first:**
  1. A strict extraction schema and a versioned prompt.
  2. A CallMissed vision call behind `LLMProvider`.
  3. A pure normaliser with plausibility checks.
  4. A signed-URL upload, then `POST /v1/scans/label`, cached by image SHA-256 and rate-limited at 30 per day.
  5. `POST /v1/products` for the confirmed draft.
- A label-eval harness picks the CallMissed vision model before M2 closes.
- Then `just contract` and i18n.
- Then **Android ∥ web** client tasks.
- After saving, the clients reuse M1's `analyze_create` and result screens.

**Tech Stack:** FastAPI, Pydantic 2, the `openai` SDK pointed at CallMissed, httpx, Supabase Storage (signed upload URLs) · Flutter (`image_picker`, dio, Riverpod) · Next.js 16 (react-hook-form + zod, Canvas resize, Vitest, Playwright).

**Spec:** `docs/superpowers/specs/2026-11-02-smartnutri-v1-design.md` (F4, F15, §3 CallMissed rules and model candidates, §4 `products`/`scans`, §5 rate limits), `.claude/skills/{callmissed,label-eval}/SKILL.md`, `docs/FEATURE_PARITY.md`. **Depends on:** Plans 1, 2 and 3 (M1: `record_to_product`, `ProductOut`, `analyze_create`, the result screens on both clients).

## Global Constraints

- **Naming contract (Plan 2):**
  - `app.core.config.get_settings()`, `app.core.security.current_account` → `AccountContext`, `app.db.session.get_session`
  - `app.core.errors.ApiError(code, status, message_key)`, `app.core.ratelimit.limit(bucket)`
  - `app.integrations.providers.LLMProvider`, `app.integrations.callmissed.CallMissedClient`, `app.integrations.storage.StorageClient`
  - ORM classes `ProductRecord` and `ScanRecord`. If Plan 2 named them differently, use Plan 2's names.
- **Prompts:** `app/prompts/extraction_v1.md`. Any later change creates `extraction_v2.md`; never edit a released version. Log the prompt version with every call.
- **Model id** comes only from `Settings.callmissed_extraction_model` (env `CALLMISSED_EXTRACTION_MODEL`). No model-id literals in code.
  - Call parameters: temperature 0; `response_format` = `json_schema` (strict) generated from the Pydantic model.
  - The label photo contains no member data, so `data_residency` is not required here. Still prefer an India-processed model when eval quality is similar.
- **Never invent values:**
  - A value not printed on the label is `null` → `None`.
  - If the provider fails, or validation fails twice, return an error with **no draft**.
  - The only derivation allowed: if a label prints only per-serving values **and** prints the serving size, then `per_100g = value × 100 / serving_size_g`, with the draft flag `derived_from_serving = true`. Without a printed serving size, per-100 g stays `None`. Never assume 100 g.
- **Confidence:** `ProductRecord.extraction_confidence` = the draft's `confidence` for label-sourced products. User edits do **not** raise it. A manual-entry product (no `scan_id`) has confidence 1.0, because a person typed it. The engine's 0.7 threshold therefore still protects allergic members.
- **Uploads:**
  - Private bucket `Settings.storage_bucket` (env `SUPABASE_STORAGE_BUCKET`, default `label-photos`), path `<account_id>/<uuid4>.<ext>`.
  - Signed upload URL valid for 600 s.
  - Server-side: size ≤ 8 MB (`413 image_too_large`); magic-byte check for JPEG, PNG or WebP (`415 unsupported_image`); the path must start with the caller's `account_id` (`404 scan_image_not_found` otherwise).
- **Cache and limits:**
  - The extraction cache key is `image_sha256`. A cache hit returns the stored draft, makes **no** CallMissed call, and does **not** count toward the limit.
  - The `label_scans` bucket allows 30 **paid** extractions per account per day. Over the limit → `429 rate_limited_scans` with `retry_after`.
- **Errors:**

| Condition | Response |
|---|---|
| Provider 402 | `503 extraction_unavailable` (also logged to Sentry) |
| Provider timeout, 5xx after retries, or invalid output twice | `502 extraction_failed` |

- **Clients:**
  - The confirm screen is mandatory before any product is saved. Blank fields stay blank, never `0`.
  - Draft warnings are shown inline.
  - A **"Enter manually"** path (an empty form) is always available, including after any extraction error.
- **Strings and colours** come from `packages/i18n` and `packages/design-tokens` only.
- **Commit scopes:** `api`, `contract`, `i18n`, `app`, `web`, `evals`. Each commit ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Per-serving-only label without a serving size:** per-100 g stays `None`, the draft says so (`warnings` has `per_100g_missing`), and the verdict is `unknown`. Owned by Task 3.
2. **The same photo uploaded twice** (same bytes, by this account or another): the second request makes no CallMissed call and leaves the rate-limit counter unchanged. Owned by Task 4.
3. **A Hindi or bilingual label:** ingredients come back in Devanagari and stay Devanagari end to end (no ASCII stripping, which was the prototype bug), so the engine's Hindi allergen terms still match. Owned by Tasks 1, 3 and 5.
4. **Model reports high confidence with an implausible value** (sugars 250 g/100 g): the draft flags `implausible_value:sugars_g`, the confirm screen highlights the field, and saving is rejected with `422 implausible_value` until it is fixed or blanked. Owned by Tasks 3, 5, 8 and 9.
5. **CallMissed out of credits or timing out:** the clients show a retry plus "Enter manually", and there is no fake draft. Owned by Tasks 2, 4, 8 and 9.

## File Map

```
apps/api/app/features/scans/schemas.py            # Task 1  NutritionExtraction, ProductDraft, ScanDraftOut
apps/api/app/prompts/extraction_v1.md             # Task 1
apps/api/app/integrations/providers.py            # Task 2  (add extract_label to LLMProvider)
apps/api/app/integrations/callmissed.py           # Task 2  (implement extract_label)
apps/api/app/features/scans/normalize.py          # Task 3  extraction → ProductDraft (pure)
apps/api/app/integrations/storage.py              # Task 4  (add signed upload + download if Plan 2 lacks them)
apps/api/app/features/scans/{service,router}.py   # Task 4
apps/api/app/features/products/{schemas,service,router}.py   # Task 5 (extend M1 files)
apps/api/tests/evals/labels/{run_eval.py,metrics.py,manifest.csv,expected/,results/}   # Task 6
packages/api-contract/**, packages/i18n/messages/*.json      # Task 7
apps/app/lib/features/scan/...                    # Task 8  (Android, parallel with Task 9)
apps/web/src/features/scan/...                    # Task 9  (web, parallel with Task 8)
docs/FEATURE_PARITY.md, docs/adr/0016-label-scan-pipeline.md        # Task 10
```

---

### Task 1: Extraction schema and prompt v1

**Files:**
- Create: `apps/api/app/features/scans/schemas.py`, `apps/api/app/prompts/extraction_v1.md`, `apps/api/tests/unit/scans/test_extraction_schema.py`

**Interfaces:**
- Produces:

```python
class NutrientsIn(BaseModel):            # model_config = ConfigDict(extra="forbid")
    energy_kcal: float | None; energy_kj: float | None; protein_g: float | None; carbs_g: float | None
    sugars_g: float | None; added_sugars_g: float | None; fat_g: float | None; sat_fat_g: float | None
    trans_fat_g: float | None; fiber_g: float | None; salt_g: float | None; sodium_mg: float | None
class NutritionExtraction(BaseModel):    # extra="forbid"; every field REQUIRED (nullable), as strict json_schema needs
    product_name: str | None; brand: str | None
    basis_detected: Literal["per_100g", "per_serving", "both", "unknown"]
    per_100g: NutrientsIn | None; per_serving: NutrientsIn | None; serving_size_g: float | None
    ingredients: list[str]               # as printed, original script, order kept
    allergen_statement: str | None; may_contain_statement: str | None
    claims: list[str]                    # front-of-pack claims as printed
    veg_mark: Literal["veg", "non_veg"] | None
    category_guess: Literal["general", "beverage", "water", "cheese", "fat"] | None
    confidence: float                    # 0..1, model's own legibility estimate
    unreadable_fields: list[str]
def extraction_json_schema() -> dict     # NutritionExtraction.model_json_schema() adapted for strict mode (additionalProperties false everywhere)
```

`extraction_v1.md` must state these rules:
- Copy numbers exactly as printed. Use `null` for anything not printed or unreadable, and never estimate.
- Detect the basis (per 100 g or ml, per serving, or both).
- Keep sodium in mg and salt in g; don't convert.
- Keep the ingredient text in its original script (Hindi stays Devanagari).
- List INS/E codes as printed.
- Front-of-pack claims are copied verbatim.
- The green or brown dot maps to `veg_mark`.
- Output only JSON that matches the schema.

- [x] **Step 1: Write failing tests**

```python
def test_schema_is_strict():
    s = extraction_json_schema()
    assert s["additionalProperties"] is False and set(s["required"]) == set(NutritionExtraction.model_fields)
def test_devanagari_ingredients_roundtrip():
    e = NutritionExtraction.model_validate(sample_extraction(ingredients=["मूंगफली", "चीनी"]))
    assert e.ingredients == ["मूंगफली", "चीनी"]
def test_rejects_unknown_keys():
    with pytest.raises(ValidationError): NutritionExtraction.model_validate(sample_extraction(extra_key=1))
def test_prompt_v1_exists_and_forbids_guessing():
    text = (PROMPTS / "extraction_v1.md").read_text()
    assert "null" in text and "never estimate" in text.lower()
```

`sample_extraction(**overrides)` is a test helper that returns a complete valid dict.

- [x] **Step 2: Run them to verify they fail.** Run: `cd apps/api && uv run pytest tests/unit/scans/test_extraction_schema.py -v`. Expected: FAIL.
- [x] **Step 3: Implement** the schemas and write the prompt.
- [x] **Step 4: Run them to verify they pass.**
- [x] **Step 5: Commit** with message `feat(api): label extraction schema and prompt v1`.

---

### Task 2: `LLMProvider.extract_label` via CallMissed

**Files:**
- Modify: `apps/api/app/integrations/providers.py`, `apps/api/app/integrations/callmissed.py`
- Create: `apps/api/tests/unit/integrations/test_callmissed_extract.py`, `apps/api/tests/fakes/llm.py` (a `FakeLLM` used by later tasks)

**Interfaces:**
- Produces:

```python
class ExtractionFailed(Exception): ...                  # invalid output twice, timeout, 5xx after retries
class ProviderUnavailable(Exception): reason: str        # e.g. "insufficient_credits"
class LLMProvider(Protocol):                             # existing protocol + this method
    async def extract_label(self, *, image: bytes, mime: str, prompt: str, prompt_version: str,
                            schema: type[BaseModel], model: str) -> BaseModel
class FakeLLM:                                           # tests/fakes/llm.py
    calls: int
    def __init__(self, result: BaseModel | Exception): ...
```

`CallMissedClient.extract_label` works like this:
- **Request:** one user message, a text part (the prompt) plus `{"type": "image_url", "image_url": {"url": "data:<mime>;base64,..."}}`. `response_format={"type": "json_schema", "json_schema": {"name": "nutrition_extraction", "strict": True, "schema": ...}}`, `temperature=0`, timeout 30 s.
- **Validation:** validate the content with `schema.model_validate_json`. On a validation error, retry **once**, then raise `ExtractionFailed`.
- **Status handling:**
  - 429: back off with jitter, honouring `Retry-After`, up to 3 tries.
  - 5xx or timeout: up to 2 retries, then `ExtractionFailed`.
  - 402: `ProviderUnavailable("insufficient_credits")`, with no retry.
- **Logging:** one structured log line per call with `model`, `prompt_version`, `latency_ms`, `status`, and tokens or credits if returned. **Never** log the image or the response body.

- [x] **Step 1: Write failing tests** (the `openai` client is built with `http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))`)

```python
async def test_request_shape(mock_cm):
    await client.extract_label(image=b"\xff\xd8...", mime="image/jpeg", prompt="P", prompt_version="extraction_v1", schema=NutritionExtraction, model="m")
    body = mock_cm.last_json()
    assert body["temperature"] == 0 and body["response_format"]["json_schema"]["strict"] is True
    assert body["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
async def test_retry_once_then_fail_on_invalid_json(mock_cm_invalid_twice):
    with pytest.raises(ExtractionFailed): await ...;  assert mock_cm_invalid_twice.calls == 2
async def test_402_raises_unavailable_without_retry(mock_cm_402): ...       # calls == 1, reason == "insufficient_credits"
async def test_429_backoff_then_success(mock_cm_429_then_ok): ...
async def test_log_has_no_body(caplog, mock_cm): ...                        # no base64 string and no "per_100g" in any log record
```

- [x] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/unit/integrations/test_callmissed_extract.py -v`. Expected: FAIL.
- [x] **Step 3: Implement.** Patch `asyncio.sleep` in tests so backoff is instant.
- [x] **Step 4: Run them to verify they pass.**
- [x] **Step 5: Commit** with message `feat(api): CallMissed vision extraction behind LLMProvider`.

---

### Task 3: Normalise the extraction into a draft (pure)

**Files:**
- Create: `apps/api/app/features/scans/normalize.py`, `apps/api/tests/unit/scans/test_normalize.py`

**Interfaces:**
- Consumes: `NutritionExtraction` (Task 1); the plausibility bounds from `app.scoring.models` (Plan 1, `Nutrients.sanitized`).
- Produces:

```python
class ProductDraft(BaseModel):
    name: str | None; brand: str | None; category: Literal["general","beverage","water","cheese","fat"]
    per_100g: NutrientsOut                        # M1 schema
    serving_size_g: float | None
    ingredients: list[str]; allergen_statement: str | None; may_contain_statement: str | None
    claims: list[str]; veg_mark: Literal["veg","non_veg"] | None
    confidence: float; derived_from_serving: bool
    warnings: list[str]                           # codes, see below
def to_draft(e: NutritionExtraction) -> ProductDraft
```

Rules:
1. `energy_kcal`: printed kcal, else `energy_kj / 4.184`.
2. If `per_100g` has no numeric values but `per_serving` and `serving_size_g` exist, set `per_100g = per_serving × 100 / serving_size_g` and `derived_from_serving = True`. If there's no serving size, per-100 g stays all `None` and warnings gains `per_100g_missing`.
3. A value outside the `Nutrients.sanitized()` bounds is **kept in the draft**, so the user can see and fix it, and warnings gains `implausible_value:<field>`.
4. Energy check: when kcal, protein, carbs and fat are all present and `|kcal − (4p + 4c + 9f)| > max(0.15 × kcal, 20)`, add `energy_mismatch`.
5. Salt check: when salt and sodium are both present and `|salt − sodium × 2.5 / 1000| > 0.2 × salt`, add `salt_sodium_mismatch`.
6. When `confidence < 0.7`, add `low_confidence` (the engine will treat ingredients as unknown).
7. `category` = `category_guess` or `"general"`. Ingredients are stripped, empties dropped, the script untouched.

- [x] **Step 1: Write failing tests**

```python
def test_per_serving_converted_with_serving_size():
    d = to_draft(ex(basis_detected="per_serving", per_100g=None, per_serving=n(sugars_g=5.0, energy_kcal=120), serving_size_g=25))
    assert d.per_100g.sugars_g == 20.0 and d.per_100g.energy_kcal == 480 and d.derived_from_serving
def test_per_serving_without_serving_size_stays_missing():
    d = to_draft(ex(per_100g=None, per_serving=n(sugars_g=5.0), serving_size_g=None))
    assert d.per_100g.sugars_g is None and "per_100g_missing" in d.warnings
def test_implausible_value_kept_and_flagged():
    d = to_draft(ex(per_100g=n(sugars_g=250))); assert d.per_100g.sugars_g == 250 and "implausible_value:sugars_g" in d.warnings
def test_energy_mismatch():
    assert "energy_mismatch" in to_draft(ex(per_100g=n(energy_kcal=100, protein_g=10, carbs_g=60, fat_g=20))).warnings
def test_kj_only():
    assert to_draft(ex(per_100g=n(energy_kj=418.4))).per_100g.energy_kcal == pytest.approx(100)
def test_missing_values_never_filled():
    d = to_draft(ex(per_100g=n(energy_kcal=400))); assert d.per_100g.protein_g is None and d.per_100g.fat_g is None
def test_devanagari_ingredients_untouched():
    assert to_draft(ex(ingredients=[" मूंगफली ", "", "नमक"])).ingredients == ["मूंगफली", "नमक"]
def test_low_confidence_warning():
    assert "low_confidence" in to_draft(ex(confidence=0.5)).warnings
```

`ex(**kw)` and `n(**kw)` are helpers that build a `NutritionExtraction` or `NutrientsIn` with everything else `None` or empty.

- [x] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/unit/scans/test_normalize.py -v`. Expected: FAIL.
- [x] **Step 3: Implement** `to_draft`. Read the bounds from Plan 1's module constants; don't copy the numbers.
- [x] **Step 4: Run them to verify they pass.**
- [x] **Step 5: Commit** with message `feat(api): normalise extraction into a reviewed draft with plausibility warnings`.

---

### Task 4: Signed upload and `POST /v1/scans/label`

**Files:**
- Modify or create: `apps/api/app/integrations/storage.py`, `apps/api/app/features/scans/{service,router}.py`, `apps/api/tests/api/scans/test_scans.py`, `apps/api/tests/fakes/storage.py`
- Modify: `apps/api/app/core/config.py` (`storage_bucket`, `label_scans_per_day: int = 30`, `callmissed_extraction_model`) and `.env.example`

**Interfaces:**
- Consumes: `FakeLLM`, `LLMProvider.extract_label` (Task 2); `to_draft`, `ProductDraft` (Task 3); `ScanRecord`; `limit`.
- Produces:

```python
class StorageClient(Protocol):
    async def create_signed_upload(self, path: str, expires_in: int) -> str     # returns a URL the client PUTs to
    async def download(self, path: str) -> bytes                                # raises StorageNotFound
def sniff_image_mime(data: bytes) -> Literal["image/jpeg","image/png","image/webp"] | None
class UploadUrlOut(BaseModel): upload_url: str; path: str; expires_in: int
class LabelScanIn(BaseModel): path: str; barcode: str | None = None
class ScanDraftOut(BaseModel): scan_id: UUID; draft: ProductDraft; cached: bool; prompt_version: str
```

| Route | operation_id | Notes |
|---|---|---|
| `POST /v1/scans/upload-url` | `scans_create_upload_url` | Body `{ "ext": "jpg"\|"png"\|"webp" }` → `UploadUrlOut`, path `<account_id>/<uuid4>.<ext>` |
| `POST /v1/scans/label` | `scans_create_label` | `LabelScanIn` → `ScanDraftOut`, errors as in Global Constraints |

**Ruling on the spec:** spec §5 says `POST /scans/label` takes a multipart image. This plan uploads straight to Storage with a signed URL and posts the path instead. The API never proxies an 8 MB body, and the photo is already in the bucket for the 30-day retention.

The service flow for `scans_create_label`:
1. Ownership check on the path.
2. Download the image.
3. Size check, then MIME sniff.
4. Compute SHA-256.
5. If any `ScanRecord` with this hash has a stored draft, insert a new `ScanRecord` for this account (same draft, `cached = True`) and return it. No provider call and no limit hit.
6. Otherwise apply `limit("label_scans")`, call `extract_label` with the prompt file and `prompt_version = "extraction_v1"`, run `to_draft`, and store a `ScanRecord` with `image_path`, `image_sha256`, `analysis = {"draft": ..., "prompt_version": ...}` and the optional barcode.
7. Map the errors.

- [x] **Step 1: Write failing tests** (`FakeStorage` + `FakeLLM` via dependency overrides)

```python
async def test_upload_url_path_scoped_to_account(auth_client): r = ...; assert r.json()["path"].startswith(str(auth_client.account_id) + "/")
async def test_extracts_and_stores_draft(auth_client, fake_storage_jpeg, fake_llm_ok): r = ...; assert r.json()["cached"] is False and fake_llm_ok.calls == 1
async def test_same_image_is_cached_and_free(auth_client, other_client, fake_storage_jpeg, fake_llm_ok, tiny_scan_limit):
    await post_label(auth_client); r = await post_label(other_client)
    assert r.json()["cached"] is True and fake_llm_ok.calls == 1 and await scan_limit_used(other_client) == 0
async def test_too_large(auth_client, fake_storage_9mb): assert (await post_label(auth_client)).status_code == 413
async def test_not_an_image(auth_client, fake_storage_pdf): assert (await post_label(auth_client)).json()["error"]["code"] == "unsupported_image"
async def test_foreign_path_404(auth_client): assert (await post_label(auth_client, path="someone-else/x.jpg")).status_code == 404
async def test_rate_limited_after_30(auth_client, fake_storage_unique_jpegs, fake_llm_ok): ...   # 31st distinct image → 429 rate_limited_scans
async def test_provider_failure_returns_error_without_draft(auth_client, fake_storage_jpeg, fake_llm_raises_failed):
    r = await post_label(auth_client); assert r.status_code == 502 and "draft" not in r.json()
async def test_out_of_credits_is_503(auth_client, fake_storage_jpeg, fake_llm_unavailable): ...
```

- [x] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/api/scans -v`. Expected: FAIL.
- [x] **Step 3: Implement** the storage methods (Supabase Storage REST with the server secret key from settings), the sniffer, the service and the router.
- [x] **Step 4: Run them to verify they pass.**
- [x] **Step 5: Commit** with message `feat(api): label scan upload, extraction cache and rate limit`.

---

### Task 5: `POST /v1/products` from a confirmed draft or manual entry

**Files:**
- Modify: `apps/api/app/features/products/{schemas,service,router}.py`
- Create: `apps/api/tests/api/products/test_create_product.py`

**Interfaces:**
- Consumes: `ProductDraft` (Task 3), `ScanRecord`, `ProductRecord`, `ProductOut` and `record_to_product` (M1), `normalize_barcode` (M1).
- Produces:

```python
class ProductCreate(BaseModel):
    scan_id: UUID | None = None          # None = manual entry
    barcode: str | None = None
    name: str; brand: str | None = None
    category: Literal["general","beverage","water","cheese","fat"] = "general"
    per_100g: NutrientsOut; serving_size_g: float | None = None
    ingredients: list[str] = []; allergen_statement: str | None = None; may_contain_statement: str | None = None
    claims: list[str] = []; veg_mark: Literal["veg","non_veg"] | None = None
POST /v1/products  operation_id="products_create"  → 201 ProductOut (source="smartnutri")
```

Rules:
- The scan must belong to the account (`404 scan_not_found`).
- Any `per_100g` value outside the sanitized bounds → `422 implausible_value` with `details={"field": ...}`.
- The barcode is normalised. An existing non-rejected product with that barcode → `409 product_exists`, with `details={"product_id": ...}`.
- Stored fields:
  - `source` = `"label"` with `extraction_confidence` = the scan draft's confidence, or `"user"` with 1.0 for manual entry.
  - `verification_status = "pending"` and `created_by = account_id`.
  - `ingredients_text` = `", ".join(ingredients)`.
- After creation, the M1 `analyze_create` with `product_id` works unchanged.

- [x] **Step 1: Write failing tests**

```python
async def test_create_from_scan_keeps_extraction_confidence(auth_client, scan_with_draft_conf_0_6):
    r = await create(auth_client, scan_id=..., ingredients=["peanuts"]); rec = await get_product(r.json()["product_id"])
    assert rec.extraction_confidence == 0.6 and rec.source == "label" and rec.verification_status == "pending"
async def test_manual_entry_confidence_one(auth_client): ...
async def test_low_confidence_product_gives_unknown_for_allergic(auth_client, scan_with_draft_conf_0_6, peanut_allergic_member):
    pid = (await create(auth_client, scan_id=..., ingredients=["sugar"])).json()["product_id"]
    v = (await auth_client.post("/v1/analyze", json={"product_id": pid, "member_ids": [...]})).json()["verdicts"][0]
    assert v["status"] == "unknown"
async def test_implausible_rejected(auth_client): ...                    # sugars_g=250 → 422 implausible_value, details.field == "sugars_g"
async def test_duplicate_barcode_conflict(auth_client, seeded_product): ...
async def test_foreign_scan_404(auth_client, other_account_scan): ...
async def test_devanagari_ingredients_reach_engine(auth_client, peanut_allergic_member):
    pid = (await create(auth_client, ingredients=["मूंगफली", "नमक"])).json()["product_id"]
    assert (await analyze(auth_client, pid, peanut_allergic_member)).json()["verdicts"][0]["status"] == "avoid"
```

- [x] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/api/products/test_create_product.py -v`. Expected: FAIL.
- [x] **Step 3: Implement.**
- [x] **Step 4: Run them to verify they pass,** plus the full `uv run pytest -q`.
- [x] **Step 5: Commit** with message `feat(api): create products from confirmed label drafts or manual entry`.

---

### Task 6: Label-eval harness

> **As built (2026-11-03):** the harness is `apps/api/scripts/label_eval.py` + `label_eval_core.py`, with `tests/evals/labels/manifest.json`, `reports/` and a git-ignored `raw/`. There is no `--dry-run`: the command exits 2 without `--yes-spend` and refuses to run in CI. `.claude/skills/label-eval/SKILL.md` and `label_eval_core.GATES` are the source of truth; the file names below are the original design. The model decision goes in ADR 0016 (or a later ADR), not 0013, which was already taken.

**Files:**
- Create:
  - `apps/api/tests/evals/labels/{metrics.py,run_eval.py,manifest.csv,expected/.gitkeep,results/.gitkeep,README.md}`
  - `apps/api/tests/unit/evals/test_metrics.py`
- Verify: `.gitignore` already ignores `apps/api/tests/evals/labels/images/`. Configure pytest to skip `tests/evals/` by default (`--ignore=tests/evals` in `addopts`).

**Interfaces:**
- Consumes: `NutritionExtraction`, `to_draft` (Tasks 1, 3); `LLMProvider.extract_label` (Task 2); `from app.scoring import analyze, Product, Nutrients, Member` (Plan 1) for allergen recall.
- Produces:

```python
# metrics.py (pure)
NUMERIC_FIELDS = ("energy_kcal","protein_g","carbs_g","sugars_g","fat_g","sat_fat_g","fiber_g","salt_g","sodium_mg")
def numeric_accuracy(pred: dict, truth: dict) -> tuple[int, int]        # (correct, total) over fields where truth is not None; correct = within ±5% or ±0.5 g
def basis_correct(pred: str, truth: str) -> bool
def ingredient_f1(pred: list[str], truth: list[str]) -> float          # token-level after app.scoring.ingredients.normalize
def hallucinations(pred: dict, truth: dict) -> int                      # fields where truth is None but pred is not
def allergen_recall(pred_draft: ProductDraft, truth_draft: ProductDraft) -> tuple[int, int]   # engine-detected allergens on truth ⊆ on pred
def summarize(rows: list[dict]) -> dict                                 # overall metrics + gates (pass/fail) per label-eval skill
# run_eval.py CLI: --model ID --prompt extraction_vN [--limit N] [--dry-run]
#   --dry-run prints image count and an estimated cost; it makes NO network calls
#   writes results/<YYYY-MM-DD>_<model>_<prompt>.md (metrics table, 5 worst images, failure types)
```

The gates are copied from `.claude/skills/label-eval/SKILL.md`: numeric ≥ 90%, basis ≥ 98%, ingredient F1 ≥ 0.9, **allergen recall = 100% (hard)**, hallucinations ≤ 2%, p95 latency ≤ 8 s.

- [x] **Step 1: Write failing tests**

```python
def test_numeric_tolerance(): assert numeric_accuracy({"sugars_g": 10.4}, {"sugars_g": 10.0}) == (1, 1) and numeric_accuracy({"sugars_g": 12}, {"sugars_g": 10.0}) == (0, 1)
def test_null_truth_not_counted_but_hallucination(): assert numeric_accuracy({"fiber_g": 3}, {"fiber_g": None}) == (0, 0) and hallucinations({"fiber_g": 3}, {"fiber_g": None}) == 1
def test_ingredient_f1_normalized(): assert ingredient_f1(["Wheat Flour (Maida)", "Sugar"], ["wheat flour (maida)", "sugar"]) == 1.0
def test_allergen_recall_miss(): assert allergen_recall(draft(ingredients=["sugar"]), draft(ingredients=["peanuts", "sugar"])) == (0, 1)
def test_summary_fails_on_any_allergen_miss(): assert summarize([row(allergen=(0, 1)), *[row()] * 49])["gates"]["allergen_recall"] is False
```

- [x] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/unit/evals -v`. Expected: FAIL.
- [x] **Step 3: Implement** `metrics.py` and `run_eval.py`. Write `manifest.csv` with the header `id,brand,category,languages,conditions,source` only, and a `README.md` describing how to add an image and its `expected/<id>.json`.
- [x] **Step 4: Run them to verify they pass.** Then run `uv run python tests/evals/labels/run_eval.py --model x --prompt extraction_v1 --dry-run`. Expected: it prints 0 images and makes no calls.
- [x] **Step 5: Commit** with message `feat(evals): label extraction eval harness and metrics`.
- [ ] **Step 6 (needs the product owner):** collect at least 50 real label photos into the git-ignored `images/`, plus the committed `expected/*.json`.
  - Run every spec §3 candidate with `--limit 10`, then on the full set.
  - **Confirm the estimated cost with the user before each full run**, because it spends CallMissed credits.
  - Record the results files, set `CALLMISSED_EXTRACTION_MODEL` in `.env.example` to the winner (the best model passing all gates, preferring India-processed models on ties), and record the decision in ADR 0016 (or a new ADR; 0013 was taken).
  - If no model passes the allergen gate, M2 does **not** close. Record that in the ADR and iterate the prompt as `extraction_v2.md`.

---

### Task 7: Contract and i18n for M2

**Files:**
- Generated: `packages/api-contract/**` (`just contract`)
- Modify: `packages/i18n/messages/{en,hi,mr}.json` (`just i18n`)

**Interfaces:**
- Produces generated operations `scans_create_upload_url`, `scans_create_label` and `products_create`.
- i18n keys:
  - `label.title`, `label.take_photo`, `label.choose_file`, `label.drop_here`, `label.uploading`, `label.reading`, `label.retake`, `label.enter_manually`
  - `confirm.title`, `confirm.subtitle` ("Check every value against the pack. Leave blank if not printed."), `confirm.field.<NutrientsOut field>`, `confirm.serving_size`, `confirm.ingredients`, `confirm.add_ingredient`, `confirm.claims`, `confirm.veg_mark.{veg,non_veg,none}`, `confirm.save`
  - `warning.{per_100g_missing,energy_mismatch,salt_sodium_mismatch,low_confidence,implausible_value}`, `warning.derived_from_serving`
  - `error.{image_too_large,unsupported_image,scan_image_not_found,rate_limited_scans,extraction_failed,extraction_unavailable,implausible_value,product_exists,scan_not_found}`
  - `notfound.go_to_label` ("We don't know this product yet — photograph its label")

- [x] **Step 1:** Run `just contract`. Confirm the three operations exist.
- [x] **Step 2:** Add the keys in en, hi and mr. Flag hi and mr as machine drafts in the PR. Run `just i18n` and the i18n key-set check.
- [x] **Step 3:** Run `just test-api`. Expected: pass.
- [x] **Step 4: Commit** with message `chore(contract): regenerate clients for M2; i18n for label scan and confirm`.

---

> **Tasks 8 and 9 run in parallel** (`flutter-builder` ∥ `web-builder`), both starting from the commit that ends Task 7. Their files are disjoint.

### Task 8: Android label capture → confirm → verdict, and the not-found flow

**Files:**
- Create:
  - `apps/app/lib/features/scan/data/label_repository.dart`
  - `apps/app/lib/features/scan/presentation/{label_capture_screen,confirm_screen,draft_form,warning_banner}.dart`
  - tests under `apps/app/test/features/scan/`
- Modify:
  - `apps/app/lib/core/router/app_router.dart` (`/scan/label?barcode=`, `/scan/confirm`)
  - M1 `result_screen.dart`: a 404 now navigates to `/scan/label?barcode=<code>` (F15)

**Interfaces:**
- Consumes: the generated `scans_create_upload_url`, `scans_create_label`, `products_create` and `analyze_create` (M1), plus the M1 `ResultScreen`.
- Produces:

```dart
class LabelRepository {
  Future<ScanDraftOut> scanLabel(XFile photo, {String? barcode});      // compress → upload-url → PUT (dio, no auth header) → scans_create_label
  Future<ProductOut> saveDraft(ProductCreate body);
}
Future<Uint8List> compressForUpload(Uint8List bytes);                  // JPEG, longest side ≤ 2000 px, ≤ 8 MB
class DraftForm extends StatefulWidget { const DraftForm({required ProductDraft draft, required void Function(ProductCreate) onSave}); }
```

Behaviour:
- The capture screen uses `image_picker` with camera or gallery.
- Errors map to i18n keys, and every error state offers **Retake** and **Enter manually** (an empty `DraftForm`).
- The confirm screen shows `warning.*` banners. Fields named in `implausible_value:*` are highlighted. Blank numbers stay blank (`null`), never `0`.
- Saving calls `products_create`, then `analyze_create` (product_id), then navigates to the M1 result view.

- [x] **Step 1: Write failing widget tests**

```dart
testWidgets('draft blanks stay blank and are sent as null', ...);                 // fiber null → field empty → ProductCreate.perHundredG.fiberG == null
testWidgets('implausible field highlighted and warning shown', ...);
testWidgets('per_100g_missing warning shown for per-serving label without serving size', ...);
testWidgets('extraction_failed shows retake + enter manually; no form prefilled', ...);
testWidgets('404 on barcode result navigates to label capture with barcode', ...);
testWidgets('save → analyze → result screen shows verdict', ...);                 // fake repositories returning fixture JSON
test('compressForUpload keeps output ≤ 8 MB', ...);
```

- [x] **Step 2: Run them to verify they fail.** Run: `cd apps/app && flutter test test/features/scan`. Expected: FAIL.
- [x] **Step 3: Implement.**
- [ ] **Step 4: Run** `flutter analyze && flutter test`. Then do a manual emulator check with a real pack: photo → confirm → verdict, and an unknown barcode → label flow.
- [x] **Step 5: Commit** with message `feat(app): label photo, confirm screen and not-found flow (M2)`.

---

### Task 9: Web label upload → confirm → verdict, and the not-found flow

**Files:**
- Create:
  - `apps/web/src/features/scan/api/{useUploadLabel,useSaveDraft}.ts`
  - `apps/web/src/features/scan/lib/{resizeImage.ts,draftSchema.ts}`
  - `apps/web/src/features/scan/components/{LabelUpload,DraftForm,WarningBanner}.tsx`
  - `apps/web/src/app/[locale]/(app)/scan/label/page.tsx`
  - `apps/web/src/app/[locale]/(app)/scan/confirm/[scanId]/page.tsx`
  - tests `apps/web/tests/features/scan/*.test.tsx`, `apps/web/e2e/scan-label.spec.ts`
- Modify: the M1 `ResultView` (404 → `router.replace` to `/[locale]/scan/label?barcode=`)

**Interfaces:**
- Consumes: the generated `scans_create_upload_url`, `scans_create_label`, `products_create` and `analyze_create`, plus the M1 result route.
- Produces:

```ts
export async function resizeImage(file: File, maxSide = 2000): Promise<Blob>       // canvas → image/jpeg, ≤ 8 MB
export const draftSchema: z.ZodType<ProductCreate>                                  // nullable numbers: "" → null, never 0
export function useUploadLabel(): UseMutationResult<ScanDraftOut, ApiError, { file: File; barcode?: string }>
export function DraftForm(props: { draft: ProductDraft | null; onSave(v: ProductCreate): void }): JSX.Element
```

Behaviour:
- `LabelUpload` has `<input type="file" accept="image/*" capture="environment">` plus drag and drop on desktop.
- Upload flow: resize, signed-URL `PUT` (fetch, no auth header), `scans_create_label`, then navigate to the confirm route.
- The error states, warnings, highlighting, blanks-stay-null rule and "Enter manually" match Android Task 8 exactly.

- [x] **Step 1: Write failing tests**

```ts
it("empty numeric inputs parse to null, not 0", () => { expect(draftSchema.parse(formWith({ fiber_g: "" })).per_100g.fiber_g).toBeNull(); });
it("highlights implausible field and shows warning", ...);
it("extraction_failed shows retake and enter-manually; form empty", ...);
it("resizeImage output ≤ 8 MB and image/jpeg", ...);
it("404 on result redirects to label page with barcode", ...);
// e2e (API stubbed with fixture JSON): upload sample label → confirm (edit sugars) → save → verdict card visible
```

- [x] **Step 2: Run them to verify they fail.** Run: `pnpm --filter @smartnutri/web test`. Expected: FAIL.
- [x] **Step 3: Implement.**
- [x] **Step 4: Run** the web lint, typecheck, test and e2e. Expected: green.
- [x] **Step 5: Commit** with message `feat(web): label upload, confirm form and not-found flow (M2)`.

---

### Task 10: Milestone gate

**Files:**
- Modify: `docs/FEATURE_PARITY.md` (F4 and F15 → ✅ on all three)

- [ ] **Step 1:** Run `just test` and `just lint`. Expected: all pass.
- [ ] **Step 2:** Run the `nutrition-safety-reviewer` agent over the M2 range. Its focus: the prompt never asks the model to guess; no invented values anywhere; confidence handling (user edits never raise it); the confirm screens on both clients; the Devanagari path; the cache and the rate limit. Fix blockers and re-run.
- [ ] **Step 3:** Confirm the Task 6 Step 6 eval ran, the model is chosen and ADR 0016 is written. If not, M2 stays open; record that in `docs/FEATURE_PARITY.md`.
- [ ] **Step 4:** Do a manual parity check on 3 real packs, including one Hindi or bilingual label and one per-serving-only label. Android and web must give identical drafts (same cached scan) and identical verdicts.
- [ ] **Step 5: Commit** with message `docs: M2 parity status`.

Note: the ADR for this milestone is `docs/adr/0016-label-scan-pipeline.md` (this plan called it ADR 0013, but 0013 was already taken). The model choice in it is still pending the eval.
