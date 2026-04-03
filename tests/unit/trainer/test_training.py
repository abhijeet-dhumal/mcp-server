"""Tests for training tools (fine_tune, run_custom_training, run_container_training)."""

from unittest.mock import MagicMock, patch

from kubeflow_mcp.trainer.api.training import (
    fine_tune,
    run_container_training,
    run_custom_training,
)


class TestFineTune:
    """Tests for fine_tune() tool."""

    def test_preview_mode(self):
        """Test preview mode returns config without submitting."""
        result = fine_tune(
            model="hf://google/gemma-2b",
            dataset="hf://tatsu-lab/alpaca",
            confirmed=False,
        )

        assert result["status"] == "preview"
        assert "config" in result
        assert result["config"]["model"] == "hf://google/gemma-2b"
        assert result["config"]["dataset"] == "hf://tatsu-lab/alpaca"

    def test_preview_includes_all_params(self):
        """Test preview includes all training parameters."""
        result = fine_tune(
            model="hf://meta-llama/Llama-3.2-1B",
            dataset="hf://squad",
            batch_size=8,
            epochs=3,
            num_nodes=2,
            lora_rank=16,
            lora_alpha=32,
            confirmed=False,
        )

        config = result["config"]
        assert config["batch_size"] == 8
        assert config["epochs"] == 3
        assert config["num_nodes"] == 2
        assert config["lora_rank"] == 16
        assert config["lora_alpha"] == 32

    def test_preview_with_runtime_patches(self):
        """Test preview includes runtime patch options."""
        result = fine_tune(
            model="hf://google/gemma-2b",
            dataset="hf://tatsu-lab/alpaca",
            node_selector={"node-type": "gpu"},
            tolerations=[{"key": "nvidia.com/gpu", "operator": "Exists"}],
            env=[{"name": "DEBUG", "value": "1"}],
            confirmed=False,
        )

        config = result["config"]
        assert config["node_selector"] == {"node-type": "gpu"}
        assert config["tolerations"] == [{"key": "nvidia.com/gpu", "operator": "Exists"}]
        assert config["env"] == [{"name": "DEBUG", "value": "1"}]

    def test_preview_masks_hf_token(self):
        """Test HF token is masked in preview."""
        result = fine_tune(
            model="hf://meta-llama/Llama-3.2-1B",
            dataset="hf://squad",
            hf_token="hf_secret_token_12345",
            confirmed=False,
        )

        assert result["config"]["hf_token"] == "***"

    @patch("kubeflow_mcp.trainer.api.training._SDK_AVAILABLE", False)
    def test_sdk_not_available(self):
        """Test error when SDK is not installed."""
        result = fine_tune(
            model="hf://google/gemma-2b",
            dataset="hf://tatsu-lab/alpaca",
            confirmed=True,
        )

        assert result["success"] is False
        assert "SDK not available" in result["error"]

    @patch("kubeflow_mcp.trainer.api.training._SDK_AVAILABLE", True)
    @patch("kubeflow_mcp.trainer.api.training.get_trainer_client")
    @patch("kubeflow_mcp.trainer.api.training.BuiltinTrainer")
    @patch("kubeflow_mcp.trainer.api.training.Initializer")
    def test_submit_builtin_trainer(
        self, mock_initializer, mock_trainer, mock_get_client
    ):
        """Test successful job submission with BuiltinTrainer."""
        mock_client = MagicMock()
        mock_client.train.return_value = "trainjob-abc123"
        mock_get_client.return_value = mock_client

        result = fine_tune(
            model="hf://google/gemma-2b",
            dataset="hf://tatsu-lab/alpaca",
            runtime="torch-tune",
            confirmed=True,
        )

        assert result["success"] is True
        assert result["data"]["job_name"] == "trainjob-abc123"
        assert result["data"]["status"] == "Created"
        mock_client.train.assert_called_once()

    @patch("kubeflow_mcp.trainer.api.training._SDK_AVAILABLE", True)
    @patch("kubeflow_mcp.trainer.api.training.get_trainer_client")
    @patch("kubeflow_mcp.trainer.api.training.CustomTrainer")
    def test_submit_custom_trainer_fallback(self, mock_trainer, mock_get_client):
        """Test fallback to CustomTrainer for non-torchtune runtimes."""
        mock_client = MagicMock()
        mock_client.train.return_value = "trainjob-xyz789"
        mock_get_client.return_value = mock_client

        result = fine_tune(
            model="hf://google/gemma-2b",
            dataset="hf://tatsu-lab/alpaca",
            runtime="torch-distributed",  # Not in hf_compatible_runtimes
            confirmed=True,
        )

        assert result["success"] is True
        assert result["data"]["job_name"] == "trainjob-xyz789"

    @patch("kubeflow_mcp.trainer.api.training._SDK_AVAILABLE", True)
    @patch("kubeflow_mcp.trainer.api.training.get_trainer_client")
    def test_submit_handles_api_error(self, mock_get_client):
        """Test error handling for K8s API errors."""
        mock_client = MagicMock()
        mock_client.train.side_effect = Exception("Quota exceeded")
        mock_get_client.return_value = mock_client

        result = fine_tune(
            model="hf://google/gemma-2b",
            dataset="hf://tatsu-lab/alpaca",
            runtime="torch-tune",
            confirmed=True,
        )

        assert result["success"] is False
        assert "Quota exceeded" in result["error"]


