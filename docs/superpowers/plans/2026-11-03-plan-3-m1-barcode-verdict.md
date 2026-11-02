# Plan 3 (M1): Barcode → Verdict Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A signed-in user scans a packaged-food barcode on **Android or web** and sees a verdict card (red/amber/green/grey, grade, one-line reason) for their primary member. The API looks the barcode up in our `products` table, then Open Food Facts (OFF) v3. A public, Google-indexable page `/[locale]/p/[barcode]` shows **generic** product facts only.

**Architecture:**
- **API first.** Add the OFF client, an OFF → scoring `Product` mapper and a barcode lookup service. Then add three routes:
  - `GET /v1/products/barcode/{code}`
  - `GET /v1/products/{barcode}/public`
  - `POST /v1/analyze`
- Then `just contract` regenerates both clients, and shared i18n keys and fixture responses are added.
- Then the **Android** and **web** tasks run **in parallel**. Their files are disjoint (`apps/app` vs `apps/web`), and both consume the regenerated clients.
- Verdicts come only from `app.scoring.analyze()`. Clients render `AnalysisResult.to_dict()` as returned.

**Tech Stack:** FastAPI, SQLAlchemy 2 async, httpx, pytest · Flutter (Riverpod, go_router, `mobile_scanner`, `smartnutri_api`) · Next.js 16 (App Router, TanStack Query, next-intl, `@zxing/browser`, Vitest, Playwright).

**Spec:** `docs/superpowers/specs/2026-11-02-smartnutri-v1-design.md` (F3, F13 basic, F11 attribution, §4, §5), `docs/FEATURE_PARITY.md`. **Depends on:** Plan 1 (rules engine) and Plan 2 (foundation: app factory, auth, DB baseline with all §4 tables and RLS, contract, i18n and token pipelines, Android and web shells).

## Global Constraints

- **Naming contract (Plan 2):**
  - `app.main:create_app()`, `app.core.config.get_settings()`
  - `app.core.security.current_account` → `AccountContext(account_id: UUID, email: str | None)`
  - `app.db.session.get_session` (AsyncSession)
  - `app.core.errors.ApiError(code, status, message_key)` with error envelope `{"error": {"code", "message_key", "details"}}`
  - `app.core.ratelimit.limit(bucket: str)`
  - `app.integrations.openfoodfacts.OffClient`
  - Routers at `app/features/<f>/router.py`, mounted at `/v1/<f>`
  - `operation_id` = `<feature>_<action>`
  - ORM classes live in `app/features/<f>/models.py`. This plan calls them `ProductRecord`, `OffCacheRecord`, `MemberRecord` and `ScanRecord`. If Plan 2 named them differently, use Plan 2's names; the behaviour here is binding.
- **Verdicts come only from `from app.scoring import analyze`.** Neither client computes, recolours or reorders a verdict. `unknown` is grey, never green.
- **OFF rules:**
  - Send a `User-Agent` from `Settings.off_user_agent` (env `OFF_USER_AGENT`) on every call.
  - Use the v3 endpoint `https://world.openfoodfacts.org/api/v3/product/{barcode}`.
  - OFF payloads are stored **only** in `off_product_cache`, never copied into `products` (ODbL).
  - Every response or screen that shows OFF data carries the attribution key `attribution.off`, which renders as "Data from Open Food Facts (ODbL)".
- **Lookup order:**
  1. `products` (by barcode, `verification_status != 'rejected'`)
  2. A fresh `off_product_cache` row (`Settings.off_cache_ttl_hours`, default 168)
  3. The OFF API, which refreshes the cache
  4. Not found.
  If OFF fails and a stale cache row exists, use the stale row.
- **Barcode format:** strip spaces and hyphens, keep leading zeros, accept only 8, 12, 13 or 14 digits. Anything else → `422 invalid_barcode`.
- **Never invent values.** A missing OFF nutrient is `None`. Do not derive per-100 g values from per-serving values in M1.
- **Public endpoint and page:** no auth, never member data or a personal verdict, `Cache-Control: public, max-age=3600`, per-IP limit bucket `public`.
- **Strings:** all strings go in `packages/i18n/messages/{en,hi,mr}.json` (then `just i18n`). Reason codes map to `reason.<code>` (web) and `reason_<code>` (ARB, generated). Colours come only from `packages/design-tokens`.
- **Disclaimer:** "Information, not medical advice" (`common.disclaimer`) is on every result screen.
- **Commit scopes:** `api`, `contract`, `i18n`, `fixtures`, `app`, `web`. Each commit ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **OFF product with only per-serving nutriments** (no `*_100g` keys): the per-100 g values stay `None`, so the verdict is `unknown` and not scored. Owned by Task 2.
2. **OFF energy only in kJ** (`energy-kj_100g` or `energy_100g`, but no `energy-kcal_100g`): convert to kcal by dividing by 4.184. Owned by Task 2.
3. **Barcode input variants:** `" 8901 0632 0108 9 "`, a 12-digit UPC with a leading zero, and `"abc123"`. The first two are normalised; `"abc123"` is rejected with 422 on API, Android and web. Owned by Tasks 1, 4, 7 and 8.
4. **OFF down with no cache:** returns `503 off_unavailable`, and the clients show "try again", not "not found". Owned by Tasks 3, 7 and 8.
5. **Member without `birth_year`:** age is `None`, child and infant rules are skipped, and there is no crash. Owned by Task 5.

