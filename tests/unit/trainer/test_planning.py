"""Tests for planning tools."""

from unittest.mock import MagicMock, patch

from kubeflow_mcp.trainer.api.planning import get_cluster_resources


def test_get_cluster_resources_success():
    """Test successful cluster resource retrieval."""
    mock_node = MagicMock()
    mock_node.metadata.name = "node-1"
    mock_node.status.allocatable = {
        "nvidia.com/gpu": "2",
        "memory": "64Gi",
        "cpu": "16",
    }

    mock_v1 = MagicMock()
    mock_v1.list_node.return_value.items = [mock_node]

    with (
        patch("kubernetes.config.load_config"),
        patch("kubernetes.client.CoreV1Api", return_value=mock_v1),
    ):
        result = get_cluster_resources()

        assert result["success"] is True
        assert result["data"]["gpu_total"] == 2
        assert result["data"]["nodes_with_gpu"] == 1
        assert result["data"]["node_count"] == 1


def test_get_cluster_resources_no_gpus():
    """Test cluster with no GPUs."""
    mock_node = MagicMock()
    mock_node.metadata.name = "cpu-node"
    mock_node.status.allocatable = {"memory": "32Gi", "cpu": "8"}

    mock_v1 = MagicMock()
    mock_v1.list_node.return_value.items = [mock_node]

    with (
        patch("kubernetes.config.load_config"),
        patch("kubernetes.client.CoreV1Api", return_value=mock_v1),
    ):
        result = get_cluster_resources()

        assert result["success"] is True
        assert result["data"]["gpu_total"] == 0
        assert result["data"]["nodes_with_gpu"] == 0


def test_get_cluster_resources_error():
    """Test error handling when K8s is unavailable."""
    with patch(
        "kubernetes.config.load_config",
        side_effect=Exception("No cluster"),
    ):
        result = get_cluster_resources()

        assert result["success"] is False
        assert "No cluster" in result["error"]
        assert result["error_code"] == "KUBERNETES_ERROR"
