"""Tests for persona policy."""

import pytest

from kubeflow_mcp.core.policy import get_allowed_tools


def test_readonly_persona():
    tools = get_allowed_tools("readonly")
    assert tools is not None
    assert "list_training_jobs" in tools
    assert "fine_tune" not in tools


def test_data_scientist_inherits_readonly():
    tools = get_allowed_tools("data-scientist")
    assert tools is not None
    assert "list_training_jobs" in tools
    assert "fine_tune" in tools
    assert "suspend_training_job" not in tools


def test_ml_engineer_inherits_data_scientist():
    tools = get_allowed_tools("ml-engineer")
    assert tools is not None
    assert "list_training_jobs" in tools
    assert "fine_tune" in tools
    assert "suspend_training_job" in tools


def test_platform_admin_has_all():
    tools = get_allowed_tools("platform-admin")
    assert tools is None


def test_unknown_persona_raises():
    with pytest.raises(ValueError, match="Unknown persona"):
        get_allowed_tools("unknown")
