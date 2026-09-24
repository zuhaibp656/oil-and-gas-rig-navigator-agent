#!/usr/bin/env python3
"""Automated Vertex AI Agent Engine (with ADK Playground) & Gemini Enterprise Deployer.

1. Configures `GOOGLE_GENAI_USE_VERTEXAI=TRUE` and `ORMWO_MODEL=gemini-2.5-flash` BEFORE importing
   `root_agent` and `ORMWOAdkApp`, ensuring cloudpickle serializes the Vertex AI runtime configuration.
2. Ensures GCS staging bucket exists (`gs://<project>-agent-staging`).
3. Deploys (or updates in-place) `ORMWOAdkApp` via `vertexai.agent_engines.create(...)` with
   `google-cloud-aiplatform[agent_engines,adk]>=1.160.0` so the deployed agent has full
   interactive **Playground** access in Google Cloud Console (`agent_framework="google-adk"`).
4. Automatically discovers Gemini Enterprise (Discovery Engine / AgentSpace) apps in the
   Argolis project and registers the deployed Reasoning Engine into Gemini Enterprise chat.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request

import google.auth
from google.auth.transport.requests import Request
import google.oauth2.credentials

os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

_ARGOLIS_ADC_PATH = Path.home() / ".config" / "gcloud" / "argolis_admin_adc.json"
_DEFAULT_ADC_PATH = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"


def get_gcloud_credentials() -> google.oauth2.credentials.Credentials:
    """Create refreshed google.oauth2.credentials.Credentials for Argolis admin."""
    for adc_path in (_ARGOLIS_ADC_PATH, _DEFAULT_ADC_PATH):
        if adc_path.exists():
            try:
                creds = google.oauth2.credentials.Credentials.from_authorized_user_file(
                    str(adc_path),
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
                creds.refresh(Request())
                if creds.token:
                    return creds
            except Exception:
                pass
    gcloud_bin = "/usr/local/google/home/zuhaibp/google-cloud-sdk/bin/gcloud"
    if not os.path.exists(gcloud_bin):
        gcloud_bin = "gcloud"
    out = subprocess.check_output(
        [gcloud_bin, "auth", "print-access-token"],
        text=True,
        stderr=subprocess.DEVNULL,
    )
    return google.oauth2.credentials.Credentials(out.strip())


def get_gcloud_access_token() -> str:
    """Retrieve active OAuth2 token for Argolis."""
    creds = get_gcloud_credentials()
    return str(creds.token)


_ORIG_AUTH_DEFAULT = google.auth.default


def _argolis_auth_default(*args, **kwargs):
    try:
        return get_gcloud_credentials(), os.environ.get("GOOGLE_CLOUD_PROJECT", "zuhaibp-ai")
    except Exception:
        return _ORIG_AUTH_DEFAULT(*args, **kwargs)


google.auth.default = _argolis_auth_default


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
    project_id: str = "zuhaibp-ai",
    region: str = "us-central1",
    staging_bucket: str = "",
    service_account: str | None = None,
) -> str:
    """Deploy or update the ORMWO Root Agent on Vertex AI Agent Engine with ADK Playground enabled."""
    if region == "global":
        region = "us-central1"

    # Force Vertex AI mode before importing the agent module so cloudpickle captures Vertex AI config
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = region
    os.environ["ORMWO_MODEL"] = "gemini-2.5-flash"

    import vertexai
    from vertexai import agent_engines
    from vertexai.preview import reasoning_engines
    from app.integration.agent import ORMWOAdkApp, root_agent

    creds = get_gcloud_credentials()
    bucket_name = staging_bucket or f"{project_id}-agent-staging"
    staging_uri = ensure_staging_bucket(project_id, region, bucket_name)

    vertexai.init(
        project=project_id,
        location=region,
        staging_bucket=staging_uri,
        credentials=creds,
    )

    adk_app = ORMWOAdkApp(
        agent=root_agent,
        enable_tracing=True,
    )

    requirements = [
        "google-cloud-aiplatform[agent_engines,adk]>=1.160.0",
        "google-adk>=2.6.0,<3.0.0",
        "google-genai>=1.0.0",
        "google-cloud-bigquery>=3.25.0,<4.0.0",
        "google-cloud-storage>=2.18.0,<4.0.0",
        "a2a-sdk[http-server]>=1.0,<2",
        "numpy>=1.26,<3.0",
        "scipy>=1.14.0",
        "pillow>=10.0.0",
    ]
    extra_packages = ["app"]
    display_name = "ORMWO - Offshore Rig Mobilization & Weather Optimizer"
    description = (
        "Offshore Rig Mobilization & Weather Optimizer (ORMWO) — 48h Metocean Risk, "
        "Monte Carlo Well Redeployment & Interactive India EEZ Map (ADK Playground & Gemini Enterprise)"
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
            print(f"[UPDATING] Existing Vertex AI Agent Engine in-place: {existing_resource_name}")
            remote_engine = agent_engines.get(existing_resource_name)
            updated = remote_engine.update(
                agent_engine=adk_app,
                requirements=requirements,
                extra_packages=extra_packages,
                display_name=display_name,
                description=description,
            )
            res_name = updated.resource_name
            state_file.write_text(res_name, encoding="utf-8")
            _print_deployment_links(project_id, region, res_name)
            return res_name
        except Exception as exc:
            print(f"[INFO] In-place update skipped ({exc}); creating new Agent Engine instance...")

    print(f"[DEPLOYING] Creating Vertex AI Agent Engine (ADK Playground Enabled) in {project_id} ({region})...")
    try:
        remote_engine = agent_engines.create(
            agent_engine=adk_app,
            requirements=requirements,
            extra_packages=extra_packages,
            display_name=display_name,
            description=description,
        )
    except Exception:
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
        "agent_framework": "google-adk",
        "playground_enabled": True,
        "agent_directory": "app",
        "region": region,
        "project_id": project_id,
        "reasoning_engine_resource_name": res_name,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    _print_deployment_links(project_id, region, res_name)
    return res_name


def _print_deployment_links(project_id: str, region: str, res_name: str) -> None:
    engine_id = res_name.rsplit("/", 1)[-1]
    print("\n" + "=" * 84)
    print(f"[SUCCESS] Deployed ORMWO Agent to Vertex AI Agent Engine!")
    print(f"  • Resource Name   : {res_name}")
    print(
        f"  • ADK Playground  : https://console.cloud.google.com/vertex-ai/agents/agent-engines/"
        f"locations/{region}/agent-engines/{engine_id}/playground?project={project_id}"
    )
    print(
        f"  • Agent Registry  : https://console.cloud.google.com/vertex-ai/agents/agent-engines"
        f"?project={project_id}"
    )
    print("=" * 84 + "\n")


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
            f"Use Resource Name '{reasoning_engine_resource_name}' when adding the ADK agent in Gemini Enterprise UI."
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
    parser = argparse.ArgumentParser(description="Deploy ORMWO Agent to Vertex AI Agent Engine & Gemini Enterprise")
    parser.add_argument("--project", default="zuhaibp-ai", help="GCP Project ID (Argolis, default: zuhaibp-ai)")
    parser.add_argument("--region", default="us-central1", help="Vertex AI Region (default: us-central1 for Playground)")
    parser.add_argument("--staging-bucket", default="", help="GCS Staging Bucket (default: <project>-agent-staging)")
    parser.add_argument("--service-account", default="", help="Custom Service Account email")
    parser.add_argument("--gemini-app-id", default="", help="Optional Gemini Enterprise Engine ID")
    args = parser.parse_args()

    bucket = args.staging_bucket or f"{args.project}-agent-staging"
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
