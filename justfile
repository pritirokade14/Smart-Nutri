# SmartNutri AI — one place for every common command.
# Install: `brew install just`. List recipes: `just`.
# Recipes marked (Plan N) work once that plan has created the files they use.

set dotenv-load := false

default:
    @just --list

# ---------- setup ----------

# Install all dependencies (Python, JS, Flutter) and git hooks
setup:
    cd apps/api && uv sync
    pnpm install
    cd apps/app && flutter pub get
    pre-commit install

# ---------- run ----------

# Run local Supabase + API + web together (Ctrl-C stops all) (Plan 2)
dev:
    #!/usr/bin/env bash
    set -euo pipefail
    supabase start
    trap 'kill 0' EXIT
    just api & just web & wait

# FastAPI dev server on :8000 (Plan 2)
api:
    cd apps/api && uv run uvicorn app.main:create_app --factory --reload --port 8000

# Next.js dev server on :3000 (Plan 2)
web:
    pnpm --filter @smartnutri/web dev

# Flutter app on a connected Android device/emulator. env/dev.json (git-ignored) holds the
# public dart-defines listed in apps/app/env/example.json, incl. SITE_URL and FEATURE_VOICE
android:
    cd apps/app && flutter run -d android --dart-define-from-file=env/dev.json

# ---------- quality ----------

# All tests
test: test-api test-app test-web

test-api:
    cd apps/api && uv run pytest -q

test-app:
    cd apps/app && flutter test

test-web:
    pnpm --filter @smartnutri/web test

# Playwright end-to-end tests for the web app (Plan 2)
e2e:
    pnpm --filter @smartnutri/web e2e

# Lint + format checks everywhere
lint:
    cd apps/api && uv run ruff check app tests && uv run ruff format --check app tests
    cd apps/app && dart format --set-exit-if-changed lib test && flutter analyze
    pnpm --filter @smartnutri/web lint

# ---------- containers ----------

# Build the API image
docker-api:
    docker build --build-context i18n=packages/i18n/messages -t smartnutri-api apps/api

# Build the web image (repo root is the build context; NEXT_PUBLIC_* are public build args)
docker-web:
    docker build -f apps/web/Dockerfile -t smartnutri-web \
        --build-arg NEXT_PUBLIC_SUPABASE_URL="${NEXT_PUBLIC_SUPABASE_URL:-}" \
        --build-arg NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY="${NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:-}" \
        --build-arg NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL:-}" \
        --build-arg NEXT_PUBLIC_SITE_URL="${NEXT_PUBLIC_SITE_URL:-}" \
        --build-arg NEXT_PUBLIC_POSTHOG_KEY="${NEXT_PUBLIC_POSTHOG_KEY:-}" \
        --build-arg NEXT_PUBLIC_SENTRY_DSN="${NEXT_PUBLIC_SENTRY_DSN:-}" \
        --build-arg NEXT_PUBLIC_FEATURE_PHONE_OTP="${NEXT_PUBLIC_FEATURE_PHONE_OTP:-false}" \
        --build-arg NEXT_PUBLIC_FEATURE_EMAIL_OTP="${NEXT_PUBLIC_FEATURE_EMAIL_OTP:-false}" \
        --build-arg NEXT_PUBLIC_FEATURE_VOICE="${NEXT_PUBLIC_FEATURE_VOICE:-false}" \
        .

# ---------- generated code (never hand-edit the outputs) ----------

# Export OpenAPI from FastAPI and regenerate the Dart + TS clients (Plan 2)
contract:
    cd apps/api && uv run python -m scripts.export_openapi > ../../packages/api-contract/openapi.json.tmp && mv ../../packages/api-contract/openapi.json.tmp ../../packages/api-contract/openapi.json
    cd packages/api-contract/dart && dart pub get && dart run swagger_parser && dart run build_runner build --delete-conflicting-outputs && dart format lib
    pnpm --filter @smartnutri/api-client generate

# Build UI strings: packages/i18n → Flutter ARB (+ type-checked keys for web) (Plan 2)
i18n:
    pnpm --filter @smartnutri/i18n build

# Build design tokens → Dart + CSS variables (Plan 2)
tokens:
    pnpm --filter @smartnutri/design-tokens build

# Regenerate everything generated
generate: contract i18n tokens

# ---------- database ----------

# Apply Alembic migrations (Alembic owns all tables + RLS) (Plan 2)
db-migrate:
    cd apps/api && uv run alembic upgrade head
    cd apps/api && uv run python -m app.jobs.seed_foods

# New migration: just db-revision "add meal_logs"
db-revision message:
    cd apps/api && uv run alembic revision --autogenerate -m "{{message}}"

# ---------- dev deploy (GitHub Actions + Workload Identity Federation) ----------

# One-time: create service accounts, WIF pool/provider and IAM for the GitHub deploy (you run it)
setup-github-deploy:
    bash scripts/setup-github-deploy.sh

# Trigger the dev deploy workflow on main (needs `gh auth login`); it deploys only if tests pass
deploy-dev:
    gh workflow run deploy-dev.yml --ref main
