# Plan 5 (M3): Family Members, Per-Member Verdicts, Claims, Custom Alerts and Explanations

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A family manager adds members with their diet, allergies, conditions and custom alerts, after giving recorded consent. Every scan result then shows a colour, a grade and a one-line reason for each member ("OK for you, Avoid for Dad"), the claim-checker findings and an AI explanation in en/hi/mr. This ships on Android and web from the same API.

**Architecture:**
- **API first.**
  - The "Plan 1b" scoring follow-up (custom alerts and `methodology()`).
  - `members` and `consents` features (tables, routes, consent gate).
  - The analyze service uses the account's real members.
  - The F7 explanation runs through the CallMissed `LLMProvider` and never touches verdicts.
- Then `just contract` and `just i18n`.
- **Clients:** the Android (Flutter) and web (Next.js) tasks run **in parallel** against the regenerated clients and the shared fixtures. Clients render reason codes; they never compute a verdict.

**Tech Stack:**
- API: Python 3.13, FastAPI, SQLAlchemy 2 (async) + Alembic, pytest.
- Android: Flutter + Riverpod 3 + go_router + the generated `smartnutri_api`.
- Web: Next.js 16 + TanStack Query + react-hook-form/zod + next-intl + the generated `@smartnutri/api-client`.
- Tests: Vitest, Playwright, flutter_test.

**Spec:** `docs/superpowers/specs/2026-11-02-smartnutri-v1-design.md`. Features F2, F6, F7, F13, F16 and the §8 "Plan 1b" follow-up. Also see `docs/FEATURE_PARITY.md`.

## Global Constraints

- **The rules engine decides; the LLM only explains.**
  - Verdicts, statuses and reason codes come only from `app.scoring.analyze()`.
  - The explanation text never changes them.
  - Clients render exactly what the API returns (ADR 0005).
- **Never `ok` for an allergic member when ingredients are unknown.** This is already enforced by the engine. M3 must not bypass it.
- **Consent gate:**
  - Saving any non-empty `conditions` or `allergens` requires active consents for **both** `health_data` and `ai_processing` at the current versions. Otherwise return `403` `{"error":{"code":"consent_required"}}`.
  - Explanations are generated only when `ai_processing` consent is active.
- **Health data to the LLM:**
  - Prompts never contain member names, member ids, account ids or email.
  - Use the India-processed model from config (`MODEL_EXPLANATION`) with `provider.data_residency = "in"`.
- **Custom alerts:**
  - Allowed keys: `palm_oil`, `maida`, `added_sugar`, `artificial_sweetener`, `msg`.
  - A match produces reason `custom_alert`, severity `caution`, params `{"alert": key, "ingredients": [...]}`.
  - `added_sugar` matches `added_sugars ∪ hidden_sugars` (no new term list). The other four use the new `custom_alerts` map in `data/ingredients.yaml`.
- **Thresholds and terms live in YAML** (`app/scoring/data/*.yaml`), marked `PENDING CLINICIAN REVIEW`. Every YAML change updates `packages/test-fixtures/expected/` in the same task.
- **Contract:**
  - Each route has an explicit `operation_id` = `<feature>_<action>`.
  - After API changes, run `just contract` and commit `packages/api-contract/` together.
  - Never hand-edit generated Dart, TS or ARB files.
- **Strings:** every user-facing string lives in `packages/i18n/messages/{en,hi,mr}.json`. Reason codes map to `reason.<code>` (ICU params), allergens to `allergen.<key>`, custom alerts to `alert.<key>`, and claims to `claim.<key>` / `claim.verdict.<verdict>`.
- **Colours:**
  - Use the design-token names only: `verdict.ok` green, `verdict.caution` amber, `verdict.avoid` red, `verdict.unknown` grey.
  - `unknown` is **never** green, and its label is "Label unclear".
- **Ownership:**
  - Every query is scoped to `AccountContext.account_id`.
  - Another account's member id returns `404 member_not_found`, never `403`.
- Every verdict view shows "Information, not medical advice".
- Commands: API from `apps/api` (`uv run pytest`), Android from `apps/app` (`flutter test`), web via `pnpm --filter @smartnutri/web test`. Repo-wide: `just test`, `just contract`, `just i18n`.

## Review Focus

1. **Conditions saved before consent:** a `POST /v1/members` with `conditions: ["diabetes"]` and no consent must return `403 consent_required`, with nothing written. Owned by Task 5 (`test_conditions_require_consent`).
2. **Free-text "other" allergen:** e.g. `"kiwi"` or Devanagari `"मूंगफली"` must reach the engine and match literally. Owned by Task 6 (`test_other_allergen_reaches_engine`).
3. **Age from birth year at the infant boundary:** someone born this year (IST) is age 0, so the infant rules fire. Owned by Task 6 (`test_birth_year_this_year_is_infant`).
4. **The LLM contradicts the verdict or echoes a name:**
   - Statuses must be unchanged.
   - No member name appears in the prompt.
   - The explanation is dropped if it names a status different from the engine's.
   - Owned by Task 7 (`test_explanation_never_changes_verdict`, `test_prompt_has_no_member_names`).
5. **Cross-account member access:** `PATCH`/`DELETE`/`analyze` with another account's member id must return 404, not leak, and not modify. Owned by Task 5 (`test_other_account_member_is_404`) and Task 6 (`test_analyze_ignores_foreign_member_ids`).

## Interfaces consumed from earlier plans

Verify the names below against the earlier plans' Interfaces blocks before Task 1. If a name differs, use the earlier plan's name; it is the source of truth.

- **Plan 1 (scoring):**
  - `app.scoring`: `analyze`, `AnalysisResult.to_dict()`, `Product`, `Nutrients`, `Member` (frozen: `id, name, age, diet, allergens, conditions, goal`), `Diet`, `Status`, `Reason`, `load_config`
  - `app.scoring.verdict.evaluate_member`
  - `app.scoring.warnings.added_sugar_terms`
  - `app.scoring.ingredients.find_terms`
