# Plan 8 (M6): Hardening and Launch

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Order:**
> - Code tasks (1–7) first. Within them, the Android and web steps of Tasks 1–4 can run in parallel (`flutter-builder` ∥ `web-builder`) after each API step and `just contract`.
> - Then infra and launch tasks (8–16), in order.
>
> **Every step marked `USER:` only the user can do** (payments, legal acceptance, identity verification, store and Meta approvals, passwords and keystores). The agent stops there, explains exactly what to click or run, and waits.

**Goal:** Make SmartNutri v1 safe and DPDP-ready (consent, deletion, retention, disclaimers, no health data in telemetry), pass a security review, deploy API and web to production on Cloud Run Mumbai, and put the Android app on the Play Store closed-testing track.

**Architecture:**
- Compliance features are API-first, mirrored on both clients:
  - a consent gate dependency;
  - `DELETE /v1/me` with storage and auth cleanup;
  - a scheduled retention Cloud Run Job.
- Telemetry goes through allow-listing wrappers (PostHog) and scrubbing hooks (Sentry).
- **Production:**
  - Supabase `smartnutri-prod` (Mumbai, Pro).
  - Cloud Run services `smartnutri-api` and `smartnutri-web` (asia-south1, min-instances 1, max 4), with images in `asia-south1-docker.pkg.dev/smartnutri-513518/smartnutri`.
  - Secrets in Secret Manager (asia-south1), written by **the user** with `scripts/push-secrets.sh`.
- Phone OTP: the Supabase Send-SMS hook calls our API, which sends a CallMissed WhatsApp AUTHENTICATION template. It is enabled only after Meta approves the template.

**Tech Stack:**
- FastAPI, Alembic and Supabase.
- `gcloud` with `CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri` for **every** gcloud command, plus Docker (`--platform linux/amd64`).
- Flutter release builds and Next.js standalone.
- Sentry, PostHog and the `standardwebhooks` Python library.

**Spec:** `docs/superpowers/specs/2026-11-02-smartnutri-v1-design.md` (§2 F1, F11; §5; §7; §8 M6). Also `SECURITY.md`, `docs/SETUP_ACCOUNTS.md`, `docs/research/2026-11-02-data-standards-regulation.md` and ADR 0012.

## Global Constraints

- **gcloud:**
  - Every command is prefixed `CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri` (project `smartnutri-513518`, region `asia-south1`).
  - **Never** change the machine's default gcloud configuration (it belongs to other companies).
- **Secrets:**
  - Claude never prints or reads secret values aloud.
  - Claude's automated Secret Manager writes are blocked by policy, so secrets are pushed **by the user** running `scripts/push-secrets.sh`.
  - Cloud Run reads secrets only via `--set-secrets`.
- **Naming contract (Plan 2), used verbatim:** `app.main:create_app()`, `get_settings()`, `current_account → AccountContext`, `get_session`, `ApiError(code, status, message_key)`, `limit(bucket)`, `StorageClient`, routers at `/v1/<f>`, `operation_id = <feature>_<action>`. Tables: accounts, members, consents, products, off_product_cache, scans, meal_logs, product_reports.
- **Consent purposes and versions:**
  - Purposes: `terms`, `health_data`, `ai_processing`.
  - Current versions come from env `CONSENT_VERSION_TERMS`, `CONSENT_VERSION_HEALTH_DATA` and `CONSENT_VERSION_AI_PROCESSING` (initial value `2026-11-v1`).
  - A missing or withdrawn consent, or an older version → `403 {"error":{"code":"consent_required","purposes":[…]}}`.
- **Retention:**
  - Label photos (`labels/…`) are deleted after **30 days**, and `scans.image_path` is set to NULL.
  - Voice answers (`voice/…`) are deleted after **24 hours**.
- **Account deletion:**
  - Removes members, meal_logs, scans (and their storage objects), consents, product_reports, voice objects and the `accounts` row, then the Supabase auth user.
  - Products the user contributed keep their data, with `created_by = NULL`.
  - Idempotent: returns `204`.
- **Telemetry:**
  - PostHog receives only allow-listed events and properties. **Never** conditions, allergens, diet, verdict reasons, statuses per member, nutrients, member names, emails or IDs other than a hashed distinct id.
  - Sentry has `send_default_pii = False`, plus scrubbing of headers, cookies, bodies and query tokens.
- **Disclaimer:** every surface that shows a verdict, explanation or voice answer shows `disclaimer.not_medical_advice`. Public pages show "calculated by SmartNutri" next to Nutri-Score.
- **Prod Cloud Run:**
  - `--min-instances=1 --max-instances=4 --cpu=1 --memory=1Gi` for the API and `--memory=512Mi` for web.
  - Service accounts `smartnutri-api-sa` and `smartnutri-web-sa` with least privilege.
- **Testing track:** Play Console personal account → internal testing → closed testing with **≥ 12 testers for 14 consecutive days**, then apply for production.

## Review Focus