## File Map

```
apps/api/app/integrations/openfoodfacts.py            # Task 1  OffClient
apps/api/app/features/products/off_mapping.py          # Task 2  OFF payload → scoring Product + ProductInfo
apps/api/app/features/products/{service,schemas,router}.py   # Tasks 3-4
apps/api/app/features/members/service.py               # Task 5  get_or_create_primary, to_scoring_member
apps/api/app/features/analyze/{schemas,service,router}.py    # Task 5
apps/api/scripts/export_fixture_responses.py           # Task 5  golden API responses for clients
apps/api/tests/fixtures/off/*.json                      # Tasks 1-2  hand-made OFF payloads
apps/api/tests/{unit,api}/...                           # per task
packages/api-contract/{openapi.json,dart,ts}            # Task 6  (generated)
packages/i18n/messages/{en,hi,mr}.json                  # Task 6
packages/design-tokens/tokens.json                      # Task 6  (verdict + grade tokens, if missing)
packages/test-fixtures/responses/{analyze,public}/*.json   # Task 5  (generated by script)
apps/app/lib/features/{scan,product,analysis}/...       # Task 7  (Android)
apps/web/src/features/{scan,product,analysis}/...       # Task 8  (web, app pages)
apps/web/src/app/[locale]/(public)/p/[barcode]/page.tsx # Task 9  (web, public page)
docs/FEATURE_PARITY.md                                  # Task 10
```

---

### Task 1: OFF client

**Files:**
- Create: `apps/api/app/integrations/openfoodfacts.py`, `apps/api/tests/unit/integrations/test_openfoodfacts.py`, `apps/api/tests/fixtures/off/8901063201089.json` (a hand-made minimal v3 "success" payload, for a biscuit)
- Modify: `apps/api/app/core/config.py` (add `off_user_agent: str`, `off_base_url: str = "https://world.openfoodfacts.org"`, `off_cache_ttl_hours: int = 168`, `off_data_confidence: float = 0.9`). Keep `apps/api/.env.example` in sync.

**Interfaces:**
- Produces:

```python
def normalize_barcode(raw: str) -> str            # raises InvalidBarcode; returns digits only
class InvalidBarcode(ValueError): ...
class OffUnavailable(Exception): ...               # network error, timeout, 5xx, or malformed body
class OffClient:
    def __init__(self, http: httpx.AsyncClient, *, base_url: str, user_agent: str) -> None
    async def get_product(self, barcode: str) -> dict | None   # v3 "product" object, or None when OFF says not found
```

Use a 10 s timeout, no retries in the client (the service decides), and request `fields` limited to: `code,product_name,brands,image_front_url,categories_tags,nutriments,serving_quantity,ingredients_text,allergens_tags,traces_tags,labels_tags`.

- [ ] **Step 1: Write failing tests**

```python
@pytest.mark.parametrize("raw,clean", [(" 8901 0632 0108 9 ", "8901063201089"), ("036000291452", "036000291452"), ("12345670", "12345670")])
def test_normalize_barcode_accepts(raw, clean): assert normalize_barcode(raw) == clean

@pytest.mark.parametrize("raw", ["abc123", "1234567", "123456789012345", ""])
def test_normalize_barcode_rejects(raw):
    with pytest.raises(InvalidBarcode): normalize_barcode(raw)

async def test_sends_user_agent_and_v3_path(off_payload):
    seen = {}
    def handler(req): seen["ua"] = req.headers["user-agent"]; seen["path"] = req.url.path; return httpx.Response(200, json=off_payload)
    client = OffClient(httpx.AsyncClient(transport=httpx.MockTransport(handler)), base_url="https://x", user_agent="SmartNutri/0.1 (contact: t@example.com)")
    assert (await client.get_product("8901063201089"))["code"] == "8901063201089"
    assert seen == {"ua": "SmartNutri/0.1 (contact: t@example.com)", "path": "/api/v3/product/8901063201089"}

async def test_not_found_returns_none():   # OFF v3: HTTP 404 with {"status": "failure", "errors": [...]}
    ...  # MockTransport returns 404 + {"status": "failure"}; assert result is None

async def test_server_error_raises_unavailable():
    ...  # MockTransport returns 503; assert pytest.raises(OffUnavailable)

async def test_timeout_raises_unavailable():
    ...  # handler raises httpx.ReadTimeout; assert pytest.raises(OffUnavailable)
```