- **Plan 2 (foundation):**
  - `app.main:create_app`, `app.core.config.get_settings`
  - `app.core.security.current_account` → `AccountContext(account_id: UUID, email: str | None)`
  - `app.db.session.get_session`, `app.db.base.Base`
  - `app.core.errors.ApiError(code, status, message_key)`, `app.core.ratelimit.limit(bucket)`
  - Test helpers `tests/api/conftest.py`: `client` (httpx AsyncClient), `auth_headers(account_id)`, `db_session`
- **Plan 3 (M1):**
  - `app/features/analyze/{router,schemas,service}.py`
  - `POST /v1/analyze` (`analyze_run`) returning `AnalyzeResponse{report, verdicts[], explanation, tips}`
  - `app.features.products.service.get_product(session, product_id) -> ProductRow`
  - `product_row_to_scoring(row) -> Product`
  - Android `lib/features/analysis/`, web `src/features/analysis/` result screens
- **Plan 4 (M2):** `app.integrations.providers.LLMProvider` (async `chat_json(*, model, messages, schema, data_residency) -> dict`), `app.integrations.callmissed.CallMissedClient`, prompt loader `app.prompts.load_prompt(name, version) -> str`.

## File Map

```
apps/api/
  app/scoring/models.py                     # Task 1 (Member.custom_alerts)
  app/scoring/custom_alerts.py              # Task 1
  app/scoring/verdict.py                    # Task 1 (wire custom alerts)
  app/scoring/data/ingredients.yaml         # Task 1 (custom_alerts map)
  app/scoring/data/thresholds.yaml          # Task 2 (sources section)
  app/scoring/methodology.py                # Task 2
  app/scoring/__init__.py                   # Tasks 1–2 (exports)
  alembic/versions/xxxx_members_consents.py # Task 3
  app/features/consents/{models,schemas,service,router,policy}.py   # Tasks 3–4
  app/features/members/{models,schemas,service,router}.py           # Tasks 3, 5
  app/features/analyze/{service,schemas}.py # Task 6 (members), Task 7 (explanation)
  app/features/analyze/explain.py           # Task 7
  app/prompts/explanation_v1.md             # Task 7
  tests/unit/scoring/test_custom_alerts.py, test_methodology.py
  tests/api/test_consents.py, test_members.py, test_analyze_members.py, test_explain.py
  tests/fixtures/test_shared_fixtures.py    # Task 8 (extend)
packages/test-fixtures/{members,products,expected}/  # Task 8
packages/i18n/messages/{en,hi,mr}.json      # Task 8
packages/api-contract/                      # Task 8 (generated)
apps/app/lib/features/members/…  apps/app/lib/features/analysis/…   # Tasks 9–10 (parallel with 11–12)
apps/web/src/features/members/…  apps/web/src/features/analysis/…   # Tasks 11–12
docs/FEATURE_PARITY.md                      # Task 13
```

---

### Task 1: Custom ingredient alerts in the engine (Plan 1b, part 1)

**Files:**
- Modify: `apps/api/app/scoring/models.py`, `apps/api/app/scoring/verdict.py`, `apps/api/app/scoring/data/ingredients.yaml`, `apps/api/app/scoring/__init__.py`, `apps/api/tests/unit/scoring/conftest.py`
- Create: `apps/api/app/scoring/custom_alerts.py`, `apps/api/tests/unit/scoring/test_custom_alerts.py`

**Interfaces:**
- Consumes: `Member`, `Reason`, `Status` (Plan 1 T2); `find_terms` (Plan 1 T3); `added_sugar_terms` (Plan 1 T5); `evaluate_member` (Plan 1 T10).
- Produces:

```python
# models.py — Member gains one field (default keeps all Plan 1 call sites valid)
custom_alerts: tuple[str, ...] = ()
CUSTOM_ALERT_KEYS: tuple[str, ...] = ("palm_oil", "maida", "added_sugar", "artificial_sweetener", "msg")

# custom_alerts.py
def custom_alert_reasons(product: Product, member: Member, cfg: ScoringConfig) -> list[Reason]
    # one Reason("custom_alert", Status.CAUTION, {"alert": key, "ingredients": [...sorted]}) per matching enabled alert, in CUSTOM_ALERT_KEYS order
```

Data, appended to `data/ingredients.yaml` exactly:

```yaml
custom_alerts:
  palm_oil:             [palm oil, palmolein, palm olein, palm kernel oil, vegetable oil (palm), edible vegetable oil (palm)]
  maida:                [maida, refined wheat flour, refined flour, मैदा]
  artificial_sweetener: [aspartame, ins951, sucralose, ins955, acesulfame potassium, acesulfame k, ins950, saccharin, ins954, neotame, ins961]
  msg:                  [monosodium glutamate, ins621, msg]
```

`evaluate_member` appends `custom_alert_reasons(...)` to the allergen, diet and condition reasons before ranking. Unknown alert keys on a member are ignored, never raised.

- [ ] **Step 1: Write failing tests** in `test_custom_alerts.py` (add a `palm_member` fixture `Member(id="m10", name="P", age=30, custom_alerts=("palm_oil","maida"))` to conftest)

```python
def test_palm_and_maida_alerts_on_biscuit(sf_biscuit, palm_member, cfg):
    rs = custom_alert_reasons(sf_biscuit, palm_member, cfg)
    assert [(r.code, r.severity, r.params["alert"]) for r in rs] == [
        ("custom_alert", Status.CAUTION, "palm_oil"), ("custom_alert", Status.CAUTION, "maida")]

def test_added_sugar_alert_uses_hidden_sugars(sf_biscuit, cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("added_sugar",))
    assert custom_alert_reasons(sf_biscuit, m, cfg)[0].params["ingredients"] == ["maltodextrin"]

def test_no_alerts_enabled_gives_no_reasons(sf_biscuit, peanut_allergic, cfg):
    assert custom_alert_reasons(sf_biscuit, peanut_allergic, cfg) == []

def test_unknown_alert_key_ignored(curd, cfg):
    assert custom_alert_reasons(curd, Member(id="x", name="X", custom_alerts=("glitter",)), cfg) == []

def test_alert_raises_ok_member_to_caution(curd, cfg):
    m = Member(id="x", name="X", age=30, custom_alerts=("added_sugar",))
    p = replace(curd, ingredients=("toned milk", "sugar"))
    assert analyze(p, [m]).verdicts[0].status == Status.CAUTION
```

