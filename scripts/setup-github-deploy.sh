#!/usr/bin/env bash
# One-time (idempotent) Google Cloud setup so GitHub Actions can deploy the dev API + web
# to Cloud Run with keyless Workload Identity Federation (no service-account keys).
#
# Run it yourself from the repo root, AFTER scripts/push-secrets.sh:
#   bash scripts/setup-github-deploy.sh
# It prints the names of what it creates and the two (non-secret) values the workflow uses.
# Safe to re-run.
set -euo pipefail

export CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri
PROJECT=smartnutri-513518
PROJECT_NUMBER=609833507754
REGION=asia-south1
AR_REPO=smartnutri
GITHUB_REPO=pritirokade14/Smart-Nutri
POOL=github
PROVIDER=github-smartnutri

API_SA_NAME=smartnutri-api-dev
WEB_SA_NAME=smartnutri-web-dev
DEPLOYER_NAME=github-deployer
API_SA="$API_SA_NAME@$PROJECT.iam.gserviceaccount.com"
WEB_SA="$WEB_SA_NAME@$PROJECT.iam.gserviceaccount.com"
DEPLOYER="$DEPLOYER_NAME@$PROJECT.iam.gserviceaccount.com"
SECRETS=(callmissed-api-key-dev supabase-secret-key-dev database-url-dev)

active_project="$(gcloud config get-value project 2>/dev/null)"
if [[ "$active_project" != "$PROJECT" ]]; then
  echo "gcloud config 'smartnutri' points at '$active_project', expected '$PROJECT'" >&2
  exit 1
fi

ensure_sa() { # name display-name
  if gcloud iam service-accounts describe "$1@$PROJECT.iam.gserviceaccount.com" --project "$PROJECT" >/dev/null 2>&1; then
    echo "service account $1: exists"
  else
    gcloud iam service-accounts create "$1" --project "$PROJECT" --display-name "$2" >/dev/null
    echo "service account $1: created"
  fi
}

echo "== APIs =="
gcloud services enable iamcredentials.googleapis.com sts.googleapis.com --project "$PROJECT"
echo "iamcredentials + sts: enabled"

echo "== Runtime service accounts =="
ensure_sa "$API_SA_NAME" "SmartNutri API (dev runtime)"
ensure_sa "$WEB_SA_NAME" "SmartNutri web (dev runtime, no roles)"
# IAM changes can lag a few seconds after creating a service account.
sleep 5
for s in "${SECRETS[@]}"; do
  gcloud secrets add-iam-policy-binding "$s" --project "$PROJECT" \
    --member "serviceAccount:$API_SA" --role roles/secretmanager.secretAccessor >/dev/null
  echo "secret $s: secretAccessor -> $API_SA_NAME"
done

echo "== Deployer service account =="
ensure_sa "$DEPLOYER_NAME" "GitHub Actions deployer (dev)"
sleep 5
gcloud projects add-iam-policy-binding "$PROJECT" \
  --member "serviceAccount:$DEPLOYER" --role roles/run.admin --condition=None >/dev/null
echo "project: run.admin -> $DEPLOYER_NAME"
gcloud artifacts repositories add-iam-policy-binding "$AR_REPO" --project "$PROJECT" --location "$REGION" \
  --member "serviceAccount:$DEPLOYER" --role roles/artifactregistry.writer >/dev/null
echo "repository $AR_REPO: artifactregistry.writer -> $DEPLOYER_NAME"
for sa in "$API_SA" "$WEB_SA"; do
  gcloud iam service-accounts add-iam-policy-binding "$sa" --project "$PROJECT" \
    --member "serviceAccount:$DEPLOYER" --role roles/iam.serviceAccountUser >/dev/null
  echo "$sa: serviceAccountUser -> $DEPLOYER_NAME"
done

echo "== Workload Identity Federation =="
if gcloud iam workload-identity-pools describe "$POOL" --project "$PROJECT" --location global >/dev/null 2>&1; then
  echo "pool $POOL: exists"
else
  gcloud iam workload-identity-pools create "$POOL" --project "$PROJECT" --location global \
    --display-name "GitHub Actions" >/dev/null
  echo "pool $POOL: created"
fi

# Only this repo, only the main branch, may exchange a GitHub token.
PROVIDER_ARGS=(
  --project "$PROJECT" --location global --workload-identity-pool "$POOL"
  --issuer-uri "https://token.actions.githubusercontent.com"
  --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref,attribute.repository_owner=assertion.repository_owner"
  --attribute-condition "assertion.repository == '$GITHUB_REPO' && assertion.ref == 'refs/heads/main'"
)
if gcloud iam workload-identity-pools providers describe "$PROVIDER" \
  --project "$PROJECT" --location global --workload-identity-pool "$POOL" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers update-oidc "$PROVIDER" "${PROVIDER_ARGS[@]}" >/dev/null
  echo "provider $PROVIDER: updated"
else
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" "${PROVIDER_ARGS[@]}" \
    --display-name "SmartNutri GitHub" >/dev/null
  echo "provider $PROVIDER: created"
fi

gcloud iam service-accounts add-iam-policy-binding "$DEPLOYER" --project "$PROJECT" \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/attribute.repository/$GITHUB_REPO" >/dev/null
echo "deployer: workloadIdentityUser <- repo $GITHUB_REPO (main branch only, via the provider condition)"

echo
echo "Done. Values used by .github/workflows/deploy-dev.yml (not secrets):"
echo "  workload_identity_provider: projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/providers/$PROVIDER"
echo "  service_account:            $DEPLOYER"
