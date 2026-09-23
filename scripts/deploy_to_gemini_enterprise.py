#!/usr/bin/env python3
"""Automated Vertex AI Reasoning Engine (Agent Garden) & Gemini Enterprise Deployer.

1. Uses `gcloud auth print-access-token` OAuth2 credentials so deployment works seamlessly
   from both CloudTop and Argolis Cloud Shell.
2. Ensures GCS staging bucket exists (`gs://<project>-ormwo-agent-staging`).
3. Deploys (or updates in-place) the ORMWO ADK Agent on Vertex AI Agent Engine (Reasoning Engine).
4. Automatically discovers all Gemini Enterprise (Discovery Engine / AgentSpace) apps in the
   Argolis project and registers the deployed agent so it appears directly in Gemini Enterprise chat.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request

import google.oauth2.credentials

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def get_gcloud_access_token() -> str:
    """Retrieve active OAuth2 token from gcloud."""
    out = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True)
    return out.strip()


def get_gcloud_credentials() -> google.oauth2.credentials.Credentials:
    """Create google.oauth2.credentials.Credentials from active gcloud session."""
    return google.oauth2.credentials.Credentials(get_gcloud_access_token())


def ensure_staging_bucket(project_id: str, region: str, bucket_name: str) -> str:
    """Create GCS staging bucket if missing."""
    from google.cloud import storage
    from google.cloud.exceptions import Conflict, NotFound

    creds = get_gcloud_credentials()
    clean_name = bucket_name.replace("gs://", "").split("/")[0]
    client = storage.Client(project=project_id, credentials=creds)
    try:
        client.get_bucket(clean_name)
        print(f"[OK] GCS Staging Bucket verified: gs://{clean_name}")
    except NotFound:
        try:
            bucket = client.bucket(clean_name)
            client.create_bucket(bucket, project=project_id, location=region)
            print(f"[CREATED] GCS Staging Bucket: gs://{clean_name} ({region})")
        except Conflict:
            print(f"[OK] GCS Staging Bucket already exists: gs://{clean_name}")
    return f"gs://{clean_name}"


def deploy_to_vertex_agent_engine(
    project_id: str,
    region: str,
    staging_bucket: str,
    service_account: str | None = None,
) -> str:
    """Deploy or update the ORMWO Root Agent on Vertex AI Reasoning Engine."""
    import vertexai
    from vertexai.preview import reasoning_engines
    from app.integration.agent import root_agent

    creds = get_gcloud_credentials()
    staging_uri = ensure_staging_bucket(project_id, region, staging_bucket)
    vertexai.init(
        project=project_id,
        location=region,
        staging_bucket=staging_uri,
        credentials=creds,
    )

    adk_app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )

    requirements = [
        "google-adk[gcp,otel-gcp]>=2.6.0,<3.0.0",
        "google-cloud-aiplatform[agent-engines]>=1.156.0",
        "google-cloud-bigquery>=3.25.0,<4.0.0",
        "google-cloud-storage>=2.18.0,<4.0.0",
        "a2a-sdk[http-server]>=1.0,<2",
        "numpy>=1.26,<3.0",
        "scipy>=1.17.1",
        "pillow>=12.3.0",
    ]
    extra_packages = ["app"]
    display_name = "ORMWO - Offshore Rig Mobilization & Weather Optimizer"
    description = (
        "Offshore Rig Mobilization & Weather Optimizer (ORMWO) — 48h Metocean Risk, "
        "Monte Carlo Well Redeployment & Interactive India EEZ Map for Gemini Enterprise"
    )

    state_file = ROOT_DIR / ".reasoning_engine_id"
    existing_resource_name: str | None = None
    if state_file.exists():
        existing_resource_name = state_file.read_text(encoding="utf-8").strip()

    if not existing_resource_name:
        try:
            for eng in reasoning_engines.ReasoningEngine.list():
                if getattr(eng, "display_name", "") == display_name:
                    existing_resource_name = eng.resource_name
                    break
        except Exception:
            pass

    if existing_resource_name:
        try:
            print(f"[UPDATING] Existing Vertex AI Reasoning Engine: {existing_resource_name}")
            existing_eng = reasoning_engines.ReasoningEngine(existing_resource_name)
            updated = existing_eng.update(
                reasoning_engine=adk_app,
                requirements=requirements,
                extra_packages=extra_packages,
                display_name=display_name,
                description=description,
            )
            res_name = updated.resource_name
            state_file.write_text(res_name, encoding="utf-8")
            print(f"[SUCCESS] Updated Vertex AI Reasoning Engine: {res_name}")
            return res_name
        except Exception as exc:
            print(f"[INFO] In-place update skipped ({exc}); creating fresh Reasoning Engine...")

    print(f"[DEPLOYING] Creating Vertex AI Reasoning Engine in {project_id} ({region})...")
    create_kwargs = {
        "reasoning_engine": adk_app,
        "requirements": requirements,
        "extra_packages": extra_packages,
        "display_name": display_name,
        "description": description,
    }
    if service_account:
        create_kwargs["service_account"] = service_account

    remote_engine = reasoning_engines.ReasoningEngine.create(**create_kwargs)
    res_name = remote_engine.resource_name
    state_file.write_text(res_name, encoding="utf-8")

    meta_path = ROOT_DIR / "deployment_metadata.json"
    meta = {
        "deployment_target": "agent_runtime",
        "is_a2a": True,
        "agent_directory": "app",
        "region": region,
        "project_id": project_id,
        "reasoning_engine_resource_name": res_name,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"[SUCCESS] Deployed Vertex AI Reasoning Engine: {res_name}")
    return res_name


def register_with_gemini_enterprise(
    project_id: str,
    reasoning_engine_resource_name: str,
    gemini_app_id: str | None = None,
    location: str = "global",
) -> None:
    """Discover Gemini Enterprise (Discovery Engine) apps in Argolis and register the ORMWO Agent."""
    token = get_gcloud_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id,
    }

    app_ids: list[str] = []
    if gemini_app_id:
        app_ids.append(f"{location}:{gemini_app_id}")
    else:
        for loc in ["global", "us", "eu"]:
            list_url = (
                f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}"
                f"/locations/{loc}/collections/default_collection/engines"
            )
            req = urllib.request.Request(list_url, headers=headers, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    for eng in data.get("engines", []):
                        eng_name = eng.get("name", "")
                        eng_id = eng_name.rsplit("/", 1)[-1]
                        tag = f"{loc}:{eng_id}"
                        if eng_id and tag not in app_ids:
                            app_ids.append(tag)
            except Exception:
                continue

    if not app_ids:
        print(
            "[INFO] No existing Gemini Enterprise engine auto-discovered via v1alpha list. "
            "You can bind the Reasoning Engine in Gemini Enterprise UI or pass --gemini-app-id."
        )
        return

    for loc_and_id in app_ids:
        loc, eng_id = loc_and_id.split(":", 1)
        reg_url = (
            f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}"
            f"/locations/{loc}/collections/default_collection/engines/{eng_id}"
            f"/assistants/default_assistant/agents"
        )
        payload = {
            "displayName": "ORMWO Rig & Metocean Optimizer",
            "description": (
                "Offshore Rig Mobilization & Weather Optimizer (ORMWO) — Renders interactive "
                "India EEZ Map (20 Rigs, 120 Wells, 48h Storm Cones & Waypoints) and CAG #15117 Audit Logs."
            ),
            "icon": {
                "uri": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/oil_barrel/default/24px.svg"
            },
            "adkAgentDefinition": {
                "toolSettings": {
                    "toolDescription": (
                        "Use ORMWO to query offshore rig telemetry, 48-hour marine weather forecasts, "
                        "Monte Carlo storm evacuation/redeployment trajectories, and India EEZ maps."
                    )
                },
                "provisionedReasoningEngine": {
                    "reasoningEngine": reasoning_engine_resource_name
                },
            },
        }
        req = urllib.request.Request(
            reg_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                res_body = json.loads(resp.read().decode("utf-8"))
                print(
                    f"[SUCCESS] Registered ORMWO Agent into Gemini Enterprise App '{eng_id}' ({loc}): "
                    f"{res_body.get('name', 'OK')}"
                )
        except urllib.error.HTTPError as http_err:
            err_text = http_err.read().decode("utf-8", errors="ignore")
            print(f"[NOTE] Gemini Enterprise App '{eng_id}' ({loc}) response ({http_err.code}): {err_text[:240]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy ORMWO Agent to Vertex AI & Gemini Enterprise")
    parser.add_argument("--project", required=True, help="GCP Project ID (Argolis)")
    parser.add_argument("--region", default="asia-south1", help="Vertex AI Region (default: asia-south1)")
    parser.add_argument("--staging-bucket", default="", help="GCS Staging Bucket (auto-created if omitted)")
    parser.add_argument("--service-account", default="", help="Custom Service Account email")
    parser.add_argument("--gemini-app-id", default="", help="Optional Gemini Enterprise Engine ID")
    args = parser.parse_args()

    bucket = args.staging_bucket or f"{args.project}-ormwo-agent-staging"
    re_name = deploy_to_vertex_agent_engine(
        project_id=args.project,
        region=args.region,
        staging_bucket=bucket,
        service_account=args.service_account or None,
    )
    register_with_gemini_enterprise(
        project_id=args.project,
        reasoning_engine_resource_name=re_name,
        gemini_app_id=args.gemini_app_id or None,
    )


if __name__ == "__main__":
    main()