- [ ] **Step 2: Run them to verify they fail.** `uv run pytest tests/unit/scoring/test_custom_alerts.py -v`. Expected: FAIL (`ModuleNotFoundError` / unexpected keyword `custom_alerts`).
- [ ] **Step 3: Implement** `custom_alerts.py`, the `Member` field, the YAML map, the `evaluate_member` wiring, and export `custom_alert_reasons` and `CUSTOM_ALERT_KEYS` from `app/scoring/__init__.py`.
- [ ] **Step 4: Run the full scoring suite.** `uv run pytest tests/unit/scoring -v`. Expected: all pass, including every Plan 1 golden test, unchanged.
- [ ] **Step 5: Commit** with message `feat(scoring): custom ingredient alerts (palm oil, maida, added sugar, sweeteners, MSG)`.

---

### Task 2: `methodology()` export (Plan 1b, part 2)

**Files:**
- Modify: `apps/api/app/scoring/data/thresholds.yaml`, `apps/api/app/scoring/__init__.py`
- Create: `apps/api/app/scoring/methodology.py`, `apps/api/tests/unit/scoring/test_methodology.py`

**Interfaces:**
- Produces:

```python
def methodology(cfg: ScoringConfig | None = None) -> dict[str, Any]
# {"version": str,                      # sha256[:12] of the 4 YAML files' bytes, stable across calls
#  "pending_clinician_review": True,
#  "sections": [ {"id": str, "source": str, "thresholds": {...}} ... ],
#  "sources": {key: {"title": str, "url": str}}}
# section ids, in this order: nutriscore_2023, high_in, allergens, diet, claims, blood_sugar, hypertension, weight_loss, child, infant, custom_alerts
```

Append a `sources:` block to `thresholds.yaml`, and give every section a `source` key from this map:

```yaml
sources:
  nutriscore_2023: {title: "Nutri-Score 2023 update (Santé publique France)", url: "https://www.santepubliquefrance.fr/nutri-score-2023-update"}
  uk_fsa_front_of_pack: {title: "UK FSA front-of-pack guidance (high thresholds)", url: "https://www.food.gov.uk/safety-hygiene/check-the-label"}
  fssai_claims_2018: {title: "FSSAI (Advertising & Claims) Regulations 2018", url: "https://www.fssai.gov.in/upload/uploadfiles/files/Compendium_Advertising_Claims_Regulations_14_12_2022.pdf"}
  fssai_labelling_2020: {title: "FSSAI Labelling & Display Regulations 2020", url: "https://www.fssai.gov.in/cms/food-safety-and-standards-regulations.php"}
  icmr_nin_2024: {title: "ICMR-NIN Dietary Guidelines for Indians 2024", url: "https://www.nin.res.in/dietaryguidelines/"}
  nhs_child_sugar: {title: "NHS: sugar limits for children", url: "https://www.nhs.uk/live-well/eat-well/food-types/how-does-sugar-in-our-diet-affect-our-health/"}
  who_infant: {title: "WHO guidance: no added sugar or salt under 2", url: "https://www.who.int/news-room/fact-sheets/detail/healthy-diet"}
section_sources: {nutriscore_2023: nutriscore_2023, high_in: uk_fsa_front_of_pack, allergens: fssai_labelling_2020, diet: fssai_labelling_2020, claims: fssai_claims_2018, blood_sugar: icmr_nin_2024, hypertension: icmr_nin_2024, weight_loss: icmr_nin_2024, child: nhs_child_sugar, infant: who_infant, custom_alerts: fssai_labelling_2020}
```

`thresholds` for each section copies the live config values: `high_in` gets `cfg.thresholds["high_in"]`, each condition group gets its `conditions.<group>` dict, and `allergens` / `diet` / `custom_alerts` get their term lists. `nutriscore_2023` gets the grade bands only, imported from `app.scoring.nutriscore` constants. Nothing is duplicated by hand.

- [ ] **Step 1: Write failing tests**

```python
def test_sections_in_order_with_sources(cfg):
    m = methodology(cfg)
    assert [s["id"] for s in m["sections"]] == ["nutriscore_2023","high_in","allergens","diet","claims",
        "blood_sugar","hypertension","weight_loss","child","infant","custom_alerts"]
    assert all(s["source"] in m["sources"] for s in m["sections"])

def test_thresholds_mirror_config(cfg):
    m = methodology(cfg)
    high = next(s for s in m["sections"] if s["id"] == "high_in")
    assert high["thresholds"] == cfg.thresholds["high_in"]

def test_flags_pending_review_and_stable_version(cfg):
    a, b = methodology(cfg), methodology(cfg)
    assert a["pending_clinician_review"] is True and a["version"] == b["version"] and len(a["version"]) == 12

def test_json_serialisable(cfg):
    import json; json.dumps(methodology(cfg))
```

