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
    cd apps/api && uv run fastapi dev app/main.py --port 8000

# Next.js dev server on :3000 (Plan 2)
web:
    pnpm --filter @smartnutri/web dev

# Flutter app on a connected Android device/emulator
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

# ---------- generated code (never hand-edit the outputs) ----------

# Export OpenAPI from FastAPI and regenerate the Dart + TS clients (Plan 2)
contract:
    cd apps/api && uv run python scripts/export_openapi.py > ../../packages/api-contract/openapi.json
    cd packages/api-contract/dart && dart run swagger_parser
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

# New migration: just db-revision "add meal_logs"
db-revision message:
    cd apps/api && uv run alembic revision --autogenerate -m "{{message}}"
