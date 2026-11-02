# Plan 6 (M4): Scan-to-Log, Daily/Weekly Summaries, Alternatives, Search, Compare and Share

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After a scan, any family member can log "I ate this" with a portion. The app then shows daily and weekly sugar, salt, protein and kcal against limits for that member. Users can find healthier alternatives, search products, compare two products side by side, and share a result or the weekly family summary without revealing anyone's health conditions. This ships on Android (with an offline log) and on web.

**Architecture:**
- **API first.**
  - A `meals` feature: snapshot nutrients at log time, idempotent on `client_id` for offline sync.
  - A pure `daily_limits` module in `app/scoring`, with limits from `thresholds.yaml`, marked pending clinician review.
  - A pure summary aggregator using **IST day boundaries**.
  - `products` gains alternatives, search and compare.
- Then `just contract` and `just i18n`.
- **Clients** (Android ∥ web), in parallel.
- **Share texts** are ICU messages in `packages/i18n` filled from API data. Both clients produce identical text, verified by shared fixtures. No API endpoint is needed for sharing.

**Tech Stack:**
- API: Python 3.13, FastAPI, SQLAlchemy 2 async + Alembic, pytest.
- Android: Flutter, Riverpod 3, go_router, drift (offline queue), `share_plus`, the generated `smartnutri_api`.
- Web: Next.js 16, TanStack Query, next-intl, `@smartnutri/api-client`, Web Share API.
- Tests: Vitest, Playwright, flutter_test.

**Spec:** `docs/superpowers/specs/2026-11-02-smartnutri-v1-design.md`. Features F8, F9, F17; §4 `meal_logs`; §5 `/meals`, `/products/{id}/alternatives`. Also see `docs/FEATURE_PARITY.md` (F8: Android offline + sync, web online-only and says so; F9: compare is two-column on desktop, stacked on mobile; F17: Web Share + copy link + `wa.me` fallback).

## Global Constraints

- **Snapshots, not live joins.** A meal log stores `nutrients` computed at log time from `per_100g × grams / 100`. Later product edits never rewrite history.
- **Missing stays missing.**
  - A nutrient that is `None` on the product is `null` in the snapshot.
  - Summaries never count `null` as 0. They set `incomplete: true` for that nutrient and still sum the known meals.
- **Limits are data:**
  - Daily limits live in `app/scoring/data/thresholds.yaml` under `daily_limits`, marked `PENDING CLINICIAN REVIEW`, with sources (WHO / ICMR-NIN 2024 / NHS).
  - Nothing threshold-like goes in `.py` files.
  - Any change goes through the `scoring-rule` skill plus fixtures.
- **Day boundaries** use `Asia/Kolkata` (`get_settings().app_timezone`). Week = the 7 IST days ending on the requested date (default: today).
- **Idempotent logging:** `POST /v1/meals` with a `client_id` already stored for the account returns `200` with the existing row and never creates a duplicate. A new log returns `201`.
- **Ownership:** a member or meal of another account returns `404` (`member_not_found` / `meal_not_found`).
- **Share privacy:**
  - Share text and images may include product name, grade, a member's **first name or relation** and the status colour word.
  - They must **never** include conditions, allergens, reason codes or nutrient totals compared with a personal limit.
  - The weekly summary share shows counts only: scans, logged items, "better swaps found".
- **Alternatives:**
  - Only products with a Nutri-Score grade **strictly better** than the source.
  - Never suggest a product whose grade is `None`.
  - Rank by grade, then sugars per 100 g ascending, then name.
  - At most 5.
  - Price-aware ranking is out of scope (v2).
- **Contract:**
  - Each route has an explicit `operation_id` = `<feature>_<action>`.
  - Run `just contract` after API changes.
  - Never hand-edit generated code.
- **Strings** come only from `packages/i18n`. **Colours** come only from design tokens. Clients never compute verdicts, limits or totals; they render the API values.
- **Web logging** is online-only in v1 and the UI says so (`meals.online_only`). Android queues offline in drift and syncs.
- Commands: API from `apps/api` (`uv run pytest`), Android from `apps/app` (`flutter test`), web via `pnpm --filter @smartnutri/web test` / `e2e`. Repo-wide: `just test`, `just contract`.

## Review Focus

1. **Offline duplicate sync:** the same `client_id` posted twice (a retry after a timeout) must produce one row. Owned by Task 3 (`test_client_id_is_idempotent`) and Task 9 (`sync retries do not duplicate`).
2. **Product with missing sugars:** the snapshot `sugars_g` is null, and the summary sets `incomplete.sugar_g = true` rather than reporting a lower total as complete. Owned by Task 4 (`test_missing_nutrient_marks_incomplete`).
3. **IST day boundary:** a meal at 23:30 IST on 3 Nov belongs to 3 Nov, not 4 Nov in UTC terms or vice versa. Owned by Task 4 (`test_ist_day_boundary`).
4. **Share leaks health data:** share text for a diabetic member must not contain "diabetes", any allergen name or reason text, on either client. Owned by Task 9 (`share text has no conditions`) and Task 11 (`shareText.privacy.test.ts`).
5. **Alternatives for an uncategorised or label-only product:** the result is an empty list with `reason: "no_category"`, not an error, and never a worse or ungraded product. Owned by Task 5 (`test_no_category_returns_empty_with_reason`, `test_never_worse_or_ungraded`).