- [ ] **Step 2: Run them to verify they fail.** Run: `cd apps/api && uv run pytest tests/unit/integrations/test_openfoodfacts.py -v`. Expected: FAIL (`ModuleNotFoundError`).
- [ ] **Step 3: Implement** to the Interfaces block. Verify the v3 not-found shape against https://openfoodfacts.github.io/openfoodfacts-server/api/ and record the URL in the module docstring.
- [ ] **Step 4: Run them to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(api): Open Food Facts v3 client with barcode normalisation`.

---

### Task 2: OFF payload → scoring `Product`

**Files:**
- Create: `apps/api/app/features/products/off_mapping.py`, `apps/api/tests/unit/products/test_off_mapping.py`, plus fixture payloads `apps/api/tests/fixtures/off/{per_serving_only,kj_only,beverage,no_ingredients}.json`

**Interfaces:**
- Consumes: `from app.scoring import Product, Nutrients, Category`.
- Produces:

```python
@dataclass(frozen=True, slots=True)
class ProductInfo:
    barcode: str; name: str | None; brand: str | None; image_url: str | None
def off_to_product(payload: dict, *, confidence: float) -> Product
def off_to_info(payload: dict) -> ProductInfo
def split_ingredients(text: str | None) -> tuple[str, ...]   # split on commas/semicolons outside parentheses; strip; drop empties
```

Mapping rules (pinned):

| scoring field | OFF source |
|---|---|
| `energy_kcal` | `nutriments["energy-kcal_100g"]`, else `energy-kj_100g / 4.184`, else `energy_100g / 4.184` (OFF `energy_100g` is kJ) |
| `protein_g`, `carbs_g`, `sugars_g`, `fat_g`, `sat_fat_g`, `fiber_g`, `salt_g` | `proteins_100g`, `carbohydrates_100g`, `sugars_100g`, `fat_100g`, `saturated-fat_100g`, `fiber_100g`, `salt_100g` |
| `sodium_mg` | `sodium_100g × 1000` |
| `fvl_percent` | `fruits-vegetables-legumes-estimate-from-ingredients_100g` |
| `category` | `categories_tags` has `en:waters` → WATER; else `en:beverages` → BEVERAGE; else `en:cheeses` → CHEESE; else `en:fats` → FAT; else GENERAL |
| `serving_size_g` | `serving_quantity` (float), else None |
| `ingredients` | `split_ingredients(ingredients_text)` |
| `allergen_statement` | `"Contains: " + ", ".join(tag.split(":")[-1])` over `allergens_tags`, else None |
| `may_contain_statement` | the same, built from `traces_tags` with the prefix `"May contain: "` |
| `claims` | `labels_tags` mapped: `en:no-added-sugar`→"no added sugar", `en:sugar-free`→"sugar free", `en:low-sugar`→"low sugar", `en:low-fat`→"low fat", `en:low-salt`→"low salt", `en:high-protein`→"high protein", `en:source-of-protein`→"source of protein"; others dropped |
| `veg_mark` | None (OFF has no reliable FSSAI dot) |
| `extraction_confidence` | the `confidence` argument (`Settings.off_data_confidence`) |
| `name` | `product_name` or `""` |

Missing or non-numeric values are `None`. **Never** fall back to per-serving values.

- [ ] **Step 1: Write failing tests**

```python
def test_maps_biscuit(off_biscuit):
    p = off_to_product(off_biscuit, confidence=0.9)
    assert p.per_100g.sugars_g == 2.0 and p.per_100g.energy_kcal == 450 and p.serving_size_g == 25
    assert "maltodextrin" in p.ingredients and p.claims == ("sugar free",) and p.extraction_confidence == 0.9

def test_per_serving_only_stays_none(off_per_serving_only):
    n = off_to_product(off_per_serving_only, confidence=0.9).per_100g
    assert n.sugars_g is None and n.energy_kcal is None

def test_energy_from_kj(off_kj_only):
    assert off_to_product(off_kj_only, confidence=0.9).per_100g.energy_kcal == pytest.approx(1882.8 / 4.184)

def test_beverage_category_and_sodium(off_beverage):
    p = off_to_product(off_beverage, confidence=0.9)
    assert p.category == Category.BEVERAGE and p.per_100g.sodium_mg == pytest.approx(10.0)

def test_split_ingredients_respects_parentheses():
    assert split_ingredients("wheat flour (maida), sugar, raising agent (ins 500(ii), ins 503), salt") == (
        "wheat flour (maida)", "sugar", "raising agent (ins 500(ii), ins 503)", "salt")

def test_allergen_and_trace_statements(off_biscuit):
    p = off_to_product(off_biscuit, confidence=0.9)
    assert p.allergen_statement == "Contains: gluten, milk" and p.may_contain_statement == "May contain: soybeans"

def test_no_ingredients(off_no_ingredients):
    assert off_to_product(off_no_ingredients, confidence=0.9).ingredients == ()
```

The fixture payloads must contain exactly the values these assertions imply. The biscuit uses the Plan 1 `sf_biscuit` nutrition, `allergens_tags=["en:gluten","en:milk"]` and `traces_tags=["en:soybeans"]`.

- [ ] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/unit/products/test_off_mapping.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** to the table. `split_ingredients` is a depth-counting scanner, not a regex.
- [ ] **Step 4: Run them to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(api): map Open Food Facts payloads to scoring products`.

