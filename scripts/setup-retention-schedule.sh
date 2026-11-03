#!/usr/bin/env bash
# Retention Cloud Run Job + daily Cloud Scheduler trigger (02:30 IST) for DEV.
# The job itself (image, env, secrets) is deployed by .github/workflows/deploy-dev.yml; this script
# does the one-time pieces the keyless deployer cannot: create the job shell, grant the deployer
# service-level rights on it, create the scheduler identity, and the schedule.
#
# You (USER) run it from the repo root with owner credentials, in this order:
#   bash scripts/setup-retention-schedule.sh setup     # job shell + IAM (before the first deploy)
#   ... merge to main; deploy-dev deploys the real image into the job ...
#   bash scripts/setup-retention-schedule.sh dry-run   # runs the job with --dry-run; logs counts only
#   bash scripts/setup-retention-schedule.sh schedule  # creates the 02:30 IST schedule (after a clean dry run)
# Safe to re-run. Needs the voice-answers bucket to exist first (docs/SETUP_ACCOUNTS.md section 2.8).
set -euo pipefail

export CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri
PROJECT=smartnutri-513518
REGION=asia-south1
JOB=smartnutri-retention-dev
API_SA="smartnutri-api-dev@$PROJECT.iam.gserviceaccount.com"
DEPLOYER="github-deployer@$PROJECT.iam.gserviceaccount.com"
SCHEDULER_SA_NAME=smartnutri-scheduler-dev
SCHEDULER_SA="$SCHEDULER_SA_NAME@$PROJECT.iam.gserviceaccount.com"
SCHEDULE_NAME=smartnutri-retention-dev-daily

active_project="$(gcloud config get-value project 2>/dev/null)"
if [[ "$active_project" != "$PROJECT" ]]; then
  echo "gcloud config 'smartnutri' points at '$active_project', expected '$PROJECT'" >&2
  exit 1
fi

cmd="${1:-}"
case "$cmd" in
  setup)
    gcloud services enable cloudscheduler.googleapis.com run.googleapis.com --project "$PROJECT"
    if gcloud run jobs describe "$JOB" --project "$PROJECT" --region "$REGION" >/dev/null 2>&1; then
      echo "cloud run job $JOB: exists"
    else
      # Placeholder image; the deploy workflow replaces it with the API image and the real command.
      gcloud run jobs create "$JOB" --project "$PROJECT" --region "$REGION" --quiet \
        --image us-docker.pkg.dev/cloudrun/container/job --service-account "$API_SA" >/dev/null
      echo "cloud run job $JOB: created (placeholder image)"
    fi
    gcloud run jobs add-iam-policy-binding "$JOB" --project "$PROJECT" --region "$REGION" \
      --member "serviceAccount:$DEPLOYER" --role roles/run.developer --condition=None >/dev/null
    echo "$JOB: run.developer -> github-deployer (this job only, never project-wide)"
    if ! gcloud iam service-accounts describe "$SCHEDULER_SA" --project "$PROJECT" >/dev/null 2>&1; then
      gcloud iam service-accounts create "$SCHEDULER_SA_NAME" --project "$PROJECT" \
        --display-name "SmartNutri scheduler (dev, runs the retention job only)" >/dev/null
      echo "service account $SCHEDULER_SA_NAME: created"
      sleep 15 # IAM is eventually consistent
    fi
    gcloud run jobs add-iam-policy-binding "$JOB" --project "$PROJECT" --region "$REGION" \
      --member "serviceAccount:$SCHEDULER_SA" --role roles/run.invoker --condition=None >/dev/null
    echo "$JOB: run.invoker -> $SCHEDULER_SA_NAME"
    echo "Next: merge to main so deploy-dev deploys the image, then run: $0 dry-run"
    ;;
  dry-run)
    # Overrides the job args for this one execution only. Counts only are logged, never paths.
    gcloud run jobs execute "$JOB" --project "$PROJECT" --region "$REGION" --wait \
      --args "-m,app.jobs.retention,--dry-run"
    echo "Check the execution logs for photos_deleted / voice_deleted / scans_nulled counts."
    echo "On a new project expect all zero. Then run: $0 schedule"
    ;;
  schedule)
    URI="https://run.googleapis.com/v2/projects/$PROJECT/locations/$REGION/jobs/$JOB:run"
    ARGS=(--project "$PROJECT" --location "$REGION" --schedule "30 2 * * *" --time-zone "Asia/Kolkata"
      --uri "$URI" --http-method POST
      --oauth-service-account-email "$SCHEDULER_SA"
      --oauth-token-scope "https://www.googleapis.com/auth/cloud-platform")
    if gcloud scheduler jobs describe "$SCHEDULE_NAME" --project "$PROJECT" --location "$REGION" >/dev/null 2>&1; then
      gcloud scheduler jobs update http "$SCHEDULE_NAME" "${ARGS[@]}" >/dev/null
      echo "schedule $SCHEDULE_NAME: updated"
    else
      gcloud scheduler jobs create http "$SCHEDULE_NAME" "${ARGS[@]}" >/dev/null
      echo "schedule $SCHEDULE_NAME: created (02:30 Asia/Kolkata daily)"
    fi
    ;;
  *)
    echo "usage: bash scripts/setup-retention-schedule.sh setup|dry-run|schedule" >&2
    exit 2
    ;;
esac