class TestRunCustomTraining:
    """Tests for run_custom_training() tool."""

    def test_preview_mode(self):
        """Test preview mode returns config without submitting."""
        script = "print('hello world')"
        result = run_custom_training(
            script=script,
            num_nodes=2,
            gpu_per_node=4,
            confirmed=False,
        )

        assert result["status"] == "preview"
        assert result["config"]["num_nodes"] == 2
        assert result["config"]["gpu_per_node"] == 4

    def test_script_truncated_in_preview(self):
        """Test long scripts are truncated in preview."""
        long_script = "x = 1\n" * 100  # Long script
        result = run_custom_training(
            script=long_script,
            confirmed=False,
        )

        assert len(result["config"]["script"]) <= 203  # 200 + "..."

    def test_rejects_dangerous_import_os(self):
        """Test rejection of dangerous import os."""
        script = "import os\nprint(os.getcwd())"
        result = run_custom_training(
            script=script,
            confirmed=True,
        )

        assert result["success"] is False
        assert "validation failed" in result["error"].lower()

    def test_rejects_dangerous_import_subprocess(self):
        """Test rejection of subprocess import."""
        script = "import subprocess\nsubprocess.run(['ls'])"
        result = run_custom_training(
            script=script,
            confirmed=True,
        )

        assert result["success"] is False

    def test_rejects_eval(self):
        """Test rejection of eval()."""
        script = "eval('print(1)')"
        result = run_custom_training(
            script=script,
            confirmed=True,
        )

        assert result["success"] is False

    def test_rejects_exec(self):
        """Test rejection of exec()."""
        script = "exec('x = 1')"
        result = run_custom_training(
            script=script,
            confirmed=True,
        )

        assert result["success"] is False

    def test_accepts_safe_script(self):
        """Test acceptance of safe Python script."""
        script = """
import torch
import torch.distributed as dist

def train():
    print("Training...")
    model = torch.nn.Linear(10, 10)
    return model

train()
"""
        result = run_custom_training(
            script=script,
            confirmed=False,  # Just validate, don't submit
        )

        assert result["status"] == "preview"

    def test_validates_job_name(self):
        """Test K8s name validation."""
        script = "print('hello')"
        result = run_custom_training(
            script=script,
            name="INVALID_NAME",  # Uppercase not allowed
            confirmed=True,
        )

        assert result["success"] is False
        assert "validation" in result["error"].lower() or "name" in result["error"].lower()

    def test_accepts_valid_job_name(self):
        """Test valid K8s name is accepted."""
        script = "print('hello')"
        result = run_custom_training(
            script=script,
            name="my-training-job",
            confirmed=False,
        )

        assert result["status"] == "preview"
        assert result["config"]["name"] == "my-training-job"

    @patch("kubeflow_mcp.trainer.api.training._SDK_AVAILABLE", False)
    def test_sdk_not_available(self):
        """Test error when SDK is not installed."""
        result = run_custom_training(
            script="print('hello')",
            confirmed=True,
        )

        assert result["success"] is False
        assert "SDK not available" in result["error"]

    @patch("kubeflow_mcp.trainer.api.training._SDK_AVAILABLE", True)
    @patch("kubeflow_mcp.trainer.api.training.get_trainer_client")
    @patch("kubeflow_mcp.trainer.api.training.CustomTrainer")
    def test_submit_success(self, mock_trainer, mock_get_client):
        """Test successful job submission."""
        mock_client = MagicMock()
        mock_client.train.return_value = "custom-job-123"
        mock_get_client.return_value = mock_client

        script = "print('training')"
        result = run_custom_training(
            script=script,
            packages=["torch", "transformers"],
            confirmed=True,
        )

        assert result["success"] is True
        assert result["data"]["job_name"] == "custom-job-123"


