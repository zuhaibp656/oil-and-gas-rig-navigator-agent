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
_SA_KEY_PATH = Path.home() / ".config" / "gcloud" / "zuhaibp_ai_deployer_sa.json"
_DEFAULT_ADC_PATH = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"


def _bootstrap_permanent_access(creds: google.oauth2.credentials.Credentials, project_id: str = "zuhaibp-ai") -> None:
    """Grant user:zuhaibp@google.com project roles on zuhaibp-ai so CloudTop never hits 1-hour Argolis RAPT expiry."""
    try:
        url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}:getIamPolicy"
        req = urllib.request.Request(
            url,
            data=b"{}",
            headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            policy = json.loads(resp.read().decode("utf-8"))
        bindings = policy.get("bindings", [])
        member = "user:zuhaibp@google.com"
        needed_roles = [
            "roles/aiplatform.admin",
            "roles/storage.admin",
            "roles/discoveryengine.admin",
            "roles/iam.serviceAccountUser",
        ]
        changed = False
        for role in needed_roles:
            found = False
            for b in bindings:
                if b.get("role") == role:
                    found = True
                    if member not in b.get("members", []):
                        b.setdefault("members", []).append(member)
                        changed = True
            if not found:
                bindings.append({"role": role, "members": [member]})
                changed = True
        if changed:
            set_url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}:setIamPolicy"
            set_req = urllib.request.Request(
                set_url,
                data=json.dumps({"policy": policy}).encode("utf-8"),
                headers={"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(set_req, timeout=5)
            print("[OK] Granted permanent CloudTop IAM access (zuhaibp@google.com) on zuhaibp-ai!")
    except Exception:
        pass


def get_gcloud_credentials() -> google.oauth2.credentials.Credentials:
    """Create refreshed google.oauth2.credentials.Credentials for Argolis / zuhaibp-ai."""
    if _SA_KEY_PATH.exists():
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file(
            str(_SA_KEY_PATH),
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        creds.refresh(Request())
        return creds

    if _ARGOLIS_ADC_PATH.exists():
        try:
            creds = google.oauth2.credentials.Credentials.from_authorized_user_file(
                str(_ARGOLIS_ADC_PATH),
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            creds.refresh(Request())
            if creds.token:
                _bootstrap_permanent_access(creds)
                return creds
        except Exception:
            pass

    if _DEFAULT_ADC_PATH.exists():
        try:
            creds = google.oauth2.credentials.Credentials.from_authorized_user_file(
                str(_DEFAULT_ADC_PATH),
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
        candidate = state_file.read_text(encoding="utf-8").strip()
        try:
            agent_engines.get(candidate)
            existing_resource_name = candidate
        except Exception:
            existing_resource_name = None

    if not existing_resource_name:
        try:
            for eng in agent_engines.list():
                if getattr(eng, "display_name", "") == display_name or "ORMWO" in getattr(eng, "display_name", ""):
                    existing_resource_name = eng.resource_name
                    state_file.write_text(existing_resource_name, encoding="utf-8")
                    break
        except Exception:
            pass

    env_vars = {
        "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
        "ORMWO_MODEL": "gemini-2.5-flash",
    }

    if existing_resource_name:
        print(f"[UPDATING] Existing Vertex AI Agent Engine in-place (strictly same deployment): {existing_resource_name}")
        remote_engine = agent_engines.get(existing_resource_name)
        updated = remote_engine.update(
            agent_engine=adk_app,
            requirements=requirements,
            extra_packages=extra_packages,
            display_name=display_name,
            description=description,
            env_vars=env_vars,
        )
        res_name = updated.resource_name
        state_file.write_text(res_name, encoding="utf-8")
        _print_deployment_links(project_id, region, res_name)
        return res_name

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

    icon_path = ROOT_DIR / "assets" / "ormwo_agent_icon.png"
    b64_icon = ""
    if icon_path.exists():
        import base64
        b64_icon = base64.b64encode(icon_path.read_bytes()).decode("ascii")

    starter_prompts = [
        {
            "text": "Run the Google DeepMind GenCast and GraphCast 48-hour metocean forecast across the Indian EEZ. Which storm zones are active and which nearby safe wells should our threatened rigs [1] through [6] relocate to?"
        },
        {
            "text": "Explain what will happen to our rigs in Mumbai High inside Red Circle 1 (STORM-ARB-01) over the next 48 hours and give me the exact relocation route and INR Crore savings for Rigs [1] to [4]."
        },
        {
            "text": "Evaluate RIG-OFFSHORE-04 (Sagar Samrat) and RIG-OFFSHORE-05 (Dhirubhai Deepwater KG1) and run the Monte Carlo preventative relocation simulation."
        },
    ]

    for loc_and_id in app_ids:
        loc, eng_id = loc_and_id.split(":", 1)
        agents_base_url = (
            f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}"
            f"/locations/{loc}/collections/default_collection/engines/{eng_id}"
            f"/assistants/default_assistant/agents"
        )
        payload = {
            "displayName": "ORMWO Rig & Metocean Optimizer",
            "description": (
                "Offshore Rig Mobilization & Weather Optimizer (ORMWO) — Google DeepMind GenCast & GraphCast "
                "48h Storm Forecasting, Safe-Well Relocation & India EEZ Command Map."
            ),
            "icon": (
                {"content": b64_icon}
                if b64_icon
                else {"uri": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/oil_barrel/default/24px.svg"}
            ),
            "starterPrompts": starter_prompts,
            "adkAgentDefinition": {
                "toolSettings": {
                    "toolDescription": (
                        "Use ORMWO to run Google DeepMind GenCast and GraphCast 48h metocean forecasts, "
                        "identify storm-locked wells to avoid, and compute zero-downtime safe well relocations across India EEZ."
                    )
                },
                "provisionedReasoningEngine": {
                    "reasoningEngine": reasoning_engine_resource_name
                },
            },
        }

        # Check if ORMWO agent already exists in this Gemini Enterprise engine so we PATCH in-place
        existing_agent_name: str | None = None
        try:
            list_req = urllib.request.Request(agents_base_url, headers=headers, method="GET")
            with urllib.request.urlopen(list_req, timeout=15) as l_resp:
                l_data = json.loads(l_resp.read().decode("utf-8"))
                for ag in l_data.get("agents", []):
                    if "ORMWO" in ag.get("displayName", ""):
                        existing_agent_name = ag.get("name")
                        break
        except Exception:
            existing_agent_name = None

        if existing_agent_name:
            patch_url = (
                f"https://discoveryengine.googleapis.com/v1alpha/{existing_agent_name}"
                "?updateMask=displayName,description,icon,starterPrompts,adkAgentDefinition"
            )
            payload["name"] = existing_agent_name
            req = urllib.request.Request(
                patch_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="PATCH",
            )
        else:
            req = urllib.request.Request(
                agents_base_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                res_body = json.loads(resp.read().decode("utf-8"))
                print(
                    f"[SUCCESS] Synced ORMWO Agent (with custom PNG icon & starter prompts) in Gemini Enterprise App '{eng_id}' ({loc}): "
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