1. **Deleting an account while a voice answer or label photo is still in storage.** Storage objects under the account prefix must go too, and a second `DELETE /v1/me` must still return 204. Owned by Task 2 (`test_delete_me_removes_storage_and_is_idempotent`).
2. **A consent withdrawn mid-session.** The next `/v1/analyze` or `/v1/voice/ask` call is refused with `consent_required`, and the clients route back to the consent screen. Owned by Task 1.
3. **Telemetry leaking health data via free-form properties** (e.g. `track("scan_completed", {"reason": "allergen_contains"})`). The property is dropped and a dev warning logged. Owned by Task 4.
4. **A Send-SMS hook call with a bad or missing signature, or replayed outside the timestamp tolerance.** Expect a 401 with no WhatsApp send; the OTP and phone number are never logged. Owned by Task 5.
5. **The retention job meeting a scan whose storage object is already gone.** It completes without error and still nulls `image_path`. Owned by Task 3.

## File Map

```
apps/api/
  app/core/consent.py                         # Task 1 require_consents()
  app/features/consents/{router,service,schemas}.py   # Task 1 (extend: GET, withdraw)
  app/features/me/{router,service}.py         # Task 2 DELETE /v1/me
  app/integrations/supabase_admin.py          # Task 2 delete_user()
  app/integrations/storage.py                 # Tasks 2–3: list_prefix(), delete_paths() if missing
  app/jobs/retention.py                       # Task 3
  app/integrations/posthog.py                 # Task 4 allow-list
  app/core/observability.py                   # Task 4 Sentry init + scrub
  app/features/auth_hooks/{router,service}.py # Task 5 POST /v1/auth/hooks/send-sms
  tests/api/{test_consent_gate,test_delete_me,test_send_sms_hook,test_security}.py
  tests/unit/{test_retention,test_telemetry}.py
apps/app/lib/features/{consent,settings}/…    # Tasks 1–2
apps/app/lib/core/telemetry/analytics.dart    # Task 4
apps/app/android/app/build.gradle.kts         # Task 12 release signing + applicationId
apps/web/src/app/[locale]/(public)/{privacy,terms}/page.tsx   # Task 1
apps/web/src/features/{consent,settings}/…    # Tasks 1–2
apps/web/src/lib/telemetry/analytics.ts       # Task 4
apps/web/e2e/security-headers.spec.ts         # Task 6
packages/i18n/messages/*.json                 # Tasks 1, 2, 5
scripts/push-secrets.sh                       # Task 9 (written by Claude, RUN BY USER)
scripts/load_smoke.py                         # Task 7
scripts/clinician_review_sheet.py             # Task 15
docs/launch/{data-safety.md, store-listing.md, clinician-review.md, RELEASE_CHECKLIST.md, privacy-policy.md, terms.md}
```

---

### Task 1: Consent gate, withdrawal and policy pages (F11)

**Files:**
- Create: `apps/api/app/core/consent.py`, `apps/api/tests/api/test_consent_gate.py`, `apps/web/src/app/[locale]/(public)/{privacy,terms}/page.tsx`, `docs/launch/{privacy-policy.md, terms.md}`
- Modify:
  - `apps/api/app/features/consents/*` (add `GET /v1/consents` `consents_list`; `POST /v1/consents` accepts `granted: bool`)
  - the analyze, scans, voice and meals routers (add the dependency)
  - the clients' consent screens (exist from M1; extend them for re-consent and withdraw)

**Interfaces:**

```python
REQUIRED = {"analyze": ("terms","health_data"), "scans": ("terms","health_data","ai_processing"),
            "voice": ("terms","health_data","ai_processing"), "meals": ("terms","health_data")}
def require_consents(*purposes: Literal["terms","health_data","ai_processing"]) -> Callable   # FastAPI dependency
class ConsentState(BaseModel): purpose: str; version: str; granted: bool; current_version: str; needs_update: bool
class ConsentWrite(BaseModel): purpose: Literal["terms","health_data","ai_processing"]; version: str; granted: bool
```

- [ ] **Step 1: Write failing API tests:**
  - `test_analyze_without_health_consent_403_lists_purposes`
  - `test_scan_needs_ai_processing_consent`
  - `test_old_version_requires_reconsent`
  - `test_withdraw_then_analyze_403` (POST `granted=false`, then analyze → 403 `consent_required`)
  - `test_get_consents_reports_needs_update`
  - `test_consent_rows_are_append_only` (withdrawal adds a row with `withdrawn_at`; it never updates the old one)
- [ ] **Step 2: Run them to verify they fail.** Run: `cd apps/api && uv run pytest tests/api/test_consent_gate.py -v`.
- [ ] **Step 3: Implement the API, then `just contract`.**
- [ ] **Step 4: Implement the clients (Android ∥ web):**
  - A `consent_required` error anywhere routes to the consent screen.
  - Settings gets "Manage consent" (withdraw) and links to Privacy and Terms.
  - The web serves `/[locale]/privacy` and `/[locale]/terms` as static public pages, rendered from `docs/launch/*.md` content copied into i18n-free MDX or TSX. Android opens these web URLs.
  - Tests:
    - Flutter: `consent_required_routes_to_consent_screen`, `withdraw_health_consent_calls_api_and_signs_out_of_scanning`
    - Vitest: the same names.
    - Playwright: `privacy and terms pages are public in en/hi/mr`