- [ ] **Step 2: Run them to verify they fail.** `uv run pytest tests/unit/scoring/test_methodology.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `methodology.py`, the YAML blocks and the export from `app/scoring/__init__.py`. The `/v1/methodology` endpoint is M5 (Plan 7); do not add a route here.
- [ ] **Step 4: Run the tests to verify they pass**, plus `uv run pytest tests/unit/scoring -q`.
- [ ] **Step 5: Commit** with message `feat(scoring): methodology() export with sources for How we score`.

- [ ] **Step 6: Safety gate.** Run the `nutrition-safety-reviewer` agent on the diff from Task 1 to Task 2 (scoring and YAML). Resolve every blocking issue before Task 3.

---

### Task 3: `members` and `consents` tables (migration, models, RLS)

**Files:**
- Create: `apps/api/alembic/versions/<rev>_members_consents.py`, `apps/api/app/features/members/models.py`, `apps/api/app/features/consents/models.py`, `apps/api/tests/api/test_rls_members.py`

**Interfaces:**
- Consumes: `app.db.base.Base`, the Plan 2 `accounts` table.
- Produces: SQLAlchemy models `MemberRow` (`members`) and `ConsentRow` (`consents`), with columns exactly as spec §4:
  - `members`:
    - `id uuid pk default gen_random_uuid()`, `account_id uuid not null fk accounts(id) on delete cascade`, `name text not null`
    - `relation text not null check (relation in ('self','child','parent','spouse','other'))`
    - `birth_year int null`, `sex text null check (sex in ('female','male','other'))`
    - `height_cm numeric null`, `weight_kg numeric null`
    - `diet text not null default 'non_veg'`
    - `allergens text[] not null default '{}'`, `conditions text[] not null default '{}'`, `custom_alerts text[] not null default '{}'`
    - `goal text null`, `is_primary bool not null default false`
    - `created_at timestamptz default now()`, `updated_at timestamptz default now()`
  - `consents`:
    - `id uuid pk`, `account_id uuid not null fk accounts(id) on delete cascade`
    - `purpose text not null check (purpose in ('terms','health_data','ai_processing'))`
    - `version text not null`, `granted_at timestamptz not null default now()`, `withdrawn_at timestamptz null`
    - index `(account_id, purpose)`

Decision rule: if a previous migration in `alembic/versions` already created either table, this migration only **adds** the missing columns and policies. Never drop or recreate.

RLS in the same migration (`op.execute`):
- Enable RLS on both tables.
- A policy `members_owner` / `consents_owner` `for all using (account_id = auth.uid()) with check (account_id = auth.uid())`.

- [ ] **Step 1: Write the failing test** `test_rls_members.py::test_rls_enabled_and_policies_exist`. It queries `pg_class.relrowsecurity` and `pg_policies` for `members` and `consents`, and asserts both have RLS on and exactly one owner policy each.
- [ ] **Step 2: Run it to verify it fails.** `uv run pytest tests/api/test_rls_members.py -v`. Expected: FAIL (tables missing).
- [ ] **Step 3: Implement** the migration and models. Run `uv run alembic upgrade head` against the test DB, then `uv run alembic downgrade -1 && uv run alembic upgrade head`; both must succeed.
- [ ] **Step 4: Run the test to verify it passes.**
- [ ] **Step 5: Commit** with message `feat(api): members and consents tables with RLS`.

---

### Task 4: Consents API

**Files:**
- Create: `apps/api/app/features/consents/{policy,schemas,service,router}.py`, `apps/api/tests/api/test_consents.py`
- Modify: `apps/api/app/main.py` (include router)

**Interfaces:**
- Produces:

```python
# policy.py
CURRENT_VERSIONS: dict[str, str] = {"terms": "2026-11-01", "health_data": "2026-11-01", "ai_processing": "2026-11-01"}
# schemas.py
class ConsentIn(BaseModel): purpose: Literal["terms","health_data","ai_processing"]; version: str; granted: bool
class ConsentState(BaseModel): purpose: str; version: str | None; granted: bool; current_version: str
# service.py
async def record_consent(session, account_id: UUID, body: ConsentIn) -> list[ConsentState]
async def consent_states(session, account_id: UUID) -> list[ConsentState]
async def has_active_consent(session, account_id: UUID, purposes: Iterable[str]) -> bool
    # active = latest row per purpose has withdrawn_at is null AND version == CURRENT_VERSIONS[purpose]
# router.py  (prefix /v1/consents)
POST ""  operation_id="consents_record" -> list[ConsentState]
GET  ""  operation_id="consents_list"   -> list[ConsentState]
```

Behaviour:
- `granted=false` sets `withdrawn_at=now()` on the active row.
- `version` ≠ `CURRENT_VERSIONS[purpose]` → `422 consent_version_mismatch`.

- [ ] **Step 1: Write failing tests**

```python
async def test_grant_then_list(client, auth_headers):
    h = auth_headers(ACC_A)
    r = await client.post("/v1/consents", json={"purpose":"health_data","version":"2026-11-01","granted":True}, headers=h)
    assert r.status_code == 200
    states = {s["purpose"]: s for s in (await client.get("/v1/consents", headers=h)).json()}
    assert states["health_data"]["granted"] is True and states["ai_processing"]["granted"] is False

async def test_withdraw_deactivates(client, auth_headers, db_session): ...
    # grant then granted=False → has_active_consent(db_session, ACC_A, ["health_data"]) is False

async def test_wrong_version_rejected(client, auth_headers):
    r = await client.post("/v1/consents", json={"purpose":"terms","version":"old","granted":True}, headers=auth_headers(ACC_A))
    assert r.status_code == 422 and r.json()["error"]["code"] == "consent_version_mismatch"

async def test_requires_auth(client):
    assert (await client.get("/v1/consents")).status_code == 401
```

- [ ] **Step 2: Run them to verify they fail.** `uv run pytest tests/api/test_consents.py -v`.
- [ ] **Step 3: Implement** to the Interfaces block.
- [ ] **Step 4: Run the tests to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(api): versioned consent records`.

---

### Task 5: Members API with the consent gate

**Files:**
- Create: `apps/api/app/features/members/{schemas,service,router}.py`, `apps/api/tests/api/test_members.py`
- Modify: `apps/api/app/main.py`

**Interfaces:**
- Consumes: `has_active_consent` (Task 4), `MemberRow` (Task 3), `CUSTOM_ALERT_KEYS` (Task 1).
- Produces:

```python
Relation = Literal["self","child","parent","spouse","other"]
DietIn = Literal["veg","eggetarian","vegan","jain","non_veg"]
ConditionIn = Literal["diabetes","prediabetes","pcos","hypertension"]
GoalIn = Literal["healthy_eating","weight_loss","weight_gain"] | None
CANONICAL_ALLERGENS = ("milk","peanut","gluten","soy","egg","tree_nut","sesame","fish","crustacean","mustard","sulphite")

class MemberIn(BaseModel):
    name: str  (1..40 chars, stripped)
    relation: Relation
    birth_year: int | None  (1900..current IST year)
    sex: Literal["female","male","other"] | None
    height_cm: float | None (30..250); weight_kg: float | None (2..300)
    diet: DietIn = "non_veg"
    allergens: list[str] = []      # canonical keys OR free text (lowercased, stripped, 2..40 chars), max 10, deduped
    conditions: list[ConditionIn] = []
    custom_alerts: list[Literal["palm_oil","maida","added_sugar","artificial_sweetener","msg"]] = []
    goal: GoalIn = None
class MemberPatch(MemberIn with every field optional)
class MemberOut(MemberIn): id: UUID; is_primary: bool; age: int | None

# service.py
async def list_members(session, account_id) -> list[MemberRow]
async def get_member(session, account_id, member_id) -> MemberRow            # raises ApiError("member_not_found", 404)
async def create_member(session, account_id, body: MemberIn) -> MemberRow
async def update_member(session, account_id, member_id, body: MemberPatch) -> MemberRow
async def delete_member(session, account_id, member_id) -> None
def age_from_birth_year(birth_year: int | None, today: date) -> int | None   # today.year - birth_year (IST date), None passthrough

# router.py (prefix /v1/members)
GET ""            operation_id="members_list"   -> list[MemberOut]
POST ""           operation_id="members_create" -> MemberOut (201)
PATCH "/{id}"     operation_id="members_update" -> MemberOut
DELETE "/{id}"    operation_id="members_delete" -> 204
```

Rules:
- The first member of an account gets `is_primary=true`.
- There are at most **10** members per account; the 11th returns `422 member_limit`.
- Deleting the primary member promotes the oldest remaining member.
- **Consent gate:** if the resulting `conditions` or `allergens` are non-empty, require `has_active_consent(..., ["health_data","ai_processing"])`, else `403 consent_required`. This applies on create and patch.
- "today" uses `Asia/Kolkata` (`get_settings().app_timezone`, default `"Asia/Kolkata"`; add the setting if Plan 2 did not).

- [ ] **Step 1: Write failing tests**

```python
async def test_create_list_primary(client, consented_headers):
    r = await client.post("/v1/members", json={"name":"Me","relation":"self"}, headers=consented_headers)
    assert r.status_code == 201 and r.json()["is_primary"] is True

async def test_conditions_require_consent(client, auth_headers, db_session):
    r = await client.post("/v1/members", json={"name":"Dad","relation":"parent","conditions":["diabetes"]}, headers=auth_headers(ACC_B))
    assert r.status_code == 403 and r.json()["error"]["code"] == "consent_required"
    assert await list_members(db_session, ACC_B) == []

async def test_other_allergen_normalised(client, consented_headers):
    r = await client.post("/v1/members", json={"name":"K","relation":"child","allergens":["Peanut"," Kiwi "]}, headers=consented_headers)
    assert r.json()["allergens"] == ["peanut", "kiwi"]

async def test_invalid_custom_alert_422(client, consented_headers):
    r = await client.post("/v1/members", json={"name":"K","relation":"child","custom_alerts":["glitter"]}, headers=consented_headers)
    assert r.status_code == 422

async def test_member_limit(client, consented_headers): ...  # 11th create → 422 member_limit

async def test_other_account_member_is_404(client, consented_headers, other_account_member_id):
    for call in (client.patch(f"/v1/members/{other_account_member_id}", json={"name":"x"}, headers=consented_headers),
                 client.delete(f"/v1/members/{other_account_member_id}", headers=consented_headers)):
        r = await call; assert r.status_code == 404 and r.json()["error"]["code"] == "member_not_found"

def test_age_from_birth_year():
    assert age_from_birth_year(2026, date(2026, 11, 3)) == 0 and age_from_birth_year(None, date(2026,11,3)) is None
```

Add the fixtures `consented_headers` (ACC_A with all three consents granted) and `other_account_member_id` (a member created under ACC_C) to `tests/api/conftest.py`.

- [ ] **Step 2: Run them to verify they fail.** `uv run pytest tests/api/test_members.py -v`.
- [ ] **Step 3: Implement** to the Interfaces block and rules.
- [ ] **Step 4: Run the tests to verify they pass**, plus `uv run pytest tests/api -q`.
- [ ] **Step 5: Commit** with message `feat(api): family members CRUD with consent gate`.

---

### Task 6: Analyze uses the account's members

**Files:**
- Modify: `apps/api/app/features/analyze/{service,schemas}.py`
- Create: `apps/api/app/features/members/mapping.py`, `apps/api/tests/api/test_analyze_members.py`

**Interfaces:**
- Consumes: `list_members`, `age_from_birth_year` (Task 5); `analyze` (Plan 1); Plan 3 analyze service.
- Produces:

```python
# members/mapping.py
def to_scoring_member(row: MemberRow, today: date) -> Member
    # id=str(row.id), name=row.name, age=age_from_birth_year, diet=Diet(row.diet), allergens=tuple(row.allergens),
    # conditions=tuple(row.conditions), goal=row.goal, custom_alerts=tuple(row.custom_alerts)

# analyze/schemas.py — verdict item (extend Plan 3's)
class ReasonOut(BaseModel): code: str; severity: Literal["ok","caution","unknown","avoid"]; params: dict[str, Any]
class MemberVerdictOut(BaseModel):
    member_id: UUID; member_name: str; relation: str
    status: Literal["ok","caution","unknown","avoid"]
    top_reason: ReasonOut | None          # reasons[0] (already sorted most severe first by the engine)
    reasons: list[ReasonOut]
# AnalyzeResponse.report.claims: list[ClaimOut{claim, verdict, reason_code, params}] (from AnalysisResult.to_dict())
```

Behaviour:
- `member_ids=None` analyses **all** of the account's members.
- `member_ids` given → only those owned by the account. Unknown or foreign ids are **silently ignored**: no error, no leak.
- With zero members, `verdicts=[]` and the report is still returned.

- [ ] **Step 1: Write failing tests**