## Interfaces consumed from earlier plans

Verify the names against the earlier plans' Interfaces blocks before Task 1; on a mismatch, the earlier plan wins.

- **Plan 1:** `app.scoring.{analyze, Product, Nutrients, Member, Status, load_config}`, `compute_nutriscore` (`app.scoring.nutriscore`), `high_in` (`app.scoring.warnings`), `Nutrients.salt()`.
- **Plan 2:** `create_app`, `get_settings` (add `app_timezone: str = "Asia/Kolkata"` if missing), `current_account` → `AccountContext`, `get_session`, `Base`, `ApiError`, `limit(bucket)`, `tests/api/conftest.py` (`client`, `auth_headers`, `db_session`).
- **Plan 3:**
  - `app.features.products.service.get_product(session, product_id) -> ProductRow` (with `per_100g`, `serving_size_g`, `barcode`, `name`, `brand`)
  - `product_row_to_scoring(row) -> Product`
  - `app.integrations.openfoodfacts.OffClient` (with `get_product(barcode)` and the cached `off_product_cache` payload)
  - `off_to_product(payload) -> Product`
  - The result screens on both clients
- **Plan 5:** `get_member`, `list_members`, `to_scoring_member(row, today)`, `MemberRow`, `seeded_family` / `consented_headers` / `other_account_member_id` test fixtures.

## File Map

```
apps/api/
  app/scoring/data/thresholds.yaml        # Task 1 (daily_limits, summary bands)
  app/scoring/daily_limits.py             # Task 1
  alembic/versions/<rev>_meal_logs.py     # Task 2
  app/features/meals/{models,schemas,service,router,summary}.py   # Tasks 2–4
  app/features/products/{alternatives,compare,search}.py          # Tasks 5–6
  app/features/products/{router,schemas}.py                       # Tasks 5–6 (extend)
  app/integrations/openfoodfacts.py       # Task 5 (search methods, if missing)
  tests/unit/scoring/test_daily_limits.py, tests/unit/meals/test_summary.py
  tests/api/test_meals.py, test_meals_summary.py, test_alternatives.py, test_compare_search.py
packages/i18n/messages/{en,hi,mr}.json    # Task 7
packages/test-fixtures/{meals,expected}/  # Task 7
packages/api-contract/                    # Task 7 (generated)
apps/app/lib/core/storage/meal_queue.dart, lib/features/meals/…, lib/features/history/…   # Tasks 8–9 (∥ 10–11)
apps/app/lib/features/product/… (alternatives, compare, search), lib/shared/share/…
apps/web/src/features/meals/…, src/features/history/…, src/features/product/…, src/features/share/…  # Tasks 10–11
docs/FEATURE_PARITY.md                    # Task 12
```

---

### Task 1: Daily limits in the engine data

**Files:**
- Modify: `apps/api/app/scoring/data/thresholds.yaml`, `apps/api/app/scoring/__init__.py`
- Create: `apps/api/app/scoring/daily_limits.py`, `apps/api/tests/unit/scoring/test_daily_limits.py`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class DailyLimits:
    sugar_g: float | None        # free/added sugar limit (adult WHO conditional 25 g; child bands)
    salt_g: float | None
    protein_target_g: float | None   # weight_kg × protein_g_per_kg; None without weight
    kcal: None                   # informational only in v1 (no personal energy target)
def daily_limits_for(member: Member, weight_kg: float | None, cfg: ScoringConfig) -> DailyLimits
def nutrient_band(value: float | None, limit: float | None, cfg: ScoringConfig) -> Literal["ok","near","over","unknown"]
    # unknown if value or limit is None; limit == 0 → over if value > 0 else ok;
    # otherwise over if value > limit; near if value >= near_pct% of limit; else ok
```

Append to `thresholds.yaml` exactly (all under the file's `PENDING CLINICIAN REVIEW` header):

```yaml
daily_limits:
  adult:  {sugar_g: 25, salt_g: 5, protein_g_per_kg: 0.83}
  child_salt_g_by_min_age: {2: 3, 7: 5, 11: 6}        # NHS bands; sugar reuses conditions.child.free_sugar_daily_limit_g
  infant: {sugar_g: 0, salt_g: 0}
  near_pct: 80
