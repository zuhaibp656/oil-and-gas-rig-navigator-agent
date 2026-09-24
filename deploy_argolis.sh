#!/usr/bin/env bash
# ==============================================================================
# One-Command Argolis Cloud Shell Deployment Script
# Offshore Rig Mobilization & Weather Optimizer (ORMWO)
# Deploys ORMWOAdkApp to Vertex AI Agent Engine (with ADK Playground enabled)
# and registers the agent in Gemini Enterprise (Discovery Engine).
# ==============================================================================
set -euo pipefail

PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null || echo 'zuhaibp-ai')}"
if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  PROJECT_ID="zuhaibp-ai"
fi
REGION="${2:-us-central1}"
GEMINI_APP_ID="${3:-}"

echo "=============================================================================="
echo " Deploying ORMWO Agent to Argolis Project : ${PROJECT_ID}"
echo " Target Vertex AI Region (Playground)     : ${REGION}"
echo "=============================================================================="

# 1. Enable required Google Cloud APIs
gcloud services enable \
  aiplatform.googleapis.com \
  discoveryengine.googleapis.com \
  bigquery.googleapis.com \
  storage.googleapis.com \
  cloudresourcemanager.googleapis.com \
  --project="${PROJECT_ID}"

# 2. Ensure Python dependencies are installed
if command -v uv >/dev/null 2>&1; then
  uv sync
  PYTHON_CMD="uv run python"
else
  python3 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install \
    "google-cloud-aiplatform[agent_engines,adk]>=1.160.0" \
    "google-adk[gcp,otel-gcp]>=2.6.0,<3.0.0" \
    "google-cloud-bigquery>=3.25.0,<4.0.0" \
    "google-cloud-storage>=2.18.0,<4.0.0" \
    "a2a-sdk[http-server]>=1.0,<2" \
    "numpy>=1.26,<3.0" \
    "scipy>=1.14.0" \
    "pillow>=10.0.0"
  PYTHON_CMD=".venv/bin/python"
fi

# 3. Deploy to Vertex AI Agent Engine (with ADK Playground) & Register with Gemini Enterprise
if [[ -n "${GEMINI_APP_ID}" ]]; then
  ${PYTHON_CMD} scripts/deploy_to_gemini_enterprise.py \
    --project "${PROJECT_ID}" \
    --region "${REGION}" \
    --gemini-app-id "${GEMINI_APP_ID}"
else
  ${PYTHON_CMD} scripts/deploy_to_gemini_enterprise.py \
    --project "${PROJECT_ID}" \
    --region "${REGION}"
fi

echo "=============================================================================="
echo " Deployment Complete!"
echo "=============================================================================="
