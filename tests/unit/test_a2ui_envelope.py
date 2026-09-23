"""Unit tests for A2UI v0.9 wire protocol serialization and envelope framing."""

import json
from app.render.a2ui_envelope import (
    A2A_DATA_PART_CLOSE_TAG,
    A2A_DATA_PART_OPEN_TAG,
    A2UI_MIME,
    wrap_a2ui_part,
)
from app.render.a2ui_lifecycle import DEFAULT_GE_CATALOG_ID, build_create_surface


def test_wrap_a2ui_part_frames_correctly():
    """wrap_a2ui_part builds a text/plain envelope tagged with <a2a_datapart_json>."""
    msg = build_create_surface(surface_id="test-surf-123")
    part = wrap_a2ui_part(msg)

    assert part.inline_data is not None
    assert part.inline_data.mime_type == "text/plain"
    assert part.part_metadata == {"mimeType": A2UI_MIME}

    raw_text = part.inline_data.data.decode("utf-8")
    assert raw_text.startswith(A2A_DATA_PART_OPEN_TAG)
    assert raw_text.endswith(A2A_DATA_PART_CLOSE_TAG)

    inner_json = raw_text[len(A2A_DATA_PART_OPEN_TAG) : -len(A2A_DATA_PART_CLOSE_TAG)]
    payload = json.loads(inner_json)

    assert payload["kind"] == "data"
    assert payload["metadata"] == {"mimeType": A2UI_MIME}
    assert payload["data"]["version"] == "v0.9"
    assert payload["data"]["createSurface"]["surfaceId"] == "test-surf-123"
    assert payload["data"]["createSurface"]["catalogId"] == DEFAULT_GE_CATALOG_ID
