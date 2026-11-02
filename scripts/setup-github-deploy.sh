#!/usr/bin/env bash
# One-time (idempotent) Google Cloud setup so GitHub Actions can deploy the dev API + web
# to Cloud Run with keyless Workload Identity Federation (no service-account keys).
#
# Run it yourself from the repo root, AFTER scripts/push-secrets.sh:
#   bash scripts/setup-github-deploy.sh
# It prints the names of what it creates and the two (non-secret) values the workflow uses.
# Safe to re-run. Run with owner credentials (the smartnutri gcloud config).
set -euo pipefail

export CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri
PROJECT=smartnutri-513518
PROJECT_NUMBER=609833507754
REGION=asia-south1
AR_REPO=smartnutri
GITHUB_REPO=pritirokade14/Smart-Nutri
GITHUB_REPO_ID=1443053989
GITHUB_OWNER_ID=263351064
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

for s in "${SECRETS[@]}"; do
  if ! gcloud secrets describe "$s" --project "$PROJECT" >/dev/null 2>&1; then
    echo "secret $s not found: run scripts/push-secrets.sh first" >&2
    exit 1
  fi
done

# IAM is eventually consistent: wait (up to ~60 s) until a new service account is visible.
wait_sa() { # email

  for _ in $(seq 1 12); do
    gcloud iam service-accounts describe "$1" --project "$PROJECT" >/dev/null 2>&1 && return 0
    sleep 5
  done
  echo "service account $1 not visible after 60 s" >&2
  return 1
}

ensure_sa() { # name display-name
  if gcloud iam service-accounts describe "$1@$PROJECT.iam.gserviceaccount.com" --project "$PROJECT" >/dev/null 2>&1; then
    echo "service account $1: exists"
  else
    gcloud iam service-accounts create "$1" --project "$PROJECT" --display-name "$2" >/dev/null
    echo "service account $1: created"
  fi
  wait_sa "$1@$PROJECT.iam.gserviceaccount.com"
}

echo "== APIs =="
gcloud services enable iam.googleapis.com iamcredentials.googleapis.com sts.googleapis.com --project "$PROJECT"
echo "iam + iamcredentials + sts: enabled"

echo "== Runtime service accounts =="
ensure_sa "$API_SA_NAME" "SmartNutri API (dev runtime)"
ensure_sa "$WEB_SA_NAME" "SmartNutri web (dev runtime, no roles)"
for s in "${SECRETS[@]}"; do
  gcloud secrets add-iam-policy-binding "$s" --project "$PROJECT" \
    --member "serviceAccount:$API_SA" --role roles/secretmanager.secretAccessor --condition=None >/dev/null
  echo "secret $s: secretAccessor -> $API_SA_NAME"
done

echo "== Deployer service account =="
ensure_sa "$DEPLOYER_NAME" "GitHub Actions deployer (dev)"
# No project-level Cloud Run role: remove the broad binding an earlier version of this script added.
if gcloud projects remove-iam-policy-binding "$PROJECT" \
  --member "serviceAccount:$DEPLOYER" --role roles/run.admin --condition=None >/dev/null 2>&1; then
  echo "project: removed run.admin from $DEPLOYER_NAME"
fi
gcloud artifacts repositories add-iam-policy-binding "$AR_REPO" --project "$PROJECT" --location "$REGION" \
  --member "serviceAccount:$DEPLOYER" --role roles/artifactregistry.writer --condition=None >/dev/null
echo "repository $AR_REPO: artifactregistry.writer -> $DEPLOYER_NAME"
for sa in "$API_SA" "$WEB_SA"; do
  gcloud iam service-accounts add-iam-policy-binding "$sa" --project "$PROJECT" \
    --member "serviceAccount:$DEPLOYER" --role roles/iam.serviceAccountUser --condition=None >/dev/null
  echo "$sa: serviceAccountUser -> $DEPLOYER_NAME"
done

