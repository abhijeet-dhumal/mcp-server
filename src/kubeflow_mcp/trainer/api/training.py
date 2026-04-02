"""Training tools for LLM fine-tuning and custom training.

Maps to TrainerClient.train() (SDK 0.4.0) with different configurations:
- fine_tune() → HuggingFace model fine-tuning with BuiltinTrainer
- run_custom_training() → User-provided training script with CustomTrainer
- run_container_training() → Pre-built container image with CustomTrainerContainer
"""

from typing import Any

from kubeflow_mcp.common.constants import ErrorCode
from kubeflow_mcp.common.types import PreviewResponse, ToolError, ToolResponse
from kubeflow_mcp.common.utils import get_trainer_client
from kubeflow_mcp.core.security import is_safe_python_code, validate_k8s_name


def fine_tune(
    model: str,
    dataset: str,
    runtime: str = "torch-tune",
    hf_token: str | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Submits a fine-tuning job for a HuggingFace model.

    Creates a training job using TorchTune with the specified runtime.
    Use list_runtimes() first to see available runtimes.

    Args:
        model: HuggingFace model path (e.g., "meta-llama/Llama-3.2-1B").
        dataset: HuggingFace dataset path (e.g., "imdatta0/ultrachat_1k").
        runtime: ClusterTrainingRuntime name (default "torch-tune").
        hf_token: HuggingFace token for gated models (optional).
        confirmed: Set True to execute. Returns preview if False.

    Returns:
        Preview: config summary if confirmed=False
        Success: {job_name, status, message}

    Note:
        Requires a compatible ClusterTrainingRuntime in the cluster.
    """
    try:
        from kubeflow.trainer.types.types import (
            HuggingFaceDatasetInitializer,
            HuggingFaceModelInitializer,
            Initializer,
        )

        config = {
            "model": model,
            "dataset": dataset,
            "runtime": runtime,
            "hf_token": "***" if hf_token else None,
        }

        if not confirmed:
            return PreviewResponse(
                message="Review config and set confirmed=True to submit job",
                config=config,
            ).model_dump()

        # Build initializer
        initializer = Initializer(
            model=HuggingFaceModelInitializer(
                storage_uri=model,
                access_token=hf_token,
            ),
            dataset=HuggingFaceDatasetInitializer(
                storage_uri=dataset,
                access_token=hf_token,
            ),
        )

        client = get_trainer_client()
        job_name = client.train(
            runtime=runtime,
            initializer=initializer,
        )

        return ToolResponse(
            data={
                "job_name": job_name,
                "status": "Created",
                "message": f"Training job '{job_name}' submitted successfully",
            }
        ).model_dump()

    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()


def run_custom_training(
    script: str,
    name: str | None = None,
    num_nodes: int = 1,
    gpu_per_node: int = 1,
    packages: list[str] | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Submits a training job with custom Python script.

    Executes user-provided training code in a distributed environment.
    Script is validated for security before execution.

    Args:
        script: Python training script content (validated for safety).
        name: Job name. Auto-generated if not provided.
        num_nodes: Number of training nodes (1-8, default 1).
        gpu_per_node: GPUs per node (1-8, default 1).
        packages: Additional pip packages to install (e.g., ["transformers"]).
        confirmed: Set True to execute. Returns preview if False.

    Returns:
        Preview: config summary if confirmed=False
        Success: {job_name, status, message}

    Note:
        Script cannot import os, subprocess, or use eval/exec.
    """
    try:
        from kubeflow.trainer.types.types import CustomTrainer

        safe, reason = is_safe_python_code(script)
        if not safe:
            return ToolError(
                error=f"Script validation failed: {reason}",
                error_code=ErrorCode.VALIDATION_ERROR,
            ).model_dump()

        if name:
            err = validate_k8s_name(name)
            if err:
                return err.model_dump()

        config = {
            "script": script[:200] + "..." if len(script) > 200 else script,
            "name": name,
            "num_nodes": num_nodes,
            "gpu_per_node": gpu_per_node,
            "packages": packages or [],
        }

        if not confirmed:
            return PreviewResponse(
                message="Review config and set confirmed=True to submit job",
                config=config,
            ).model_dump()

        # Create a function that executes the script
        def train_func():
            exec(script)  # noqa: S102

        trainer = CustomTrainer(
            func=train_func,
            packages_to_install=packages,
            num_nodes=num_nodes,
            resources_per_node={"gpu": gpu_per_node} if gpu_per_node > 0 else None,
        )

        client = get_trainer_client()
        job_name = client.train(trainer=trainer)

        return ToolResponse(
            data={
                "job_name": job_name,
                "status": "Created",
                "message": f"Custom training job '{job_name}' submitted",
            }
        ).model_dump()

    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()


def run_container_training(
    image: str,
    command: list[str] | None = None,
    num_nodes: int = 1,
    gpu_per_node: int = 1,
    env: dict[str, str] | None = None,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Submits a training job using a pre-built container image.

    Runs distributed training with a custom Docker/OCI image.
    Use when you have a pre-packaged training environment.

    Args:
        image: Container image (e.g., "pytorch/pytorch:2.0-cuda11.8").
        command: Container command (e.g., ["python", "train.py"]).
        num_nodes: Number of training nodes (1-8, default 1).
        gpu_per_node: GPUs per node (1-8, default 1).
        env: Environment variables as key-value pairs.
        confirmed: Set True to execute. Returns preview if False.

    Returns:
        Preview: config summary if confirmed=False
        Success: {job_name, status, message}

    Note:
        Image must be accessible from the cluster (public or with imagePullSecrets).
    """
    try:
        from kubeflow.trainer.types.types import CustomTrainerContainer

        config = {
            "image": image,
            "command": command,
            "num_nodes": num_nodes,
            "gpu_per_node": gpu_per_node,
            "env": env,
        }

        if not confirmed:
            return PreviewResponse(
                message="Review config and set confirmed=True to submit job",
                config=config,
            ).model_dump()

        # Note: SDK 0.4.0 CustomTrainerContainer doesn't support custom command
        # The command should be baked into the container image's ENTRYPOINT/CMD
        trainer = CustomTrainerContainer(
            image=image,
            num_nodes=num_nodes,
            resources_per_node={"gpu": gpu_per_node} if gpu_per_node > 0 else None,
            env=env,
        )

        client = get_trainer_client()
        job_name = client.train(trainer=trainer)

        return ToolResponse(
            data={
                "job_name": job_name,
                "status": "Created",
                "message": f"Container training job '{job_name}' submitted",
            }
        ).model_dump()

    except Exception as e:
        return ToolError(
            error=str(e),
            error_code=ErrorCode.SDK_ERROR,
        ).model_dump()
