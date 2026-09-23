#!/usr/bin/env bash
# ==============================================================================
# ORMWO (Offshore Rig Mobilization & Weather Optimizer)
# Turnkey Argolis Cloud Shell One-Command Deployment Script
#
# What this script does automatically in your Argolis Cloud Shell:
#   1. Detects your active GCP Project ID & Project Number (or uses $PROJECT_ID).
#   2. Enables all required APIs (Vertex AI, Discovery Engine / Gemini Enterprise,
#      BigQuery, Cloud Storage, Cloud Run, IAM).
#   3. Creates the dedicated Service Account (ormwo-agent-sa@<PROJECT>.iam.gserviceaccount.com)
#      and binds all required IAM roles to both the SA and Vertex AI / Gemini Enterprise
#      Service Agents.
#   4. Creates the GCS Staging Bucket and the BigQuery CAG Report #15117 Governance
#      Audit dataset & table (`ongc_rig_ops.governance_audit_log`).
#   5. Installs `uv` & `google-agents-cli`, runs unit tests, deploys the agent to
#      Vertex AI Agent Runtime (Reasoning Engine / Agent Garden), and registers it
#      into your Argolis Gemini Enterprise App.
#   6. Prints direct clickable Web Console URLs for Gemini Enterprise, Vertex AI
#      Agent Builder, and Cloud Shell Web Preview.
# ==============================================================================

set -euo pipefail

echo "=============================================================================="
echo "  ORMWO — Offshore Rig Mobilization & Weather Optimizer (Argolis Deployer)   "
echo "=============================================================================="

# 1. Auto-detect GCP Project ID & Region
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}"
if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  read -rp "Enter your Argolis GCP Project ID: " PROJECT_ID
  gcloud config set project "${PROJECT_ID}"
fi

REGION="${REGION:-asia-south1}"
GEMINI_APP_ID="${GEMINI_APP_ID:-}"
PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
SA_NAME="ormwo-agent-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
STAGING_BUCKET="${PROJECT_ID}-ormwo-agent-staging"

echo "-> Target Project ID     : ${PROJECT_ID} (Number: ${PROJECT_NUMBER})"
echo "-> Target Vertex Region  : ${REGION}"
echo "-> Agent Service Account : ${SA_EMAIL}"
echo "-> GCS Staging Bucket    : gs://${STAGING_BUCKET}"

# 2. Enable Required Google Cloud APIs
echo ""
echo "[1/6] Enabling required Google Cloud & Gemini Enterprise APIs..."
gcloud services enable \
  aiplatform.googleapis.com \
  discoveryengine.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com \
  iam.googleapis.com \
  cloudresourcemanager.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  --project="${PROJECT_ID}"

# 3. Create Dedicated Service Account & Grant IAM Permissions
echo ""
echo "[2/6] Provisioning Service Account & IAM permissions..."
if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SA_NAME}" \
    --display-name="ORMWO Offshore Rig & Weather Optimizer Service Account" \
    --project="${PROJECT_ID}"
  echo "Created Service Account: ${SA_EMAIL}"
else
  echo "Service Account already exists: ${SA_EMAIL}"
fi

ROLES=(
  "roles/aiplatform.admin"
  "roles/aiplatform.user"
  "roles/discoveryengine.admin"
  "roles/bigquery.dataEditor"
  "roles/bigquery.jobUser"
  "roles/storage.admin"
  "roles/logging.logWriter"
)

for ROLE in "${ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" \
    --condition=None \
    --quiet >/dev/null
done

# Trigger & authorize Vertex AI Reasoning Engine & Discovery Engine Service Agents
gcloud beta services identity create --service=aiplatform.googleapis.com --project="${PROJECT_ID}" 2>/dev/null || true
RE_SERVICE_AGENT="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
AI_SERVICE_AGENT="service-${PROJECT_NUMBER}@gcp-sa-aiplatform.iam.gserviceaccount.com"

for AGENT_SA in "${RE_SERVICE_AGENT}" "${AI_SERVICE_AGENT}"; do
  for ROLE in "roles/aiplatform.user" "roles/storage.objectAdmin" "roles/bigquery.dataEditor" "roles/bigquery.jobUser"; do
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
      --member="serviceAccount:${AGENT_SA}" \
      --role="${ROLE}" \
      --condition=None \
      --quiet >/dev/null 2>&1 || true
  done
done

# 4. Create GCS Staging Bucket & BigQuery CAG #15117 Governance Dataset/Table
echo ""
echo "[3/6] Creating GCS Staging Bucket & BigQuery CAG Governance Audit Table..."
if ! gcloud storage buckets describe "gs://${STAGING_BUCKET}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${STAGING_BUCKET}" --project="${PROJECT_ID}" --location="${REGION}"
fi

bq --project_id="${PROJECT_ID}" --location="${REGION}" mk --dataset \
  --description="ONGC / India EEZ Offshore Rig Mobilization & CAG Report 15117 Audit Dataset" \
  "${PROJECT_ID}:ongc_rig_ops" 2>/dev/null || true

bq --project_id="${PROJECT_ID}" query --use_legacy_sql=false "
CREATE TABLE IF NOT EXISTS \`${PROJECT_ID}.ongc_rig_ops.governance_audit_log\` (
  audit_reference_id STRING,
  recorded_at_utc STRING,
  cag_compliance_ref STRING,
  event_type STRING,
  payload_sha256 STRING,
  payload JSON
);" 2>/dev/null || true

export ORMWO_BQ_AUDIT_TABLE="${PROJECT_ID}.ongc_rig_ops.governance_audit_log"

# 5. Install uv & google-agents-cli, Sync Dependencies, and Run Unit Tests
echo ""
echo "[4/6] Installing uv & google-agents-cli and verifying unit tests..."
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi

uv sync --default-index https://pypi.org/simple
uv run pytest tests/unit -v

# 6. Deploy to Vertex AI Agent Runtime (Reasoning Engine) & Register in Gemini Enterprise
echo ""
echo "[5/6] Deploying ORMWO Agent to Vertex AI Agent Runtime & Gemini Enterprise..."
if command -v agents-cli >/dev/null 2>&1; then
  agents-cli deploy --project "${PROJECT_ID}" || true
fi

uv run python scripts/deploy_to_gemini_enterprise.py \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --staging-bucket "${STAGING_BUCKET}" \
  --service-account "${SA_EMAIL}" \
  --gemini-app-id "${GEMINI_APP_ID}"

echo ""
echo "=============================================================================="
echo "  [6/6] DEPLOYMENT COMPLETE — DIRECT ACCESS LINKS                            "
echo "=============================================================================="
echo "1. Gemini Enterprise / AgentSpace Console:"
echo "   https://console.cloud.google.com/gen-app-builder/engines?project=${PROJECT_ID}"
echo ""
echo "2. Vertex AI Agent Engine (Reasoning Engine / Agent Garden):"
echo "   https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=${PROJECT_ID}"
echo ""
echo "3. BigQuery CAG #15117 Governance Audit Table:"
echo "   https://console.cloud.google.com/bigquery?project=${PROJECT_ID}&ws=!1m5!1m4!4m3!1s${PROJECT_ID}!2songc_rig_ops!3sgovernance_audit_log"
echo ""
echo "4. Optional — Launch Local A2A Web Playground in Cloud Shell (Port 8080):"
echo "   uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8080"
echo "   (Then click 'Web Preview' -> 'Preview on port 8080' in Cloud Shell)"
echo "=============================================================================="
