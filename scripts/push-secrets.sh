#!/usr/bin/env bash
# Copy the API secrets into Google Secret Manager (project smartnutri-513518, asia-south1).
#
# RUN BY THE USER, never by Claude (Plan 8 Task 9). From the repo root:
#   bash scripts/push-secrets.sh dev             # reads apps/api/.env
#   bash scripts/push-secrets.sh prod            # reads apps/api/.env.production
#   bash scripts/push-secrets.sh prod --dry-run  # names only; no gcloud calls, no values read
# With no argument it behaves as `dev` (the Plan 2 usage).
#
# Each variable maps to the secret <lowercase-with-dashes>-<env>, e.g. CALLMISSED_API_KEY ->
# callmissed-api-key-prod. Empty variables are skipped. A missing secret is created with
# user-managed replication in asia-south1; an existing one gets a new version. Values are
# piped through stdin (--data-file=-) and never echoed. Output per secret:
# "<name>: created|updated|skipped(empty)".
set -euo pipefail

export CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri
PROJECT=smartnutri-513518
LOCATION=asia-south1

VARS=(
  CALLMISSED_API_KEY
  SUPABASE_SECRET_KEY
  DATABASE_URL
  GOOGLE_WEB_CLIENT_SECRET
  SUPABASE_SEND_SMS_HOOK_SECRET
  SENTRY_DSN
  POSTHOG_API_KEY
)

ENV_NAME="dev"
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    dev | prod) ENV_NAME="$arg" ;;
    --dry-run) DRY_RUN=1 ;;
    *) echo "usage: bash scripts/push-secrets.sh <dev|prod> [--dry-run]" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ "$ENV_NAME" == "prod" ]]; then
  ENV_FILE="$ROOT/apps/api/.env.production"
else
  ENV_FILE="$ROOT/apps/api/.env"
fi

secret_name() {
  printf '%s-%s' "$(printf '%s' "$1" | tr '[:upper:]_' '[:lower:]-')" "$ENV_NAME"
}

if [[ "$DRY_RUN" == 1 ]]; then
  for var in "${VARS[@]}"; do
    secret_name "$var"
    echo
  done
  exit 0
fi

[[ -f "$ENV_FILE" ]] || { echo "missing $ENV_FILE" >&2; exit 1; }

active_project="$(gcloud config get-value project 2>/dev/null)"
if [[ "$active_project" != "$PROJECT" ]]; then
  echo "gcloud config 'smartnutri' points at '$active_project', expected '$PROJECT'" >&2
  exit 1
fi

# Value of KEY from the env file: text after the first '=', surrounding quotes removed.
# Not `source`d, so nothing in the file is executed.
env_value() {
  awk -v key="$1" '
    $0 ~ "^[[:space:]]*" key "[[:space:]]*=" {
      sub(/^[^=]*=/, ""); sub(/^[[:space:]]+/, ""); sub(/[[:space:]]+$/, "")
      if ($0 ~ /^".*"$/ || $0 ~ /^'\''.*'\''$/) $0 = substr($0, 2, length($0) - 2)
      print; exit
    }' "$ENV_FILE"
}

for var in "${VARS[@]}"; do
  name="$(secret_name "$var")"
  value="$(env_value "$var")"
  if [[ -z "$value" ]]; then
    echo "$name: skipped(empty)"
    continue
  fi
  if gcloud secrets describe "$name" --project "$PROJECT" >/dev/null 2>&1; then
    printf '%s' "$value" | gcloud secrets versions add "$name" --project "$PROJECT" \
      --data-file=- >/dev/null
    status="updated"
  else
    printf '%s' "$value" | gcloud secrets create "$name" --project "$PROJECT" \
      --replication-policy=user-managed --locations="$LOCATION" --data-file=- >/dev/null
    status="created"
  fi
  unset value
  echo "$name: $status"
done