echo "== Cloud Run services (placeholder, then service-scoped roles) =="
# Public (allUsers invoker): auth is enforced in the app. The deployer gets run.developer on
# each service only, never project-wide. The workflow deploys real images over the placeholder.
for pair in "smartnutri-api-dev:$API_SA" "smartnutri-web-dev:$WEB_SA"; do
  svc="${pair%%:*}"
  sa="${pair#*:}"
  if gcloud run services describe "$svc" --project "$PROJECT" --region "$REGION" >/dev/null 2>&1; then
    echo "cloud run service $svc: exists"
  else
    gcloud run services create "$svc" --project "$PROJECT" --region "$REGION" \
      --image us-docker.pkg.dev/cloudrun/container/hello --service-account "$sa" \
      --no-allow-unauthenticated >/dev/null
    echo "cloud run service $svc: created (placeholder image)"
  fi
  gcloud run services add-iam-policy-binding "$svc" --project "$PROJECT" --region "$REGION" \
    --member allUsers --role roles/run.invoker --condition=None >/dev/null
  echo "$svc: run.invoker -> allUsers"
  gcloud run services add-iam-policy-binding "$svc" --project "$PROJECT" --region "$REGION" \
    --member "serviceAccount:$DEPLOYER" --role roles/run.developer --condition=None >/dev/null
  echo "$svc: run.developer -> $DEPLOYER_NAME"
done

echo "== Workload Identity Federation =="
if gcloud iam workload-identity-pools describe "$POOL" --project "$PROJECT" --location global >/dev/null 2>&1; then
  echo "pool $POOL: exists"
else
  gcloud iam workload-identity-pools create "$POOL" --project "$PROJECT" --location global \
    --display-name "GitHub Actions" >/dev/null
  echo "pool $POOL: created"
fi

# A deleted provider is soft-deleted for 30 days and keeps its name: undelete it first.
provider_state="$(gcloud iam workload-identity-pools providers describe "$PROVIDER" \
  --project "$PROJECT" --location global --workload-identity-pool "$POOL" --format='value(state)' 2>/dev/null || true)"
if [[ "$provider_state" == "DELETED" ]]; then
  gcloud iam workload-identity-pools providers undelete "$PROVIDER" \
    --project "$PROJECT" --location global --workload-identity-pool "$POOL" >/dev/null
  echo "provider $PROVIDER: undeleted"
fi

# Trust: this repo (by immutable ids, so a renamed or recreated repo cannot match), main branch,
# only the deploy-dev workflow file, only push / manual dispatch events.
PROVIDER_ARGS=(
  --project "$PROJECT" --location global --workload-identity-pool "$POOL"
  --issuer-uri "https://token.actions.githubusercontent.com"
  --attribute-mapping "google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref,attribute.repository_owner=assertion.repository_owner,attribute.repository_id=assertion.repository_id,attribute.repository_owner_id=assertion.repository_owner_id,attribute.workflow_ref=assertion.workflow_ref,attribute.event_name=assertion.event_name"
  --attribute-condition "assertion.repository_id == '$GITHUB_REPO_ID' && assertion.repository_owner_id == '$GITHUB_OWNER_ID' && assertion.ref == 'refs/heads/main' && assertion.workflow_ref == '$GITHUB_REPO/.github/workflows/deploy-dev.yml@refs/heads/main' && (assertion.event_name == 'push' || assertion.event_name == 'workflow_dispatch')"
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
  --member "principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/attribute.repository_id/$GITHUB_REPO_ID" --condition=None >/dev/null
echo "deployer: workloadIdentityUser <- repository id $GITHUB_REPO_ID ($GITHUB_REPO; main + deploy-dev.yml only, via the provider condition)"

echo
echo "Done. Values used by .github/workflows/deploy-dev.yml (not secrets):"
echo "  workload_identity_provider: projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/providers/$PROVIDER"
echo "  service_account:            $DEPLOYER"
