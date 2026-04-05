"""Pytest configuration."""

import pytest


@pytest.fixture(autouse=True)
def _reset_trainer_client_cache():
    """Clear :func:`get_trainer_client` LRU cache so tests never share a real cluster client.

    Patches replace symbols on modules, but unpatching restores the original cached
    wrapper; without clearing, a prior test can leave a real ``TrainerClient`` in the
    cache and cause flakes or hangs (e.g. follow-on tests that expect mocks).
    """
    from kubeflow_mcp.common.utils import reset_clients

    reset_clients()
    yield
    reset_clients()


@pytest.fixture
def mock_k8s_client():
    """Mock Kubernetes client for testing."""
    return None