```

Then extend Plan 5's maps in the same file:
- `sources` gains `who_free_sugars: {title: "WHO guideline: sugars intake for adults and children", url: "https://www.who.int/publications/i/item/9789241549028"}`.
- `section_sources` gains `daily_limits: who_free_sugars`.

Age banding reuses the Plan 1 child and infant ages (`conditions.infant.max_age`, and `conditions.child.max_age` added by Plan 1 Task 9 per ledger ruling R2). `age=None` → adult limits.

- [ ] **Step 1: Write failing tests**

```python
def test_adult_limits_with_weight(cfg):
    l = daily_limits_for(Member(id="a", name="A", age=40), 70.0, cfg)
    assert (l.sugar_g, l.salt_g, l.protein_target_g, l.kcal) == (25, 5, pytest.approx(58.1), None)

def test_child_bands(cfg):
    l = daily_limits_for(Member(id="c", name="C", age=8), None, cfg)
    assert (l.sugar_g, l.salt_g, l.protein_target_g) == (24, 5, None)

def test_infant_zero_limits(cfg):
    assert daily_limits_for(Member(id="i", name="I", age=1), None, cfg).sugar_g == 0

def test_bands(cfg):
    assert [nutrient_band(v, 25, cfg) for v in (10, 20, 26, None)] == ["ok", "near", "over", "unknown"]
    assert nutrient_band(1, 0, cfg) == "over" and nutrient_band(0, 0, cfg) == "ok"
```

- [ ] **Step 2: Run them to verify they fail.** `uv run pytest tests/unit/scoring/test_daily_limits.py -v`.
- [ ] **Step 3: Implement** and export `daily_limits_for`, `nutrient_band` and `DailyLimits`. If Plan 5's `methodology()` exists, add a `daily_limits` section to it, and extend `test_methodology.py::test_sections_in_order_with_sources` with `daily_limits` appended last.
- [ ] **Step 4: Run the tests to verify they pass**, plus `uv run pytest tests/unit/scoring -q`.
- [ ] **Step 5: Commit** with message `feat(scoring): daily limits for sugar, salt and protein (pending clinician review)`.
- [ ] **Step 6: Safety gate.** Run `nutrition-safety-reviewer` on this diff. Resolve blocking issues.

---

### Task 2: `meal_logs` table

**Files:**
- Create: `apps/api/alembic/versions/<rev>_meal_logs.py`, `apps/api/app/features/meals/models.py`, `apps/api/tests/api/test_rls_meals.py`

**Interfaces:**
- `MealLogRow` (`meal_logs`), with the spec §4 columns plus two additions needed for RLS and offline sync:
  - `id uuid pk default gen_random_uuid()`
  - `account_id uuid not null fk accounts(id) on delete cascade` — **added** so RLS keys on `account_id` like every table
  - `member_id uuid not null fk members(id) on delete cascade`, `product_id uuid not null fk products(id)`
  - `grams numeric not null check (grams > 0 and grams <= 5000)`, `eaten_at timestamptz not null default now()`
  - `nutrients jsonb not null` (snapshot)
  - `client_id uuid null` — **added** for offline idempotency, with `unique (account_id, client_id)`
  - `created_at timestamptz default now()`
  - index `(member_id, eaten_at desc)`
- RLS enabled, with policy `meal_logs_owner` on `account_id = auth.uid()`.

- [ ] **Step 1: Write the failing test** `test_rls_meals.py::test_meal_logs_rls_and_unique_client_id`. It asserts RLS is on, one owner policy exists, and inserting two rows with the same `(account_id, client_id)` raises `IntegrityError`.
- [ ] **Step 2: Run it to verify it fails.**
- [ ] **Step 3: Implement** the migration and model. Check `alembic downgrade -1 && alembic upgrade head`.
- [ ] **Step 4: Run it to verify it passes.**
- [ ] **Step 5: Commit** with message `feat(api): meal_logs table with RLS and offline idempotency key`.

---

### Task 3: Log, list and undo meals

**Files:**
- Create: `apps/api/app/features/meals/{schemas,service,router}.py`, `apps/api/tests/api/test_meals.py`
- Modify: `apps/api/app/main.py`

**Interfaces:**

```python
class MealIn(BaseModel):
    member_id: UUID; product_id: UUID
    grams: float | None = None        # exactly one of grams / servings
    servings: float | None = None     # requires product.serving_size_g
    eaten_at: datetime | None = None  # tz-aware; default now; not > now + 5 min; not older than 30 days
    client_id: UUID | None = None
class NutrientSnapshot(BaseModel):
    energy_kcal: float | None; sugars_g: float | None; salt_g: float | None
    protein_g: float | None; fat_g: float | None; sat_fat_g: float | None; carbs_g: float | None
class MealOut(BaseModel):
    id: UUID; member_id: UUID; product_id: UUID; product_name: str; grade: str | None
    grams: float; eaten_at: datetime; nutrients: NutrientSnapshot; client_id: UUID | None
