"""Integration tests for the root agent."""

from app.agent import root_agent


def test_agent_configuration():
    assert root_agent.name == "rig_navigator_agent"
    assert len(root_agent.tools) >= 2
    assert root_agent.before_model_callback is not None
    assert root_agent.after_model_callback is not None
    assert root_agent.after_agent_callback is not None
