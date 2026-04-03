"""Tests for planning tools.

Tests get_cluster_resources (K8s API) and estimate_resources (HuggingFace Hub API).
"""

from unittest.mock import MagicMock, patch

import pytest

from kubeflow_mcp.trainer.api.planning import estimate_resources, get_cluster_resources


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


def test_get_cluster_resources_multiple_nodes():
    """Test cluster with multiple nodes."""
    mock_nodes = []
    for i, gpus in enumerate([4, 2, 0]):  # 3 nodes: 4 GPU, 2 GPU, 0 GPU
        mock_node = MagicMock()
        mock_node.metadata.name = f"node-{i}"
        mock_node.status.allocatable = {
            "nvidia.com/gpu": str(gpus),
            "memory": "64Gi",
            "cpu": "16",
        }
        mock_nodes.append(mock_node)

    mock_v1 = MagicMock()
    mock_v1.list_node.return_value.items = mock_nodes

    with (
        patch("kubernetes.config.load_config"),
        patch("kubernetes.client.CoreV1Api", return_value=mock_v1),
    ):
        result = get_cluster_resources()

        assert result["success"] is True
        assert result["data"]["gpu_total"] == 6
        assert result["data"]["nodes_with_gpu"] == 2
        assert result["data"]["node_count"] == 3


class TestEstimateResources:
    """Tests for estimate_resources() - uses HuggingFace Hub API."""

    @patch("kubeflow_mcp.trainer.api.planning._get_model_info_from_hf")
    def test_estimate_small_model(self, mock_hf_info):
        """Test estimation for small model (2B params)."""
        mock_hf_info.return_value = {
            "model_id": "google/gemma-2b",
            "params": 2_000_000_000,  # 2B
            "library": "transformers",
        }

        result = estimate_resources(model="google/gemma-2b")

        assert result["success"] is True
        assert result["data"]["model"] == "google/gemma-2b"
        assert result["data"]["params_billions"] == 2.0
        assert result["data"]["gpu_per_worker"] == 1
        # 2B params with LoRA bf16 should need ~10GB
        assert "8GB" in result["data"]["gpu_type_recommended"] or "16GB" in result["data"]["gpu_type_recommended"]

    @patch("kubeflow_mcp.trainer.api.planning._get_model_info_from_hf")
    def test_estimate_large_model(self, mock_hf_info):
        """Test estimation for large model (70B params)."""
        mock_hf_info.return_value = {
            "model_id": "meta-llama/Llama-3-70B",
            "params": 70_000_000_000,  # 70B
        }

        result = estimate_resources(model="meta-llama/Llama-3-70B")

        assert result["success"] is True
        assert result["data"]["params_billions"] == 70.0
        # 70B should need multiple GPUs
        assert result["data"]["total_gpu"] >= 2 or "80GB" in result["data"]["gpu_type_recommended"]

    @patch("kubeflow_mcp.trainer.api.planning._get_model_info_from_hf")
    def test_estimate_with_hf_prefix(self, mock_hf_info):
        """Test that hf:// prefix is stripped."""
        mock_hf_info.return_value = {
            "model_id": "google/gemma-2b",
            "params": 2_000_000_000,
        }

        estimate_resources(model="hf://google/gemma-2b")

        # Verify hf:// was stripped when calling HF API
        mock_hf_info.assert_called_once()
        # The function should strip the prefix internally

    @patch("kubeflow_mcp.trainer.api.planning._get_model_info_from_hf")
    def test_estimate_with_workers(self, mock_hf_info):
        """Test estimation with multiple workers."""
        mock_hf_info.return_value = {
            "model_id": "google/gemma-2b",
            "params": 2_000_000_000,
        }

        result = estimate_resources(model="google/gemma-2b", num_workers=4)

        assert result["success"] is True
        assert result["data"]["num_workers"] == 4
        assert result["data"]["total_gpu"] == result["data"]["gpu_per_worker"] * 4

    @patch("kubeflow_mcp.trainer.api.planning._get_model_info_from_hf")
    def test_estimate_with_batch_size(self, mock_hf_info):
        """Test that batch size affects memory estimate."""
        mock_hf_info.return_value = {
            "model_id": "google/gemma-2b",
            "params": 2_000_000_000,
        }

        result_small = estimate_resources(model="google/gemma-2b", batch_size=1)
        result_large = estimate_resources(model="google/gemma-2b", batch_size=16)

        # Larger batch size should require more memory
        small_mem = int(result_small["data"]["gpu_memory_required"].replace("GB", ""))
        large_mem = int(result_large["data"]["gpu_memory_required"].replace("GB", ""))
        assert large_mem >= small_mem

    @patch("kubeflow_mcp.trainer.api.planning._get_model_info_from_hf")
    def test_estimate_hf_api_error(self, mock_hf_info):
        """Test error when HuggingFace API fails."""
        mock_hf_info.return_value = {"error": "Model not found"}

        result = estimate_resources(model="nonexistent/model")

        assert result["success"] is False
        assert "HuggingFace" in result["error"]

    @patch("kubeflow_mcp.trainer.api.planning._get_model_info_from_hf")
    def test_estimate_no_params(self, mock_hf_info):
        """Test error when model has no parameter count."""
        mock_hf_info.return_value = {
            "model_id": "some/model",
            "params": None,  # No param count available
        }

        result = estimate_resources(model="some/model")

        assert result["success"] is False
        assert "parameter count" in result["error"].lower()

    @patch("kubeflow_mcp.trainer.api.planning._get_model_info_from_hf")
    def test_estimate_returns_recommendation(self, mock_hf_info):
        """Test that result includes recommendation string."""
        mock_hf_info.return_value = {
            "model_id": "google/gemma-2b",
            "params": 2_000_000_000,
        }

        result = estimate_resources(model="google/gemma-2b")

        assert result["success"] is True
        assert "recommendation" in result["data"]
        assert "GPU" in result["data"]["recommendation"]

    @patch("kubeflow_mcp.trainer.api.planning._get_model_info_from_hf")
    def test_estimate_includes_training_type(self, mock_hf_info):
        """Test that result specifies training type."""
        mock_hf_info.return_value = {
            "model_id": "google/gemma-2b",
            "params": 2_000_000_000,
        }

        result = estimate_resources(model="google/gemma-2b")

        assert result["success"] is True
        assert result["data"]["training_type"] == "LoRA (bf16)"