def snapshot(per_100g: Nutrients, grams: float) -> NutrientSnapshot     # each field = value*grams/100 rounded to 1 dp; None stays None; salt via Nutrients.salt()
async def log_meal(session, account_id, body: MealIn) -> tuple[MealLogRow, bool]   # (row, created)
async def list_meals(session, account_id, member_id, start: datetime, end: datetime, limit: int = 200) -> list[MealLogRow]
async def delete_meal(session, account_id, meal_id) -> None
# router (prefix /v1/meals)
POST ""        operation_id="meals_log"    -> MealOut (201 new / 200 existing client_id)
GET  ""        operation_id="meals_list"   query member_id (required), from, to (default: last 7 IST days) -> list[MealOut]
DELETE "/{id}" operation_id="meals_delete" -> 204
```

Errors (422):
- Both or neither of grams/servings → `portion_required`.
- servings without `serving_size_g` → `serving_size_unknown`.
- Bad `eaten_at` → `eaten_at_out_of_range`.

- [ ] **Step 1: Write failing tests**

```python
async def test_log_by_servings_snapshots(client, consented_headers, seeded_family, sf_biscuit_product_id, me_id):
    r = await client.post("/v1/meals", json={"member_id": me_id, "product_id": sf_biscuit_product_id, "servings": 2}, headers=consented_headers)
    assert r.status_code == 201
    n = r.json()["nutrients"]; assert (r.json()["grams"], n["energy_kcal"], n["sugars_g"], n["salt_g"]) == (50, 225.0, 1.0, 0.5)  # 25 g serving ×2; salt 0.9→0.45→0.5 (1 dp)

async def test_client_id_is_idempotent(client, consented_headers, seeded_family, sf_biscuit_product_id, me_id):
    body = {"member_id": me_id, "product_id": sf_biscuit_product_id, "grams": 30, "client_id": str(uuid4())}
    a = await client.post("/v1/meals", json=body, headers=consented_headers)
    b = await client.post("/v1/meals", json=body, headers=consented_headers)
    assert (a.status_code, b.status_code) == (201, 200) and a.json()["id"] == b.json()["id"]

async def test_portion_required(client, consented_headers, seeded_family, sf_biscuit_product_id, me_id):
    r = await client.post("/v1/meals", json={"member_id": me_id, "product_id": sf_biscuit_product_id}, headers=consented_headers)
    assert r.status_code == 422 and r.json()["error"]["code"] == "portion_required"

async def test_foreign_member_404(client, consented_headers, other_account_member_id, sf_biscuit_product_id):
    r = await client.post("/v1/meals", json={"member_id": other_account_member_id, "product_id": sf_biscuit_product_id, "grams": 10}, headers=consented_headers)
    assert r.status_code == 404

def test_snapshot_keeps_none():
    s = snapshot(Nutrients(energy_kcal=400, sugars_g=None), 50)
    assert (s.energy_kcal, s.sugars_g) == (200.0, None)
```

(The salt expectation above assumes 1-decimal rounding: 0.9 × 50 / 100 = 0.45 → `round(0.45, 1)` = 0.5 under `Decimal` ROUND_HALF_UP. Use `Decimal` ROUND_HALF_UP explicitly.)

- [ ] **Step 2: Run them to verify they fail.** `uv run pytest tests/api/test_meals.py -v`.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(api): scan-to-log with nutrient snapshots and idempotent client_id`.

---

### Task 4: Daily and weekly summary

**Files:**
- Create: `apps/api/app/features/meals/summary.py`, `apps/api/tests/unit/meals/test_summary.py`, `apps/api/tests/api/test_meals_summary.py`
- Modify: `apps/api/app/features/meals/{schemas,router}.py`

**Interfaces:**

```python
NUTRIENTS = ("energy_kcal", "sugars_g", "salt_g", "protein_g")
class Totals(BaseModel): energy_kcal: float; sugars_g: float; salt_g: float; protein_g: float
class DaySummary(BaseModel): date: date; totals: Totals; items: int
class Summary(BaseModel):
    member_id: UUID; period: Literal["day","week"]; start: date; end: date
    totals: Totals; incomplete: dict[str, bool]                 # per nutrient: any meal had null
    limits: dict[str, float | None]                              # sugar_g, salt_g, protein_target_g, kcal(None) — per DAY
    bands: dict[str, Literal["ok","near","over","unknown"]]      # day: vs daily limit; week: vs limit*7 (protein: target*7, "over" not used for protein → "ok"/"near"/"unknown")
    days: list[DaySummary]                                       # 1 for day, 7 for week (zero-filled, oldest first)
def summarise(meals: Sequence[MealLogRow], limits: DailyLimits, period: str, end_date: date, tz: ZoneInfo, cfg) -> Summary   # pure
# router
GET "/summary" operation_id="meals_summary" query member_id, period=day|week, date (IST, default today) -> Summary
```

For protein (a target, not a limit), the band is computed as `nutrient_band(total, target)`, with `over` mapped to `ok`.

- [ ] **Step 1: Write failing unit tests** (`test_summary.py`, building `MealLogRow` stand-ins)