```python
async def test_family_verdicts_on_biscuit(client, consented_headers, seeded_family, sf_biscuit_product_id):
    r = await client.post("/v1/analyze", json={"product_id": sf_biscuit_product_id, "language": "en"}, headers=consented_headers)
    by_name = {v["member_name"]: v["status"] for v in r.json()["verdicts"]}
    assert by_name == {"Dad": "avoid", "Riya": "avoid", "Me": "caution"}   # diabetic, milk-allergic child, weight-loss

async def test_other_allergen_reaches_engine(client, consented_headers, kiwi_member, kiwi_product_id):
    v = (await client.post("/v1/analyze", json={"product_id": kiwi_product_id, "member_ids":[kiwi_member]}, headers=consented_headers)).json()["verdicts"][0]
    assert v["status"] == "avoid" and v["top_reason"]["code"] == "allergen_contains"

async def test_birth_year_this_year_is_infant(client, consented_headers, newborn_member, cola_product_id):
    v = (await client.post("/v1/analyze", json={"product_id": cola_product_id, "member_ids":[newborn_member]}, headers=consented_headers)).json()["verdicts"][0]
    assert "infant_added_sugar" in {r["code"] for r in v["reasons"]}

async def test_analyze_ignores_foreign_member_ids(client, consented_headers, other_account_member_id, cola_product_id):
    r = await client.post("/v1/analyze", json={"product_id": cola_product_id, "member_ids":[other_account_member_id]}, headers=consented_headers)
    assert r.status_code == 200 and r.json()["verdicts"] == []

async def test_claims_in_report(client, consented_headers, seeded_family, sf_biscuit_product_id):
    claims = (await client.post("/v1/analyze", json={"product_id": sf_biscuit_product_id}, headers=consented_headers)).json()["report"]["claims"]
    assert claims[0]["claim"] == "sugar_free" and claims[0]["verdict"] == "contradicted"
```

The `seeded_family` fixture creates Me (self, birth_year 1991, goal weight_loss), Dad (parent, 1954, veg, diabetes) and Riya (child, 2018, veg, allergens [milk]). Product fixtures insert the Plan 1 golden products as `products` rows, loaded from `packages/test-fixtures/products/*.json`.

- [ ] **Step 2: Run them to verify they fail.** `uv run pytest tests/api/test_analyze_members.py -v`.
- [ ] **Step 3: Implement** the mapping, the member loading in the analyze service, and the schema fields.
- [ ] **Step 4: Run the tests to verify they pass**, plus `uv run pytest tests/api -q`.
- [ ] **Step 5: Commit** with message `feat(api): per-member verdicts for the account's family`.

---

### Task 7: AI explanation (F7) that never changes verdicts

**Files:**
- Create: `apps/api/app/features/analyze/explain.py`, `apps/api/app/prompts/explanation_v1.md`, `apps/api/tests/api/test_explain.py`
- Modify: `apps/api/app/features/analyze/service.py`, `apps/api/app/features/analyze/schemas.py`, `apps/api/app/core/config.py` (only if `MODEL_EXPLANATION` is missing)

**Interfaces:**
- Consumes: `LLMProvider.chat_json` (Plan 4), `load_prompt` (Plan 4), `has_active_consent` (Task 4).
- Produces:

```python
class ExplanationOut(BaseModel):
    text: str | None; tips: list[str]; language: Literal["en","hi","mr"]
    source: Literal["llm","unavailable"]; prompt_version: str
EXPLANATION_SCHEMA: dict   # {"type":"object","required":["text","tips"],"properties":{"text":{"type":"string","maxLength":900},"tips":{"type":"array","maxItems":3,"items":{"type":"string","maxLength":140}}}}
def build_explanation_input(result: AnalysisResult, members: Sequence[MemberRow], language: str) -> dict
    # members anonymised as "member_1".."member_n" with relation only; statuses + reason codes + params; report facts; NO names/ids
async def explain(llm: LLMProvider, result: AnalysisResult, members: Sequence[MemberRow], language: str) -> ExplanationOut
```

Rules:
- Call `chat_json(model=settings.model_explanation, messages=[system=explanation_v1.md, user=json(input)], schema=EXPLANATION_SCHEMA, data_residency="in")`.
- **Guard:** if the returned `text` contains a status word for a member that contradicts the engine (the prompt instructs it to say "member_N: <status>"), or any member name, or the account email → return `source="unavailable"`, `text=None`, `tips=[]`.
- Any provider error or timeout (8 s) → `source="unavailable"`. Never use invented fallback prose.
- No `ai_processing` consent → no LLM call and `source="unavailable"`.
- The analyze response's `verdicts` are computed **before** and returned **unchanged** regardless of the explanation.

The prompt `explanation_v1.md` instructs the model to:
- Explain the given statuses only, in the requested language.
- Never give medical advice or claim to treat any disease.
- Give ≤3 practical tips.
- Refer to people only as `member_N` (the server then substitutes relation words).

- [ ] **Step 1: Write failing tests** (with a `FakeLLM` implementing `LLMProvider` that records calls)

```python
async def test_prompt_has_no_member_names(fake_llm, family_result, family_rows):
    await explain(fake_llm, family_result, family_rows, "hi")
    sent = json.dumps(fake_llm.calls[0]["messages"])
    assert "Dad" not in sent and "Riya" not in sent and str(family_rows[0].id) not in sent
    assert fake_llm.calls[0]["data_residency"] == "in"

async def test_explanation_never_changes_verdict(client, consented_headers, seeded_family, sf_biscuit_product_id, fake_llm_says_ok):
    r = (await client.post("/v1/analyze", json={"product_id": sf_biscuit_product_id}, headers=consented_headers)).json()
    assert {v["member_name"]: v["status"] for v in r["verdicts"]}["Dad"] == "avoid"
    assert r["explanation"]["source"] == "unavailable"     # LLM claimed member_1 is ok → dropped

async def test_provider_error_is_unavailable(failing_llm, family_result, family_rows):
    out = await explain(failing_llm, family_result, family_rows, "en")
    assert (out.source, out.text, out.tips) == ("unavailable", None, [])

async def test_no_ai_consent_no_call(client, health_only_consent_headers, seeded_family, cola_product_id, fake_llm):
    r = (await client.post("/v1/analyze", json={"product_id": cola_product_id}, headers=health_only_consent_headers)).json()
    assert fake_llm.calls == [] and r["explanation"]["source"] == "unavailable"
```

