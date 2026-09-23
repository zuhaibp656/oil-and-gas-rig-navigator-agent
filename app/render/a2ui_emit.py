"""Bridge module for building and emitting A2UI v0.9 surfaces in Gemini Enterprise chat.

Out: list of types.Part ready to attach to the model's response.
Rule: Deterministic Python execution only. The LLM never touches these messages directly.
"""

from __future__ import annotations

import json
import logging
from google.genai import types

try:
    from app.contracts import FleetSummary, RigUnit
    from app.render.a2ui_envelope import wrap_a2ui_part
    from app.render.a2ui_lifecycle import (
        build_create_surface,
        build_update_components,
        build_update_data_model,
    )
    from app.render.rig_fleet_card import build_rig_fleet_components
    from app.render.rig_map_vega import SPEC_KEY, build_rig_fleet_map_spec
except ImportError:
    from contracts import FleetSummary, RigUnit
    from render.a2ui_envelope import wrap_a2ui_part
    from render.a2ui_lifecycle import (
        build_create_surface,
        build_update_components,
        build_update_data_model,
    )
    from render.rig_fleet_card import build_rig_fleet_components
    from render.rig_map_vega import SPEC_KEY, build_rig_fleet_map_spec

logger = logging.getLogger(__name__)

# Payload limits
_MAX_PAYLOAD_BYTES: int = 400 * 1024


def build_rig_fleet_surface(summary: FleetSummary, surface_id: str) -> list[types.Part]:
    """Build the three lifecycle Parts that render the Rig Fleet Map & Status Card in chat."""
    spec = build_rig_fleet_map_spec(summary)
    components = build_rig_fleet_components(summary)

    messages = [
        build_create_surface(surface_id=surface_id),
        build_update_data_model(surface_id=surface_id, value={SPEC_KEY: spec}),
        build_update_components(surface_id=surface_id, components=components),
    ]

    parts = [wrap_a2ui_part(msg) for msg in messages]
    logger.info("build_rig_fleet_surface: surface=%s parts=%d", surface_id, len(parts))
    return parts