```python
def test_ist_day_boundary(cfg):
    m = meal(eaten_at=datetime(2026,11,3,18,0,tzinfo=UTC), sugars=10)   # 23:30 IST on 3 Nov
    s = summarise([m], ADULT_LIMITS, "day", date(2026,11,3), ZoneInfo("Asia/Kolkata"), cfg)
    assert s.totals.sugars_g == 10 and s.days[0].date == date(2026,11,3)

def test_missing_nutrient_marks_incomplete(cfg):
    s = summarise([meal(sugars=None, kcal=100), meal(sugars=5, kcal=100)], ADULT_LIMITS, "day", TODAY, IST, cfg)
    assert s.totals.sugars_g == 5 and s.incomplete["sugars_g"] is True and s.incomplete["energy_kcal"] is False

def test_week_has_seven_zero_filled_days(cfg):
    s = summarise([meal(day=TODAY, sugars=30)], ADULT_LIMITS, "week", TODAY, IST, cfg)
    assert len(s.days) == 7 and s.days[-1].totals.sugars_g == 30 and s.days[0].totals.sugars_g == 0

def test_day_band_over_limit(cfg):
    s = summarise([meal(sugars=30)], ADULT_LIMITS, "day", TODAY, IST, cfg)
    assert s.bands["sugar_g"] == "over"
```

- [ ] **Step 2: Write the failing API test** `test_meals_summary.py::test_summary_endpoint_for_diabetic_parent`. Seed Dad with two biscuit logs today (1 serving = 25 g each) → `GET /v1/meals/summary?member_id=…&period=day` returns `totals.sugars_g == 1.0` and `limits.sugar_g == 25`. The member's `weight_kg` comes from the members row.
- [ ] **Step 3: Run them to verify they fail.**
- [ ] **Step 4: Implement** `summarise` and the route (load the member via `get_member`, build `Member` via `to_scoring_member`, limits via `daily_limits_for`).
- [ ] **Step 5: Run them to verify they pass**, then commit with message `feat(api): daily and weekly nutrient summaries with IST boundaries`.

---

### Task 5: Alternatives

**Files:**
- Create: `apps/api/app/features/products/alternatives.py`, `apps/api/tests/api/test_alternatives.py`
- Modify: `apps/api/app/features/products/{router,schemas}.py`, `apps/api/app/integrations/openfoodfacts.py` (add `search_by_category` if missing)

**Interfaces:**

```python
# openfoodfacts.py (if missing)
async def search_by_category(self, category_tag: str, page_size: int = 24) -> list[dict]   # OFF v2 search, User-Agent, cached ≥24 h in off_product_cache
class AlternativeOut(BaseModel):
    barcode: str | None; product_id: UUID | None; name: str; brand: str | None
    grade: Literal["A","B","C","D","E"]; sugars_g: float | None; high_in: list[str]
    member_status: Literal["ok","caution","unknown","avoid"] | None   # only when member_id given
class AlternativesOut(BaseModel): items: list[AlternativeOut]; reason: Literal["ok","no_category","no_better_found","source_ungraded"]
def rank_alternatives(source_grade: str | None, candidates: Sequence[tuple[Product, dict]]) -> list[tuple[Product, dict]]   # pure; strictly better grade, no None grade, sort grade→sugars→name, max 5
# router
GET "/{product_id}/alternatives" operation_id="products_alternatives" query member_id? -> AlternativesOut
```

Behaviour:
- The source category comes from the OFF payload's first specific `categories_tags` entry (the last tag in the list). Products without one return `reason="no_category"`.
- A source grade of `None` returns `reason="source_ungraded"`.
- `member_status` uses `analyze(product, [member])` server-side; clients never compute it.

- [ ] **Step 1: Write failing tests**

```python
def test_rank_strictly_better_and_never_ungraded():
    ranked = rank_alternatives("D", [(prod("x", grade="C", sugars=8), {}), (prod("y", grade="D", sugars=1), {}),
                                     (prod("z", grade=None, sugars=0), {}), (prod("w", grade="A", sugars=20), {})])
    assert [p.name for p, _ in ranked] == ["w", "x"]

async def test_no_category_returns_empty_with_reason(client, consented_headers, label_only_product_id):
    r = (await client.get(f"/v1/products/{label_only_product_id}/alternatives", headers=consented_headers)).json()
    assert r == {"items": [], "reason": "no_category"}

async def test_never_worse_or_ungraded(client, consented_headers, namkeen_off_product_id, fake_off_category):
    items = (await client.get(f"/v1/products/{namkeen_off_product_id}/alternatives", headers=consented_headers)).json()["items"]
    assert items and all(i["grade"] < "E" for i in items)

async def test_member_status_from_engine(client, consented_headers, seeded_family, dad_id, namkeen_off_product_id, fake_off_category):
    items = (await client.get(f"/v1/products/{namkeen_off_product_id}/alternatives?member_id={dad_id}", headers=consented_headers)).json()["items"]
    assert all(i["member_status"] in {"ok","caution","unknown","avoid"} for i in items)
```