- [ ] **Step 2: Run them to verify they fail.** `uv run pytest tests/api/test_explain.py -v`.
- [ ] **Step 3: Implement** `explain.py`, the prompt file and the analyze wiring. The provider is injected via a FastAPI dependency so tests can override it.
- [ ] **Step 4: Run the tests to verify they pass**, plus `uv run pytest -q`.
- [ ] **Step 5: Commit** with message `feat(api): guarded LLM explanation for analysis results (en/hi/mr)`.
- [ ] **Step 6: Safety gate.** Run `nutrition-safety-reviewer` on the Task 6–7 diff (analyze mapping, prompt, guard). Resolve blocking issues.

---

### Task 8: Contract, i18n and shared fixtures

**Files:**
- Modify: `packages/i18n/messages/{en,hi,mr}.json`, `apps/api/tests/fixtures/test_shared_fixtures.py`
- Create: `packages/test-fixtures/members/{me_weight_loss,dad_diabetic,riya_milk_child,palm_alert_adult,kiwi_child}.json`, `packages/test-fixtures/expected/sf_biscuit.<member>.json` (one per family member), `packages/test-fixtures/expected/sf_biscuit.palm_alert_adult.json`
- Regenerate: `packages/api-contract/{openapi.json,dart/,ts/}`

**Interfaces:**
- Produces:
  - **i18n keys** in all three files:
    - `reason.<code>` for **every** code the engine can emit, including `custom_alert`. Check with `rg -o '"[a-z_]+"' apps/api/app/scoring` against the key list.
    - `allergen.<11 keys>`, `alert.<5 keys>`, `claim.<7 keys>`, `claim.verdict.{supported,contradicted,unverifiable}`.
    - `verdict.status.{ok,caution,unknown,avoid}`; `unknown` reads "Label unclear".
    - `verdict.for_member` = `"{status} for {name}"`, `verdict.disclaimer`.
    - `members.form.*`, `members.relation.*`, `members.diet.*`, `members.condition.*`, `members.goal.*`.
    - `consent.health_data.title/body`, `consent.ai_processing.title/body`, `consent.terms.title/body`.
    - `errors.consent_required`, `errors.member_limit`, `errors.member_not_found`.
  - **Expected fixture format:** `{"status": "avoid", "reason_codes": ["misleading_sugar_claim", "hidden_sugars"], "top_reason": "misleading_sugar_claim"}`.

- [ ] **Step 1: Write the failing fixture test** `test_shared_fixtures.py::test_family_expected_files_match_engine`. For every `expected/<product>.<member>.json`, it loads both fixtures, runs `analyze`, and asserts status, the ordered reason codes and the top reason.
- [ ] **Step 2: Add the fixture files and i18n keys.** Run `just i18n`. Then run `uv run pytest tests/fixtures -v`. Expected: PASS.
- [ ] **Step 3: Add the i18n completeness test** `packages/i18n` `check` (if Plan 2 created it) or `test_i18n_keys.py` in `apps/api/tests/unit`. It asserts that every engine reason code has `reason.<code>` in en, hi and mr. Run it.
- [ ] **Step 4: Regenerate the contract.** `just contract`, then `cd apps/app && flutter analyze` and `pnpm --filter @smartnutri/web typecheck`. Expected: no errors in generated code. Fix call sites only.
- [ ] **Step 5: Commit** with message `chore(contract): members, consents, per-member verdicts; i18n and family fixtures`.

---

### Task 9: Android — members and consent *(parallelisable with Task 11)*

**Files:**
- Create: `apps/app/lib/features/members/{data/members_repository.dart, domain/member.dart, presentation/members_list_screen.dart, presentation/member_form_screen.dart, presentation/consent_sheet.dart, presentation/members_providers.dart}`, `apps/app/test/features/members/member_form_test.dart`, `apps/app/test/features/members/consent_sheet_test.dart`
- Modify: `apps/app/lib/core/router/app_router.dart` (routes `/members`, `/members/new`, `/members/:id`)

**Interfaces:**
- Consumes the generated `smartnutri_api` operations: `membersList`, `membersCreate`, `membersUpdate`, `membersDelete`, `consentsList`, `consentsRecord`.
- Produces:
  - `membersProvider` (`AsyncNotifier<List<MemberOut>>`) with `create`, `update` and `remove`.
  - `consentStateProvider`.
  - `MemberFormScreen` with these fields:
    - name, relation, birth year picker, sex, height, weight, diet
    - allergen chips: 11 canonical + "Other" free-text chips
    - condition checkboxes
    - custom-alert switches
    - goal
- When the user adds a condition or allergen without consent, `ConsentSheet` opens. It shows the health_data and ai_processing texts, and records both before the save.
- The API `consent_required` error also opens the sheet, never a raw error.

- [ ] **Step 1: Write failing widget tests**
  - `member_form_test.dart::saves member with other allergen`: enter "Kiwi" under Other → the repository receives `allergens: ["kiwi"]`.
  - `member_form_test.dart::shows consent sheet before saving conditions`: tick diabetes with consent false → `ConsentSheet` is visible and the repository is not called.
  - `consent_sheet_test.dart::records both purposes`: accept → two `consentsRecord` calls with `CURRENT_VERSIONS` from `consentsList`.
  - All labels are looked up via `AppLocalizations`, so the tests also run in `hi`.
- [ ] **Step 2: Run them to verify they fail.** `flutter test test/features/members`.
- [ ] **Step 3: Implement** the feature (feature-first, Riverpod, no business logic in widgets, colours from tokens).
- [ ] **Step 4: Run the tests to verify they pass**, plus `flutter analyze`.
- [ ] **Step 5: Commit** with message `feat(app): family members and consent on Android`.

---

### Task 10: Android — per-member verdicts, claims and explanation on the result screen *(parallelisable with Task 12)*