- [ ] **Step 5:** Claude drafts `docs/launch/privacy-policy.md` and `terms.md`, covering:
  - DPDP notice: purposes, data categories, India processing, retention (30 days photos, 24 h voice), withdrawal, grievance contact, children's profiles managed by an adult, no sale of data, OFF attribution, "not medical advice".

  **USER: have a lawyer review both documents** before the public launch (Task 16 blocks on this).
- [ ] **Step 6: Run all tests, then commit** with message `feat: consent gate, withdrawal and policy pages (F11)`.

---

### Task 2: Account deletion `DELETE /v1/me` (F11)

**Files:**
- Create: `apps/api/app/integrations/supabase_admin.py`, `apps/api/tests/api/test_delete_me.py`
- Modify: `apps/api/app/features/me/{router,service}.py`, `apps/api/app/integrations/storage.py` (add `list_prefix(prefix) -> list[str]` and `delete_paths(paths) -> None` if missing, each with a unit test), the client settings screens

**Interfaces:**

```python
class SupabaseAdmin(Protocol):
    async def delete_user(self, user_id: UUID) -> None   # DELETE {SUPABASE_URL}/auth/v1/admin/users/{id} with SUPABASE_SECRET_KEY; 404 treated as success
def get_supabase_admin() -> SupabaseAdmin            # FastAPI dependency in supabase_admin.py; tests override it
# get_storage() -> StorageClient comes from Plan 2's storage.py (add it there if missing)
@router.delete("", operation_id="me_delete", status_code=204)
async def delete_me(account=Depends(current_account), session=Depends(get_session), storage: StorageClient = Depends(get_storage), admin: SupabaseAdmin = Depends(get_supabase_admin)) -> Response
```

Order:
1. Storage `labels/{account_id}/` (and, superseded by ADR 0020 on 2026-11-04, no voice folder: voice audio is never stored).
2. In one DB transaction: meal_logs → members → scans → product_reports → consents → `UPDATE products SET created_by=NULL WHERE created_by=:id` → accounts.
3. The auth user.

If step 3 fails, return **503** `deletion_incomplete` (the DB is already clean, and a retry finishes the job).

- [ ] **Step 1: Write failing tests:**
  - `test_delete_me_removes_all_rows`
  - `test_delete_me_removes_storage_and_is_idempotent` (second call returns 204)
  - `test_contributed_products_kept_without_owner`
  - `test_auth_admin_failure_returns_503_and_retry_succeeds`
  - `test_other_accounts_data_untouched`
- [ ] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/api/test_delete_me.py -v`.
- [ ] **Step 3: Implement, then `just contract`.**
- [ ] **Step 4: Clients (Android ∥ web):**
  - Settings → "Delete account": a dialog that requires typing `DELETE` (key `settings.delete_confirm_word`), then calls `meDelete`, signs out and shows a goodbye screen.
  - Tests: `delete_requires_typed_confirmation`, `delete_success_signs_out`, `delete_503_shows_retry`.
- [ ] **Step 5: Commit** with message `feat: account deletion with storage and auth cleanup (F11)`.

---

### Task 3: Retention job (30-day photos, 24-hour voice)

> **Note 2026-11-04 (ADR 0020):** the voice part is removed. No voice audio is stored, so the job has no voice window or bucket: `RetentionResult` is `photos_deleted, scans_nulled, tombstones_purged, ...` and there is no `--voice-hours`.

**Files:**
- Create: `apps/api/app/jobs/__init__.py`, `apps/api/app/jobs/retention.py`, `apps/api/tests/unit/test_retention.py`

**Interfaces:**

```python
@dataclass(frozen=True) class RetentionResult: photos_deleted: int; voice_deleted: int; scans_nulled: int
async def run_retention(now: datetime, session: AsyncSession, storage: StorageClient,
                        photo_days: int = 30, voice_hours: int = 24) -> RetentionResult
def main() -> None   # `python -m app.jobs.retention`; logs counts only
```

- [ ] **Step 1: Write failing tests** (fake storage with timestamps, test DB):
  - `test_photos_older_than_30_days_deleted_and_image_path_nulled`
  - `test_photo_29_days_old_kept`
  - `test_voice_older_than_24h_deleted`
  - `test_missing_storage_object_still_nulls_image_path`
  - `test_run_is_idempotent`
- [ ] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/unit/test_retention.py -v`.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the tests to verify they pass.** The deployment happens in Task 10.
- [ ] **Step 5: Commit** with message `feat(api): retention job for label photos and voice answers`.

---

### Task 4: Telemetry without health data (Sentry + PostHog)

**Files:**
- Create: `apps/api/app/core/observability.py`, `apps/api/app/integrations/posthog.py`, `apps/api/tests/unit/test_telemetry.py`, `apps/app/lib/core/telemetry/analytics.dart` (+ test), `apps/web/src/lib/telemetry/analytics.ts` (+ test)
- Modify: `apps/api/app/main.py` (call `init_sentry`), the Flutter `bootstrap.dart` and Next `instrumentation.ts` Sentry init (`sendDefaultPii: false`, `beforeSend` scrubber)