`fake_off_category` monkeypatches `OffClient.search_by_category` to return recorded payloads from `apps/api/tests/fixtures/off/namkeen_category.json`. There are no network calls in tests.

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(api): healthier alternatives from the same OFF category`.

---

### Task 6: Search and compare

**Files:**
- Create: `apps/api/app/features/products/{search,compare}.py`, `apps/api/tests/api/test_compare_search.py`
- Modify: `apps/api/app/features/products/{router,schemas}.py`, `openfoodfacts.py` (add `search_text` if missing)

**Interfaces:**

```python
class SearchHit(BaseModel): product_id: UUID | None; barcode: str | None; name: str; brand: str | None; grade: str | None; source: Literal["ours","off"]
async def search_products(session, off: OffClient, q: str, limit: int = 20) -> list[SearchHit]
    # q 2..80 chars; our products (name/brand ILIKE, verified or pending) first, then OFF text search; de-dup by barcode
class CompareSide(BaseModel): product_id: UUID; name: str; grade: str | None; per_100g: dict[str, float | None]; high_in: list[str]; member_status: str | None
class CompareOut(BaseModel): a: CompareSide; b: CompareSide; better: dict[str, Literal["a","b","same","unknown"]]
    # keys energy_kcal, sugars_g, salt_g, sat_fat_g (lower better), protein_g, fiber_g (higher better), grade (A best); unknown if either None
def compare(a: tuple[Product, NutriScoreResult], b: tuple[Product, NutriScoreResult]) -> dict[str, str]   # pure
GET "/search"  operation_id="products_search"  query q, limit -> list[SearchHit]   (rate-limited bucket "search": 60/min/account)
GET "/compare" operation_id="products_compare" query a, b (product ids), member_id? -> CompareOut
```

- [ ] **Step 1: Write failing tests**

```python
def test_compare_pure(namkeen, oats):
    b = compare((namkeen, compute_nutriscore(namkeen)), (oats, compute_nutriscore(oats)))
    assert (b["sugars_g"], b["protein_g"], b["grade"], b["salt_g"]) == ("b", "a", "b", "b")

async def test_compare_endpoint_member_status(client, consented_headers, seeded_family, dad_id, sf_biscuit_product_id, oats_product_id):
    r = (await client.get(f"/v1/products/compare?a={sf_biscuit_product_id}&b={oats_product_id}&member_id={dad_id}", headers=consented_headers)).json()
    assert r["a"]["member_status"] == "avoid" and r["better"]["grade"] == "b"

async def test_search_ours_first(client, consented_headers, sf_biscuit_product_id, fake_off_search):
    hits = (await client.get("/v1/products/search?q=biscuit", headers=consented_headers)).json()
    assert hits[0]["source"] == "ours"

async def test_search_query_too_short_422(client, consented_headers):
    assert (await client.get("/v1/products/search?q=a", headers=consented_headers)).status_code == 422
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them to verify they pass**, plus `uv run pytest -q`.
- [ ] **Step 5: Commit** with message `feat(api): product search and side-by-side compare`.

---

### Task 7: Contract, i18n (including share templates) and fixtures

**Files:**
- Modify: `packages/i18n/messages/{en,hi,mr}.json`
- Create:
  - `packages/test-fixtures/meals/week_family.json` (meals for Me, Dad and Riya across 7 IST days, including one with null sugars)
  - `packages/test-fixtures/expected/week_family.dad_diabetic.json` (the `Summary` the API must return)
  - `packages/test-fixtures/expected/share_result.sf_biscuit.json`, `packages/test-fixtures/expected/share_weekly.week_family.json` (exact share strings per locale)
- Modify: `apps/api/tests/fixtures/test_shared_fixtures.py`
- Regenerate: `packages/api-contract/`

**i18n keys** in en, hi and mr:
- `meals.log.title`, `meals.log.servings`, `meals.log.grams`, `meals.log.save`, `meals.log.undo`, `meals.online_only`, `meals.queued_offline`
- `summary.title.day/week`, `summary.nutrient.{energy_kcal,sugars_g,salt_g,protein_g}`, `summary.band.{ok,near,over,unknown}`, `summary.incomplete`, `summary.limits_note` ("Limits pending clinician review")
- `alternatives.title`, `alternatives.reason.{no_category,no_better_found,source_ungraded}`
- `search.placeholder`, `compare.title`, `compare.better.{a,b,same,unknown}`
- Share templates (ICU, privacy-safe):
  - `share.result`: `"{product} — Nutri-Score {grade} (calculated by SmartNutri). {verdicts} Checked with SmartNutri: {url}"`
  - `share.result.member`: `"{who}: {status}"`
  - `share.weekly`: `"Our week on SmartNutri: {scans} products checked, {logged} items logged, {swaps} healthier swaps found. {url}"`
