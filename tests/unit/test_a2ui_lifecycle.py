"""Unit tests for A2UI v0.9 lifecycle messages."""

from app.contracts import A2uiCatalogVersion
from app.render.a2ui_lifecycle import (
    build_create_surface,
    build_delete_surface,
    build_update_components,
    build_update_data_model,
)


def test_build_create_surface():
    msg = build_create_surface("s1")
    assert msg.message_type == "createSurface"
    assert msg.surface_id == "s1"
    assert "catalogId" in msg.payload


def test_build_update_data_model_uses_value():
    """Verify updateDataModel uses payload key 'value', NOT 'data'."""
    spec = {"$schema": "https://vega.github.io/schema/vega-lite/v5.json"}
    msg = build_update_data_model("s1", value={"spec": spec})
    assert msg.message_type == "updateDataModel"
    assert "value" in msg.payload
    assert "data" not in msg.payload
    assert msg.payload["value"]["spec"] == spec


def test_build_update_components():
    comps = [{"id": "root", "component": "Card", "child": "c1"}]
    msg = build_update_components("s1", components=comps)
    assert msg.message_type == "updateComponents"
    assert msg.payload["components"] == comps


def test_build_delete_surface():
    msg = build_delete_surface("s1")
    assert msg.message_type == "deleteSurface"