**Interfaces:**

```python
ALLOWED_EVENTS = {"app_opened": set(), "scan_started": {"method"}, "scan_completed": {"method", "found"},
                  "verdicts_shown": {"member_count"}, "meal_logged": set(), "voice_asked": {"language"},
                  "report_submitted": {"reason"}, "share_clicked": {"kind"}, "account_deleted": set()}
def scrub_event(event: dict, hint: dict) -> dict | None   # drops request.data, cookies, headers Authorization/Cookie, query params named *token*/*code*; user → {"id": sha256(account_id)}
def track(distinct_id: UUID, event: str, props: Mapping[str, str | int | bool] = {}) -> None
    # unknown event → ignored + warning; unknown prop keys → dropped; distinct id hashed (sha256 hex)
```

Clients mirror `ALLOWED_EVENTS` exactly: Dart `Analytics.track` and TS `track`.

- [ ] **Step 1: Write failing tests:**
  - API:
    - `test_scrub_removes_auth_header_cookies_body`
    - `test_scrub_hashes_user_id`
    - `test_track_drops_unknown_props` (e.g. `reason="allergen_contains"` on `scan_completed` is dropped)
    - `test_track_ignores_unknown_event`
    - `test_distinct_id_is_hashed`
  - Flutter: `track_drops_unknown_props`
  - Vitest: `track drops unknown props`
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.** Replace every existing direct PostHog or Sentry call with the wrappers: `grep -rn "posthog\|captureEvent" apps/` must show only the wrappers.
- [ ] **Step 4: Run the tests to verify they pass.**
- [ ] **Step 5: Commit** with message `feat: telemetry wrappers with health-data allow-list and Sentry scrubbing`.

---

### Task 5: Send-SMS hook for WhatsApp OTP (code ready, switched off)

**Files:**
- Create: `apps/api/app/features/auth_hooks/{router,service}.py`, `apps/api/tests/api/test_send_sms_hook.py`
- Modify: `apps/api/app/core/config.py` + `.env.example` (`PHONE_OTP_ENABLED=false`, `SUPABASE_SEND_SMS_HOOK_SECRET=`, `CALLMISSED_WHATSAPP_OTP_TEMPLATE=smartnutri_otp`, `CALLMISSED_WHATSAPP_PHONE_NUMBER_ID=`), `apps/api/pyproject.toml` (`standardwebhooks`), the clients' phone-login UI flag (`PHONE_OTP_ENABLED` in `env/*.json`, `NEXT_PUBLIC_PHONE_OTP_ENABLED`)

**Interfaces:**

```python
@router.post("/send-sms", operation_id="auth_hooks_send_sms", include_in_schema=False)   # mounted at /v1/auth/hooks
async def send_sms(request: Request) -> dict   # verifies Standard Webhooks signature (secret "v1,whsec_…"), 5-min tolerance
# body: {"user": {"id", "phone"}, "sms": {"otp"}} → CallMissed POST /api/v1/whatsapp/messages/template
#   {"to": phone, "template": CALLMISSED_WHATSAPP_OTP_TEMPLATE, "language": "en", "components": [OTP body + button params]} with Idempotency-Key = sha256(user.id + otp)
# PHONE_OTP_ENABLED=false → 503 {"error":{"code":"phone_otp_disabled"}}
```

- [ ] **Step 1: Write failing tests:**
  - `test_valid_signature_sends_template_once`
  - `test_bad_signature_401_no_send`
  - `test_replay_outside_tolerance_401`
  - `test_disabled_flag_503`
  - `test_otp_and_phone_never_logged` (`caplog`)
  - `test_callmissed_failure_returns_500_without_details` (Supabase then shows a generic error)
- [ ] **Step 2: Run them to verify they fail.** Run: `uv run pytest tests/api/test_send_sms_hook.py -v`.
- [ ] **Step 3: Implement.** Keep the flag `false`. The client phone tab is hidden unless its flag is true.
- [ ] **Step 4: Run the tests to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(api): Supabase Send-SMS hook via CallMissed WhatsApp OTP (disabled)`.

---

### Task 6: Disclaimer audit and security pass

**Files:**
- Create: `apps/api/tests/api/test_security.py`, `apps/web/e2e/security-headers.spec.ts`, `apps/app/test/compliance/disclaimer_test.dart`, `apps/web/tests/compliance/disclaimer.test.tsx`

- [ ] **Step 1: Write failing tests (API):**
  - `test_cors_rejects_unknown_origin`: no `access-control-allow-origin` for `https://evil.example`.
  - `test_expired_jwt_401`, `test_wrong_audience_jwt_401` and `test_alg_none_jwt_401`.
  - `test_error_body_has_no_exception_text`: force an internal error; the body must equal `{"error":{"code":"internal_error","message_key":"error.internal"}}`.
  - `test_every_expensive_route_has_a_rate_limit`: introspect routes; `scans/label`, `analyze`, `voice/ask`, `products/{id}/reports` and the public endpoints have a `limit(...)` dependency.
  - `test_public_endpoints_expose_no_member_fields`: the JSON keys of `/v1/products/{barcode}/public` and `/v1/methodology` must not include `member`, `verdict`, `allergen_state` or `name` (except the product name).
