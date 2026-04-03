"""Tests for lifecycle tools (SDK + K8s direct).

Tests delete_training_job (SDK), suspend_training_job (K8s), resume_training_job (K8s).
"""

from unittest.mock import MagicMock, patch

import pytest

from kubeflow_mcp.trainer.api.lifecycle import (
    delete_training_job,
    resume_training_job,
    suspend_training_job,
)


class TestDeleteTrainingJob:
    """Tests for delete_training_job() - uses SDK."""

    @patch("kubeflow_mcp.trainer.api.lifecycle.get_trainer_client")
    def test_delete_success(self, mock_get_client):
        """Test successful job deletion."""
        mock_client = MagicMock()
        mock_client.delete_job.return_value = None
        mock_get_client.return_value = mock_client

        result = delete_training_job(name="my-job")

        assert result["success"] is True
        assert result["data"]["job"] == "my-job"
        assert result["data"]["deleted"] is True
        mock_client.delete_job.assert_called_once_with(name="my-job")

    @patch("kubeflow_mcp.trainer.api.lifecycle.get_trainer_client")
    def test_delete_not_found(self, mock_get_client):
        """Test deleting non-existent job."""
        mock_client = MagicMock()
        mock_client.delete_job.side_effect = RuntimeError("TrainJob 'missing' not found")
        mock_get_client.return_value = mock_client

        result = delete_training_job(name="missing")

        assert result["success"] is False
        assert "not found" in result["error"].lower()
        assert result["error_code"] == "RESOURCE_NOT_FOUND"

    @patch("kubeflow_mcp.trainer.api.lifecycle.get_trainer_client")
    def test_delete_sdk_error(self, mock_get_client):
        """Test SDK error handling."""
        mock_client = MagicMock()
        mock_client.delete_job.side_effect = RuntimeError("Permission denied")
        mock_get_client.return_value = mock_client

        result = delete_training_job(name="my-job")

        assert result["success"] is False
        assert "Permission denied" in result["error"]


class TestSuspendTrainingJob:
    """Tests for suspend_training_job() - uses K8s API directly."""

    @patch("kubernetes.config.load_config")
    @patch("kubernetes.client.CustomObjectsApi")
    def test_suspend_success(self, mock_custom_api, mock_load_config):
        """Test successful job suspension."""
        mock_api = MagicMock()
        mock_custom_api.return_value = mock_api
        mock_api.patch_namespaced_custom_object.return_value = {"status": "patched"}

        result = suspend_training_job(name="my-job")

        assert result["success"] is True
        assert result["data"]["job"] == "my-job"
        assert result["data"]["suspended"] is True
        assert result["data"]["namespace"] == "default"

        # Verify correct K8s API call
        mock_api.patch_namespaced_custom_object.assert_called_once_with(
            group="kubeflow.org",
            version="v1",
            namespace="default",
            plural="trainjobs",
            name="my-job",
            body={"spec": {"suspend": True}},
        )

    @patch("kubernetes.config.load_config")
    @patch("kubernetes.client.CustomObjectsApi")
    def test_suspend_custom_namespace(self, mock_custom_api, mock_load_config):
        """Test suspension in custom namespace."""
        mock_api = MagicMock()
        mock_custom_api.return_value = mock_api

        result = suspend_training_job(name="my-job", namespace="ml-team")

        assert result["success"] is True
        assert result["data"]["namespace"] == "ml-team"
        mock_api.patch_namespaced_custom_object.assert_called_once()
        call_kwargs = mock_api.patch_namespaced_custom_object.call_args[1]
        assert call_kwargs["namespace"] == "ml-team"

    @patch("kubernetes.config.load_config")
    @patch("kubernetes.client.CustomObjectsApi")
    def test_suspend_not_found(self, mock_custom_api, mock_load_config):
        """Test suspending non-existent job."""
        mock_api = MagicMock()
        mock_custom_api.return_value = mock_api
        mock_api.patch_namespaced_custom_object.side_effect = Exception(
            "trainjobs.kubeflow.org 'missing' not found"
        )

        result = suspend_training_job(name="missing")

        assert result["success"] is False
        assert "not found" in result["error"].lower()
        assert result["error_code"] == "RESOURCE_NOT_FOUND"

    @patch("kubernetes.config.load_config")
    @patch("kubernetes.client.CustomObjectsApi")
    def test_suspend_k8s_error(self, mock_custom_api, mock_load_config):
        """Test K8s API error handling."""
        mock_api = MagicMock()
        mock_custom_api.return_value = mock_api
        mock_api.patch_namespaced_custom_object.side_effect = Exception("Forbidden")

        result = suspend_training_job(name="my-job")

        assert result["success"] is False
        assert "Forbidden" in result["error"]

    @patch("kubernetes.config.load_config")
    @patch("kubernetes.client.CustomObjectsApi")
    def test_suspend_verifies_patch_body(self, mock_custom_api, mock_load_config):
        """Test that suspend patch body is correct."""
        mock_api = MagicMock()
        mock_custom_api.return_value = mock_api

        suspend_training_job(name="my-job")

        call_kwargs = mock_api.patch_namespaced_custom_object.call_args[1]
        assert call_kwargs["body"] == {"spec": {"suspend": True}}
        assert call_kwargs["group"] == "kubeflow.org"
        assert call_kwargs["version"] == "v1"
        assert call_kwargs["plural"] == "trainjobs"


