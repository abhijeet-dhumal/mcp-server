"""Pytest configuration."""

import pytest


@pytest.fixture
def mock_k8s_client():
    """Mock Kubernetes client for testing."""
    return None
