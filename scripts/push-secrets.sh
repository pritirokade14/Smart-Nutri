#!/usr/bin/env bash
# Copy the dev API secrets from apps/api/.env into Google Secret Manager
# (project smartnutri-513518, region asia-south1).
#
# Run it yourself from the repo root:   bash scripts/push-secrets.sh
# It never prints a secret value: only secret names and "ok".
# Re-running adds a new version to each existing secret.
set -euo pipefail

export CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri
PROJECT=smartnutri-513518
LOCATION=asia-south1
ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/apps/api/.env"

# secret name in Secret Manager -> variable name in apps/api/.env
SECRETS=(
  "callmissed-api-key-dev:CALLMISSED_API_KEY"
  "supabase-secret-key-dev:SUPABASE_SECRET_KEY"
  "database-url-dev:DATABASE_URL"
)

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

for pair in "${SECRETS[@]}"; do
  name="${pair%%:*}"
  var="${pair##*:}"
  value="$(env_value "$var")"
  if [[ -z "$value" ]]; then
    echo "$name: $var is empty in apps/api/.env" >&2
    exit 1
  fi
  if gcloud secrets describe "$name" --project "$PROJECT" >/dev/null 2>&1; then
    printf '%s' "$value" | gcloud secrets versions add "$name" --project "$PROJECT" --data-file=- >/dev/null
  else
    printf '%s' "$value" | gcloud secrets create "$name" --project "$PROJECT" \
      --replication-policy=user-managed --locations="$LOCATION" --data-file=- >/dev/null
  fi
  unset value
  echo "$name ok"
done