- Errors: `errors.{portion_required,serving_size_unknown,eaten_at_out_of_range,meal_not_found}`

`who` = first name, or `members.relation.<relation>` when the name is empty. `status` = `verdict.status.<status>`. **No condition or reason text is ever interpolated.**

- [ ] **Step 1: Write the failing fixture test** `test_week_family_summary_matches_expected`. It inserts `meals/week_family.json`, calls `/v1/meals/summary?period=week&date=<fixture end date>`, and asserts equality with `expected/week_family.dad_diabetic.json`.
- [ ] **Step 2: Add the fixtures and keys, then run** `just i18n` and `uv run pytest tests/fixtures -v`. Expected: PASS.
- [ ] **Step 3: Regenerate the contract.** `just contract`, `flutter analyze`, `pnpm --filter @smartnutri/web typecheck`.
- [ ] **Step 4: Commit** with message `chore(contract): meals, summary, alternatives, search, compare; share templates and fixtures`.

---

### Task 8: Android — log, offline queue and sync *(parallelisable with Task 10)*

**Files:**
- Create:
  - `apps/app/lib/core/storage/meal_queue.dart` (drift table `PendingMeals{clientId PK, memberId, productId, grams?, servings?, eatenAt, attempts, lastError}`)
  - `apps/app/lib/features/meals/{data/meals_repository.dart, data/meal_sync.dart, presentation/log_meal_sheet.dart, presentation/meals_providers.dart}`
  - `apps/app/test/features/meals/meal_sync_test.dart`, `apps/app/test/features/meals/log_meal_sheet_test.dart`
- Modify: `apps/app/lib/features/analysis/presentation/result_screen.dart` (an "I ate this" button per member card)

**Interfaces:**
- `MealsRepository.log(MealDraft)`:
  - Always writes the draft to `PendingMeals` with a new `clientId` (uuid v4).
  - Then attempts `mealsLog`.
  - On a 201/200 response it deletes the queue row.
  - On a network error it keeps the row and shows `meals.queued_offline`.
- `MealSync.flush()` runs on app start, on resume and on connectivity regain. It posts the queued rows **in eatenAt order** with their stored `clientId`. A 4xx (except 429) drops the row and records `lastError`; a 5xx or network error keeps it with `attempts++`.
- The log sheet offers servings (default 1, only when the product has a serving size) or grams.

- [ ] **Step 1: Write failing tests**
  - `meal_sync_test.dart::sync retries do not duplicate`: the fake API returns a network error and then 200 for the same clientId → exactly one `mealsLog` success, the queue is empty, and both attempts carried the same clientId.
  - `meal_sync_test.dart::4xx drops row`.
  - `log_meal_sheet_test.dart::servings hidden without serving size`.
- [ ] **Step 2: Run them to verify they fail.** `flutter test test/features/meals`.
- [ ] **Step 3: Implement** (drift codegen via `dart run build_runner build`; generated files are committed per apps/app/AGENTS.md).
- [ ] **Step 4: Run them to verify they pass**, plus `flutter analyze`.
- [ ] **Step 5: Commit** with message `feat(app): scan-to-log with offline queue and idempotent sync`.

---

### Task 9: Android — history, weekly dashboard, alternatives, search, compare and share *(parallelisable with Task 11)*

**Files:**
- Create:
  - `apps/app/lib/features/history/presentation/{history_screen.dart, weekly_dashboard.dart}`
  - `apps/app/lib/features/product/presentation/{alternatives_section.dart, search_screen.dart, compare_screen.dart}`
  - `apps/app/lib/shared/share/share_text.dart`
  - `apps/app/test/features/history/weekly_dashboard_fixture_test.dart`, `apps/app/test/shared/share_text_test.dart`
- Modify: `app_router.dart` (`/history`, `/search`, `/compare?a=&b=`), `result_screen.dart` (alternatives + share button), `pubspec.yaml` (`share_plus`)

**Interfaces:**
- `String shareResultText(AppLocalizations l, AnalyzeResponse r, String productName, String url)` and `String shareWeeklyText(AppLocalizations l, int scans, int logged, int swaps, String url)`. Both build strings only from `share.*` keys.
- `WeeklyDashboard(summary)`:
  - One bar per nutrient per day.
  - The band colour comes from tokens.
  - The `summary.incomplete` note shows when any flag is true.
  - The `summary.limits_note` always shows.
- `CompareScreen` renders `CompareOut.better` chips.