---

### Task 3: Barcode lookup service

**Files:**
- Create: `apps/api/app/features/products/service.py`, `apps/api/tests/api/products/test_lookup_service.py`

**Interfaces:**
- Consumes: `OffClient`, `normalize_barcode`, `OffUnavailable` (Task 1); `off_to_product`, `off_to_info`, `ProductInfo` (Task 2); `ProductRecord`, `OffCacheRecord`; `get_settings()`.
- Produces:

```python
@dataclass(frozen=True, slots=True)
class ProductLookup:
    source: Literal["smartnutri", "openfoodfacts"]
    product_id: UUID | None          # None for OFF products
    info: ProductInfo
    product: scoring.Product
    attribution: str | None          # "attribution.off" for OFF, else None
async def lookup_by_barcode(session: AsyncSession, off: OffClient, barcode: str) -> ProductLookup | None
def record_to_product(record: ProductRecord) -> scoring.Product      # also used by Task 5 and M2
def record_to_info(record: ProductRecord) -> ProductInfo
```

Apply the lookup order and stale-cache fallback from Global Constraints. When the cache is stale and OFF returns `None`, delete the cache row. When OFF raises and there is no cache row, re-raise `OffUnavailable`.

- [ ] **Step 1: Write failing tests** (test DB from Plan 2's `tests/api` fixtures, plus a `FakeOff` that counts calls)

```python
async def test_own_product_wins_without_off_call(session, fake_off, seeded_product): ...   # source == "smartnutri", fake_off.calls == 0
async def test_rejected_own_product_falls_through_to_off(session, fake_off): ...           # verification_status="rejected" → OFF used
async def test_fresh_cache_hit_no_off_call(session, fake_off): ...                         # cache fetched_at=now-1h → calls == 0, source "openfoodfacts"
async def test_stale_cache_refetches_and_updates(session, fake_off): ...                   # fetched_at=now-200h → calls == 1, row.fetched_at updated
async def test_off_down_uses_stale_cache(session, failing_off): ...                        # returns the stale data, no exception
async def test_off_down_no_cache_raises(session, failing_off):
    with pytest.raises(OffUnavailable): await lookup_by_barcode(session, failing_off, "8901063201089")
async def test_not_found_everywhere_returns_none(session, fake_off_empty): ...
async def test_off_data_never_written_to_products(session, fake_off): ...                  # products table row count unchanged
```

- [ ] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/api/products/test_lookup_service.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `service.py`.
- [ ] **Step 4: Run them to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(api): barcode lookup across products, OFF cache and OFF`.

---

### Task 4: Product routes (authenticated and public)

**Files:**
- Create or modify: `apps/api/app/features/products/{schemas,router}.py`, `apps/api/tests/api/products/test_product_routes.py`
- Modify: `apps/api/app/main.py` (mount the router if Plan 2 doesn't auto-discover routers), `apps/api/app/integrations/openfoodfacts.py` (a `get_off_client()` dependency built from settings and a shared `httpx.AsyncClient`)

**Interfaces:**
- Consumes: `lookup_by_barcode`, `ProductLookup` (Task 3); `from app.scoring import analyze`.
- Produces (both routes are under `/v1/products`):

| Route | operation_id | Auth | Success | Errors |
|---|---|---|---|---|
| `GET /barcode/{code}` | `products_get_by_barcode` | yes | `200 ProductOut` | `422 invalid_barcode`, `404 product_not_found`, `503 off_unavailable` |
| `GET /{barcode}/public?language=en\|hi\|mr` | `products_get_public` | **no** | `200 PublicProductOut` + `Cache-Control: public, max-age=3600` | same as above, plus `429 rate_limited` (bucket `public`) |

```python
class NutrientsOut(BaseModel): energy_kcal: float|None; protein_g: float|None; carbs_g: float|None; sugars_g: float|None; fat_g: float|None; sat_fat_g: float|None; fiber_g: float|None; salt_g: float|None; sodium_mg: float|None
class ProductOut(BaseModel):
    source: Literal["smartnutri","openfoodfacts"]; product_id: UUID|None; barcode: str|None
    name: str|None; brand: str|None; image_url: str|None; category: str
    per_100g: NutrientsOut; serving_size_g: float|None; ingredients: list[str]; claims: list[str]
    attribution: str|None
class PublicProductOut(BaseModel):
    product: ProductOut
    report: dict          # analyze(product, members=[]).to_dict()["report"]; no "verdicts" key anywhere
    score_label: Literal["calculated_by_smartnutri"]
```

`PublicProductOut` is built from `analyze(product, [])`, so the report is the engine's product-level report. It contains no member data.

- [ ] **Step 1: Write failing tests**

```python
async def test_barcode_requires_auth(client): assert (await client.get("/v1/products/barcode/8901063201089")).status_code == 401
async def test_barcode_found_from_off(auth_client, fake_off): r = await auth_client.get(".../barcode/8901063201089"); assert r.json()["source"] == "openfoodfacts" and r.json()["attribution"] == "attribution.off"
async def test_barcode_invalid(auth_client): assert (await auth_client.get("/v1/products/barcode/abc123")).json()["error"]["code"] == "invalid_barcode"
async def test_barcode_not_found(auth_client, fake_off_empty): assert (await auth_client.get(".../barcode/8901063201089")).status_code == 404
async def test_off_unavailable_is_503(auth_client, failing_off): assert (await ...).json()["error"]["code"] == "off_unavailable"
async def test_public_needs_no_auth_and_has_no_verdicts(client, fake_off):
    r = await client.get("/v1/products/8901063201089/public")
    assert r.status_code == 200 and r.headers["cache-control"] == "public, max-age=3600"
    assert "verdicts" not in r.text and r.json()["score_label"] == "calculated_by_smartnutri"
    assert r.json()["report"]["nutriscore"]["grade"] == "D"
async def test_public_rate_limited(client, fake_off, tiny_public_limit): ...   # (limit+1)-th request → 429 rate_limited
```

- [ ] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/api/products/test_product_routes.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the schemas, the router and the dependencies. Override `get_off_client` in tests via `app.dependency_overrides`.
- [ ] **Step 4: Run them to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(api): barcode and public product routes`.

---

### Task 5: `POST /v1/analyze`, primary member and fixture responses

**Files:**
- Create: `apps/api/app/features/members/service.py` (if Plan 2 has no members service yet), `apps/api/app/features/analyze/{schemas,service,router}.py`, `apps/api/scripts/export_fixture_responses.py`, `apps/api/tests/api/analyze/test_analyze.py`, `apps/api/tests/api/analyze/test_shared_fixtures.py`
- Generated: `packages/test-fixtures/responses/analyze/<product>.json`, `packages/test-fixtures/responses/public/<product>.json`

**Interfaces:**
- Consumes: `lookup_by_barcode`, `record_to_product` (Task 3); `from app.scoring import analyze, Member, Diet`; `MemberRecord`, `ScanRecord`.
- Produces:

```python
# members/service.py (M3 extends this file with CRUD)
async def get_or_create_primary(session, account_id: UUID) -> MemberRecord   # relation="self", is_primary=True, diet="non_veg", empty lists
def to_scoring_member(record: MemberRecord, *, today: date) -> scoring.Member  # age = today.year - birth_year, or None

# analyze/schemas.py
class AnalyzeRequest(BaseModel):
    product_id: UUID | None = None
    barcode: str | None = None
    member_ids: list[UUID] | None = None
    language: Literal["en","hi","mr"] = "en"
    # validator: exactly one of product_id / barcode, else ApiError("invalid_product_ref", 422)
class ReasonOut(BaseModel): code: str; severity: Literal["ok","caution","unknown","avoid"]; params: dict[str, Any]
class VerdictOut(BaseModel): member_id: UUID; member_name: str; status: Literal["ok","caution","unknown","avoid"]; reasons: list[ReasonOut]
class AnalyzeOut(BaseModel):
    scan_id: UUID; product: ProductOut; report: dict; verdicts: list[VerdictOut]
    explanation: str | None = None       # filled from M3 (F7); always null in M1
    tips: list[str] = []
# analyze/router.py
POST /v1/analyze  operation_id="analyze_create"  auth required  rate limit bucket "analyze"
```

**Ruling on the spec:** spec §5 lists `{product_id, member_ids?, language}`. OFF products have no `product_id`, so `barcode` is accepted as the alternative product reference. This changes no client contract beyond the extra field.

Service behaviour:
1. Resolve the product (by id → `record_to_product`, or by barcode → `lookup_by_barcode`). A missing product → `404 product_not_found`.
2. Members come from `member_ids`, scoped to the account. Any foreign or unknown id → `404 member_not_found`. With no `member_ids`, use `[get_or_create_primary(...)]`.
3. Run `analyze(product, members)`. Map the result to `VerdictOut` in member order, attaching `member_name`.
4. Insert a `ScanRecord`: `account_id`, `product_id` (nullable), `analysis = result.to_dict() | {"barcode": barcode}`.
5. Return `AnalyzeOut`.

`scripts/export_fixture_responses.py` loads `packages/test-fixtures/{products,members}`, calls the **service** function directly (with in-memory records, no DB) and writes deterministic JSON. It uses sorted keys, fixed UUIDs derived with `uuid5(NAMESPACE_URL, name)`, and `scan_id` = uuid5 of the product name. It also writes the public response for every product.

- [ ] **Step 1: Write failing tests**

```python
async def test_requires_exactly_one_product_ref(auth_client):
    r = await auth_client.post("/v1/analyze", json={"language": "en"}); assert r.json()["error"]["code"] == "invalid_product_ref"
async def test_primary_member_created_once(auth_client, seeded_product):
    await auth_client.post("/v1/analyze", json={"product_id": str(seeded_product.id)})
    await auth_client.post("/v1/analyze", json={"product_id": str(seeded_product.id)})
    assert await count_members(auth_client.account_id) == 1
async def test_foreign_member_is_404(auth_client, other_account_member, seeded_product): ...
async def test_member_without_birth_year_does_not_crash(auth_client, member_no_birth_year, cola_product): ...   # 200, no child_* codes
async def test_scan_row_written(auth_client, seeded_product): ...                                             # 1 scan for this account
async def test_off_barcode_analyze(auth_client, fake_off): ...                                                # barcode path, product.source == "openfoodfacts"

# test_shared_fixtures.py: the source of truth for both clients
@pytest.mark.parametrize("product,member", all_expected_pairs())   # from packages/test-fixtures/expected/<product>.<member>.json
async def test_fixture_verdicts(product, member, auth_client, load_fixture_product, load_fixture_member):
    r = await auth_client.post("/v1/analyze", json={"product_id": ..., "member_ids": [...]})
    v = r.json()["verdicts"][0]; exp = read_expected(product, member)
    assert v["status"] == exp["status"] and [x["code"] for x in v["reasons"]] == exp["reason_codes"]
def test_fixture_responses_are_current(tmp_path):
    run_export(tmp_path)   # scripts/export_fixture_responses.py into tmp
    assert dir_equal(tmp_path, FIXTURES / "responses")     # CI fails if stale; fix with the script, never by hand
```

- [ ] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/api/analyze -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the members helpers, the analyze schemas, service and router, and the export script.
- [ ] **Step 4: Generate fixture responses and run the tests.** Run: `uv run python scripts/export_fixture_responses.py && uv run pytest tests/api/analyze -v`. Expected: all pass.
- [ ] **Step 5: Commit** with message `feat(api): analyze endpoint with primary member and shared fixture responses`. Include `packages/test-fixtures/responses/`.

---

### Task 6: Contract, i18n and tokens for M1

**Files:**
- Generated: `packages/api-contract/{openapi.json,dart/,ts/}` (via `just contract`)
- Modify: `packages/i18n/messages/{en,hi,mr}.json`, then `just i18n`. Modify `packages/design-tokens/tokens.json` only if the verdict and grade tokens are missing, then `just tokens`.

**Interfaces:**
- Produces generated client operations: `products_get_by_barcode`, `products_get_public`, `analyze_create`.
- i18n keys (identical key set in all three files):
  - `scan.title`, `scan.manual_entry`, `scan.manual_placeholder`, `scan.submit`, `scan.camera_denied`, `scan.not_found`, `scan.retry`, `scan.off_unavailable`
  - `result.title`, `result.grade`, `result.calculated_by_smartnutri`, `result.high_in.{sugar,fat,sat_fat,salt}`
  - `status.{ok,caution,unknown,avoid}`; `status.unknown_hint` ("Label unclear")
  - `reason.<code>` for every Plan 1 reason code: `allergen_contains, allergen_may_contain, allergen_unknown, diet_violation, diet_unknown, sugar_high, sugar_moderate, misleading_sugar_claim, hidden_sugars, carbs_per_serving_high, salt_high, salt_moderate, sodium_additives, energy_dense, nutriscore_low, good_protein_density, child_sugar_high, child_sugar_moderate, child_caffeine, infant_added_sugar, infant_added_salt, infant_honey, nutrient_missing`. Use ICU params named after the reason's `params` keys (e.g. `{allergen}`, `{diet}`, `{claim}`, `{ingredients}`, `{pct}`, `{grade}`, `{nutrient}`).
  - `allergen.<key>` for the 11 canonical allergens; `diet.<key>` for the 5 diets; `nutrient.<field>` for each `NutrientsOut` field
  - `attribution.off`, `common.disclaimer`, `error.invalid_barcode`, `error.product_not_found`, `error.off_unavailable`, `error.rate_limited`
- Tokens: `color.verdict.{ok,caution,unknown,avoid}` (unknown is neutral grey) and `color.grade.{A,B,C,D,E}`.

- [ ] **Step 1:** Run `just contract`. Confirm the three operation ids appear in `packages/api-contract/openapi.json`, and that `git diff packages/api-contract` shows only generated changes.
- [ ] **Step 2:** Add the i18n keys. Draft the hi and mr text, and list them in the PR description as **"machine draft, needs native review"**. Run `just i18n`. Run the i18n check (`pnpm --filter @smartnutri/i18n check`). Expected: key sets identical.
- [ ] **Step 3:** Add any missing tokens, then run `just tokens`.
- [ ] **Step 4:** Run `just test-api`. Expected: pass, including the contract-drift check if Plan 2 added it.
- [ ] **Step 5: Commit** with message `chore(contract): regenerate clients for M1; i18n and tokens for scan and result`.

---

> **Tasks 7 and 8 run in parallel** (`flutter-builder` ∥ `web-builder`). Both start from the commit that ends Task 6. Their files are disjoint. Task 9 is web-only and can run in parallel with Task 7.

### Task 7: Android scan → result

**Files:**
- Create:
  - `apps/app/lib/features/scan/presentation/{scan_screen,manual_barcode_field}.dart`
  - `apps/app/lib/features/product/data/product_repository.dart`
  - `apps/app/lib/features/analysis/data/analysis_repository.dart`
  - `apps/app/lib/features/analysis/presentation/{result_screen,verdict_card,reason_line}.dart`
  - `apps/app/lib/shared/widgets/off_attribution.dart`
  - tests under `apps/app/test/features/...`
- Modify: `apps/app/lib/core/router/app_router.dart` (routes `/scan`, `/result`)

**Interfaces:**
- Consumes: the `smartnutri_api` operations `products_get_by_barcode` and `analyze_create` (whatever names swagger_parser generates for them), Plan 2's configured client provider, the generated l10n and tokens.
- Produces:

```dart
String? normalizeBarcode(String raw);                 // same rule as the API: digits only, length 8/12/13/14, else null
class AnalysisRepository { Future<AnalyzeOut> analyzeBarcode(String barcode, {String language}); }
class VerdictCard extends StatelessWidget { const VerdictCard({required VerdictOut verdict}); }  // colour = token for verdict.status
String topReasonText(AppLocalizations l10n, VerdictOut v);   // highest-severity reason → localized reason_<code> with params; "" when none
```

Behaviour:
- `ScanScreen` uses `mobile_scanner` (EAN-13, EAN-8, UPC-A, UPC-E). It stops after the first valid code and navigates to `/result?barcode=`.
- If camera permission is denied, show `scan.camera_denied` plus the manual field.
- `ResultScreen` calls `analyzeBarcode`:
  - `404` → `scan.not_found` with a retry. (M2 replaces this with the label flow.)
  - `503` → `scan.off_unavailable` with a retry.
  - Success → product header, grade chip (`color.grade.*`), "high in" chips, one `VerdictCard` per verdict, `OffAttribution` when `attribution != null`, and `common.disclaimer`.

- [ ] **Step 1: Write failing widget and unit tests**

```dart
test('normalizeBarcode', () { expect(normalizeBarcode(' 8901 0632 0108 9 '), '8901063201089'); expect(normalizeBarcode('abc123'), isNull); });
for (final c in sharedFixtureCases()) {      // reads packages/test-fixtures/responses/analyze/*.json + expected/*
  testWidgets('VerdictCard ${c.product}.${c.member}', (t) async {
    await t.pumpWidget(wrap(VerdictCard(verdict: c.verdict)));
    expect(find.text(c.localizedStatus), findsOneWidget);
    expect(cardColor(t), c.expectedTokenColor);          // unknown ≠ ok colour
  });
}
testWidgets('top reason for diabetic on sf_biscuit is misleading_sugar_claim', ...);
testWidgets('OFF attribution shown only for openfoodfacts source', ...);
testWidgets('disclaimer always shown on result', ...);
testWidgets('404 shows not-found with retry; 503 shows off-unavailable', ...);   // fake repository throwing typed errors
```

- [ ] **Step 2: Run them to verify they fail.** Run: `cd apps/app && flutter test test/features`. Expected: FAIL.
- [ ] **Step 3: Implement** the screens, repositories (Riverpod providers wrapping the generated client) and routes. No HTTP or business logic in widgets.
- [ ] **Step 4: Run** `flutter analyze && flutter test`. Expected: clean and passing. Then do a manual check on an emulator: `just android`, scan a real Indian pack (or enter its barcode), and see the verdict.
- [ ] **Step 5: Commit** with message `feat(app): barcode scan and verdict result screen (M1)`.

---

### Task 8: Web scan → result (app pages)

**Files:**
- Create:
  - `apps/web/src/features/scan/components/{BarcodeScanner,ManualBarcodeForm}.tsx`
  - `apps/web/src/features/scan/lib/{barcode.ts,detector.ts}`
  - `apps/web/src/features/analysis/api/useAnalyzeBarcode.ts`
  - `apps/web/src/features/analysis/components/{ResultView,VerdictCard,ReasonLine,GradeChip,OffAttribution}.tsx`
  - `apps/web/src/app/[locale]/(app)/scan/page.tsx`
  - `apps/web/src/app/[locale]/(app)/result/[barcode]/page.tsx`
  - `apps/web/tests/features/{scan,analysis}/*.test.tsx`
  - `apps/web/e2e/scan-manual.spec.ts`

**Interfaces:**
- Consumes: the `@smartnutri/api-client` operations `products_get_by_barcode` and `analyze_create` via `src/lib/api/client.ts`, next-intl messages and the token CSS variables.
- Produces:

```ts
export function normalizeBarcode(raw: string): string | null            // same rule as the API
export async function createDetector(video: HTMLVideoElement): Promise<{ stop(): void; onCode(cb: (code: string) => void): void }>
  // uses window.BarcodeDetector (ean_13, ean_8, upc_a, upc_e) when available, else @zxing/browser BrowserMultiFormatReader
export function useAnalyzeBarcode(barcode: string, language: Locale): UseQueryResult<AnalyzeOut, ApiError>
export function VerdictCard(props: { verdict: VerdictOut }): JSX.Element
export function topReasonText(t: Translator, v: VerdictOut): string
```

Behaviour:
- The scan page is a Client Component. It asks for the camera.
  - On denial or no camera, show `scan.camera_denied`. The manual form is always visible.
  - A valid code goes to `/[locale]/result/[barcode]`.
- The result page renders `ResultView`, with the same states and content as Android Task 7: not-found, off-unavailable, grade, high-in chips, cards, attribution and disclaimer.

- [ ] **Step 1: Write failing tests**

```ts
test("normalizeBarcode", () => { expect(normalizeBarcode(" 8901 0632 0108 9 ")).toBe("8901063201089"); expect(normalizeBarcode("abc123")).toBeNull(); });
describe.each(sharedFixtureCases())("VerdictCard %s", (c) => {
  it("renders status text and token class", () => {
    render(<VerdictCard verdict={c.verdict} />, { wrapper: Intl(c.locale) });
    expect(screen.getByText(c.localizedStatus)).toBeInTheDocument();
    expect(screen.getByTestId("verdict-card")).toHaveAttribute("data-status", c.expected.status);   // CSS maps data-status → token var
  });
});
it("falls back to zxing when BarcodeDetector is missing", async () => { delete (window as any).BarcodeDetector; ... expect(zxingCtor).toHaveBeenCalled(); });
it("shows manual form when camera permission denied", ...);
it("404 → not-found; 503 → off-unavailable", ...);       // MSW or a fetch stub on the generated client
// e2e/scan-manual.spec.ts (Playwright, API stubbed with page.route + fixture JSON)
test("manual barcode → verdict card", async ({ page }) => { /* enter 8901063201089 → see status for primary member + disclaimer */ });
```

- [ ] **Step 2: Run them to verify they fail.** Run: `pnpm --filter @smartnutri/web test`. Expected: FAIL.
- [ ] **Step 3: Implement** the components, hooks and pages. Use `"use client"` only for the scanner, the form and the result view.
- [ ] **Step 4: Run** `pnpm --filter @smartnutri/web lint && pnpm --filter @smartnutri/web typecheck && pnpm --filter @smartnutri/web test && pnpm --filter @smartnutri/web e2e`. Expected: all green.
- [ ] **Step 5: Commit** with message `feat(web): barcode scan and verdict result (M1)`.

---

### Task 9: Web public product page

**Files:**
- Create: `apps/web/src/app/[locale]/(public)/p/[barcode]/page.tsx`, `apps/web/src/features/product/components/PublicProduct.tsx`, `apps/web/tests/features/product/PublicProduct.test.tsx`

**Interfaces:**
- Consumes: the `products_get_public` operation (server-side, no session), and `packages/test-fixtures/responses/public/*.json`.
- Produces:

```ts
export const revalidate = 3600
export async function generateMetadata({ params }): Promise<Metadata>   // title "<name> – nutrition facts | SmartNutri", hreflang alternates en/hi/mr
export default async function Page({ params }): Promise<JSX.Element>    // notFound() on 404; error boundary text on 503
export function PublicProduct(props: { data: PublicProductOut }): JSX.Element
```

The page shows: name, brand and image; the Nutri-Score grade with `result.calculated_by_smartnutri`; "high in" chips; claim checks; ingredients; OFF attribution; and a call to action ("Check it for your family" → sign-in). **No member data and no verdict card.**

- [ ] **Step 1: Write failing tests**

```ts
it.each(publicFixtures())("renders %s without personal data", (f) => {
  render(<PublicProduct data={f.data} />, { wrapper: Intl("en") });
  expect(screen.getByText(/calculated by SmartNutri/i)).toBeInTheDocument();
  expect(screen.queryByTestId("verdict-card")).toBeNull();
});
it("shows OFF attribution for openfoodfacts source", ...);
it("generateMetadata sets hreflang for en, hi, mr", ...);
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement** the page as a Server Component. Fetch with the generated client using `next: { revalidate: 3600 }`.
- [ ] **Step 4: Run** the web lint, typecheck, test and build. Then check `curl -s localhost:3000/en/p/8901063201089 | grep -c verdict` returns `0`.
- [ ] **Step 5: Commit** with message `feat(web): public product page with generic facts (M1)`.

---

### Task 10: Milestone gate

**Files:**
- Modify: `docs/FEATURE_PARITY.md` (F3 → ✅ on all three; F13 → 🟡 "basic"; F11 → 🟡 "OFF attribution")

- [ ] **Step 1:** Run `just test` and `just lint` at the repo root. Expected: all pass.
- [ ] **Step 2:** Run the `nutrition-safety-reviewer` agent over the M1 range. Its focus: verdict rendering on both clients, `unknown` colour, the public page has no personal data, and OFF mapping never invents values. Fix any blocking issue in a follow-up commit, and re-run.
- [ ] **Step 3:** Do a manual parity check. Scan the same three real packs on Android and web, and confirm identical statuses and top reasons.
- [ ] **Step 4:** Update `docs/FEATURE_PARITY.md`.
- [ ] **Step 5: Commit** with message `docs: M1 parity status`.