- [ ] **Step 2: Write failing tests (clients):**
  - Disclaimer:
    - Flutter `every_verdict_surface_shows_disclaimer` pumps the result screen, the voice answer sheet, the history detail and the share card with fixtures, and finds `disclaimer.not_medical_advice` in each.
    - Vitest does the same for the web components.
  - Playwright `security-headers.spec.ts` checks, on `/en` and `/en/scan`:
    - CSP present with `script-src 'nonce-`
    - `x-frame-options: DENY`
    - `referrer-policy: strict-origin-when-cross-origin`
    - session cookies `Secure; SameSite=Lax` (JS-readable by design, ADR 0014); HSTS header present in production
- [ ] **Step 3: Run them, fix every failure** (each fix in the owning module), then rerun until green.
- [ ] **Step 4: Run** `gitleaks git --no-banner --redact .` from the repo root. Expected: `no leaks found`. Then run the `nutrition-safety-reviewer` agent and a whole-branch code review (Opus). Fix the blocking findings.
- [ ] **Step 5: Commit** with message `test: security and disclaimer compliance suite`.

---

### Task 7: Load sanity script

**Files:**
- Create: `scripts/load_smoke.py`

**Interfaces:**

```python
# uv run --with httpx python scripts/load_smoke.py --base-url URL --rps 20 --seconds 60 --barcode 8901063012345
# hits GET /v1/health and GET /v1/products/{barcode}/public; prints p50/p95/max ms, counts by status; exit 1 if p95 > 800 ms or any 5xx
```

- [ ] **Step 1: Write the script.** Use asyncio with `httpx.AsyncClient`, a fixed request rate via `asyncio.sleep` scheduling, and no authenticated or paid endpoints. It **never** calls CallMissed-backed routes.
- [ ] **Step 2: Run it against the dev API** started with `just api`: `uv run --with httpx python scripts/load_smoke.py --base-url http://localhost:8000 --rps 20 --seconds 30 --barcode <a seeded barcode>`. Expected: exit 0, p95 < 800 ms, no 5xx.
- [ ] **Step 3: Commit** with message `chore: load smoke script`. It runs again against prod in Task 10.

---

### Task 8: Production Supabase

- [ ] **Step 1: USER:** in the Supabase dashboard (org **SmartNutri**), create project **`smartnutri-prod`** in **South Asia (Mumbai)**. Upgrade the org to **Pro**: payment is a USER action. Use Supabase's "Generate a password". Use the same security choices as dev: new tables not exposed automatically, automatic RLS on.
- [ ] **Step 2:** Claude copies the prod values into the git-ignored `apps/api/.env.production` the same way as for dev (the copy button → clipboard → file; never printed):
  - `SUPABASE_URL`, `SUPABASE_PROJECT_REF`, `SUPABASE_JWKS_URL`
  - `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`
  - `SUPABASE_DB_PASSWORD`, `DATABASE_URL` (Session pooler, `aws-0-ap-south-1`)

  Run: `cd apps/api && set -a && . ./.env.production && set +a && uv run alembic upgrade head`. Expected: the migration log ends at the head revision with no errors. This includes the storage bucket `label-photos` (private; no voice bucket since ADR 0020) if it are created by migrations; otherwise add a migration `create_storage_buckets` (`insert into storage.buckets … on conflict do nothing`, with storage RLS policies) and rerun.
- [ ] **Step 3:** Claude configures prod Auth:
  - Site URL `https://<domain>` (from Task 11; use the Cloud Run web URL until then).
  - Redirect URLs `https://<domain>/**` and `com.smartnutri.app://login-callback`.
  - Email provider on.
  - Google provider: the client IDs as in dev. **USER pastes the client secret** (Claude never types secrets).
- [ ] **Step 4:** Verify: `DB=$(grep '^DATABASE_URL=' apps/api/.env.production | cut -d= -f2- | sed 's/+psycopg//') uv run --with 'psycopg[binary]' python -c "import os,psycopg; print(psycopg.connect(os.environ['DB'], connect_timeout=15).execute('select version()').fetchone()[0][:15])"`. Expected: `PostgreSQL 17.x`.

---

### Task 9: Secrets to Secret Manager (script by Claude, run by USER)

**Files:**
- Create: `scripts/push-secrets.sh`

**Interface:**

```
bash scripts/push-secrets.sh <dev|prod> [--dry-run]
  reads apps/api/.env (dev) or apps/api/.env.production (prod)
  for each of: CALLMISSED_API_KEY SUPABASE_SECRET_KEY DATABASE_URL GOOGLE_WEB_CLIENT_SECRET SUPABASE_SEND_SMS_HOOK_SECRET SENTRY_DSN POSTHOG_API_KEY
    secret name = lowercase-with-dashes + "-<env>"   (e.g. callmissed-api-key-prod)
    skip if empty; create with --replication-policy=user-managed --locations=asia-south1 if missing, else versions add
    value piped via --data-file=- ; NEVER echoed
  prints "<name>: created|updated|skipped(empty)"; --dry-run prints names only and makes no gcloud calls
  uses CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri; `set -euo pipefail`; exits non-zero on any gcloud failure
```