- [ ] **Step 1: Write failing tests**
  - `share_text_test.dart::share text has no conditions`: build from the `sf_biscuit` family response for Dad (diabetes) → the string equals `expected/share_result.sf_biscuit.json["en"]`, and it contains none of "diabetes", "diabetic", "milk", "allergy" or any `reason.*` text. The same runs for `hi`.
  - `share_text_test.dart::weekly share matches fixture`.
  - `weekly_dashboard_fixture_test.dart::renders week_family for Dad`: 7 day bars, the sugar band token for an "over" day, and the incomplete note shown.
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement** (`Share.share(text)` via `share_plus`. Alternatives and compare render API values only).
- [ ] **Step 4: Run them to verify they pass**, plus `flutter analyze`.
- [ ] **Step 5: Commit** with message `feat(app): history, weekly dashboard, alternatives, search, compare and share`.

---

### Task 10: Web — log and history *(parallelisable with Task 8)*

**Files:**
- Create:
  - `apps/web/src/features/meals/{api/meals.ts, components/LogMealDialog.tsx, hooks/useMeals.ts}`
  - `apps/web/src/features/history/components/{WeeklyDashboard.tsx, DayList.tsx}`
  - `apps/web/src/app/[locale]/(app)/history/page.tsx`
  - `apps/web/tests/features/meals/LogMealDialog.test.tsx`, `apps/web/tests/features/history/WeeklyDashboard.fixtures.test.tsx`
- Modify: the result page (an "I ate this" button per member card)

**Interfaces:**
- `LogMealDialog` sends `meals_log` with a fresh `crypto.randomUUID()` `client_id` per attempt series. It reuses the same id when the user retries after an error, so the request stays idempotent.
- It always shows `meals.online_only`.
- `WeeklyDashboard` has the same contract as Android's: bands from token CSS vars, the incomplete note, and the limits note.

- [ ] **Step 1: Write failing Vitest tests**
  - "retry reuses client_id": the first call rejects, the second succeeds, and both payloads have the same `client_id`.
  - "shows online-only notice".
  - `WeeklyDashboard.fixtures.test.tsx`: renders `expected/week_family.dad_diabetic.json` with 7 bars, the over-band variable on the right day, and the incomplete note.
- [ ] **Step 2: Run them to verify they fail.** `pnpm --filter @smartnutri/web test meals history`.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them to verify they pass**, plus lint and typecheck.
- [ ] **Step 5: Commit** with message `feat(web): scan-to-log, history and weekly dashboard`.

---

### Task 11: Web — alternatives, search, compare and share *(parallelisable with Task 9)*

**Files:**
- Create:
  - `apps/web/src/features/product/components/{Alternatives.tsx, SearchBox.tsx, CompareTable.tsx}`
  - `apps/web/src/app/[locale]/(app)/search/page.tsx`, `.../compare/page.tsx`
  - `apps/web/src/features/share/{shareText.ts, ShareButton.tsx}`
  - `apps/web/tests/features/share/shareText.privacy.test.ts`, `apps/web/tests/features/product/CompareTable.test.tsx`
  - `apps/web/e2e/log-and-share.spec.ts`

**Interfaces:**
- `shareResultText(t, response, productName, url)` and `shareWeeklyText(t, scans, logged, swaps, url)` are byte-identical to Android's output for the same locale (fixtures enforce this).
- `ShareButton`:
  - Uses `navigator.share({text, url})` when available.
  - Otherwise shows "Copy link" (`navigator.clipboard.writeText`) and a WhatsApp link `https://wa.me/?text=${encodeURIComponent(text)}`.
- The share URL is `${NEXT_PUBLIC_SITE_URL}/${locale}/p/${barcode}` for barcoded products (the public page is built in M5), else `${NEXT_PUBLIC_SITE_URL}/${locale}`.
- `CompareTable` is two columns at ≥ md breakpoint and stacked below.

- [ ] **Step 1: Write failing tests**
  - `shareText.privacy.test.ts`: equals `expected/share_result.sf_biscuit.json[locale]` for en, hi and mr, and contains no condition, allergen or reason text.
  - `CompareTable.test.tsx`: "stacks on narrow viewport" and "marks better side".
  - `log-and-share.spec.ts` (Playwright): log the biscuit for Dad → history shows today's sugar → Share falls back to the copy-link and WhatsApp buttons when `navigator.share` is undefined.
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run them to verify they pass**, plus lint and typecheck.
- [ ] **Step 5: Commit** with message `feat(web): alternatives, search, compare and privacy-safe share`.

---

### Task 12: Slice gate — safety review and parity

**Files:**
- Modify: `docs/FEATURE_PARITY.md` (F8, F9, F17)

- [ ] **Step 1: Run everything.** `just test` and `just lint`. Expected: all green.
- [ ] **Step 2: Run the `nutrition-safety-reviewer`** over the slice:
  - Daily limits and bands.
  - "Unknown" and "incomplete" are never shown as fine.
  - Share privacy on both clients.
  - Alternatives never worse or ungraded.

  Fix blocking issues in the owning task's files and re-run their tests.
- [ ] **Step 3: Update parity statuses.** F8 Android notes "offline + sync"; web notes "online-only (by design)". Mark ✅ only when both clients' tests pass.
- [ ] **Step 4: Commit** with message `docs: M4 parity status`.