**Files:**
- Create: `apps/app/lib/features/analysis/presentation/member_verdict_card.dart`, `.../claims_section.dart`, `.../explanation_card.dart`, `apps/app/lib/features/analysis/presentation/reason_text.dart`, `apps/app/test/features/analysis/member_verdicts_fixture_test.dart`
- Modify: `apps/app/lib/features/analysis/presentation/result_screen.dart` (Plan 3)

**Interfaces:**
- `String reasonText(AppLocalizations l, ReasonOut r)` maps `code` and `params` to `reason.<code>`, translating `allergen`, `alert` and `claim` params through their key groups. An unknown code falls back to `reason.unknown_code`, and is logged to Sentry without health data.
- `MemberVerdictCard(verdict)`:
  - Colour token per status, `verdict.for_member`, then `top_reason` as the one-line "why".
  - Expanding shows all reasons.
  - `unknown` uses the grey token and the "Label unclear" text.
- `ClaimsSection`: one row per claim with its verdict chip.
- `ExplanationCard`: hidden when `source == "unavailable"`. Always shows `verdict.disclaimer`.

- [ ] **Step 1: Write the failing fixture test.** `member_verdicts_fixture_test.dart` loads `packages/test-fixtures/expected/sf_biscuit.*.json` into an `AnalyzeResponse`. For each member it asserts:
  - The card colour equals `AppTokens.verdict[status]`.
  - The headline text equals `l.verdictForMember(statusLabel, name)`.
  - The "why" line equals `reasonText(l, top_reason)`.
  - The unknown case shows "Label unclear" and is never green.
- [ ] **Step 2: Run it to verify it fails.** `flutter test test/features/analysis`.
- [ ] **Step 3: Implement** the widgets and wire them into `result_screen.dart`.
- [ ] **Step 4: Run the tests to verify they pass**, plus `flutter analyze`.
- [ ] **Step 5: Commit** with message `feat(app): per-member verdict cards, claims and explanation`.

---

### Task 11: Web — members and consent *(parallelisable with Task 9)*

**Files:**
- Create:
  - `apps/web/src/app/[locale]/(app)/members/page.tsx`, `.../members/new/page.tsx`, `.../members/[id]/page.tsx`
  - `apps/web/src/features/members/{api/members.ts, components/MemberForm.tsx, components/ConsentDialog.tsx, components/MembersList.tsx, hooks/useMembers.ts}`
  - `apps/web/tests/features/members/MemberForm.test.tsx`, `apps/web/tests/features/members/ConsentDialog.test.tsx`

**Interfaces:**
- Consumes `@smartnutri/api-client` operations `members_*` and `consents_*`.
- `memberFormSchema` (zod) mirrors `MemberIn`'s limits:
  - name 1–40
  - birth year 1900–current year
  - height 30–250, weight 2–300
  - ≤10 allergens
  - custom alerts from the 5 keys
- Messages come from `packages/i18n`.
- `ConsentDialog` behaves exactly like Android's `ConsentSheet`.

- [ ] **Step 1: Write failing Vitest tests:** `MemberForm.test.tsx`:
  - "submits normalised other allergen": "Kiwi" → mutation payload `allergens: ["kiwi"]`.
  - "opens consent dialog before saving conditions".
  - "shows member_limit error text from i18n".
- [ ] **Step 2: Run them to verify they fail.** `pnpm --filter @smartnutri/web test members`.
- [ ] **Step 3: Implement** the pages (client components only where forms need them), hooks via TanStack Query and the generated client.
- [ ] **Step 4: Run the tests to verify they pass**, plus `pnpm --filter @smartnutri/web lint typecheck`.
- [ ] **Step 5: Commit** with message `feat(web): family members and consent`.

---

### Task 12: Web — per-member verdicts, claims and explanation *(parallelisable with Task 10)*

**Files:**
- Create: `apps/web/src/features/analysis/components/{MemberVerdictCard.tsx, ClaimsSection.tsx, ExplanationCard.tsx}`, `apps/web/src/features/analysis/reasonText.ts`, `apps/web/tests/features/analysis/memberVerdicts.fixtures.test.tsx`, `apps/web/e2e/family-verdict.spec.ts`
- Modify: the Plan 3 result page `apps/web/src/app/[locale]/(app)/product/[id]/page.tsx`

**Interfaces:**
- `reasonText(t, reason)` has the same mapping rules as Android's `reasonText`.
- The components render only API data. The colour comes from the token CSS variables `--verdict-<status>`.

- [ ] **Step 1: Write failing tests:**
  - `memberVerdicts.fixtures.test.tsx` runs the same assertions as Task 10 over `expected/sf_biscuit.*.json`: colour variable, headline, "why" line, and "Label unclear" never green.
  - `family-verdict.spec.ts` (Playwright, against the API with seeded data): add member "Dad" (diabetes, after consent) → open the sugar-free biscuit result → Dad's card shows the avoid colour and the misleading-claim line.
- [ ] **Step 2: Run them to verify they fail.** `pnpm --filter @smartnutri/web test analysis` and `pnpm --filter @smartnutri/web e2e family-verdict`.
- [ ] **Step 3: Implement** the components and wire them into the result page.
- [ ] **Step 4: Run the tests to verify they pass**, plus lint and typecheck.
- [ ] **Step 5: Commit** with message `feat(web): per-member verdict cards, claims and explanation`.

---

### Task 13: Slice gate — safety review and parity

**Files:**
- Modify: `docs/FEATURE_PARITY.md` (F2, F6, F7, F13, F16 → ✅ for API, Android and web only when their tests pass)

- [ ] **Step 1: Run everything.** `just test` and `just lint`. Expected: all green.
- [ ] **Step 2: Run the `nutrition-safety-reviewer`** on the whole slice diff, focusing on the result-screen UI on both clients (colours, "unknown" never green, disclaimer present, no names sent to the LLM). Fix blocking issues in the owning task's files and re-run the affected tests.
- [ ] **Step 3: Update the `FEATURE_PARITY.md` statuses.** Note any platform still pending, with a reason. Never mark ✅ on one client only.
- [ ] **Step 4: Commit** with message `docs: M3 parity status`.