class TestRunContainerTraining:
    """Tests for run_container_training() tool."""

    def test_preview_mode(self):
        """Test preview mode returns config without submitting."""
        result = run_container_training(
            image="pytorch/pytorch:2.0-cuda11.8",
            num_nodes=2,
            gpu_per_node=4,
            confirmed=False,
        )

        assert result["status"] == "preview"
        assert result["config"]["image"] == "pytorch/pytorch:2.0-cuda11.8"
        assert result["config"]["num_nodes"] == 2
        assert result["config"]["gpu_per_node"] == 4

    def test_preview_with_env(self):
        """Test preview includes environment variables."""
        result = run_container_training(
            image="myorg/trainer:v1",
            env={"BATCH_SIZE": "32", "LR": "0.001"},
            confirmed=False,
        )

        assert result["config"]["env"] == {"BATCH_SIZE": "32", "LR": "0.001"}

    def test_preview_with_volumes(self):
        """Test preview includes volume configuration."""
        volumes = [{"name": "data", "persistentVolumeClaim": {"claimName": "my-pvc"}}]
        volume_mounts = [{"name": "data", "mountPath": "/data"}]

        result = run_container_training(
            image="pytorch/pytorch:2.0",
            volumes=volumes,
            volume_mounts=volume_mounts,
            confirmed=False,
        )

        assert result["config"]["volumes"] == volumes
        assert result["config"]["volume_mounts"] == volume_mounts

    def test_preview_with_node_selector(self):
        """Test preview includes node selector."""
        result = run_container_training(
            image="pytorch/pytorch:2.0",
            node_selector={"nvidia.com/gpu.product": "A100"},
            tolerations=[{"key": "gpu", "operator": "Exists"}],
            confirmed=False,
        )

        assert result["config"]["node_selector"] == {"nvidia.com/gpu.product": "A100"}
        assert result["config"]["tolerations"] == [{"key": "gpu", "operator": "Exists"}]

    @patch("kubeflow_mcp.trainer.api.training._SDK_AVAILABLE", False)
    def test_sdk_not_available(self):
        """Test error when SDK is not installed."""
        result = run_container_training(
            image="pytorch/pytorch:2.0",
            confirmed=True,
        )

        assert result["success"] is False
        assert "SDK not available" in result["error"]

    @patch("kubeflow_mcp.trainer.api.training._SDK_AVAILABLE", True)
    @patch("kubeflow_mcp.trainer.api.training.get_trainer_client")
    @patch("kubeflow_mcp.trainer.api.training.CustomTrainerContainer")
    def test_submit_success(self, mock_container, mock_get_client):
        """Test successful container job submission."""
        mock_client = MagicMock()
        mock_client.train.return_value = "container-job-456"
        mock_get_client.return_value = mock_client

        result = run_container_training(
            image="ghcr.io/myorg/trainer:v1",
            num_nodes=2,
            gpu_per_node=4,
            confirmed=True,
        )

        assert result["success"] is True
        assert result["data"]["job_name"] == "container-job-456"
        assert result["data"]["status"] == "Created"

    @patch("kubeflow_mcp.trainer.api.training._SDK_AVAILABLE", True)
    @patch("kubeflow_mcp.trainer.api.training.get_trainer_client")
    def test_submit_handles_error(self, mock_get_client):
        """Test error handling for submission failures."""
        mock_client = MagicMock()
        mock_client.train.side_effect = Exception("Image pull failed")
        mock_get_client.return_value = mock_client

        result = run_container_training(
            image="invalid/image:notfound",
            confirmed=True,
        )

        assert result["success"] is False
        assert "Image pull failed" in result["error"]

    def test_cpu_only_training(self):
        """Test CPU-only training configuration."""
        result = run_container_training(
            image="python:3.10",
            gpu_per_node=0,  # No GPUs
            confirmed=False,
        )

        assert result["config"]["gpu_per_node"] == 0