class TestResumeTrainingJob:
    """Tests for resume_training_job() - uses K8s API directly."""

    @patch("kubernetes.config.load_config")
    @patch("kubernetes.client.CustomObjectsApi")
    def test_resume_success(self, mock_custom_api, mock_load_config):
        """Test successful job resumption."""
        mock_api = MagicMock()
        mock_custom_api.return_value = mock_api
        mock_api.patch_namespaced_custom_object.return_value = {"status": "patched"}

        result = resume_training_job(name="my-job")

        assert result["success"] is True
        assert result["data"]["job"] == "my-job"
        assert result["data"]["resumed"] is True

        # Verify correct K8s API call - suspend: False to resume
        mock_api.patch_namespaced_custom_object.assert_called_once_with(
            group="kubeflow.org",
            version="v1",
            namespace="default",
            plural="trainjobs",
            name="my-job",
            body={"spec": {"suspend": False}},
        )

    @patch("kubernetes.config.load_config")
    @patch("kubernetes.client.CustomObjectsApi")
    def test_resume_custom_namespace(self, mock_custom_api, mock_load_config):
        """Test resumption in custom namespace."""
        mock_api = MagicMock()
        mock_custom_api.return_value = mock_api

        result = resume_training_job(name="my-job", namespace="prod")

        assert result["success"] is True
        assert result["data"]["namespace"] == "prod"

    @patch("kubernetes.config.load_config")
    @patch("kubernetes.client.CustomObjectsApi")
    def test_resume_not_found(self, mock_custom_api, mock_load_config):
        """Test resuming non-existent job."""
        mock_api = MagicMock()
        mock_custom_api.return_value = mock_api
        mock_api.patch_namespaced_custom_object.side_effect = Exception(
            "trainjobs.kubeflow.org 'missing' not found"
        )

        result = resume_training_job(name="missing")

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @patch("kubernetes.config.load_config")
    @patch("kubernetes.client.CustomObjectsApi")
    def test_resume_verifies_patch_body(self, mock_custom_api, mock_load_config):
        """Test that resume patch body is correct (suspend: False)."""
        mock_api = MagicMock()
        mock_custom_api.return_value = mock_api

        resume_training_job(name="my-job")

        call_kwargs = mock_api.patch_namespaced_custom_object.call_args[1]
        assert call_kwargs["body"] == {"spec": {"suspend": False}}


class TestK8sApiContract:
    """Tests that verify K8s API contract for TrainJob CRD."""

    @patch("kubernetes.config.load_config")
    @patch("kubernetes.client.CustomObjectsApi")
    def test_trainjob_crd_group(self, mock_custom_api, mock_load_config):
        """Verify TrainJob CRD group is kubeflow.org."""
        mock_api = MagicMock()
        mock_custom_api.return_value = mock_api

        suspend_training_job(name="test")

        call_kwargs = mock_api.patch_namespaced_custom_object.call_args[1]
        assert call_kwargs["group"] == "kubeflow.org"

    @patch("kubernetes.config.load_config")
    @patch("kubernetes.client.CustomObjectsApi")
    def test_trainjob_crd_version(self, mock_custom_api, mock_load_config):
        """Verify TrainJob CRD version is v1."""
        mock_api = MagicMock()
        mock_custom_api.return_value = mock_api

        suspend_training_job(name="test")

        call_kwargs = mock_api.patch_namespaced_custom_object.call_args[1]
        assert call_kwargs["version"] == "v1"

    @patch("kubernetes.config.load_config")
    @patch("kubernetes.client.CustomObjectsApi")
    def test_trainjob_crd_plural(self, mock_custom_api, mock_load_config):
        """Verify TrainJob CRD plural is trainjobs."""
        mock_api = MagicMock()
        mock_custom_api.return_value = mock_api

        suspend_training_job(name="test")

        call_kwargs = mock_api.patch_namespaced_custom_object.call_args[1]
        assert call_kwargs["plural"] == "trainjobs"