- [ ] **Step 1: Write the script.** Check it: `bash -n scripts/push-secrets.sh && bash scripts/push-secrets.sh prod --dry-run`. Expected: 7 lines of `<name>-prod`, with no values printed.
- [ ] **Step 2: Commit** with message `chore: push-secrets script (run by the user)`.
- [ ] **Step 3: USER:** run `! bash scripts/push-secrets.sh prod` in Claude Code.
  Expected: each name prints `created` or `updated`. Claude then verifies with `CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri gcloud secrets list --format="value(name)"` (names only).

---

### Task 10: Production deploy on Cloud Run (API, web, retention job)

- [ ] **Step 1:** Service accounts and permissions:

```bash
export CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri
gcloud services enable cloudscheduler.googleapis.com
gcloud iam service-accounts create smartnutri-api-sa --display-name="SmartNutri API"
gcloud iam service-accounts create smartnutri-web-sa --display-name="SmartNutri web"
for s in $(gcloud secrets list --format="value(name)" --filter="name~-prod$"); do
  gcloud secrets add-iam-policy-binding "$s" --member="serviceAccount:smartnutri-api-sa@smartnutri-513518.iam.gserviceaccount.com" --role=roles/secretmanager.secretAccessor >/dev/null; done
gcloud auth configure-docker asia-south1-docker.pkg.dev --quiet
```

  Expected: no errors. The secret bindings print nothing.
- [ ] **Step 2:** Build and deploy the API. Load non-secret values first: `set -a; . apps/api/.env.production; set +a`. Then set `R=asia-south1-docker.pkg.dev/smartnutri-513518/smartnutri` and `TAG=$(git rev-parse --short HEAD)`:

```bash
docker build --platform linux/amd64 -f apps/api/Dockerfile -t $R/api:$TAG . && docker push $R/api:$TAG
gcloud run deploy smartnutri-api --image $R/api:$TAG --region asia-south1 --service-account smartnutri-api-sa@smartnutri-513518.iam.gserviceaccount.com \
  --min-instances 1 --max-instances 4 --cpu 1 --memory 1Gi --allow-unauthenticated \
  --set-env-vars "ENVIRONMENT=prod,ALLOWED_ORIGINS=$WEB_ORIGIN,SUPABASE_URL=$SUPABASE_URL,SUPABASE_JWKS_URL=$SUPABASE_JWKS_URL,PHONE_OTP_ENABLED=false" \
  --set-secrets CALLMISSED_API_KEY=callmissed-api-key-prod:latest,SUPABASE_SECRET_KEY=supabase-secret-key-prod:latest,DATABASE_URL=database-url-prod:latest,SENTRY_DSN=sentry-dsn-prod:latest,POSTHOG_API_KEY=posthog-api-key-prod:latest
curl -s https://<api-run-url>/v1/health
```

  `WEB_ORIGIN` is the web Cloud Run URL (from Step 3) until Task 11 gives the domain; deploy once, then redeploy after Step 3 with the real origin. Expected: the `/health` response defined by Plan 2 (HTTP 200). Secrets only ever come in via `--set-secrets`.
- [ ] **Step 3:** Build and deploy web. `NEXT_PUBLIC_*` are build args; there are no secrets in web. Put the four public prod values in the git-ignored `apps/web/.env.production.local` and load them: `set -a; . apps/web/.env.production.local; set +a`.

```bash
docker build --platform linux/amd64 -f apps/web/Dockerfile --build-arg NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL --build-arg NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=$NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY \
  --build-arg NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL --build-arg NEXT_PUBLIC_POSTHOG_KEY=$NEXT_PUBLIC_POSTHOG_KEY -t $R/web:$TAG . && docker push $R/web:$TAG
gcloud run deploy smartnutri-web --image $R/web:$TAG --region asia-south1 --service-account smartnutri-web-sa@smartnutri-513518.iam.gserviceaccount.com \
  --min-instances 1 --max-instances 4 --memory 512Mi --allow-unauthenticated
```

  Expected: `/en` returns 200, and `/en/how-we-score` returns 200 with the CSP header.
- [ ] **Step 4:** Retention job and daily schedule (02:30 IST):

```bash
gcloud run jobs create smartnutri-retention --image $R/api:$TAG --region asia-south1 --service-account smartnutri-api-sa@smartnutri-513518.iam.gserviceaccount.com \
  --command python --args -m,app.jobs.retention --set-secrets DATABASE_URL=database-url-prod:latest,SUPABASE_SECRET_KEY=supabase-secret-key-prod:latest --set-env-vars "SUPABASE_URL=$SUPABASE_URL"
gcloud run jobs execute smartnutri-retention --region asia-south1 --wait
gcloud scheduler jobs create http smartnutri-retention-daily --location asia-south1 --schedule "30 2 * * *" --time-zone "Asia/Kolkata" \
  --uri "https://run.googleapis.com/v2/projects/smartnutri-513518/locations/asia-south1/jobs/smartnutri-retention:run" --http-method POST \
  --oauth-service-account-email smartnutri-api-sa@smartnutri-513518.iam.gserviceaccount.com
gcloud projects add-iam-policy-binding smartnutri-513518 --member="serviceAccount:smartnutri-api-sa@smartnutri-513518.iam.gserviceaccount.com" --role=roles/run.invoker
```

  Expected: the execution succeeds, and the logs show `photos_deleted=0 scans_nulled=0 tombstones_purged=0` (no voice count since ADR 0020).
