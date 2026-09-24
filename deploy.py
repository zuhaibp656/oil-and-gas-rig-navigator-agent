#!/usr/bin/env python3
"""Top-level deployment entrypoint for Vertex AI Agent Engine (with ADK Playground) & Gemini Enterprise.

Usage:
    uv run python deploy.py
    uv run python deploy.py --project zuhaibp-ai --region us-central1
"""

from scripts.deploy_to_gemini_enterprise import main

if __name__ == "__main__":
    main()