- [ ] **Step 5:** Run `uv run --with httpx python scripts/load_smoke.py --base-url https://<api-run-url> --rps 20 --seconds 60 --barcode <seeded>`. Expected: exit 0. Record the numbers in `docs/launch/RELEASE_CHECKLIST.md`.

---

### Task 11: Domain and HTTPS

- [ ] **Step 1: USER:** buy the domain (e.g. `smartnutri.in`) and verify it in Google Search Console with the same Google account (the project owner's Google account). Claude gives the DNS TXT value from the Search Console screen.
- [ ] **Step 2: Check Cloud Run domain-mapping support:** `CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri gcloud beta run domain-mappings create --service smartnutri-web --domain app.<domain> --region asia-south1`.
  - **If it succeeds:** also map `api.<domain>` to `smartnutri-api`. **USER** adds the printed DNS records.
  - **If it reports the region is unsupported:** use a global external Application Load Balancer:
    - a serverless NEG per service (`gcloud compute network-endpoint-groups create smartnutri-web-neg --region asia-south1 --network-endpoint-type serverless --cloud-run-service smartnutri-web`, and the same for the API);
    - backend services, a URL map routing `app.<domain>` → web and `api.<domain>` → api;
    - a Google-managed certificate for both hosts, a target HTTPS proxy, and a global forwarding rule on a reserved global IP;
    - **USER** adds the A records for that IP.
- [ ] **Step 3:** Once the certificate is `ACTIVE`, update:
  - API `ALLOWED_ORIGINS=https://app.<domain>`
  - the web build arg `NEXT_PUBLIC_API_BASE_URL=https://api.<domain>` (rebuild and redeploy)
  - the Supabase prod Site URL and redirect URLs
  - the Google OAuth web client: JS origin `https://app.<domain>`

  Expected: `curl -sI https://app.<domain>/en` returns 200 with HSTS, and Google login works end to end on prod web.

---

### Task 12: Android release build

- [ ] **Step 1:** In `apps/app/android/app/build.gradle.kts`:
  - set `applicationId = "com.smartnutri.app"` and `namespace = "com.smartnutri.app"` if Plan 2 has not already;
  - add a `release` `signingConfig` read from `android/key.properties` (git-ignored);
  - set the version from `pubspec.yaml` (`1.0.0+1`).
- [ ] **Step 2: USER:** create the upload keystore and key file. You choose and keep the passwords; Claude never sees them.

```bash
keytool -genkeypair -v -keystore ~/smartnutri-upload.jks -keyalg RSA -keysize 4096 -validity 10000 -alias upload
# then create apps/app/android/key.properties with storePassword, keyPassword, keyAlias=upload, storeFile=/Users/apple/smartnutri-upload.jks
```

- [ ] **Step 3:** Build: `cd apps/app && flutter build appbundle --release --dart-define-from-file=env/prod.json`. Expected: `build/app/outputs/bundle/release/app-release.aab`. `env/prod.json` holds prod public values only.
- [ ] **Step 4:** Print the upload certificate SHA-1: `keytool -list -v -keystore ~/smartnutri-upload.jks -alias upload | grep SHA1`. **USER** types the store password.

---

### Task 13: Google Play Console (personal account)

- [ ] **Step 1: USER:** at play.google.com/console, sign up as **Personal**, pay **$25**, and complete **identity verification** and any device verification.
- [ ] **Step 2:** Claude drafts:
  - `docs/launch/store-listing.md`: app name "SmartNutri AI", short and full description in en and hi, category Health & Fitness, contact email placeholder, privacy policy URL `https://app.<domain>/en/privacy`, and a screenshot list captured from the emulator with `adb exec-out screencap -p`.
  - `docs/launch/data-safety.md`: the Data safety answers:
    - **collected:** email, user IDs, health info (conditions, allergies, diet), photos (labels), audio (voice questions, not stored beyond 24 h), app activity;
    - **processed in India:** yes;
    - **encrypted in transit:** yes;
    - **deletion request:** in-app plus a web URL;
    - **not shared with third parties for ads:** yes;
    - **no ads.**
- [ ] **Step 3: USER:** create the app ("SmartNutri AI", default language English (India), App, Free). Fill in:
  - the store listing from the draft;
  - the content rating questionnaire;
  - target audience **18+**;
  - **Data safety** from the draft;
  - the **Health apps declaration** (a nutrition and wellness information app, **not a medical device**, with the disclaimer shown);
  - ads: none;
  - the privacy policy URL.
- [ ] **Step 4: USER:** upload `app-release.aab` to **Internal testing** and accept **Play App Signing**.
  Claude then reads the **app signing key SHA-1** shown in Play Console → App integrity.
- [ ] **Step 5:** Claude creates two more Android OAuth clients in Google Cloud: `smartnutri-android-upload` (upload SHA-1) and `smartnutri-android-play` (Play signing SHA-1), both with package `com.smartnutri.app`. Add both client IDs to Supabase **prod** Google provider's Client IDs (comma list).
  Expected: Google sign-in works on the Play-installed internal build.
- [ ] **Step 6: USER:** when the build is ready for real people, create the **Closed testing** track, add **12+ tester emails**, and share the opt-in link. **Keep at least 12 testers opted in for 14 consecutive days**, then apply for production access in Play Console.

---

### Task 14: Google OAuth production publish and WhatsApp OTP enablement

- [ ] **Step 1: USER:** in Google Auth Platform (project `smartnutri-513518`):
  - **Branding:** homepage `https://app.<domain>`, privacy policy URL, terms URL, authorised domain `<domain>` (verified in Task 11).
  - **Audience → Publish app.** Scopes stay `openid email profile` (non-sensitive), so no Google verification review is expected; adding a logo can trigger brand review, so skip the logo for v1.
- [ ] **Step 2: USER:** in the CallMissed console (the project's CallMissed account):
  - connect the WhatsApp Business Account (Meta Embedded Signup);
  - submit an **AUTHENTICATION** template `smartnutri_otp` with an OTP button (`one_tap` with package `com.smartnutri.app` and the app signature hash, else `copy_code`).

  Claude computes the 11-character app signature hash from the Play signing certificate and gives it to the user. Meta approval: **USER waits.**
- [ ] **Step 3** (after approval):
  - **USER:** in Supabase prod → Auth → Hooks, enable **Send SMS** with HTTPS URL `https://api.<domain>/v1/auth/hooks/send-sms`, and generate the hook secret. **USER** adds it to `apps/api/.env.production` as `SUPABASE_SEND_SMS_HOOK_SECRET` and runs `! bash scripts/push-secrets.sh prod`.
  - **USER:** enable the **Phone** provider.
  - Claude redeploys the API with `PHONE_OTP_ENABLED=true` and `--set-secrets SUPABASE_SEND_SMS_HOOK_SECRET=supabase-send-sms-hook-secret-prod:latest`, and rebuilds the clients with the phone flag on.
  - Expected: a test phone number receives the WhatsApp OTP and logs in on both clients.
- [ ] **Step 4: USER:** CallMissed plan decision for launch traffic (the current Enterprise account, or Starter/Pro). Raise the `smartnutri-prod` key budget cap above ₹10,000 if needed.

---

### Task 15: Clinician review sheet

**Files:**
- Create: `scripts/clinician_review_sheet.py`, `docs/launch/clinician-review.md` (generated)

- [ ] **Step 1: Write the script.** It loads `apps/api/app/scoring/data/thresholds.yaml` (via `app.scoring.load_config`) and writes a Markdown table with one row per threshold: path, value, unit, source (from `methodology()` sources), the question for the clinician ("Is this appropriate for Indian adults/children?"), and blank "Approved / Change to / Signed" columns.
  Run: `cd apps/api && uv run python ../../scripts/clinician_review_sheet.py > ../../docs/launch/clinician-review.md`. Expected: one row per numeric threshold, none missing (the script asserts the count equals the number of numeric leaves).
- [ ] **Step 2: Commit** with message `docs: clinician review sheet generated from thresholds.yaml`.
- [ ] **Step 3: USER:** have a qualified dietitian or doctor fill in and sign the sheet.
  Claude then applies the changes with the `scoring-rule` skill (tests and fixtures updated, `nutrition-safety-reviewer` approval). Only after full sign-off may a PR remove the `# PENDING CLINICIAN REVIEW` marker, which turns the methodology banner off.

---

### Task 16: Release checklist and tag

**Files:**
- Create: `docs/launch/RELEASE_CHECKLIST.md`
- Modify: `docs/FEATURE_PARITY.md` (F11 ✅ on all three)

- [ ] **Step 1: Write the checklist** with a status per line:
  - `just test` green; CI green on `v1-rebuild`
  - safety review approved; gitleaks clean
  - **USER:** privacy policy and terms reviewed by a lawyer
  - consent, deletion and retention verified on prod
  - Sentry receives a test error with no PII
  - PostHog shows only allow-listed events
  - load smoke numbers recorded
  - domain HTTPS working
  - Google login on prod web and on the Play internal build
  - closed testing started on the date shown, with the 14-day end date
  - the clinician sheet status
  - phone OTP status (on or off)
  - the ₹1,000 GCP budget alert in place
  - the rollback command (`gcloud run services update-traffic smartnutri-api --to-revisions <prev>=100 --region asia-south1`)
- [ ] **Step 2: Run** `just test && just lint`. Expected: green. Update `FEATURE_PARITY.md`.
- [ ] **Step 3: Commit** with message `docs: v1 release checklist`. Tag locally: `git tag v1.0.0-beta.1`.
- [ ] **Step 4: USER:** approve pushing the branch and tag, and merging `v1-rebuild` → `main`. Claude never pushes or merges without this approval.
